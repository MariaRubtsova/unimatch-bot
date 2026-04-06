from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from api.auth import get_current_user_id
from db.database import get_db
from db.models import User, Program, UserDeadline, ChecklistItem, DocumentTemplate

ADMIN_USER_ID = 1379996156

router = APIRouter(prefix="/admin-api", tags=["admin"])


def require_admin(user_id: int = Depends(get_current_user_id)) -> int:
    if user_id != ADMIN_USER_ID:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    programs_count = (await db.execute(select(func.count()).select_from(Program))).scalar()
    active_programs = (await db.execute(
        select(func.count()).select_from(Program).where(Program.is_active == True)
    )).scalar()
    deadlines_count = (await db.execute(select(func.count()).select_from(UserDeadline))).scalar()
    templates_count = (await db.execute(select(func.count()).select_from(DocumentTemplate))).scalar()
    return {
        "users": users_count,
        "programs": programs_count,
        "active_programs": active_programs,
        "deadlines": deadlines_count,
        "templates": templates_count,
    }


# ── Programs ───────────────────────────────────────────────────────────────────

class ProgramIn(BaseModel):
    university_name: str
    program_name: str
    country: str
    field: str
    degree_type: str
    min_gpa: float = 0.0
    avg_gpa: Optional[float] = None
    min_ielts: float = 0.0
    avg_ielts: Optional[float] = None
    tuition_year: Optional[int] = None
    deadline: Optional[str] = None
    url: Optional[str] = None
    requirements_text: Optional[str] = None
    is_active: bool = True


@router.get("/programs")
async def list_programs(
    page: int = 1,
    search: str = "",
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    limit = 20
    offset = (page - 1) * limit
    q = select(Program).order_by(Program.id.desc())
    if search:
        q = q.where(
            Program.university_name.ilike(f"%{search}%") |
            Program.program_name.ilike(f"%{search}%") |
            Program.country.ilike(f"%{search}%")
        )
    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar()
    result = await db.execute(q.limit(limit).offset(offset))
    programs = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "items": [
            {
                "id": p.id,
                "university_name": p.university_name,
                "program_name": p.program_name,
                "country": p.country,
                "field": p.field,
                "degree_type": p.degree_type,
                "min_gpa": p.min_gpa,
                "min_ielts": p.min_ielts,
                "tuition_year": p.tuition_year,
                "deadline": str(p.deadline) if p.deadline else None,
                "url": p.url,
                "is_active": p.is_active,
            }
            for p in programs
        ],
    }


@router.post("/programs", status_code=201)
async def create_program(
    body: ProgramIn,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    deadline = date.fromisoformat(body.deadline) if body.deadline else None
    prog = Program(
        university_name=body.university_name,
        program_name=body.program_name,
        country=body.country,
        field=body.field,
        degree_type=body.degree_type,
        min_gpa=body.min_gpa,
        avg_gpa=body.avg_gpa,
        min_ielts=body.min_ielts,
        avg_ielts=body.avg_ielts,
        tuition_year=body.tuition_year,
        deadline=deadline,
        url=body.url,
        requirements_text=body.requirements_text,
        is_active=body.is_active,
    )
    db.add(prog)
    await db.commit()
    await db.refresh(prog)
    return {"id": prog.id}


@router.put("/programs/{program_id}")
async def update_program(
    program_id: int,
    body: ProgramIn,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Program).where(Program.id == program_id))
    prog = result.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump().items():
        if field == "deadline":
            setattr(prog, field, date.fromisoformat(value) if value else None)
        else:
            setattr(prog, field, value)
    await db.commit()
    return {"status": "ok"}


@router.delete("/programs/{program_id}")
async def delete_program(
    program_id: int,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(Program).where(Program.id == program_id))
    await db.commit()
    return {"status": "ok"}


# ── Users ──────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    page: int = 1,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    limit = 20
    offset = (page - 1) * limit
    total = (await db.execute(select(func.count()).select_from(User))).scalar()
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))
    users = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "items": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "first_name": u.first_name,
                "created_at": str(u.created_at)[:10] if u.created_at else None,
                "last_active": str(u.last_active)[:10] if u.last_active else None,
            }
            for u in users
        ],
    }


# ── Document Templates ─────────────────────────────────────────────────────────

class TemplateIn(BaseModel):
    degree_type: str
    item_name: str
    hint: Optional[str] = None
    order_index: int = 0


@router.get("/templates")
async def list_templates(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DocumentTemplate).order_by(DocumentTemplate.degree_type, DocumentTemplate.order_index)
    )
    templates = result.scalars().all()
    return [
        {
            "id": t.id,
            "degree_type": t.degree_type,
            "item_name": t.item_name,
            "hint": t.hint,
            "order_index": t.order_index,
        }
        for t in templates
    ]


@router.post("/templates", status_code=201)
async def create_template(
    body: TemplateIn,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    tmpl = DocumentTemplate(**body.model_dump())
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return {"id": tmpl.id}


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    body: TemplateIn,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in body.model_dump().items():
        setattr(tmpl, field, value)
    await db.commit()
    return {"status": "ok"}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(DocumentTemplate).where(DocumentTemplate.id == template_id))
    await db.commit()
    return {"status": "ok"}
