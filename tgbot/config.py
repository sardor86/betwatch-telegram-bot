from dataclasses import dataclass

from environs import Env

BASE_URL = 'https://betwatch.fr'


@dataclass
class RedisConfig:
    host: str
    port: int


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class Config:
    tg_bot: TgBot
    redis: RedisConfig


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.str("ADMINS").split(","))),
        ),
        redis=RedisConfig(
            host=env.str("REDIS_HOST"),
            port=env.int("REDIS_PORT"),
        )
    )
