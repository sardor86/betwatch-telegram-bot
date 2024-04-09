from .users import UserFilter


def register_all_filters(dp):
    dp.filters_factory.bind(UserFilter)
