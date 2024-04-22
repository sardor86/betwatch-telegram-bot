import json
import logging

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.filters import UserFilter
from tgbot.keyboards import start_bot_keyboard, get_filters_keyboard, run_bot_keyboard
from .send_matches import parser

logger = logging.getLogger(__name__)


async def user_start(message: Message):
    logger.info('command /start has called')
    await message.reply('Что бы запустить бота нажмите запустить', reply_markup=(await start_bot_keyboard()))


async def bot_start(message: Message):
    logger.info('bot is working')
    await message.reply("Бот запущен", reply_markup=(await run_bot_keyboard()))

    logger.info('creating filters')
    filters = {
        'online_matches': False,
        'pre_matches': False,
        'from_price': 0,
        'to_price': 99999,
        'from_percentage': 0,
        'to_percentage': 100,
        'from_coefficient': 0,
        'to_coefficient': 99999,
        'from_time_1': 0,
        'to_time_1': 45,
        'from_time_2': 45,
        'to_time_2': 90,
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
    logger.info('stopping parser')
    await message.bot.redis.set(
        f'bot-{message.from_user.id}', json.dumps('stop')
    )
    await message.reply('бот остановлен', reply_markup=(await start_bot_keyboard()))


async def get_filters(message: Message):
    logger.info('get filters')
    filters = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(filters)))


def register_user(dp: Dispatcher):
    logger.info('register main user handler')
    dp.message.register(user_start, Command('start'), UserFilter())
    dp.message.register(bot_start, UserFilter(), lambda message: message.text == 'Запустить')
    dp.message.register(stop_parser, UserFilter(), lambda message: message.text == 'Приостановить бота')
    dp.message.register(get_filters, UserFilter(), lambda message: message.text == 'Фильтры')
