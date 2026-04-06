from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.auth import get_current_user_id
from db.database import get_db
from db.models import ChecklistItem, Program, UserDeadline
from datetime import date

router = APIRouter(prefix="/checklist", tags=["checklist"])


class ChecklistItemOut(BaseModel):
    id: int
    item_name: str
    hint: Optional[str]
    is_done: bool


class ChecklistResponse(BaseModel):
    program_name: str
    university_name: str
    deadline: Optional[str]
    days_left: int
    items: list[ChecklistItemOut]


class ToggleRequest(BaseModel):
    is_done: bool


@router.get("/{program_id}", response_model=ChecklistResponse)
async def get_checklist(
    program_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    prog_result = await db.execute(select(Program).where(Program.id == program_id))
    program = prog_result.scalar_one_or_none()

    items_result = await db.execute(
        select(ChecklistItem)
        .where(ChecklistItem.user_id == user_id)
        .where(ChecklistItem.program_id == program_id)
        .order_by(ChecklistItem.id)
    )
    items = items_result.scalars().all()

    deadline_result = await db.execute(
        select(UserDeadline)
        .where(UserDeadline.user_id == user_id)
        .where(UserDeadline.program_id == program_id)
        .limit(1)
    )
    ud = deadline_result.scalar_one_or_none()

    today = date.today()
    deadline_str = str(ud.deadline) if ud and ud.deadline else None
    days_left = (ud.deadline - today).days if ud and ud.deadline else 0

    return ChecklistResponse(
        program_name=program.program_name if program else "Программа",
        university_name=program.university_name if program else "",
        deadline=deadline_str,
        days_left=days_left,
        items=[
            ChecklistItemOut(id=i.id, item_name=i.item_name, hint=i.hint, is_done=i.is_done)
            for i in items
        ],
    )


@router.patch("/{item_id}")
async def toggle_item(
    item_id: int,
    body: ToggleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(ChecklistItem)
        .where(ChecklistItem.id == item_id)
        .where(ChecklistItem.user_id == user_id)
        .values(is_done=body.is_done)
    )
    await db.commit()
    return {"status": "ok"}
