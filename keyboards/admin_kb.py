"""Клавіатури для адміністратора."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Discipline, Question

CB_ADMIN_DISC = "admin_disc"
CB_ADMIN_QUESTIONS = "admin_questions"
CB_ADMIN_STATS = "admin_stats"
CB_ADMIN_EXPORT = "admin_export"

CB_DISC_ADD = "disc_add"
CB_DISC_LIST = "disc_list"
CB_DISC_RENAME = "disc_rename"
CB_DISC_TOGGLE = "disc_toggle"
CB_DISC_DELETE = "disc_delete"

CB_Q_ADD = "q_add"
CB_Q_LIST = "q_list"


def admin_main_kb() -> InlineKeyboardMarkup:
    """Головне меню адміністратора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Дисципліни", callback_data=CB_ADMIN_DISC)],
            [InlineKeyboardButton(text="❓ Питання", callback_data=CB_ADMIN_QUESTIONS)],
            [InlineKeyboardButton(text="📈 Загальна статистика", callback_data=CB_ADMIN_STATS)],
            [InlineKeyboardButton(text="⬇️ Експорт CSV", callback_data=CB_ADMIN_EXPORT)],
        ]
    )


def disciplines_admin_kb() -> InlineKeyboardMarkup:
    """Меню керування дисциплінами."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Створити", callback_data=CB_DISC_ADD)],
            [InlineKeyboardButton(text="📋 Список", callback_data=CB_DISC_LIST)],
            [InlineKeyboardButton(text="✏️ Перейменувати", callback_data=CB_DISC_RENAME)],
            [InlineKeyboardButton(text="🔁 Активність", callback_data=CB_DISC_TOGGLE)],
            [InlineKeyboardButton(text="🗑️ Видалити", callback_data=CB_DISC_DELETE)],
        ]
    )


def questions_admin_kb() -> InlineKeyboardMarkup:
    """Меню керування питаннями."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати питання", callback_data=CB_Q_ADD)],
            [InlineKeyboardButton(text="📋 Список питань", callback_data=CB_Q_LIST)],
        ]
    )


def disciplines_pick_kb(
    disciplines: list[Discipline], action: str
) -> InlineKeyboardMarkup:
    """Inline-клавіатура для вибору дисципліни в адмін-сценаріях."""
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if d.is_active else '⛔'} {d.name}",
                callback_data=f"{action}:{d.id}",
            )
        ]
        for d in disciplines
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def correct_answer_kb(options_count: int) -> InlineKeyboardMarkup:
    """Inline-клавіатура для вибору правильного варіанта (1..N)."""
    rows = [
        [
            InlineKeyboardButton(
                text=f"{i + 1}", callback_data=f"correct:{i}"
            )
            for i in range(options_count)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def add_more_answers_kb() -> InlineKeyboardMarkup:
    """Inline-клавіатура для завершення введення варіантів відповідей."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Готово (обрати правильний)", callback_data="answers_done")]
        ]
    )


def questions_page_kb(
    questions: list[Question],
    discipline_id: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Inline-клавіатура зі сторінкою списку питань і навігацією."""
    rows: list[list[InlineKeyboardButton]] = []
    for q in questions:
        short = q.text if len(q.text) <= 40 else q.text[:37] + "…"
        rows.append([InlineKeyboardButton(text=short, callback_data=f"q_view:{q.id}")])
        rows.append(
            [
                InlineKeyboardButton(text="✏️", callback_data=f"q_edit:{q.id}"),
                InlineKeyboardButton(text="🗑️", callback_data=f"q_del:{q.id}"),
            ]
        )
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="◀️", callback_data=f"q_page:{discipline_id}:{page - 1}"
            )
        )
    nav.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    if page < total_pages - 1:
        nav.append(
            InlineKeyboardButton(
                text="▶️", callback_data=f"q_page:{discipline_id}:{page + 1}"
            )
        )
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    """Inline-клавіатура «Так / Ні» для підтвердження небезпечних дій."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Так", callback_data=yes_data),
                InlineKeyboardButton(text="❌ Ні", callback_data=no_data),
            ]
        ]
    )
