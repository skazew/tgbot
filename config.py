"""Конфігурація бота: завантаження змінних оточення з .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> list[int]:
    """Парсити рядок ADMIN_IDS у список цілих чисел."""
    if not raw:
        return []
    result: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            result.append(int(chunk))
    return result


@dataclass(frozen=True)
class Config:
    """Контейнер конфігурації застосунку."""

    bot_token: str
    database_url: str
    admin_ids: list[int] = field(default_factory=list)
    quiz_length: int = 10
    log_level: str = "INFO"


def load_config() -> Config:
    """Зібрати конфігурацію з оточення."""
    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./quiz_bot.db"),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        quiz_length=int(os.getenv("QUIZ_LENGTH", "10")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Глобальні константи (не магічні числа)
QUESTIONS_PAGE_SIZE = 5
TOP_RATING_LIMIT = 10
RECENT_ATTEMPTS_LIMIT = 5
MIN_ANSWER_OPTIONS = 2
MAX_ANSWER_OPTIONS = 6
MAX_QUESTION_TEXT_LEN = 1000
MAX_ANSWER_TEXT_LEN = 255
MAX_DISCIPLINE_NAME_LEN = 128
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5
