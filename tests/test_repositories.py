"""Тести репозиторіїв з in-memory SQLite."""
from __future__ import annotations

import pytest

from database.repositories import (
    DisciplineRepository,
    QuestionRepository,
    UserRepository,
)


class TestUserRepository:

    async def test_get_or_create_creates_new(self, session) -> None:
        repo = UserRepository(session)
        user = await repo.get_or_create(
            telegram_id=111, full_name="Іван Петренко", username="ivan"
        )
        assert user.id is not None
        assert user.telegram_id == 111
        assert user.role == "user"

    async def test_get_or_create_returns_existing(self, session) -> None:
        repo = UserRepository(session)
        a = await repo.get_or_create(
            telegram_id=222, full_name="Олена", username="ol"
        )
        b = await repo.get_or_create(
            telegram_id=222, full_name="Олена", username="ol"
        )
        assert a.id == b.id

    async def test_get_or_create_promotes_to_admin(self, session) -> None:
        repo = UserRepository(session)
        await repo.get_or_create(telegram_id=333, full_name="X", username=None)
        promoted = await repo.get_or_create(
            telegram_id=333, full_name="X", username=None, is_admin=True
        )
        assert promoted.role == "admin"

    async def test_is_admin_via_env(self, session) -> None:
        repo = UserRepository(session)
        await repo.get_or_create(telegram_id=999, full_name="A", username=None)
        assert await repo.is_admin(999, [999]) is True
        assert await repo.is_admin(999, []) is False


class TestDisciplineRepository:

    async def test_create_and_get_by_name(self, session) -> None:
        repo = DisciplineRepository(session)
        d = await repo.create("Python", "опис")
        assert d.id is not None
        found = await repo.get_by_name("Python")
        assert found is not None and found.id == d.id

    async def test_list_active_excludes_inactive(self, session) -> None:
        repo = DisciplineRepository(session)
        d1 = await repo.create("Active", None)
        d2 = await repo.create("Inactive", None)
        await repo.set_active(d2.id, False)
        active = await repo.list_active()
        names = {d.name for d in active}
        assert "Active" in names
        assert "Inactive" not in names
        assert d1.id in {d.id for d in active}


class TestQuestionRepository:

    async def test_create_with_answers_and_selectinload(self, session) -> None:
        disc = await DisciplineRepository(session).create("D", None)
        q_repo = QuestionRepository(session)
        question = await q_repo.create_with_answers(
            discipline_id=disc.id,
            text="Питання?",
            answers=[("Так", True), ("Ні", False)],
        )
        loaded = await q_repo.get_with_answers(question.id)
        assert loaded is not None
        assert len(loaded.answers) == 2
        correct = [a for a in loaded.answers if a.is_correct]
        assert len(correct) == 1
        assert correct[0].text == "Так"

    async def test_list_by_discipline_loads_answers(self, session) -> None:
        disc = await DisciplineRepository(session).create("D", None)
        q_repo = QuestionRepository(session)
        await q_repo.create_with_answers(
            discipline_id=disc.id,
            text="Q1",
            answers=[("a", True), ("b", False)],
        )
        await q_repo.create_with_answers(
            discipline_id=disc.id,
            text="Q2",
            answers=[("c", False), ("d", True), ("e", False)],
        )
        questions = await q_repo.list_by_discipline(disc.id)
        assert len(questions) == 2
        # Перевіряємо, що answers вже підвантажені (без додаткового запиту)
        for q in questions:
            assert len(q.answers) >= 2

    async def test_count_and_page(self, session) -> None:
        disc = await DisciplineRepository(session).create("D", None)
        q_repo = QuestionRepository(session)
        for i in range(7):
            await q_repo.create_with_answers(
                discipline_id=disc.id,
                text=f"Q{i}",
                answers=[("a", True), ("b", False)],
            )
        assert await q_repo.count_by_discipline(disc.id) == 7
        page = await q_repo.page_by_discipline(disc.id, offset=5, limit=5)
        assert len(page) == 2
