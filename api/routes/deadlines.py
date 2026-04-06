from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.auth import get_current_user_id
from db.database import get_db
from db.models import UserDeadline, Program, ChecklistItem, DocumentTemplate, User
from sqlalchemy.dialects.postgresql import insert as pg_insert

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


class DeadlineAdd(BaseModel):
    program_ids: list[int]


class DeadlineItem(BaseModel):
    id: int
    program_id: int
    program_name: str
    university_name: str
    country: str
    deadline: Optional[str]
    days_left: int


@router.get("/", response_model=list[DeadlineItem])
async def get_deadlines(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserDeadline, Program)
        .join(Program, UserDeadline.program_id == Program.id)
        .where(UserDeadline.user_id == user_id)
        .order_by(UserDeadline.deadline.asc())
    )
    rows = result.all()
    today = date.today()
    return [
        DeadlineItem(
            id=ud.id,
            program_id=ud.program_id,
            program_name=prog.program_name,
            university_name=prog.university_name,
            country=prog.country,
            deadline=str(ud.deadline) if ud.deadline else None,
            days_left=(ud.deadline - today).days if ud.deadline else 0,
        )
        for ud, prog in rows
    ]


@router.post("/")
async def add_deadlines(
    body: DeadlineAdd,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Ensure user exists
    await db.execute(
        pg_insert(User).values(user_id=user_id).on_conflict_do_nothing()
    )

    for program_id in body.program_ids:
        prog_result = await db.execute(select(Program).where(Program.id == program_id))
        program = prog_result.scalar_one_or_none()
        if not program:
            continue

        # Add deadline
        stmt = pg_insert(UserDeadline).values(
            user_id=user_id,
            program_id=program_id,
            deadline=program.deadline,
        ).on_conflict_do_nothing()
        await db.execute(stmt)

        # Create checklist from templates
        existing = await db.execute(
            select(ChecklistItem)
            .where(ChecklistItem.user_id == user_id)
            .where(ChecklistItem.program_id == program_id)
        )
        if not existing.first():
            templates = await db.execute(
                select(DocumentTemplate)
                .where(DocumentTemplate.degree_type.in_(["all", program.degree_type]))
                .order_by(DocumentTemplate.order_index)
            )
            for tmpl in templates.scalars().all():
                db.add(ChecklistItem(
                    user_id=user_id,
                    program_id=program_id,
                    item_name=tmpl.item_name,
                    hint=tmpl.hint,
                    is_done=False,
                ))

    await db.commit()
    return {"status": "ok", "added": len(body.program_ids)}


@router.delete("/{deadline_id}")
async def remove_deadline(
    deadline_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(UserDeadline)
        .where(UserDeadline.id == deadline_id)
        .where(UserDeadline.user_id == user_id)
    )
    await db.commit()
    return {"status": "ok"}
