"""Клавіатури для звичайних користувачів."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from database.models import Answer, Discipline

BTN_QUIZ = "📚 Обрати вікторину"
BTN_STATS = "📊 Моя статистика"
BTN_RATING = "🏆 Рейтинг"
BTN_HELP = "ℹ️ Довідка"
BTN_ADMIN = "⚙️ Адміністрування"


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Головне reply-меню. Якщо адмін — додає кнопку адміністрування."""
    rows = [
        [KeyboardButton(text=BTN_QUIZ)],
        [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_RATING)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=BTN_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


SECTIONS: list[tuple[str, str, list[str]]] = [
    (
        "it",
        "💻 IT",
        ["Програмування Python", "Бази даних", "Алгоритми", "Веброзробка"],
    ),
    (
        "humanities",
        "📜 Гуманітарні",
        ["Історія України", "Українська література", "Українська культура"],
    ),
    (
        "world",
        "🌍 Світ і природа",
        ["Географія світу", "Природа і наука"],
    ),
    (
        "math",
        "🧮 Математика",
        ["Математика"],
    ),
    (
        "cinema",
        "🎬 Кіно та культура",
        ["Світове кіно"],
    ),
    (
        "sport",
        "⚽ Спорт",
        ["Футбол", "Олімпійські ігри"],
    ),
    (
        "general",
        "🧠 Загальні знання",
        ["Загальні знання"],
    ),
]


def get_section(key: str) -> tuple[str, list[str]] | None:
    """Повернути (заголовок, список назв дисциплін) розділу за ключем."""
    for k, title, names in SECTIONS:
        if k == key:
            return title, names
    return None


def sections_kb(prefix: str) -> InlineKeyboardMarkup:
    """Inline-клавіатура зі списком розділів; callback_data = `{prefix}:{key}`."""
    rows = [
        [InlineKeyboardButton(text=title, callback_data=f"{prefix}:{key}")]
        for key, title, _ in SECTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def disciplines_kb(
    disciplines: list[Discipline], prefix: str
) -> InlineKeyboardMarkup:
    """Inline-клавіатура зі списком дисциплін; callback_data = `{prefix}:{id}`."""
    rows = [
        [InlineKeyboardButton(text=d.name, callback_data=f"{prefix}:{d.id}")]
        for d in disciplines
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def disciplines_in_section_kb(
    disciplines: list[Discipline],
    section_key: str,
    disc_prefix: str,
    back_callback: str,
) -> InlineKeyboardMarkup:
    """Дисципліни розділу + кнопка «Назад до розділів»."""
    section = get_section(section_key)
    name_set: set[str] = set(section[1]) if section else set()
    filtered = [d for d in disciplines if d.name in name_set]
    rows = [
        [InlineKeyboardButton(text=d.name, callback_data=f"{disc_prefix}:{d.id}")]
        for d in filtered
    ]
    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад до розділів", callback_data=back_callback)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def answers_kb(question_id: int, answers: list[Answer]) -> InlineKeyboardMarkup:
    """Inline-клавіатура з варіантами відповідей на питання."""
    rows = [
        [
            InlineKeyboardButton(
                text=a.text, callback_data=f"answer:{question_id}:{a.id}"
            )
        ]
        for a in answers
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
