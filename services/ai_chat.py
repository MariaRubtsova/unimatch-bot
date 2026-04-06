import os
import httpx
import logging
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Program

logger = logging.getLogger(__name__)

YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_API_KEY = os.getenv("YANDEX_GPT_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID", "")
YANDEX_MODEL = os.getenv("YANDEX_GPT_MODEL", "yandexgpt-lite")

SYSTEM_PROMPT = """Ты — дружелюбный и экспертный помощник по поступлению в зарубежные университеты. Тебя зовут UniMatch AI.

Отвечай на русском языке, кратко и по делу.

Правила:
1. Если вопрос про конкретные программы, университеты, требования, дедлайны, стоимость — используй контекст с данными из базы программ.
2. Если вопрос общий (зачем учиться за рубежом, как писать мотивационное письмо, что такое GPA, как получить визу, советы по поступлению) — отвечай из своих знаний как эксперт.
3. Если в базе нет подходящих программ — честно скажи и дай общий совет.
4. Не выдумывай конкретные программы которых нет в базе.
5. Будь мотивирующим и поддерживающим."""


COUNTRY_ALIASES = {
    "германии": "germany", "германия": "germany",
    "франции": "france", "франция": "france",
    "великобритании": "uk", "британии": "uk", "англии": "uk",
    "сша": "usa", "америке": "usa", "америка": "usa",
    "канаде": "canada", "канада": "canada",
    "нидерландах": "netherlands", "голландии": "netherlands",
    "швеции": "sweden", "швеция": "sweden",
    "финляндии": "finland", "финляндия": "finland",
    "австрии": "austria", "австрия": "austria",
    "испании": "spain", "испания": "spain",
    "италии": "italy", "италия": "italy",
    "чехии": "czech", "чехия": "czech",
    "польши": "poland", "польша": "poland",
}

FIELD_ALIASES = {
    "компьютерных": "cs", "программировани": "cs", "айти": "cs",
    "бизнес": "business", "менеджмент": "business", "mba": "mba",
    "инженери": "engineering", "технологи": "engineering",
    "медицин": "medicine", "врач": "medicine",
}


async def search_relevant_programs(query: str, session: AsyncSession, limit: int = 8) -> list[dict]:
    """Simple full-text search for relevant programs (RAG retrieval step)."""
    words = query.lower().split()
    # translate Russian geo/field terms to English
    translated = []
    for word in words:
        for ru, en in COUNTRY_ALIASES.items():
            if ru in word:
                translated.append(en)
        for ru, en in FIELD_ALIASES.items():
            if ru in word:
                translated.append(en)
        translated.append(word)

    filters = []
    for word in translated[:10]:
        filters.append(Program.requirements_text.ilike(f"%{word}%"))
        filters.append(Program.program_name.ilike(f"%{word}%"))
        filters.append(Program.university_name.ilike(f"%{word}%"))
        filters.append(Program.country.ilike(f"%{word}%"))
        filters.append(Program.field.ilike(f"%{word}%"))

    result = await session.execute(
        select(Program)
        .where(Program.is_active == True)
        .where(or_(*filters))
        .limit(limit)
    )
    programs = result.scalars().all()

    # fallback: return all active programs if nothing found
    if not programs:
        result = await session.execute(
            select(Program).where(Program.is_active == True).limit(limit)
        )
        programs = result.scalars().all()

    return [
        {
            "university": p.university_name,
            "program": p.program_name,
            "country": p.country,
            "degree": p.degree_type,
            "min_gpa": p.min_gpa,
            "min_ielts": p.min_ielts,
            "tuition": p.tuition_year,
            "deadline": str(p.deadline) if p.deadline else None,
            "requirements": (p.requirements_text or "")[:300],
        }
        for p in programs
    ]


def build_context(programs: list[dict]) -> str:
    if not programs:
        return "Релевантных программ в базе не найдено."
    lines = ["Найденные программы:"]
    for i, p in enumerate(programs, 1):
        lines.append(
            f"{i}. {p['program']} — {p['university']} ({p['country']})\n"
            f"   Тип: {p['degree']}, GPA min: {p['min_gpa']}, IELTS min: {p['min_ielts']}, "
            f"Стоимость: {p['tuition'] or '?'} EUR/год, Дедлайн: {p['deadline'] or '?'}\n"
            f"   Требования: {p['requirements']}"
        )
    return "\n".join(lines)


async def ask_yandex_gpt(user_message: str, context: str) -> str:
    """Send request to YandexGPT with RAG context."""
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        return "⚠️ YandexGPT не настроен. Укажите YANDEX_GPT_API_KEY и YANDEX_GPT_FOLDER_ID в .env"

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.4,
            "maxTokens": 800,
        },
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": f"Контекст:\n{context}\n\nВопрос: {user_message}"},
        ],
    }

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(YANDEX_GPT_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["result"]["alternatives"][0]["message"]["text"]
        except Exception as e:
            logger.error(f"YandexGPT error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"YandexGPT response: {e.response.status_code} {e.response.text}")
                return f"Ошибка ИИ ({e.response.status_code}): {e.response.text[:200]}"
            return f"Ошибка ИИ: {str(e)[:200]}"


async def get_ai_response(user_message: str, session: AsyncSession) -> str:
    """Full RAG pipeline: retrieve → build context → generate."""
    programs = await search_relevant_programs(user_message, session)
    context = build_context(programs)
    return await ask_yandex_gpt(user_message, context)
