from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal
from db.models import User
from bot.keyboards import main_menu, admin_button

ADMIN_USER_ID = 1379996156
from sqlalchemy.dialects.postgresql import insert

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        await _upsert_user(session, message)

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я помогу тебе подобрать программы для поступления в зарубежные университеты.\n\n"
        "Нажми «Подобрать программы», чтобы начать поиск.",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — главное меню\n"
        "/profile — твой профиль\n"
        "/deadlines — сохранённые дедлайны\n"
        "/export — скачать .ics файл с дедлайнами\n"
        "/help — эта справка\n\n"
        "Или используй кнопки меню ниже.",
        parse_mode="HTML",
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await message.answer(
        "👤 Твой профиль хранится в Mini App.\n"
        "Нажми «Подобрать программы», чтобы обновить данные.",
        reply_markup=main_menu(),
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if message.from_user.id != ADMIN_USER_ID:
        return
    await message.answer(
        "⚡ <b>Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=admin_button(),
    )


async def _upsert_user(session: AsyncSession, message: Message) -> None:
    stmt = insert(User).values(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    ).on_conflict_do_update(
        index_elements=["user_id"],
        set_={"last_active": User.last_active},
    )
    await session.execute(stmt)
    await session.commit()
