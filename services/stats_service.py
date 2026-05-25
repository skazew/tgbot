"""Сервіс агрегації статистики для користувачів і адміністраторів."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from config import RECENT_ATTEMPTS_LIMIT
from database.models import Attempt
from database.repositories import AttemptRepository
from services.quiz_service import calculate_percentage


@dataclass
class UserStats:
    """Зведена статистика користувача."""

    attempts_count: int
    average_percentage: float
    best_percentage: float
    recent: list[Attempt]


@dataclass
class GlobalStats:
    """Зведена статистика по всіх користувачах."""

    total_attempts: int
    most_active_full_name: str | None
    most_active_count: int
    hardest_discipline_name: str | None
    hardest_discipline_avg: float | None


async def build_user_stats(session: AsyncSession, user_id: int) -> UserStats:
    """Зібрати статистику для конкретного користувача."""
    repo = AttemptRepository(session)
    return UserStats(
        attempts_count=await repo.count_user_attempts(user_id),
        average_percentage=await repo.user_average_percentage(user_id),
        best_percentage=await repo.user_best_percentage(user_id),
        recent=await repo.list_user_recent(user_id, RECENT_ATTEMPTS_LIMIT),
    )


async def build_global_stats(session: AsyncSession) -> GlobalStats:
    """Зібрати глобальну статистику для адміністратора."""
    repo = AttemptRepository(session)
    total = await repo.total_count()
    active = await repo.most_active_user()
    hardest = await repo.hardest_discipline()
    return GlobalStats(
        total_attempts=total,
        most_active_full_name=active[0].full_name if active else None,
        most_active_count=active[1] if active else 0,
        hardest_discipline_name=hardest[0].name if hardest else None,
        hardest_discipline_avg=hardest[1] if hardest else None,
    )


def format_user_stats(stats: UserStats) -> str:
    """Сформувати HTML-текст статистики користувача."""
    if stats.attempts_count == 0:
        return (
            "<b>Ваша статистика</b>\n"
            "Ви ще не пройшли жодної вікторини. Почніть із кнопки «📚 Обрати вікторину»."
        )
    lines = [
        "<b>Ваша статистика</b>",
        f"Пройдено вікторин: <b>{stats.attempts_count}</b>",
        f"Середній бал: <b>{stats.average_percentage}%</b>",
        f"Найкращий результат: <b>{stats.best_percentage}%</b>",
        "",
        "<b>Останні спроби:</b>",
    ]
    for attempt in stats.recent:
        percent = calculate_percentage(attempt.correct_count, attempt.total_count)
        when = attempt.finished_at.strftime("%Y-%m-%d %H:%M") if attempt.finished_at else "—"
        lines.append(
            f"• {when} — {attempt.discipline.name}: "
            f"{attempt.correct_count}/{attempt.total_count} ({percent}%)"
        )
    return "\n".join(lines)


def format_global_stats(stats: GlobalStats) -> str:
    """Сформувати HTML-текст зведеної статистики."""
    if stats.total_attempts == 0:
        return "<b>Загальна статистика</b>\nЩе немає жодного проходження."
    lines = [
        "<b>Загальна статистика</b>",
        f"Усього проходжень: <b>{stats.total_attempts}</b>",
    ]
    if stats.most_active_full_name:
        lines.append(
            f"Найактивніший користувач: <b>{stats.most_active_full_name}</b> "
            f"({stats.most_active_count} спроб)"
        )
    if stats.hardest_discipline_name is not None:
        lines.append(
            f"Найскладніша дисципліна: <b>{stats.hardest_discipline_name}</b> "
            f"(середній бал {stats.hardest_discipline_avg}%)"
        )
    return "\n".join(lines)
