"""Тести валідаторів вхідних даних."""
from __future__ import annotations

from config import (
    MAX_ANSWER_TEXT_LEN,
    MAX_DISCIPLINE_NAME_LEN,
    MAX_QUESTION_TEXT_LEN,
)
from utils.validators import (
    validate_answer_text,
    validate_discipline_name,
    validate_question_text,
)


class TestValidateQuestionText:
    def test_empty(self) -> None:
        result = validate_question_text("")
        assert result.is_valid is False
        assert result.error

    def test_only_whitespace(self) -> None:
        assert validate_question_text("    \n\t").is_valid is False

    def test_normal(self) -> None:
        result = validate_question_text("Скільки буде 2+2?")
        assert result.is_valid is True
        assert result.value == "Скільки буде 2+2?"

    def test_max_boundary(self) -> None:
        text = "a" * MAX_QUESTION_TEXT_LEN
        assert validate_question_text(text).is_valid is True

    def test_over_max(self) -> None:
        text = "a" * (MAX_QUESTION_TEXT_LEN + 1)
        assert validate_question_text(text).is_valid is False

    def test_trims_whitespace(self) -> None:
        result = validate_question_text("  hi  ")
        assert result.value == "hi"


class TestValidateAnswerText:
    def test_empty(self) -> None:
        assert validate_answer_text("").is_valid is False

    def test_normal(self) -> None:
        assert validate_answer_text("Варіант 1").is_valid is True

    def test_max_boundary(self) -> None:
        text = "a" * MAX_ANSWER_TEXT_LEN
        assert validate_answer_text(text).is_valid is True

    def test_over_max(self) -> None:
        text = "a" * (MAX_ANSWER_TEXT_LEN + 1)
        assert validate_answer_text(text).is_valid is False


class TestValidateDisciplineName:
    def test_empty(self) -> None:
        assert validate_discipline_name("   ").is_valid is False

    def test_normal(self) -> None:
        result = validate_discipline_name("Python")
        assert result.is_valid is True
        assert result.value == "Python"

    def test_max_boundary(self) -> None:
        name = "a" * MAX_DISCIPLINE_NAME_LEN
        assert validate_discipline_name(name).is_valid is True

    def test_over_max(self) -> None:
        name = "a" * (MAX_DISCIPLINE_NAME_LEN + 1)
        assert validate_discipline_name(name).is_valid is False
