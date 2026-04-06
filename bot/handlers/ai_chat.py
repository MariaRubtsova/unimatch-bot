from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db.database import AsyncSessionLocal
from services.ai_chat import get_ai_response
from bot.keyboards import main_menu, cancel_keyboard

router = Router()


class ChatState(StatesGroup):
    waiting_for_question = State()


@router.message(F.text == "💬 Задать вопрос")
async def enter_chat(message: Message, state: FSMContext) -> None:
    await state.set_state(ChatState.waiting_for_question)
    await message.answer(
        "💬 Задай любой вопрос об университетах и поступлении.\n\n"
        "Например: «Какие требования к GPA в TU Munich?» или "
        "«Программы MBA в Нидерландах дешевле 10 000 евро»\n\n"
        "Нажми ❌ Отмена, чтобы вернуться в меню.",
        reply_markup=cancel_keyboard(),
    )


@router.message(ChatState.waiting_for_question, F.text == "❌ Отмена")
async def cancel_chat(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Вернулись в главное меню.", reply_markup=main_menu())


@router.message(ChatState.waiting_for_question)
async def handle_question(message: Message, state: FSMContext) -> None:
    await message.answer("🤔 Ищу информацию...")

    async with AsyncSessionLocal() as session:
        answer = await get_ai_response(message.text, session)

    await message.answer(answer, reply_markup=cancel_keyboard())
