"""FSM-стани адмін-сценаріїв."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AddDisciplineStates(StatesGroup):

    entering_name = State()


class RenameDisciplineStates(StatesGroup):

    picking = State()
    entering_new_name = State()


class AddQuestionStates(StatesGroup):

    picking_discipline = State()
    entering_text = State()
    entering_answer = State()
    picking_correct = State()


class EditQuestionStates(StatesGroup):

    entering_new_text = State()
