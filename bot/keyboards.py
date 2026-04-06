import os
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
)

MINI_APP_URL = os.getenv("MINI_APP_URL", "http://localhost:8000/mini_app/index.html")


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Подобрать программы", web_app=WebAppInfo(url=MINI_APP_URL))],
            [KeyboardButton(text="📅 Мои дедлайны")],
            [KeyboardButton(text="💬 Задать вопрос")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )
