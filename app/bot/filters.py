# app/bot/filters.py
from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.core.config import cfg


class IsOwnerPM(BaseFilter):
    """Пропускает только сообщения владельца в личке"""

    async def __call__(self, message: Message) -> bool:
        if not message.chat or message.chat.type != "private":
            return False
        owner_id = cfg.OWNER_ID
        if owner_id == 0:
            return True
        return message.from_user is not None and message.from_user.id == owner_id
