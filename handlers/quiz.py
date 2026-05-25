"""Обробники сценарію проходження вікторини."""
from __future__ import annotations

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import load_config
from database.engine import async_session
from database.repositories import (
    AttemptRepository,
    DisciplineRepository,
    QuestionRepository,
    UserRepository,
)
from keyboards.user_kb import (
    BTN_QUIZ,
    answers_kb,
    disciplines_in_section_kb,
    get_section,
    sections_kb,
)
from services.quiz_service import format_summary, select_questions
from states.quiz_states import QuizStates

router = Router()
logger = logging.getLogger(__name__)
_config = load_config()

CB_QUIZ_SEC = "quiz_sec"
CB_QUIZ_DISC = "quiz_disc"
CB_QUIZ_BACK = "quiz_back_sec"


@router.message(Command("quiz"))
@router.message(F.text == BTN_QUIZ)
async def cmd_quiz(message: Message, state: FSMContext) -> None:
    """Показати список розділів вікторини."""
    await state.set_state(QuizStates.choosing_section)
    await message.answer(
        "Оберіть розділ:",
        reply_markup=sections_kb(prefix=CB_QUIZ_SEC),
    )


@router.callback_query(
    QuizStates.choosing_section, F.data.startswith(f"{CB_QUIZ_SEC}:")
)
async def on_section_chosen(call: CallbackQuery, state: FSMContext) -> None:
    """Користувач обрав розділ — показати дисципліни цього розділу."""
    if call.data is None or call.message is None:
        await call.answer()
        return
    section_key = call.data.split(":", 1)[1]
    section = get_section(section_key)
    if section is None:
        await call.answer("Розділ не знайдено", show_alert=True)
        return
    title, names = section

    async with async_session() as session:
        all_disciplines = await DisciplineRepository(session).list_active()
    available = [d for d in all_disciplines if d.name in set(names)]
    if not available:
        await call.answer()
        await call.message.edit_text(
            f"У розділі <b>{title}</b> поки немає доступних дисциплін."
        )
        await state.clear()
        return

    await state.update_data(section_key=section_key)
    await state.set_state(QuizStates.choosing_discipline)
    await call.answer()
    await call.message.edit_text(
        f"Розділ: <b>{title}</b>\nОберіть дисципліну:",
        reply_markup=disciplines_in_section_kb(
            all_disciplines,
            section_key=section_key,
            disc_prefix=CB_QUIZ_DISC,
            back_callback=CB_QUIZ_BACK,
        ),
    )


@router.callback_query(QuizStates.choosing_discipline, F.data == CB_QUIZ_BACK)
async def on_back_to_sections(call: CallbackQuery, state: FSMContext) -> None:
    """Повернутися від списку дисциплін до списку розділів."""
    if call.message is None:
        await call.answer()
        return
    await state.set_state(QuizStates.choosing_section)
    await call.answer()
    await call.message.edit_text(
        "Оберіть розділ:", reply_markup=sections_kb(prefix=CB_QUIZ_SEC)
    )


@router.callback_query(QuizStates.choosing_discipline, F.data.startswith(f"{CB_QUIZ_DISC}:"))
async def on_discipline_chosen(call: CallbackQuery, state: FSMContext) -> None:
    """Користувач обрав дисципліну — підготувати питання і надіслати перше."""
    if call.data is None or call.message is None or call.from_user is None:
        await call.answer()
        return
    try:
        discipline_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Некоректний вибір", show_alert=True)
        return

    async with async_session() as session:
        disc_repo = DisciplineRepository(session)
        discipline = await disc_repo.get_by_id(discipline_id)
        if discipline is None or not discipline.is_active:
            await call.answer("Дисципліну не знайдено", show_alert=True)
            return
        q_repo = QuestionRepository(session)
        all_questions = await q_repo.list_by_discipline(discipline_id)

    if not all_questions:
        await call.answer()
        await call.message.edit_text(
            "У цій дисципліні поки немає питань. Оберіть іншу."
        )
        await state.clear()
        return

    selected = select_questions(all_questions, _config.quiz_length)
    question_ids = [q.id for q in selected]

    await state.update_data(
        discipline_id=discipline_id,
        question_ids=question_ids,
        current_index=0,
        correct_count=0,
        started_at=datetime.utcnow().isoformat(),
    )
    await state.set_state(QuizStates.answering_question)
    await call.answer()
    await call.message.edit_text(
        f"Дисципліна: <b>{discipline.name}</b>\n"
        f"Питань буде: <b>{len(question_ids)}</b>\nПочнемо!"
    )
    await _send_question(call, state)


