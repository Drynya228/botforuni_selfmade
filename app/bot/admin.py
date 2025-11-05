# app/bot/admin.py
from __future__ import annotations

import os
from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from app.core.db import db
from app.bot.filters import IsOwnerPM

router = Router()
# Команды этого роутера доступны ТОЛЬКО владельцу и ТОЛЬКО в ЛС
router.message.filter(IsOwnerPM())

# -----------------------------------------------------------------------------
# Вспомогательные функции
# -----------------------------------------------------------------------------

async def _ensure_tracked_schema():
    """На случай, если ensure_schema не выполнился — создадим таблицу."""
    sql = """
    create table if not exists tracked_chats (
      chat_id bigint primary key,
      label   text,
      added_at timestamptz default now(),
      active  boolean default true,
      source  text
    );
    """
    async with db() as conn:
        await conn.execute(sql)

async def _chat_exists(chat_id: int) -> bool:
    async with db() as conn:
        row = await conn.fetchrow("select 1 from tracked_chats where chat_id=$1", chat_id)
    return row is not None

# -----------------------------------------------------------------------------
# Команды
# -----------------------------------------------------------------------------

@router.message(F.text == "/status")
async def cmd_status(m: Message):
    await _ensure_tracked_schema()
    async with db() as conn:
        total_msgs = await conn.fetchval("select count(*) from messages")
        total_tracked = await conn.fetchval("select count(*) from tracked_chats")
        total_active = await conn.fetchval("select count(*) from tracked_chats where active=true")
    await m.answer(
        "Статус:\n"
        f"• сообщений в базе: {total_msgs or 0}\n"
        f"• чатов в списке: {total_tracked or 0}\n"
        f"• активных чатов: {total_active or 0}"
    )

@router.message(F.text.startswith("/tracked"))
async def cmd_tracked(m: Message):
    await _ensure_tracked_schema()
    async with db() as conn:
        rows = await conn.fetch(
            "select chat_id, label, active, source, added_at "
            "from tracked_chats order by added_at desc limit 100"
        )
    if not rows:
        return await m.answer(
            "Список пуст.\n"
            "Добавь чат так: <code>/track -1001234567890</code>\n"
            "Chat ID можно узнать, например, через @userinfobot (или добавь меня в группу и пришли сюда ID).",
            parse_mode="HTML"
        )
    lines = []
    for r in rows:
        flag = "✅" if r["active"] else "⏳"
        lines.append(f"{flag} id={r['chat_id']}  {r['label'] or ''}  src={r['source'] or ''}")
    await m.answer("Трекаемые чаты:\n" + "\n".join(lines))

@router.message(F.text.startswith("/track"))
async def cmd_track(m: Message):
    """
    Формат: /track <chat_id>
    Пример: /track -1001234567890

    Примечание:
    - Бот сам не может вступить по ссылке — добавь его в чат руками.
    - Для групп: в BotFather → /setprivacy → Disable, чтобы получать сообщения.
    - Для каналов: дай боту права администратора.
    """
    await _ensure_tracked_schema()

    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await m.answer("Использование: /track <chat_id>\nПример: /track -1001234567890")

    arg = parts[1].strip()
    try:
        chat_id = int(arg)
    except ValueError:
        return await m.answer(
            "chat_id должен быть числом.\n"
            "Подсказка: узнай chat_id через @userinfobot или другой сервис, "
            "затем повтори: /track <chat_id>"
        )

    label = f"chat {chat_id}"
    async with db() as conn:
        await conn.execute(
            """
            insert into tracked_chats(chat_id, label, active, source)
            values($1,$2,true,$3)
            on conflict (chat_id)
            do update set active=true, label=excluded.label, source=excluded.source
            """,
            chat_id, label, str(chat_id)
        )

    await m.answer(
        "Ок, добавил в список.\n"
        f"id={chat_id}\n\n"
        "Теперь:\n"
        "1) Добавь бота в этот чат (или убедись, что он уже внутри).\n"
        "2) Для групп: BotFather → /setprivacy → Disable.\n"
        "3) Для каналов: сделай бота админом.\n\n"
        "Как только в чате появится новое сообщение — индексирование начнётся автоматически."
    )

@router.message(F.text.startswith("/untrack"))
async def cmd_untrack(m: Message):
    await _ensure_tracked_schema()

    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await m.answer("Использование: /untrack <chat_id>")

    try:
        chat_id = int(parts[1].strip())
    except ValueError:
        return await m.answer("chat_id должен быть числом.")

    existed = await _chat_exists(chat_id)
    async with db() as conn:
        await conn.execute("delete from tracked_chats where chat_id=$1", chat_id)

    if existed:
        await m.answer(f"Готово. Чат {chat_id} удалён из списка.")
    else:
        await m.answer(f"Чат {chat_id} не был в списке.")
