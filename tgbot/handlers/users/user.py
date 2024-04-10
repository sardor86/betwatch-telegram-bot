import json
import asyncio

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.filters import UserFilter
from tgbot.keyboards import start_bot_keyboard, get_filters_keyboard, run_bot_keyboard


async def check_matches(old_matches_list: list, new_matches_list: list) -> dict | None:
    result: dict = {
        'old_matches': [],
        'new_matches': []
    }

    for new_match in new_matches_list:
        if new_match['name'] in [old_match['name'] for old_match in old_matches_list]:
            result['old_matches'].append(new_match)
            continue
        result['new_matches'].append(new_match)

    return result


async def get_old_data(data: dict, old_dates: list) -> dict:
    for old_date in old_dates:
        if old_date['name'] == data['name']:
            return old_date


async def send_message(message: Message, match: dict):
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
        await asyncio.sleep(15)
        if json.loads(await message.bot.redis.get(f'bot-{message.from_user.id}')) == 'stop':
            break

        filters = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
        await message.bot.parser.get_matches(online_matches=filters['online_matches'],
                                             pre_matches=filters['pre_matches'])

        old_matches_list = json.loads(await message.bot.redis.get(f'parser-{message.from_user.id}'))
        new_matches_list = [(await message.bot.parser.get_match_info(match)) for match in message.bot.parser.matches]

        matches_list = await check_matches(old_matches_list, new_matches_list)

        for new_matches in matches_list['new_matches']:
            await send_message(message, new_matches)

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

        await message.bot.redis.set(f'parser-{message.from_user.id}', json.dumps(new_matches_list))


async def user_start(message: Message):
    await message.reply('Что бы запустить бота нажмите запустить', reply_markup=(await start_bot_keyboard()))


async def bot_start(message: Message):
    await message.reply("Бот запущен", reply_markup=(await run_bot_keyboard()))

    if not (await message.bot.redis.get(f'filter-{message.from_user.id}')):
        filters = {
            'online_matches': False,
            'pre_matches': False,
            'from_price': 0,
            'to_price': 99999,
            'from_percentage': 0,
            'to_percentage': 100,
            'from_coefficient': 0,
            'to_coefficient': 99999,
            'from_time': 0,
            'to_time': 150,
            'up_from_percentage': 0,
            'up_to_percentage': 100,
            'block_list': []
        }

        await message.bot.redis.set(
            f'filter-{message.from_user.id}',
            json.dumps(filters)
        )
    await message.bot.redis.set(
        f'bot-{message.from_user.id}', json.dumps('working')
    )

    await message.bot.redis.set(f'parser-{message.from_user.id}', json.dumps(list([])))
    await parser(message)


async def stop_parser(message: Message):
    await message.bot.redis.set(
        f'bot-{message.from_user.id}', json.dumps('stop')
    )
    await message.reply('бот остановлен', reply_markup=(await start_bot_keyboard()))


async def get_filters(message: Message):
    filters = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(filters)))


def register_user(dp: Dispatcher):
    dp.message.register(user_start, Command('start'), UserFilter())
    dp.message.register(bot_start, UserFilter(), lambda message: message.text == 'Запустить')
    dp.message.register(stop_parser, UserFilter(), lambda message: message.text == 'Приостановить бота')
    dp.message.register(get_filters, UserFilter(), lambda message: message.text == 'Фильтры')
