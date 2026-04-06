from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.auth import get_current_user_id
from db.database import get_db
from db.models import Program
from services.scoring import UserProfile, rank_programs

router = APIRouter(prefix="/match", tags=["match"])


class MatchRequest(BaseModel):
    gpa: float
    ielts: float
    budget: int
    field: str
    degree_type: str
    country: Optional[str] = None


class ProgramResult(BaseModel):
    program_id: int
    university_name: str
    program_name: str
    country: str
    tuition_year: Optional[int]
    min_ielts: float
    deadline: Optional[str]
    url: Optional[str]
    score: float


@router.post("/", response_model=list[ProgramResult])
async def match_programs(
    body: MatchRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(Program).where(Program.is_active == True)

    if body.country and body.country.lower() not in ("другая", "любая", "🌍 любая"):
        query = query.where(Program.country.ilike(f"%{body.country}%"))

    if body.degree_type:
        query = query.where(Program.degree_type == body.degree_type.lower())

    result = await db.execute(query)
    programs = result.scalars().all()

    programs_data = [
        {
            "id": p.id,
            "university_name": p.university_name,
            "program_name": p.program_name,
            "country": p.country,
            "field": p.field,
            "degree_type": p.degree_type,
            "min_gpa": p.min_gpa,
            "avg_gpa": p.avg_gpa,
            "min_ielts": p.min_ielts,
            "avg_ielts": p.avg_ielts,
            "tuition_year": p.tuition_year,
            "deadline": p.deadline,
            "url": p.url,
        }
        for p in programs
    ]

    profile = UserProfile(
        gpa=body.gpa,
        ielts=body.ielts,
        budget=body.budget,
        field=body.field,
        degree_type=body.degree_type,
        country=body.country,
    )

    ranked = rank_programs(profile, programs_data)
    return [
        ProgramResult(
            program_id=r.program_id,
            university_name=r.university_name,
            program_name=r.program_name,
            country=r.country,
            tuition_year=r.tuition_year,
            min_ielts=r.min_ielts,
            deadline=r.deadline,
            url=r.url,
            score=r.score,
        )
        for r in ranked
    ]
