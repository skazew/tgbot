"""Обробники адмін-сценаріїв: дисципліни, питання, статистика, експорт."""
from __future__ import annotations

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Message,
)

from config import (
    MAX_ANSWER_OPTIONS,
    MIN_ANSWER_OPTIONS,
    QUESTIONS_PAGE_SIZE,
    load_config,
)
from database.engine import async_session
from database.repositories import (
    AttemptRepository,
    DisciplineRepository,
    QuestionRepository,
    UserRepository,
)
from keyboards.admin_kb import (
    CB_ADMIN_DISC,
    CB_ADMIN_EXPORT,
    CB_ADMIN_QUESTIONS,
    CB_ADMIN_STATS,
    CB_DISC_ADD,
    CB_DISC_DELETE,
    CB_DISC_LIST,
    CB_DISC_RENAME,
    CB_DISC_TOGGLE,
    CB_Q_ADD,
    CB_Q_LIST,
    add_more_answers_kb,
    admin_main_kb,
    confirm_kb,
    correct_answer_kb,
    disciplines_admin_kb,
    disciplines_pick_kb,
    questions_admin_kb,
    questions_page_kb,
)
from keyboards.user_kb import BTN_ADMIN
from services.stats_service import build_global_stats, format_global_stats
from states.admin_states import (
    AddDisciplineStates,
    AddQuestionStates,
    EditQuestionStates,
    RenameDisciplineStates,
)
from utils.csv_export import build_attempts_csv
from utils.validators import (
    validate_answer_text,
    validate_discipline_name,
    validate_question_text,
)

router = Router()
logger = logging.getLogger(__name__)
_config = load_config()


async def _is_admin(telegram_id: int) -> bool:
    if telegram_id in _config.admin_ids:
        return True
    async with async_session() as session:
        return await UserRepository(session).is_admin(telegram_id, _config.admin_ids)


async def _guard(message_or_call: Message | CallbackQuery) -> bool:
    user = message_or_call.from_user
    if user is None or not await _is_admin(user.id):
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.answer("Доступ лише для адміністраторів.", show_alert=True)
        else:
            await message_or_call.answer("Доступ лише для адміністраторів.")
        return False
    return True


# ---------- Адмін-меню ----------

@router.message(Command("admin"))
@router.message(F.text == BTN_ADMIN)
async def cmd_admin(message: Message) -> None:
    if not await _guard(message):
        return
    await message.answer("<b>Меню адміністратора</b>", reply_markup=admin_main_kb())


@router.callback_query(F.data == CB_ADMIN_DISC)
async def cb_admin_disc(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "<b>Дисципліни</b>", reply_markup=disciplines_admin_kb()
        )


@router.callback_query(F.data == CB_ADMIN_QUESTIONS)
async def cb_admin_questions(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "<b>Питання</b>", reply_markup=questions_admin_kb()
        )


@router.callback_query(F.data == CB_ADMIN_STATS)
@router.message(Command("stats_all"))
async def cmd_stats_all(event: Message | CallbackQuery) -> None:
    if not await _guard(event):
        return
    async with async_session() as session:
        stats = await build_global_stats(session)
    text = format_global_stats(stats)
    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message:
            await event.message.edit_text(text)
    else:
        await event.answer(text)


