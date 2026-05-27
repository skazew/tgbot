"""Точка входу Telegram-бота «Вікторина для перевірки знань»."""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import load_config
from database.engine import init_db
from handlers import admin as admin_handlers
from handlers import fallback as fallback_handlers
from handlers import quiz as quiz_handlers
from handlers import start as start_handlers
from handlers import stats as stats_handlers


def setup_logging(level_name: str) -> None:
    """Налаштувати логування у файл і stdout."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[file_handler, stream_handler])


async def on_error(event: ErrorEvent) -> bool:
    """Глобальний error handler: логувати traceback, не показувати його користувачу."""
    logger = logging.getLogger("error")
    logger.exception("Необроблена помилка: %s", event.exception)
    update = event.update
    if update and update.message:
        try:
            await update.message.answer("Сталася помилка, спробуйте пізніше.")
        except Exception:  # noqa: BLE001
            pass
    elif update and update.callback_query:
        try:
            await update.callback_query.answer(
                "Сталася помилка, спробуйте пізніше.", show_alert=True
            )
        except Exception:  # noqa: BLE001
            pass
    return True


async def main() -> None:
    """Точка входу: ініціалізувати застосунок і запустити polling."""
    config = load_config()
    setup_logging(config.log_level)
    logger = logging.getLogger("bot")

    if not config.bot_token:
        logger.error("BOT_TOKEN не задано. Перевірте .env")
        sys.exit(1)

    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_handlers.router)
    dp.include_router(quiz_handlers.router)
    dp.include_router(stats_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(fallback_handlers.router)  # завжди останній
    dp.errors.register(on_error)

    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот зупинено")


if __name__ == "__main__":
    asyncio.run(main())
