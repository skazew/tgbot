"""Репозиторії для доступу до даних (Data Access Layer)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Answer, Attempt, Discipline, Question, User


class UserRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        full_name: str,
        username: str | None,
        is_admin: bool = False,
    ) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if user is not None:
            if is_admin and user.role != "admin":
                user.role = "admin"
                await self.session.commit()
            return user
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            role="admin" if is_admin else "user",
            created_at=datetime.utcnow(),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def is_admin(self, telegram_id: int, admin_ids: list[int]) -> bool:
        if telegram_id in admin_ids:
            return True
        user = await self.get_by_telegram_id(telegram_id)
        return user is not None and user.role == "admin"


class DisciplineRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, description: str | None = None) -> Discipline:
        discipline = Discipline(name=name, description=description, is_active=True)
        self.session.add(discipline)
        await self.session.commit()
        await self.session.refresh(discipline)
        return discipline

    async def get_by_id(self, discipline_id: int) -> Discipline | None:
        return await self.session.get(Discipline, discipline_id)

    async def get_by_name(self, name: str) -> Discipline | None:
        stmt = select(Discipline).where(Discipline.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_active(self) -> list[Discipline]:
        stmt = select(Discipline).where(Discipline.is_active.is_(True)).order_by(Discipline.name)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_all(self) -> list[Discipline]:
        stmt = select(Discipline).order_by(Discipline.name)
        return list((await self.session.execute(stmt)).scalars().all())

    async def rename(self, discipline_id: int, new_name: str) -> Discipline | None:
        discipline = await self.get_by_id(discipline_id)
        if discipline is None:
            return None
        discipline.name = new_name
        await self.session.commit()
        await self.session.refresh(discipline)
        return discipline

    async def set_active(self, discipline_id: int, is_active: bool) -> Discipline | None:
        discipline = await self.get_by_id(discipline_id)
        if discipline is None:
            return None
        discipline.is_active = is_active
        await self.session.commit()
        await self.session.refresh(discipline)
        return discipline

    async def delete(self, discipline_id: int) -> bool:
        discipline = await self.get_by_id(discipline_id)
        if discipline is None:
            return False
        await self.session.delete(discipline)
        await self.session.commit()
        return True


class QuestionRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_with_answers(
        self,
        discipline_id: int,
        text: str,
        answers: list[tuple[str, bool]],
        difficulty: int = 1,
    ) -> Question:
        question = Question(
            discipline_id=discipline_id, text=text, difficulty=difficulty
        )
        question.answers = [
            Answer(text=a_text, is_correct=is_correct) for a_text, is_correct in answers
        ]
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def get_with_answers(self, question_id: int) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.answers))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_by_discipline(self, discipline_id: int) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.discipline_id == discipline_id)
            .options(selectinload(Question.answers))
            .order_by(Question.id)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_by_discipline(self, discipline_id: int) -> int:
        stmt = select(func.count(Question.id)).where(
            Question.discipline_id == discipline_id
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def page_by_discipline(
        self, discipline_id: int, offset: int, limit: int
    ) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.discipline_id == discipline_id)
            .options(selectinload(Question.answers))
            .order_by(Question.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def update_text(self, question_id: int, new_text: str) -> Question | None:
        question = await self.get_with_answers(question_id)
        if question is None:
            return None
        question.text = new_text
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def delete(self, question_id: int) -> bool:
        question = await self.session.get(Question, question_id)
        if question is None:
            return False
        await self.session.delete(question)
        await self.session.commit()
        return True


class AnswerRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, answer_id: int) -> Answer | None:
        return await self.session.get(Answer, answer_id)


class AttemptRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        discipline_id: int,
        correct_count: int,
        total_count: int,
        started_at: datetime,
        finished_at: datetime,
    ) -> Attempt:
        attempt = Attempt(
            user_id=user_id,
            discipline_id=discipline_id,
            correct_count=correct_count,
            total_count=total_count,
            started_at=started_at,
            finished_at=finished_at,
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def list_user_recent(self, user_id: int, limit: int) -> list[Attempt]:
        stmt = (
            select(Attempt)
            .where(Attempt.user_id == user_id)
            .options(selectinload(Attempt.discipline))
            .order_by(desc(Attempt.finished_at))
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_user_attempts(self, user_id: int) -> int:
        stmt = select(func.count(Attempt.id)).where(Attempt.user_id == user_id)
        return int((await self.session.execute(stmt)).scalar_one())

    async def user_average_percentage(self, user_id: int) -> float:
        stmt = select(
            func.coalesce(func.sum(Attempt.correct_count), 0),
            func.coalesce(func.sum(Attempt.total_count), 0),
        ).where(Attempt.user_id == user_id)
        correct, total = (await self.session.execute(stmt)).one()
        if not total:
            return 0.0
        return round((correct / total) * 100, 2)

    async def user_best_percentage(self, user_id: int) -> float:
        stmt = select(Attempt).where(Attempt.user_id == user_id)
        attempts = list((await self.session.execute(stmt)).scalars().all())
        if not attempts:
            return 0.0
        return round(
            max(
                (a.correct_count / a.total_count) * 100
                for a in attempts
                if a.total_count > 0
            ),
            2,
        )

    async def top_by_discipline(
        self, discipline_id: int, limit: int
    ) -> list[tuple[User, float]]:
        stmt = (
            select(Attempt)
            .where(Attempt.discipline_id == discipline_id)
            .options(selectinload(Attempt.user))
        )
        attempts = list((await self.session.execute(stmt)).scalars().all())
        best: dict[int, tuple[User, float]] = {}
        for attempt in attempts:
            if attempt.total_count <= 0:
                continue
            pct = (attempt.correct_count / attempt.total_count) * 100
            current = best.get(attempt.user_id)
            if current is None or pct > current[1]:
                best[attempt.user_id] = (attempt.user, round(pct, 2))
        ranked = sorted(best.values(), key=lambda item: item[1], reverse=True)
        return ranked[:limit]

    async def total_count(self) -> int:
        stmt = select(func.count(Attempt.id))
        return int((await self.session.execute(stmt)).scalar_one())

    async def most_active_user(self) -> tuple[User, int] | None:
        stmt = (
            select(Attempt.user_id, func.count(Attempt.id).label("cnt"))
            .group_by(Attempt.user_id)
            .order_by(desc("cnt"))
            .limit(1)
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return None
        user = await self.session.get(User, row[0])
        if user is None:
            return None
        return user, int(row[1])

    async def hardest_discipline(self) -> tuple[Discipline, float] | None:
        stmt = select(Attempt).options(selectinload(Attempt.discipline))
        attempts = list((await self.session.execute(stmt)).scalars().all())
        if not attempts:
            return None
        by_disc: dict[int, list[Attempt]] = {}
        for a in attempts:
            by_disc.setdefault(a.discipline_id, []).append(a)
        averages: list[tuple[Discipline, float]] = []
        for disc_id, items in by_disc.items():
            total_correct = sum(i.correct_count for i in items)
            total_total = sum(i.total_count for i in items)
            if total_total <= 0:
                continue
            avg = round((total_correct / total_total) * 100, 2)
            averages.append((items[0].discipline, avg))
        if not averages:
            return None
        return min(averages, key=lambda item: item[1])

    async def list_all_for_export(self) -> list[Attempt]:
        stmt = (
            select(Attempt)
            .options(
                selectinload(Attempt.user), selectinload(Attempt.discipline)
            )
            .order_by(Attempt.id)
        )
        return list((await self.session.execute(stmt)).scalars().all())
