# app/bot/filters.py
import os
from aiogram.filters import BaseFilter
from aiogram.types import Message

OWNER_ID = int((os.getenv("OWNER_ID") or "0").strip() or "0")


class IsOwnerPM(BaseFilter):
    """Пропускает только сообщения владельца в личке"""

    async def __call__(self, message: Message) -> bool:
        if not message.chat or message.chat.type != "private":
            return False
        if OWNER_ID == 0:
            return True
        return message.from_user is not None and message.from_user.id == OWNER_ID
