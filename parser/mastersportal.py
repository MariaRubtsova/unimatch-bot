"""
Parser for Mastersportal.eu
Run manually: python -m parser.mastersportal

Requires:
  pip install httpx beautifulsoup4 playwright
  playwright install chromium
"""
import asyncio
import logging
import re
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.database import AsyncSessionLocal
from db.models import Program

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BASE_URL = "https://www.mastersportal.com"

FIELD_MAP = {
    "computer science": "cs",
    "information technology": "cs",
    "software": "cs",
    "business": "business",
    "management": "business",
    "mba": "business",
    "engineering": "engineering",
    "science": "science",
    "medicine": "medicine",
    "health": "medicine",
}

COUNTRY_MAP = {
    "germany": "Германия",
    "netherlands": "Нидерланды",
    "canada": "Канада",
    "switzerland": "Швейцария",
}


def detect_field(text: str) -> str:
    text_lower = text.lower()
    for keyword, field in FIELD_MAP.items():
        if keyword in text_lower:
            return field
    return "other"


def parse_tuition(text: str) -> Optional[int]:
    match = re.search(r"(\d[\d\s,]+)", text.replace(",", ""))
    if match:
        try:
            return int(match.group(1).replace(" ", ""))
        except ValueError:
            pass
    return None


def parse_deadline(text: str) -> Optional[date]:
    # Try common formats: "1 January 2026", "01/01/2026"
    import dateutil.parser
    try:
        return dateutil.parser.parse(text, fuzzy=True).date()
    except Exception:
        return None


async def fetch_program_list(country: str, degree: str, page: int = 1) -> list[dict]:
    """Fetch a page of programs from Mastersportal."""
    url = f"{BASE_URL}/studies/{degree}/{country}.html?limit=20&start={(page-1)*20}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UniMatchBot/1.0)"}

    async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return []

    soup = BeautifulSoup(resp.text, "html.parser")
    programs = []

    for card in soup.select(".CourseCard"):
        try:
            name_el = card.select_one(".CourseName") or card.select_one("h3")
            uni_el = card.select_one(".UniversityName") or card.select_one(".institution")
            tuition_el = card.select_one(".Tuition") or card.select_one("[data-tuition]")
            url_el = card.select_one("a[href]")

            if not name_el or not uni_el:
                continue

            prog_name = name_el.get_text(strip=True)
            uni_name = uni_el.get_text(strip=True)
            tuition = parse_tuition(tuition_el.get_text()) if tuition_el else None
            prog_url = BASE_URL + url_el["href"] if url_el and url_el["href"].startswith("/") else None

            programs.append({
                "program_name": prog_name,
                "university_name": uni_name,
                "country": COUNTRY_MAP.get(country.lower(), country.capitalize()),
                "field": detect_field(prog_name),
                "degree_type": degree,
                "min_gpa": 2.5,
                "avg_gpa": 3.0,
                "min_ielts": 6.0,
                "avg_ielts": 6.5,
                "tuition_year": tuition,
                "url": prog_url,
            })
        except Exception as e:
            logger.warning(f"Error parsing card: {e}")

    logger.info(f"Fetched {len(programs)} programs from {url}")
    return programs


async def save_programs(programs: list[dict]) -> int:
    saved = 0
    async with AsyncSessionLocal() as session:
        for p in programs:
            stmt = pg_insert(Program).values(**p).on_conflict_do_nothing()
            await session.execute(stmt)
            saved += 1
        await session.commit()
    return saved


async def run_parser():
    countries = ["germany", "netherlands", "canada"]
    degrees = ["master", "bachelor"]
    total = 0

    for country in countries:
        for degree in degrees:
            for page in range(1, 4):  # 3 pages per combination
                programs = await fetch_program_list(country, degree, page)
                if not programs:
                    break
                saved = await save_programs(programs)
                total += saved
                await asyncio.sleep(1)  # polite delay

    logger.info(f"Parser done. Total saved: {total} programs.")


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_parser())
