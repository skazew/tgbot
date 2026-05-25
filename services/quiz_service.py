"""Бізнес-логіка вікторини: підрахунок результату та вибір питань."""
from __future__ import annotations

import random
from collections.abc import Sequence

from database.models import Question


def calculate_percentage(correct: int, total: int) -> float:
    """Підрахувати відсоток правильних відповідей із заокругленням до 0.01.

    При total == 0 повертає 0.0 (захист від ділення на нуль).
    """
    if total <= 0:
        return 0.0
    return round((correct / total) * 100, 2)


def select_questions(
    questions: Sequence[Question], limit: int
) -> list[Question]:
    """Випадково обрати не більше `limit` питань зі списку.

    Якщо доступних питань менше за `limit`, повертає всі наявні.
    """
    if limit <= 0:
        return []
    pool = list(questions)
    if len(pool) <= limit:
        random.shuffle(pool)
        return pool
    return random.sample(pool, limit)


def format_summary(correct: int, total: int) -> str:
    """Сформувати рядок підсумку вікторини."""
    percent = calculate_percentage(correct, total)
    return (
        f"<b>Вікторину завершено!</b>\n"
        f"Правильних: {correct} з {total}\n"
        f"Ваш результат: {percent}%"
    )
