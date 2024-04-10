import json

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.filters import UserFilter
from tgbot.keyboards import start_bot_keyboard, get_filters_keyboard


async def user_start(message: Message):
    await message.reply("Бот запущен", reply_markup=(await start_bot_keyboard()))

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


async def get_filters(message: Message):
    filters = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(filters)))


def register_user(dp: Dispatcher):
    dp.message.register(user_start, Command('start'), UserFilter())
    dp.message.register(get_filters, UserFilter(), lambda message: message.text == 'Фильтры')
