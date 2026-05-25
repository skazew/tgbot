"""FSM-стани адмін-сценаріїв."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AddDisciplineStates(StatesGroup):
    """Стани створення дисципліни."""

    entering_name = State()


class RenameDisciplineStates(StatesGroup):
    """Стани перейменування дисципліни."""

    picking = State()
    entering_new_name = State()


class AddQuestionStates(StatesGroup):
    """Стани створення питання."""

    picking_discipline = State()
    entering_text = State()
    entering_answer = State()
    picking_correct = State()


class EditQuestionStates(StatesGroup):
    """Стани редагування тексту питання."""

    entering_new_text = State()
