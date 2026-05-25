"""FSM-стани сценарію вікторини."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    """Стани проходження вікторини."""

    choosing_section = State()
    choosing_discipline = State()
    answering_question = State()