@router.callback_query(F.data == CB_ADMIN_EXPORT)
@router.message(Command("export"))
async def cmd_export(event: Message | CallbackQuery) -> None:
    if not await _guard(event):
        return
    async with async_session() as session:
        attempts = await AttemptRepository(session).list_all_for_export()
    if not attempts:
        text = "Немає даних для експорту."
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        else:
            await event.answer(text)
        return
    data = build_attempts_csv(attempts)
    file = BufferedInputFile(
        data, filename=f"attempts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    target = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()
    if target is not None:
        await target.answer_document(file, caption="Експорт спроб")
    logger.info("Адмін tg=%s викликав експорт", event.from_user.id if event.from_user else "?")


# ---------- Створення дисципліни ----------

@router.callback_query(F.data == CB_DISC_ADD)
async def cb_disc_add(call: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(call):
        return
    await call.answer()
    await state.set_state(AddDisciplineStates.entering_name)
    if call.message:
        await call.message.answer("Введіть назву нової дисципліни:")


@router.message(AddDisciplineStates.entering_name)
async def on_disc_name(message: Message, state: FSMContext) -> None:
    result = validate_discipline_name(message.text or "")
    if not result.is_valid:
        await message.answer(f"{result.error}\nСпробуйте ще раз:")
        return
    async with async_session() as session:
        repo = DisciplineRepository(session)
        if await repo.get_by_name(result.value or "") is not None:
            await message.answer("Дисципліна з такою назвою вже існує. Введіть іншу:")
            return
        discipline = await repo.create(result.value or "")
    await state.clear()
    logger.info(
        "Адмін tg=%s створив дисципліну '%s' (id=%s)",
        message.from_user.id if message.from_user else "?",
        discipline.name,
        discipline.id,
    )
    await message.answer(f"Дисципліну <b>{discipline.name}</b> створено.")


# ---------- Список дисциплін ----------

@router.callback_query(F.data == CB_DISC_LIST)
async def cb_disc_list(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_all()
    if not disciplines:
        text = "Дисциплін ще немає."
    else:
        lines = ["<b>Дисципліни:</b>"]
        for d in disciplines:
            marker = "✅" if d.is_active else "⛔"
            lines.append(f"{marker} #{d.id} {d.name}")
        text = "\n".join(lines)
    await call.answer()
    if call.message:
        await call.message.edit_text(text, reply_markup=disciplines_admin_kb())


# ---------- Перейменування ----------

@router.callback_query(F.data == CB_DISC_RENAME)
async def cb_disc_rename(call: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_all()
    if not disciplines:
        await call.answer("Немає дисциплін", show_alert=True)
        return
    await state.set_state(RenameDisciplineStates.picking)
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "Оберіть дисципліну:",
            reply_markup=disciplines_pick_kb(disciplines, "disc_rename_pick"),
        )


@router.callback_query(
    RenameDisciplineStates.picking, F.data.startswith("disc_rename_pick:")
)
async def cb_disc_rename_pick(call: CallbackQuery, state: FSMContext) -> None:
    if call.data is None:
        return
    discipline_id = int(call.data.split(":", 1)[1])
    await state.update_data(discipline_id=discipline_id)
    await state.set_state(RenameDisciplineStates.entering_new_name)
    await call.answer()
    if call.message:
        await call.message.answer("Введіть нову назву:")


@router.message(RenameDisciplineStates.entering_new_name)
async def on_disc_new_name(message: Message, state: FSMContext) -> None:
    result = validate_discipline_name(message.text or "")
    if not result.is_valid:
        await message.answer(f"{result.error}\nСпробуйте ще раз:")
        return
    data = await state.get_data()
    discipline_id = int(data["discipline_id"])
    async with async_session() as session:
        repo = DisciplineRepository(session)
        if await repo.get_by_name(result.value or "") is not None:
            await message.answer("Така назва вже існує. Введіть іншу:")
            return
        updated = await repo.rename(discipline_id, result.value or "")
    await state.clear()
    if updated is None:
        await message.answer("Дисципліну не знайдено.")
    else:
        await message.answer(f"Нова назва: <b>{updated.name}</b>")


# ---------- Активність ----------

@router.callback_query(F.data == CB_DISC_TOGGLE)
async def cb_disc_toggle(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_all()
    if not disciplines:
        await call.answer("Немає дисциплін", show_alert=True)
        return
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "Натисніть, щоб перемкнути активність:",
            reply_markup=disciplines_pick_kb(disciplines, "disc_toggle_pick"),
        )


@router.callback_query(F.data.startswith("disc_toggle_pick:"))
async def cb_disc_toggle_pick(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    discipline_id = int(call.data.split(":", 1)[1])
    async with async_session() as session:
        repo = DisciplineRepository(session)
        d = await repo.get_by_id(discipline_id)
        if d is None:
            await call.answer("Не знайдено", show_alert=True)
            return
        updated = await repo.set_active(discipline_id, not d.is_active)
    await call.answer(
        f"{'Активовано' if updated and updated.is_active else 'Деактивовано'}"
    )
    if call.message and updated is not None:
        await call.message.edit_text(
            f"Дисципліна <b>{updated.name}</b>: "
            f"{'активна' if updated.is_active else 'неактивна'}",
            reply_markup=disciplines_admin_kb(),
        )


# ---------- Видалення ----------

@router.callback_query(F.data == CB_DISC_DELETE)
async def cb_disc_delete(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_all()
    if not disciplines:
        await call.answer("Немає дисциплін", show_alert=True)
        return
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "Оберіть дисципліну для видалення:",
            reply_markup=disciplines_pick_kb(disciplines, "disc_delete_pick"),
        )


@router.callback_query(F.data.startswith("disc_delete_pick:"))
async def cb_disc_delete_pick(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    discipline_id = int(call.data.split(":", 1)[1])
    async with async_session() as session:
        d = await DisciplineRepository(session).get_by_id(discipline_id)
    if d is None:
        await call.answer("Не знайдено", show_alert=True)
        return
    await call.answer()
    if call.message:
        await call.message.edit_text(
            f"Видалити дисципліну <b>{d.name}</b> разом із усіма питаннями?",
            reply_markup=confirm_kb(
                yes_data=f"disc_delete_yes:{discipline_id}",
                no_data="disc_delete_no",
            ),
        )


@router.callback_query(F.data.startswith("disc_delete_yes:"))
async def cb_disc_delete_yes(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    discipline_id = int(call.data.split(":", 1)[1])
    async with async_session() as session:
        ok = await DisciplineRepository(session).delete(discipline_id)
    await call.answer("Видалено" if ok else "Не знайдено", show_alert=True)
    if call.message:
        await call.message.edit_text(
            "Видалено." if ok else "Не вдалося видалити.",
            reply_markup=disciplines_admin_kb(),
        )
    logger.info(
        "Адмін tg=%s видалив дисципліну id=%s",
        call.from_user.id if call.from_user else "?",
        discipline_id,
    )


@router.callback_query(F.data == "disc_delete_no")
async def cb_disc_delete_no(call: CallbackQuery) -> None:
    await call.answer("Скасовано")
    if call.message:
        await call.message.edit_text("Скасовано.", reply_markup=disciplines_admin_kb())


# ---------- Додавання питання ----------

@router.callback_query(F.data == CB_Q_ADD)
async def cb_q_add(call: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_all()
    if not disciplines:
        await call.answer("Спочатку створіть дисципліну", show_alert=True)
        return
    await state.set_state(AddQuestionStates.picking_discipline)
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "Оберіть дисципліну для нового питання:",
            reply_markup=disciplines_pick_kb(disciplines, "q_add_disc"),
        )


@router.callback_query(
    AddQuestionStates.picking_discipline, F.data.startswith("q_add_disc:")
)
async def on_q_add_disc(call: CallbackQuery, state: FSMContext) -> None:
    if call.data is None:
        return
    discipline_id = int(call.data.split(":", 1)[1])
    await state.update_data(discipline_id=discipline_id, answers=[])
    await state.set_state(AddQuestionStates.entering_text)
    await call.answer()
    if call.message:
        await call.message.answer("Введіть текст питання:")


@router.message(AddQuestionStates.entering_text)
async def on_q_text(message: Message, state: FSMContext) -> None:
    result = validate_question_text(message.text or "")
    if not result.is_valid:
        await message.answer(f"{result.error}\nСпробуйте ще раз:")
        return
    await state.update_data(question_text=result.value, answers=[])
    await state.set_state(AddQuestionStates.entering_answer)
    await message.answer(
        f"Введіть варіант відповіді №1 (мінімум {MIN_ANSWER_OPTIONS}, "
        f"максимум {MAX_ANSWER_OPTIONS}):"
    )


@router.message(AddQuestionStates.entering_answer)
async def on_q_answer(message: Message, state: FSMContext) -> None:
    result = validate_answer_text(message.text or "")
    if not result.is_valid:
        await message.answer(f"{result.error}\nСпробуйте ще раз:")
        return
    data = await state.get_data()
    answers: list[str] = list(data.get("answers", []))
    answers.append(result.value or "")
    await state.update_data(answers=answers)

    if len(answers) >= MAX_ANSWER_OPTIONS:
        await message.answer(
            f"Досягнуто максимуму ({MAX_ANSWER_OPTIONS}). Оберіть правильний варіант:",
            reply_markup=correct_answer_kb(len(answers)),
        )
        await state.set_state(AddQuestionStates.picking_correct)
        return

    if len(answers) >= MIN_ANSWER_OPTIONS:
        await message.answer(
            f"Збережено варіант {len(answers)}. Введіть наступний "
            f"або натисніть кнопку нижче, щоб завершити.",
            reply_markup=add_more_answers_kb(),
        )
    else:
        await message.answer(f"Збережено. Введіть варіант №{len(answers) + 1}:")


@router.callback_query(
    AddQuestionStates.entering_answer, F.data == "answers_done"
)
async def on_q_answers_done(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    answers: list[str] = list(data.get("answers", []))
    if len(answers) < MIN_ANSWER_OPTIONS:
        await call.answer(
            f"Потрібно щонайменше {MIN_ANSWER_OPTIONS} варіанти", show_alert=True
        )
        return
    await state.set_state(AddQuestionStates.picking_correct)
    await call.answer()
    if call.message:
        await call.message.answer(
            "Оберіть номер правильного варіанта:",
            reply_markup=correct_answer_kb(len(answers)),
        )


@router.callback_query(
    AddQuestionStates.picking_correct, F.data.startswith("correct:")
)
async def on_q_correct(call: CallbackQuery, state: FSMContext) -> None:
    if call.data is None:
        return
    correct_index = int(call.data.split(":", 1)[1])
    data = await state.get_data()
    answers: list[str] = list(data.get("answers", []))
    if correct_index < 0 or correct_index >= len(answers):
        await call.answer("Невалідний номер", show_alert=True)
        return
    discipline_id = int(data["discipline_id"])
    text = str(data["question_text"])
    pairs = [(a, i == correct_index) for i, a in enumerate(answers)]
    async with async_session() as session:
        question = await QuestionRepository(session).create_with_answers(
            discipline_id=discipline_id, text=text, answers=pairs
        )
    await state.clear()
    await call.answer("Збережено")
    if call.message:
        await call.message.answer(
            f"Питання #{question.id} збережено ({len(answers)} варіантів)."
        )
    logger.info(
        "Адмін tg=%s додав питання id=%s у дисципліну id=%s",
        call.from_user.id if call.from_user else "?",
        question.id,
        discipline_id,
    )


# ---------- Список / редагування / видалення питань ----------

@router.callback_query(F.data == CB_Q_LIST)
async def cb_q_list(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        disciplines = await DisciplineRepository(session).list_all()
    if not disciplines:
        await call.answer("Немає дисциплін", show_alert=True)
        return
    await call.answer()
    if call.message:
        await call.message.edit_text(
            "Оберіть дисципліну:",
            reply_markup=disciplines_pick_kb(disciplines, "q_list_disc"),
        )


@router.callback_query(F.data.startswith("q_list_disc:"))
async def cb_q_list_disc(call: CallbackQuery) -> None:
    if call.data is None:
        return
    discipline_id = int(call.data.split(":", 1)[1])
    await _render_questions_page(call, discipline_id, page=0)


@router.callback_query(F.data.startswith("q_page:"))
async def cb_q_page(call: CallbackQuery) -> None:
    if call.data is None:
        return
    _, disc_raw, page_raw = call.data.split(":")
    await _render_questions_page(call, int(disc_raw), int(page_raw))


async def _render_questions_page(
    call: CallbackQuery, discipline_id: int, page: int
) -> None:
    if not await _guard(call):
        return
    async with async_session() as session:
        q_repo = QuestionRepository(session)
        total = await q_repo.count_by_discipline(discipline_id)
        offset = page * QUESTIONS_PAGE_SIZE
        questions = await q_repo.page_by_discipline(
            discipline_id, offset, QUESTIONS_PAGE_SIZE
        )
        discipline = await DisciplineRepository(session).get_by_id(discipline_id)
    if discipline is None:
        await call.answer("Дисципліну не знайдено", show_alert=True)
        return
    if total == 0:
        await call.answer()
        if call.message:
            await call.message.edit_text(
                f"<b>{discipline.name}</b>\nПитань ще немає.",
                reply_markup=questions_admin_kb(),
            )
        return
    total_pages = (total + QUESTIONS_PAGE_SIZE - 1) // QUESTIONS_PAGE_SIZE
    await call.answer()
    if call.message:
        await call.message.edit_text(
            f"<b>{discipline.name}</b> — питання (стор. {page + 1}/{total_pages}):",
            reply_markup=questions_page_kb(
                questions, discipline_id, page, total_pages
            ),
        )


@router.callback_query(F.data.startswith("q_view:"))
async def cb_q_view(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    qid = int(call.data.split(":", 1)[1])
    async with async_session() as session:
        question = await QuestionRepository(session).get_with_answers(qid)
    if question is None:
        await call.answer("Питання не знайдено", show_alert=True)
        return
    lines = [f"<b>Питання #{question.id}</b>", question.text, "", "<b>Варіанти:</b>"]
    for i, a in enumerate(question.answers, start=1):
        mark = "✅" if a.is_correct else "▫️"
        lines.append(f"{mark} {i}. {a.text}")
    await call.answer()
    if call.message:
        await call.message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("q_edit:"))
async def cb_q_edit(call: CallbackQuery, state: FSMContext) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    qid = int(call.data.split(":", 1)[1])
    await state.update_data(question_id=qid)
    await state.set_state(EditQuestionStates.entering_new_text)
    await call.answer()
    if call.message:
        await call.message.answer("Введіть новий текст питання:")


@router.message(EditQuestionStates.entering_new_text)
async def on_q_edit_text(message: Message, state: FSMContext) -> None:
    result = validate_question_text(message.text or "")
    if not result.is_valid:
        await message.answer(f"{result.error}\nСпробуйте ще раз:")
        return
    data = await state.get_data()
    qid = int(data["question_id"])
    async with async_session() as session:
        updated = await QuestionRepository(session).update_text(qid, result.value or "")
    await state.clear()
    if updated is None:
        await message.answer("Питання не знайдено.")
    else:
        await message.answer(f"Питання #{updated.id} оновлено.")


@router.callback_query(F.data.startswith("q_del:"))
async def cb_q_del(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    qid = int(call.data.split(":", 1)[1])
    await call.answer()
    if call.message:
        await call.message.answer(
            f"Видалити питання #{qid}?",
            reply_markup=confirm_kb(
                yes_data=f"q_del_yes:{qid}", no_data="q_del_no"
            ),
        )


@router.callback_query(F.data.startswith("q_del_yes:"))
async def cb_q_del_yes(call: CallbackQuery) -> None:
    if not await _guard(call):
        return
    if call.data is None:
        return
    qid = int(call.data.split(":", 1)[1])
    async with async_session() as session:
        ok = await QuestionRepository(session).delete(qid)
    await call.answer("Видалено" if ok else "Не знайдено", show_alert=True)
    if call.message:
        await call.message.edit_text(
            "Видалено." if ok else "Не знайдено.",
        )
    logger.info(
        "Адмін tg=%s видалив питання id=%s",
        call.from_user.id if call.from_user else "?",
        qid,
    )


@router.callback_query(F.data == "q_del_no")
async def cb_q_del_no(call: CallbackQuery) -> None:
    await call.answer("Скасовано")
    if call.message:
        await call.message.edit_text("Скасовано.")


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()
