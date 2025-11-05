# app/bot/filters.py
import os
from aiogram.filters import BaseFilter
from aiogram.types import Message

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

class IsOwnerPM(BaseFilter):
    """Пропускает только сообщения ВЛАДЕЛЬЦА в ЛИЧКЕ"""
    async def __call__(self, m: Message) -> bool:
        return (
            m.chat and m.chat.type == "private"
            and m.from_user and m.from_user.id == OWNER_ID
        )
