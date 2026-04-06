import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from api.routes import match, deadlines, checklist, chat, export, auth_routes, admin_api
from db.database import engine
from db.models import Base
from admin.views import setup_admin

logger = logging.getLogger(__name__)


async def _run_bot():
    """Run Telegram bot polling in background."""
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token:
        logger.warning("BOT_TOKEN not set — bot will not start")
        return
    try:
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from bot.handlers import start, deadlines as dl_handler, ai_chat
        from services.notifications import setup_scheduler

        bot = Bot(token=bot_token)
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(start.router)
        dp.include_router(dl_handler.router)
        dp.include_router(ai_chat.router)

        scheduler = setup_scheduler(bot)
        scheduler.start()
        logger.info("Bot polling started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Bot error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            pass  # pgvector may already exist or not be available
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    # Start bot in background
    bot_task = asyncio.create_task(_run_bot())

    yield

    bot_task.cancel()
    try:
        await asyncio.wait_for(bot_task, timeout=5)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass


app = FastAPI(title="UniMatch API", version="1.0.0", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change_me"))
setup_admin(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(match.router)
app.include_router(deadlines.router)
app.include_router(checklist.router)
app.include_router(chat.router)
app.include_router(export.router)
app.include_router(admin_api.router)

# Serve Mini App static files with no-cache headers
from fastapi.responses import FileResponse
from fastapi import Request

mini_app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mini_app")

@app.get("/mini_app/admin.html")
async def serve_admin_app(request: Request):
    return FileResponse(
        os.path.join(mini_app_path, "admin.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )


@app.get("/mini_app/index.html")
async def serve_mini_app(request: Request):
    return FileResponse(
        os.path.join(mini_app_path, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

app.mount("/mini_app", StaticFiles(directory=mini_app_path, html=True), name="mini_app")


@app.get("/health")
async def health():
    return {"status": "ok"}
