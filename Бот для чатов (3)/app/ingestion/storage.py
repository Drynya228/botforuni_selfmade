import os
import aiohttp
import pathlib
from aiogram import Bot
from app.core.config import cfg

BASE_DIR = pathlib.Path("/srv/app/.data")
BASE_DIR.mkdir(parents=True, exist_ok=True)

async def save_telegram_file(bot: Bot, file_id: str, chat_id: int, message_id: int, filename: str | None = None) -> str:
    file = await bot.get_file(file_id)
    local = BASE_DIR / f"{chat_id}_{message_id}_{filename or file.file_unique_id}"
    await bot.download_file(file.file_path, destination=local)
    return str(local)