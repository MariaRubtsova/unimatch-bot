from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user_id
from db.database import get_db
from db.models import UserDeadline, Program
from services.ics_export import generate_ics

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/ics")
async def export_ics(
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
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=unimatch_deadlines.ics"},
    )
