from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button import KeyboardButton


async def start_bot_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text='Фильтры')],
        [KeyboardButton(text='Приостановить бота')]
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
