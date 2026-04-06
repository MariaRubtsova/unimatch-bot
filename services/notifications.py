import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal
from db.models import UserDeadline, Program

logger = logging.getLogger(__name__)


async def check_and_send_notifications(bot) -> None:
    """Check deadlines and send Telegram notifications."""
    today = date.today()

    async with AsyncSessionLocal() as session:
        # Load all active deadlines with their programs
        result = await session.execute(
            select(UserDeadline, Program)
            .join(Program, UserDeadline.program_id == Program.id)
            .where(UserDeadline.deadline >= today)
        )
        rows = result.all()

    for deadline_row, program in rows:
        days_left = (deadline_row.deadline - today).days
        user_id = deadline_row.user_id
        name = f"{program.program_name} — {program.university_name}"

        async with AsyncSessionLocal() as session:
            if days_left <= 1 and not deadline_row.notified_1:
                await _send(bot, user_id, f"⚠️ {name} — завтра дедлайн! Всё готово?")
                await session.execute(
                    update(UserDeadline)
                    .where(UserDeadline.id == deadline_row.id)
                    .values(notified_1=True)
                )
                await session.commit()

            elif days_left <= 7 and not deadline_row.notified_7:
                await _send(bot, user_id, f"📅 {name} — через неделю! Проверь чеклист.")
                await session.execute(
                    update(UserDeadline)
                    .where(UserDeadline.id == deadline_row.id)
                    .values(notified_7=True)
                )
                await session.commit()

            elif days_left <= 30 and not deadline_row.notified_30:
                await _send(bot, user_id, f"📌 {name} — через 30 дней. Начни собирать документы!")
                await session.execute(
                    update(UserDeadline)
                    .where(UserDeadline.id == deadline_row.id)
                    .values(notified_30=True)
                )
                await session.commit()


async def _send(bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logger.warning(f"Failed to notify user {user_id}: {e}")


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_notifications,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot],
        id="deadline_notifications",
        replace_existing=True,
    )
    return scheduler
