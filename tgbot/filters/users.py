import logging

from aiogram.filters import Filter
from aiogram.types import Message

from tgbot.config import Config


logger = logging.getLogger(__name__)


class UserFilter(Filter):
    """
    This is user filter
    With this filter only allowed users can use the bot
    Allowed users have written in .env file as USERS
    """
    async def __call__(self, message: Message) -> bool:
        logger.info('check user')
        config: Config = message.bot.config
        return message.from_user.id in config.tg_bot.admin_ids
