"""Обробники /start, /help, /cancel та основних reply-кнопок."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import load_config
from database.engine import async_session
from database.repositories import UserRepository
from keyboards.user_kb import BTN_HELP, main_menu

router = Router()
logger = logging.getLogger(__name__)
_config = load_config()

HELP_TEXT = (
    "<b>Довідка</b>\n"
    "Цей бот допомагає перевірити знання у форматі вікторини.\n\n"
    "<b>Доступні команди:</b>\n"
    "/start — реєстрація та головне меню\n"
    "/quiz — обрати дисципліну та розпочати вікторину\n"
    "/stats — переглянути свою статистику\n"
    "/cancel — перервати поточну вікторину\n"
    "/help — ця довідка\n\n"
    "Адмін-команди (тільки для адміністраторів):\n"
    "/admin — меню адміністратора\n"
    "/stats_all — зведена статистика\n"
    "/export — експорт усіх спроб у CSV"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обробити /start: зареєструвати користувача і показати головне меню."""
    await state.clear()
    if message.from_user is None:
        return
    is_admin = message.from_user.id in _config.admin_ids
    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name or "Без імені",
            username=message.from_user.username,
            is_admin=is_admin,
        )
    logger.info("Користувач %s (tg=%s) увійшов", user.full_name, user.telegram_id)
    await message.answer(
        f"Вітаємо, <b>{user.full_name}</b>! 👋\n"
        f"Це бот-вікторина для перевірки знань.\n"
        f"Оберіть дію з меню нижче або скористайтеся командою /help.",
        reply_markup=main_menu(is_admin=user.role == "admin" or is_admin),
    )


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    """Вивести довідку."""
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Скасувати поточний FSM-сценарій."""
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Немає активного сценарію.")
    else:
        await message.answer("Скасовано.")
