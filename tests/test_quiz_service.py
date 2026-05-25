"""Тести бізнес-логіки сервісу вікторини."""
from __future__ import annotations

import pytest

from database.models import Question
from services.quiz_service import calculate_percentage, select_questions


class TestCalculatePercentage:
    """Перевірка обрахунку відсотків."""

    def test_normal(self) -> None:
        assert calculate_percentage(5, 10) == 50.0

    def test_all_correct(self) -> None:
        assert calculate_percentage(7, 7) == 100.0

    def test_zero_total(self) -> None:
        assert calculate_percentage(0, 0) == 0.0

    def test_negative_total(self) -> None:
        assert calculate_percentage(3, -1) == 0.0

    def test_rounding(self) -> None:
        # 1 / 3 = 0.3333..., у відсотках 33.33
        assert calculate_percentage(1, 3) == 33.33


def _make_pool(n: int) -> list[Question]:
    """Створити фейковий пул питань."""
    return [Question(id=i, discipline_id=1, text=f"q{i}", difficulty=1) for i in range(1, n + 1)]


class TestSelectQuestions:
    """Перевірка вибірки питань."""

    def test_limit_respected(self) -> None:
        pool = _make_pool(20)
        chosen = select_questions(pool, limit=5)
        assert len(chosen) == 5

    def test_returns_all_when_pool_smaller(self) -> None:
        pool = _make_pool(3)
        chosen = select_questions(pool, limit=10)
        assert len(chosen) == 3
        assert {q.id for q in chosen} == {1, 2, 3}

    def test_limit_zero_returns_empty(self) -> None:
        assert select_questions(_make_pool(5), limit=0) == []

    def test_randomness_across_runs(self) -> None:
        """Серед кількох прогонів повинні зʼявитися різні комбінації."""
        pool = _make_pool(50)
        seen_orders: set[tuple[int, ...]] = set()
        for _ in range(20):
            chosen = select_questions(pool, limit=10)
            seen_orders.add(tuple(q.id for q in chosen))
        # При 50 питаннях і 20 прогонах випадковості майже неможливо отримати лише 1 варіант
        assert len(seen_orders) > 1

    def test_no_duplicates(self) -> None:
        pool = _make_pool(20)
        chosen = select_questions(pool, limit=10)
        ids = [q.id for q in chosen]
        assert len(ids) == len(set(ids))
