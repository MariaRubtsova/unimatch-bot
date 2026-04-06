from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    gpa: float
    ielts: float
    budget: int          # EUR/year
    field: str           # cs / business / engineering / science / medicine / other
    degree_type: str     # master / bachelor / mba / phd
    country: Optional[str] = None


@dataclass
class ProgramScore:
    program_id: int
    university_name: str
    program_name: str
    country: str
    tuition_year: Optional[int]
    min_ielts: float
    deadline: Optional[str]
    url: Optional[str]
    score: float         # 0–100


def score_program(profile: UserProfile, program: dict) -> Optional[float]:
    """
    Calculate match score for a program based on user profile.
    Returns None if the program is filtered out (hard filter: GPA below minimum).

    Weights:
      GPA    40%
      IELTS  30%
      Budget 20%
      Field  10%
    """
    min_gpa = program.get("min_gpa", 0.0) or 0.0
    avg_gpa = program.get("avg_gpa") or min_gpa or 3.0
    min_ielts = program.get("min_ielts", 0.0) or 0.0
    avg_ielts = program.get("avg_ielts") or min_ielts or 6.5
    tuition = program.get("tuition_year") or 0

    # Hard filter: GPA must meet the minimum
    if profile.gpa < min_gpa:
        return None

    total = 0.0

    # GPA score (40 pts max)
    gpa_score = min((profile.gpa / avg_gpa) * 40, 40)
    total += gpa_score

    # IELTS score (30 pts max)
    if profile.ielts >= min_ielts:
        ielts_score = min((profile.ielts / avg_ielts) * 30, 30)
        total += ielts_score

    # Budget score (20 pts)
    if tuition == 0 or profile.budget >= tuition:
        total += 20

    # Field match (10 pts)
    if program.get("field", "").lower() == profile.field.lower():
        total += 10

    return round(min(total, 100), 1)


def rank_programs(profile: UserProfile, programs: list[dict]) -> list[ProgramScore]:
    """
    Score and rank all programs for the given user profile.
    Returns list sorted by score descending, filtered programs excluded.
    """
    scored = []
    for p in programs:
        s = score_program(profile, p)
        if s is None:
            continue
        scored.append(ProgramScore(
            program_id=p["id"],
            university_name=p["university_name"],
            program_name=p["program_name"],
            country=p["country"],
            tuition_year=p.get("tuition_year"),
            min_ielts=p.get("min_ielts", 0.0),
            deadline=str(p["deadline"]) if p.get("deadline") else None,
            url=p.get("url"),
            score=s,
        ))
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored
