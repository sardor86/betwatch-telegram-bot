import json
import asyncio
import logging

from aiogram.types import Message

logger = logging.getLogger(__name__)


async def filter_matches(old_matches_list: list, new_matches_list: list) -> dict | None:
    logger.info('filter old and new matches')
    result: dict = {
        'old_matches': [],
        'new_matches': []
    }

    for new_match in new_matches_list:
        if not new_match['runners']:
            continue

        if new_match['name'] in [old_match['name'] for old_match in old_matches_list]:
            result['old_matches'].append(new_match)
            continue
        result['new_matches'].append(new_match)

    return result


async def get_old_data(data: dict, old_dates: list) -> dict:
    logger.info('get old data')
    for old_date in old_dates:
        if old_date['name'] == data['name']:
            return old_date


async def send_message(message: Message, match: dict):
    logger.info('send match info message')
    if len(match['runners']) == 0:
        return

    try:
        message_result = (f'{match["name"]}\n'
                          f'type: {match["type"]}\n')

        if match['type'] == 'live':
            message_result += f'🕐{match["time"]} мин\n'
            message_result += f'⚽{match["score"]}\n'
        else:
            message_result += f'🕐{match["time"]}\n'

        for match_runner in match['runners']:
            message_result += (f'{match_runner["name"]}: \n'
                               f'💰{match_runner["price"]} '
                               f'📈{match_runner["coefficient"]} '
                               f'💯{match_runner["percentage"]}\n')
    except KeyError:
        return

    await message.bot.send_message(message.chat.id, message_result)


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
        new_matches_list = [(await message.bot.parser.get_match_info(match)) for match in message.bot.parser.matches]

        logger.info('filter matches')
        matches_list = await filter_matches(old_matches_list, new_matches_list)

        logger.info('send new matches')
        for new_matches in matches_list['new_matches']:
            await send_message(message, new_matches)

        logger.info('check and send old matches')
        for match in matches_list['old_matches']:
            old_match = await get_old_data(match, old_matches_list)
            for runner in match['runners']:
                old_runner = await get_old_data(runner, old_match['runners'])
                message_match = match.copy()
                message_match['runners'] = list([runner])
                if not old_runner:
                    try:
                        if runner['price'] == old_runner['price']:
                            continue
                        if runner['percentage'] == old_runner['percentage']:
                            continue
                        if runner['coefficient'] == old_runner['coefficient']:
                            continue
                    except TypeError:
                        continue

                    await send_message(message, message_match)

                else:
                    await send_message(message, message_match)

        logger.info('save new matches list to redis')
        await message.bot.redis.set(f'parser-{message.from_user.id}', json.dumps(new_matches_list))
