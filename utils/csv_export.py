"""Експорт спроб у формат CSV."""
from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from database.models import Attempt

CSV_HEADERS = [
    "ID",
    "Користувач",
    "Telegram ID",
    "Дисципліна",
    "Правильних",
    "Усього",
    "Відсоток",
    "Завершено",
]


def build_attempts_csv(attempts: Iterable[Attempt]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(CSV_HEADERS)
    for attempt in attempts:
        percent = (
            round((attempt.correct_count / attempt.total_count) * 100, 2)
            if attempt.total_count
            else 0.0
        )
        finished = (
            attempt.finished_at.strftime("%Y-%m-%d %H:%M:%S")
            if attempt.finished_at
            else ""
        )
        writer.writerow(
            [
                attempt.id,
                attempt.user.full_name if attempt.user else "",
                attempt.user.telegram_id if attempt.user else "",
                attempt.discipline.name if attempt.discipline else "",
                attempt.correct_count,
                attempt.total_count,
                percent,
                finished,
            ]
        )
    return ("﻿" + buffer.getvalue()).encode("utf-8")
