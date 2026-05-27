"""Резервний обробник: реагує на будь-яке невпізнане повідомлення чи натискання.

Роутер реєструється ОСТАННІМ у bot.py, тому спрацьовує лише тоді, коли жоден
інший хендлер (команди, кнопки меню, FSM-вікторини) не обробив апдейт. Без нього
бот мовчки ігнорує довільний текст, і це сприймається як «бот не працює».
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from config import load_config
from keyboards.user_kb import main_menu

router = Router()
logger = logging.getLogger(__name__)
_config = load_config()


@router.message()
async def fallback_message(message: Message) -> None:
    """Підказати користувачу, як користуватися ботом."""
    logger.info(
        "Невпізнане повідомлення від tg=%s (тип=%s): %r",
        message.from_user.id if message.from_user else "?",
        message.content_type,
        message.text,
    )
    is_admin = bool(message.from_user and message.from_user.id in _config.admin_ids)
    await message.answer(
        "Не зрозумів повідомлення. 🤔\n"
        "Скористайтеся кнопками меню нижче або командою /help.",
        reply_markup=main_menu(is_admin=is_admin),
    )


@router.callback_query()
async def fallback_callback(callback: CallbackQuery) -> None:
    """Відповісти на застаріле/невпізнане натискання inline-кнопки."""
    logger.info(
        "Невпізнане натискання від tg=%s: data=%r",
        callback.from_user.id if callback.from_user else "?",
        callback.data,
    )
    await callback.answer(
        "Ця кнопка вже неактивна. Почніть з /start або /quiz.", show_alert=True
    )
