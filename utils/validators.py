"""Валідація користувацького вводу для адмін-сценаріїв."""
from __future__ import annotations

from dataclasses import dataclass

from config import (
    MAX_ANSWER_TEXT_LEN,
    MAX_DISCIPLINE_NAME_LEN,
    MAX_QUESTION_TEXT_LEN,
)


@dataclass(frozen=True)
class ValidationResult:

    is_valid: bool
    error: str | None = None
    value: str | None = None


def _clean(text: str) -> str:
    return (text or "").strip()


def validate_question_text(text: str) -> ValidationResult:
    cleaned = _clean(text)
    if not cleaned:
        return ValidationResult(False, "Текст питання не може бути порожнім.")
    if len(cleaned) > MAX_QUESTION_TEXT_LEN:
        return ValidationResult(
            False,
            f"Текст питання задовгий (максимум {MAX_QUESTION_TEXT_LEN} символів).",
        )
    return ValidationResult(True, None, cleaned)


def validate_answer_text(text: str) -> ValidationResult:
    cleaned = _clean(text)
    if not cleaned:
        return ValidationResult(False, "Текст відповіді не може бути порожнім.")
    if len(cleaned) > MAX_ANSWER_TEXT_LEN:
        return ValidationResult(
            False,
            f"Текст відповіді задовгий (максимум {MAX_ANSWER_TEXT_LEN} символів).",
        )
    return ValidationResult(True, None, cleaned)


def validate_discipline_name(text: str) -> ValidationResult:
    cleaned = _clean(text)
    if not cleaned:
        return ValidationResult(False, "Назва дисципліни не може бути порожньою.")
    if len(cleaned) > MAX_DISCIPLINE_NAME_LEN:
        return ValidationResult(
            False,
            f"Назва задовга (максимум {MAX_DISCIPLINE_NAME_LEN} символів).",
        )
    return ValidationResult(True, None, cleaned)
