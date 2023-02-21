from dataclasses import dataclass, asdict
from yaml import load as load_yaml, Loader, dump as dump_yaml

from typing import List


@dataclass
class Config:
    bot_token: str
    db_uri: str
    db_name: str
    channel_id: int
    channel_url: str
    logs_channel_id: int
    admins: List[int]
    per_page_limit: int
    inline_cache_time: int
    checker_timeout: int


CONFIG_FILENAME: str = "config.yml"


with open(CONFIG_FILENAME, "r", encoding="utf-8") as file:
    data: dict = load_yaml(
        stream = file,
        Loader = Loader
    )


config: Config = Config(
    **data
)


def save_config(config: Config) -> None:
    with open(CONFIG_FILENAME, "w", encoding="utf-8") as file:
        dump_yaml(
            data = asdict(
                obj = config
            ),
            stream = file,
            allow_unicode = True,
            indent = 2
        )


__all__ = (
    "CONFIG_FILENAME",
    "config",
    "save_config",
)
