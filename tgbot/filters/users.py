import typing

from aiogram.filters import Filter
from aiogram.types import Message

from tgbot.config import Config


class UserFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        config: Config = message.bot.config
        return message.from_user.id in config.tg_bot.admin_ids
