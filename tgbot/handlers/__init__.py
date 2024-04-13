import logging

from aiogram import Dispatcher

from tgbot.handlers.users import register_all_user_handlers

logger = logging.getLogger(__name__)


def register_all_handlers(dp: Dispatcher):
    logger.info('registering all handlers')
    register_all_user_handlers(dp)
