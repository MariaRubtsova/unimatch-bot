from datetime import date
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import UserDeadline, Program
from services.ics_export import generate_ics

router = Router()


@router.message(Command("deadlines"))
async def cmd_deadlines(message: Message) -> None:
    user_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserDeadline, Program)
            .join(Program, UserDeadline.program_id == Program.id)
            .where(UserDeadline.user_id == user_id)
            .where(UserDeadline.deadline >= date.today())
            .order_by(UserDeadline.deadline.asc())
        )
        rows = result.all()

    if not rows:
        await message.answer("У тебя пока нет сохранённых дедлайнов.\nДобавь программы через «Подобрать программы».")
        return

    lines = ["📅 <b>Твои дедлайны:</b>\n"]
    for ud, prog in rows:
        days_left = (ud.deadline - date.today()).days
        emoji = "🔴" if days_left <= 7 else "🟡" if days_left <= 30 else "🟢"
        lines.append(
            f"{emoji} <b>{prog.program_name}</b>\n"
            f"   {prog.university_name} • {ud.deadline.strftime('%d.%m.%Y')} "
            f"(через {days_left} дн.)"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    user_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserDeadline, Program)
            .join(Program, UserDeadline.program_id == Program.id)
            .where(UserDeadline.user_id == user_id)
            .order_by(UserDeadline.deadline.asc())
        )
        rows = result.all()

    if not rows:
        await message.answer("Нет дедлайнов для экспорта.")
        return

    deadlines_data = [
        {
            "program_name": prog.program_name,
            "university_name": prog.university_name,
            "deadline": ud.deadline,
            "url": prog.url,
        }
        for ud, prog in rows
    ]

    ics_bytes = generate_ics(deadlines_data)
    await message.answer_document(
        BufferedInputFile(ics_bytes, filename="unimatch_deadlines.ics"),
        caption="📆 Открой файл в Google Calendar, Apple Calendar или Outlook.",
    )
