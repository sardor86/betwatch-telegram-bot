from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from tgbot.filters import UserFilter
from tgbot.keyboards import start_bot_keyboard


async def user_start(message: Message):
    await message.reply("Бот запущен", reply_markup=(await start_bot_keyboard()))


def register_user(dp: Dispatcher):
    dp.message.register(user_start, Command('start'), UserFilter())
