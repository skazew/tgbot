"""Бізнес-логіка вікторини: підрахунок результату та вибір питань."""
from __future__ import annotations

import random
from collections.abc import Sequence

from database.models import Question


def calculate_percentage(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((correct / total) * 100, 2)


def select_questions(
    questions: Sequence[Question], limit: int
) -> list[Question]:
    if limit <= 0:
        return []
    pool = list(questions)
    if len(pool) <= limit:
        random.shuffle(pool)
        return pool
    return random.sample(pool, limit)


def format_summary(correct: int, total: int) -> str:
    percent = calculate_percentage(correct, total)
    return (
        f"<b>Вікторину завершено!</b>\n"
        f"Правильних: {correct} з {total}\n"
        f"Ваш результат: {percent}%"
    )
