import json
import asyncio
import logging

from aiogram.types import Message
from aiogram.exceptions import TelegramNetworkError

logger = logging.getLogger(__name__)


async def sort_matches(old_matches_list: list, new_matches_list: list) -> dict | None:
    logger.info('sort old and new matches')
    result: dict = {
        'old_matches': [],
        'new_matches': []
    }

    for new_match in new_matches_list:
        if not new_matches_list[new_match]['runners']:
            continue
        if str(new_match) in old_matches_list:
            result['old_matches'].append(new_matches_list[new_match])
            continue
        result['new_matches'].append(new_matches_list[new_match])
    return result


async def get_old_data(data: dict, old_datas: list) -> dict | None:
    logger.info('get old data')
    for old_data in old_datas:
        if old_data['name'] == data['name']:
            return old_data


async def send_message(message: Message, match: dict):
    logger.info('send match info message')
    if len(match['runners']) == 0:
        return

    try:
        message_result = (f'{match["match"]}\n'
                          f'type: {match["type"]}\n')

        if match['type'] == 'live':
            message_result += f'🕐{match["time"]} мин\n'
            message_result += f'⚽{match["score"]}\n'
        else:
            message_result += f'🕐{match["time"]}\n'

        for match_runner in match['runners']:
            message_result += (f'⭕{match_runner["name"]}: \n'
                               f'💰{match_runner["price"]} '
                               f'📈{match_runner["coefficient"]} '
                               f'💯{match_runner["percentage"]}\n')
            if 'change_percent' in match_runner:
                message_result = message_result[:-1]
                message_result += f'🔥{match_runner["change_percent"]}\n'
    except KeyError:
        return

    try:
        await message.bot.send_message(message.chat.id, message_result)
    except TelegramNetworkError:
        return


async def parser(message: Message):
    while True:
        await asyncio.sleep(60)

        logger.info('check is parser working')
        if json.loads(await message.bot.redis.get(f'bot-{message.from_user.id}')) == 'stop':
            break

        logger.info('get all matches')
        await message.bot.parser.get_all_matches()

        logger.info('get old and new matches info')
        old_matches_list = json.loads(await message.bot.redis.get(f'parser-{message.from_user.id}'))
        new_matches_list = message.bot.parser.matches

        logger.info('filter matches')
        matches_list = await sort_matches(old_matches_list, new_matches_list)

        logger.info('send new matches')
        for new_matches in matches_list['new_matches']:
            await send_message(message, new_matches)

        logger.info('check and send old matches')
        filters = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
        for match in matches_list['old_matches']:
            old_match = old_matches_list[str(match['id'])]
            result_runners = []
            for runner in match['runners']:
                old_runner = await get_old_data(runner, old_match['runners'])
                if old_runner:
                    change_percent = runner['percentage'] - old_runner['percentage']
                    if filters['up_from_percentage'] <= change_percent <= filters['up_to_percentage']:
                        runner['change_percent'] = change_percent
                        result_runners.append(runner)
                else:
                    result_runners.append(runner)
            result_match = match
            result_match['runners'] = result_runners
            await send_message(message, result_match)
        logger.info('save new matches list to redis')
        await message.bot.redis.set(f'parser-{message.from_user.id}', json.dumps(new_matches_list))
