# app/ingestion/storage.py
import os
import pathlib
from aiogram import Bot

BASE_DIR = pathlib.Path("/srv/app/.data")
BASE_DIR.mkdir(parents=True, exist_ok=True)

async def save_telegram_file(bot: Bot, file_id: str, chat_id: int, message_id: int, filename: str | None = None) -> str:
    f = await bot.get_file(file_id)
    name = filename or f.file_unique_id
    local = BASE_DIR / f"{chat_id}_{message_id}_{name}"
    await bot.download_file(f.file_path, destination=local)
    return str(local)
