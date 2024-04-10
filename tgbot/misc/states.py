from aiogram.fsm.state import State, StatesGroup


class SetFilters(StatesGroup):
    change_filters = State()


class SetBlockList(StatesGroup):
    change_block_list = State()
