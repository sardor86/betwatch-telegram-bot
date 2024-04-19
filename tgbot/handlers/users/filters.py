import json
import logging

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from tgbot.misc import SetFilters, SetBlockList
from tgbot.filters import UserFilter
from tgbot.keyboards import get_filters_keyboard, get_category_set_filter_keyboard

logger = logging.getLogger(__name__)


async def change_filters_start(callback: CallbackQuery, state: FSMContext):
    logger.info(f'change {callback.data[7:]} filter start')
    await callback.message.edit_text('Напишите значение:')
    await state.set_state(SetFilters.change_filters)
    await state.update_data(filter=callback.data[7:])


async def change_filters_end(message: Message, state: FSMContext):
    data = await state.get_data()
    filter_data = None

    logger.info(f'change {data["filter"]} filter end')

    logger.info('check message text')
    if message.text.isdigit():
        filter_data = int(message.text)
    elif data['filter'][-11:] == 'coefficient':
        try:
            filter_data = float(message.text)
        except ValueError:
            await message.reply('Это не число')

    logger.info('save filters')
    parser_filter = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
    parser_filter[data['filter']] = filter_data

    await message.bot.redis.set(f'filter-{message.from_user.id}', json.dumps(parser_filter))
    await state.clear()

    logger.info('send filters')
    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(parser_filter)))


async def set_category_filter_start(callback: CallbackQuery, state: FSMContext):
    logger.info('change category filter start')
    await callback.message.edit_text('Выберите категорию', reply_markup=(await get_category_set_filter_keyboard()))
    await state.set_state(SetFilters.change_filters)


async def set_category_filter_end(callback: CallbackQuery, state: FSMContext):
    logger.info('change category filter end')
    parser_filter = json.loads(await callback.bot.redis.get(f'filter-{callback.from_user.id}'))

    logger.info('save filters')
    parser_filter['online_matches'] = callback.data == 'filter_category_live_matches'
    parser_filter['pre_matches'] = callback.data == 'filter_category_pre_matches'
    await callback.bot.redis.set(f'filter-{callback.from_user.id}', json.dumps(parser_filter))

    logger.info('send filters')
    await callback.message.edit_text('Фильтры', reply_markup=(await get_filters_keyboard(parser_filter)))

    await state.clear()


async def block_list_filter_start(callback: CallbackQuery, state: FSMContext):
    logger.info('change block list filter start')
    await callback.message.edit_text('Block list какие не желательные данные хотите получить отправте в виде:\n'
                                     'First Half Goals 0.5;First Half Goals 1.5;Over/Under 0.5 Goals\n'
                                     'без пробелов с ;')
    await state.set_state(SetBlockList.change_block_list)


async def block_list_filter_end(message: Message, state: FSMContext):
    logger.info('change block list filter end')

    logger.info('save block list filter')
    parser_filters = json.loads(await message.bot.redis.get(f'filter-{message.from_user.id}'))
    parser_filters['block_list'] = message.text.split(';')
    await message.bot.redis.set(f'filter-{message.from_user.id}', json.dumps(parser_filters))

    logger.info('send filters')
    await message.reply('Фильтры', reply_markup=(await get_filters_keyboard(parser_filters)))
    await state.clear()


async def save_filters(callback: CallbackQuery):
    logger.info('save all filters')
    filters = json.loads(await callback.bot.redis.get(f'filter-{callback.from_user.id}'))

    logger.info('save filters from redis to parser')
    callback.bot.parser.live_matches = filters['online_matches']
    callback.bot.parser.pre_matches = filters['pre_matches']

    callback.bot.parser.from_price = filters['from_price']
    callback.bot.parser.to_price = filters['to_price']

    callback.bot.parser.from_percentage = filters['from_percentage']
    callback.bot.parser.to_percentage = filters['to_percentage']

    callback.bot.parser.from_coefficient = filters['from_coefficient']
    callback.bot.parser.to_coefficient = filters['to_coefficient']

    callback.bot.parser.from_time_1 = filters['from_time_1']
    callback.bot.parser.to_time_1 = filters['to_time_1']

    callback.bot.parser.from_time_2 = filters['from_time_2']
    callback.bot.parser.to_time_2 = filters['to_time_2']

    callback.bot.parser.block_list = filters['block_list']

    await callback.message.edit_text('Фильтры сохранены')


def register_filters(dp: Dispatcher):
    logger.info('register filters handlers')
    dp.callback_query.register(save_filters, UserFilter(), lambda callback: callback.data == 'save_filters')

    dp.callback_query.register(set_category_filter_start, UserFilter(), lambda callback: callback.data == 'category')
    dp.callback_query.register(set_category_filter_end,
                               StateFilter(SetFilters.change_filters),
                               lambda callback: callback.data[:15] == 'filter_category',
                               UserFilter())

    dp.callback_query.register(change_filters_start, lambda callback: callback.data[:6] == 'filter', UserFilter())
    dp.message.register(change_filters_end, StateFilter(SetFilters.change_filters), UserFilter())

    dp.callback_query.register(block_list_filter_start, lambda callback: callback.data == 'block_list', UserFilter())
    dp.message.register(block_list_filter_end, StateFilter(SetBlockList.change_block_list), UserFilter())
