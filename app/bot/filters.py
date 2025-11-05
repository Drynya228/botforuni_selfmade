# app/bot/filters.py
from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.core.config import OwnerConfig

OWNER_IDS = OwnerConfig().owners

class IsOwnerPM(BaseFilter):
    """Пропускает только сообщения ВЛАДЕЛЬЦА в ЛИЧКЕ"""
    async def __call__(self, m: Message) -> bool:
        return (
            m.chat and m.chat.type == "private"
            and m.from_user
            and (
                not OWNER_IDS
                or m.from_user.id in OWNER_IDS
            )
        )