async def _send_question(call: CallbackQuery, state: FSMContext) -> None:
    """Надіслати поточне питання користувачу."""
    if call.message is None:
        return
    data = await state.get_data()
    idx: int = data["current_index"]
    question_ids: list[int] = data["question_ids"]
    if idx >= len(question_ids):
        await _finish_quiz(call, state)
        return
    qid = question_ids[idx]
    async with async_session() as session:
        question = await QuestionRepository(session).get_with_answers(qid)
    if question is None:
        await call.message.answer("Не вдалося завантажити питання.")
        await state.clear()
        return
    text = (
        f"<b>Питання {idx + 1} з {len(question_ids)}</b>\n\n"
        f"{question.text}"
    )
    await call.message.answer(
        text, reply_markup=answers_kb(question.id, question.answers)
    )


@router.callback_query(QuizStates.answering_question, F.data.startswith("answer:"))
async def on_answer(call: CallbackQuery, state: FSMContext) -> None:
    """Обробити вибір варіанта відповіді."""
    if call.data is None or call.message is None or call.from_user is None:
        await call.answer()
        return
    try:
        _, qid_raw, aid_raw = call.data.split(":")
        question_id = int(qid_raw)
        answer_id = int(aid_raw)
    except ValueError:
        await call.answer("Некоректна відповідь", show_alert=True)
        return

    async with async_session() as session:
        question = await QuestionRepository(session).get_with_answers(question_id)
    if question is None:
        await call.answer("Питання не знайдено", show_alert=True)
        return

    chosen = next((a for a in question.answers if a.id == answer_id), None)
    correct = next((a for a in question.answers if a.is_correct), None)
    if chosen is None or correct is None:
        await call.answer("Помилка варіантів відповіді", show_alert=True)
        return

    data = await state.get_data()
    correct_count: int = data["correct_count"]
    idx: int = data["current_index"]

    if chosen.is_correct:
        correct_count += 1
        verdict = "✅ Правильно"
    else:
        verdict = f"❌ Неправильно. Правильна: <b>{correct.text}</b>"

    new_text = (
        f"<b>Питання {idx + 1}</b>\n\n"
        f"{question.text}\n\n"
        f"Ваша відповідь: {chosen.text}\n"
        f"{verdict}"
    )
    await call.message.edit_text(new_text)
    await call.answer()

    await state.update_data(correct_count=correct_count, current_index=idx + 1)
    await _send_question(call, state)


async def _finish_quiz(call: CallbackQuery, state: FSMContext) -> None:
    """Зафіксувати спробу у БД і повідомити підсумок."""
    if call.message is None or call.from_user is None:
        return
    data = await state.get_data()
    correct = int(data["correct_count"])
    total = len(data["question_ids"])
    discipline_id = int(data["discipline_id"])
    started_at = datetime.fromisoformat(data["started_at"])
    finished_at = datetime.utcnow()

    async with async_session() as session:
        user = await UserRepository(session).get_by_telegram_id(call.from_user.id)
        if user is not None:
            await AttemptRepository(session).create(
                user_id=user.id,
                discipline_id=discipline_id,
                correct_count=correct,
                total_count=total,
                started_at=started_at,
                finished_at=finished_at,
            )
    logger.info(
        "tg=%s завершив вікторину: %s/%s (дисципліна id=%s)",
        call.from_user.id,
        correct,
        total,
        discipline_id,
    )
    await state.clear()
    await call.message.answer(format_summary(correct, total))
