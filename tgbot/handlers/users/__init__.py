import logging

from aiogram import Dispatcher

from .user import register_user
from .filters import register_filters
from .send_matches import parser


logger = logging.getLogger(__name__)


def register_all_user_handlers(dp: Dispatcher):
    logger.info('register all user handlers')
    register_user(dp)
    register_filters(dp)
