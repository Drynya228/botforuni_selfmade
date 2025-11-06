# app/bot/filters.py
from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.core.config import OwnerConfig


OWNER_IDS = OwnerConfig().owners


class IsOwnerPM(BaseFilter):
    """Пропускает только сообщения владельца в личке"""

    async def __call__(self, message: Message) -> bool:
        if not message.chat or message.chat.type != "private":
            return False

        if not message.from_user:
            return False

        if not OWNER_IDS:
            return True

        return message.from_user.id in OWNER_IDS
