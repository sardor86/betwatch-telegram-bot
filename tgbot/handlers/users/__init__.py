from aiogram import Dispatcher

from .user import register_user
from .filters import register_filters


def register_all_user_handlers(dp: Dispatcher):
    register_user(dp)
    register_filters(dp)
