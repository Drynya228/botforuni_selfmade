import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from app.core.config import cfg
from app.bot.commands import register_commands
from app.bot.handlers import register_handlers

# Инициализация один раз на все приложение

tg_bot = Bot(token=cfg.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
tg_dispatcher = Dispatcher()

register_commands(tg_dispatcher)
register_handlers(tg_dispatcher)

# Для webhook-пути из FastAPI
async def feed_update(bot: Bot, update: dict):
    await tg_dispatcher._process_update(bot, Update.model_validate(update))

Dispatcher.feed_update = feed_update  # type: ignore[attr-defined]