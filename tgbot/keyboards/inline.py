from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def get_filters_keyboard(filters):
    keyboard = [
        [
            InlineKeyboardButton(text=f"От {filters['from_price']} €", callback_data="filter_from_price"),
            InlineKeyboardButton(text=f"До {filters['to_price']} €", callback_data="filter_to_price")
        ],
        [
            InlineKeyboardButton(text=f"От {filters['from_percentage']} %", callback_data="filter_from_percentage"),
            InlineKeyboardButton(text=f"До {filters['to_percentage']} %", callback_data="filter_to_percentage")
        ],
        [
            InlineKeyboardButton(text=f"От {filters['from_coefficient']} кф", callback_data="filter_from_coefficient"),
            InlineKeyboardButton(text=f"До {filters['to_coefficient']} кф", callback_data="filter_to_coefficient")
        ],
        [
            InlineKeyboardButton(text=f"Block List: {filters['block_list']}", callback_data="block_list"),
        ],
        [
            InlineKeyboardButton(text="Сохранить", callback_data="save_filters"),
        ]
    ]

    if filters['online_matches']:
        keyboard.insert(0, [InlineKeyboardButton(text='Онлайн матчи', callback_data='category')])
        keyboard.insert(4, [
            InlineKeyboardButton(text=f"От {filters['from_time']} мин", callback_data="from_time"),
            InlineKeyboardButton(text=f"До {filters['to_time']} мин I", callback_data="to_time")
        ])
    elif filters['pre_matches']:
        keyboard.insert(0, [InlineKeyboardButton(text='Предстоящие матчи', callback_data='category')])
    else:
        keyboard.insert(0, [InlineKeyboardButton(text='Все матчи', callback_data='category')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard, resize_keyboard=True)


async def get_category_set_filter_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text='Все матчи', callback_data='filter_category_all_matches'),
            InlineKeyboardButton(text='Онлайн матчи', callback_data='filter_category_live_matches'),
            InlineKeyboardButton(text='Предстоящие матчи', callback_data='filter_category_pre_matches'),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard, resize_keyboard=True)
