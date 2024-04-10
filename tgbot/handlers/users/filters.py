import json

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from tgbot.misc import SetFilters, SetBlockList
from tgbot.filters import UserFilter
from tgbot.keyboards import get_filters_keyboard, get_category_set_filter_keyboard


async def change_filters_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Напишите значение:')
    await state.set_state(SetFilters.change_filters)
    await state.update_data(filter=callback.data[7:])


async def change_filters_end(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply('Это не число')
        return

    data = await state.get_data()
    parser_filter = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
    parser_filter[data['filter']] = int(message.text)

    await message.bot.redis.set(f'filter-{message.from_user.id}', json.dumps(parser_filter))
    await state.clear()

    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(parser_filter)))


async def set_category_filter_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Выберите категорию', reply_markup=(await get_category_set_filter_keyboard()))
    await state.set_state(SetFilters.change_filters)


async def set_category_filter_end(callback: CallbackQuery, state: FSMContext):
    parser_filter = json.loads(await callback.bot.redis.get(f'filter-{callback.from_user.id}'))

    parser_filter['online_matches'] = callback.data == 'filter_category_live_matches'
    parser_filter['pre_matches'] = callback.data == 'filter_category_pre_matches'

    await callback.bot.redis.set(f'filter-{callback.from_user.id}', json.dumps(parser_filter))
    await callback.message.edit_text('Фильтры', reply_markup=(await get_filters_keyboard(parser_filter)))

    await state.clear()


async def block_list_filter_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Block list какие не жедательные данные хотите получить отправте в виде:\n'
                                     'First Half Goals 0.5;First Half Goals 1.5;Over/Under 0.5 Goals\n'
                                     'без пробелов с ;')
    await state.set_state(SetBlockList.change_block_list)


async def block_list_filter_end(message: Message, state: FSMContext):
    parser_filters = await message.bot.redis.get(f'filter-{message.from_user.id}')
    parser_filters['block_list'] = message.text.split(';')

    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(parser_filters)))
    await state.clear()


def register_filters(dp: Dispatcher):
    dp.callback_query.register(set_category_filter_start, UserFilter(), lambda callback: callback.data == 'category')
    dp.callback_query.register(set_category_filter_end,
                               StateFilter(SetFilters.change_filters),
                               lambda callback: callback.data[:15] == 'filter_category',
                               UserFilter())

    dp.callback_query.register(change_filters_start, lambda callback: callback.data[:6] == 'filter', UserFilter())
    dp.message.register(change_filters_end, StateFilter(SetFilters.change_filters), UserFilter())

    dp.callback_query.register(block_list_filter_start, lambda callback: callback.data == 'block_list', UserFilter())
    dp.message.register(block_list_filter_end, StateFilter(SetBlockList.change_block_list), UserFilter())
