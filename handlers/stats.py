"""Обробники статистики користувача та рейтингу."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config import TOP_RATING_LIMIT
from database.engine import async_session
from database.repositories import (
    AttemptRepository,
    DisciplineRepository,
    UserRepository,
)
from keyboards.user_kb import BTN_RATING, BTN_STATS, disciplines_kb
from services.stats_service import build_user_stats, format_user_stats

router = Router()

CB_RATING_DISC = "rating_disc"


@router.message(Command("stats"))
@router.message(F.text == BTN_STATS)
async def cmd_stats(message: Message) -> None:
    """Вивести статистику користувача."""
    if message.from_user is None:
        return
    async with async_session() as session:
        user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
        if user is None:
            await message.answer("Спочатку натисніть /start.")
            return
        stats = await build_user_stats(session, user.id)
    await message.answer(format_user_stats(stats))


@router.message(F.text == BTN_RATING)
@router.message(Command("rating"))
async def cmd_rating(message: Message) -> None:
    """Запропонувати обрати дисципліну для перегляду рейтингу."""
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_active()
    if not disciplines:
        await message.answer("Поки немає активних дисциплін.")
        return
    await message.answer(
        "Оберіть дисципліну для перегляду рейтингу:",
        reply_markup=disciplines_kb(disciplines, prefix=CB_RATING_DISC),
    )


@router.callback_query(F.data.startswith(f"{CB_RATING_DISC}:"))
async def on_rating_discipline(call: CallbackQuery) -> None:
    """Вивести топ-N користувачів за обраною дисципліною."""
    if call.data is None or call.message is None:
        await call.answer()
        return
    try:
        discipline_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Помилка", show_alert=True)
        return
    async with async_session() as session:
        discipline = await DisciplineRepository(session).get_by_id(discipline_id)
        if discipline is None:
            await call.answer("Дисципліну не знайдено", show_alert=True)
            return
        ranked = await AttemptRepository(session).top_by_discipline(
            discipline_id, TOP_RATING_LIMIT
        )
    if not ranked:
        await call.answer()
        await call.message.edit_text(
            f"<b>Рейтинг — {discipline.name}</b>\nЩе немає проходжень."
        )
        return
    lines = [f"<b>Рейтинг — {discipline.name}</b>"]
    for i, (user, pct) in enumerate(ranked, start=1):
        lines.append(f"{i}. {user.full_name} — {pct}%")
    await call.answer()
    await call.message.edit_text("\n".join(lines))
