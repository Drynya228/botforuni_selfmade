# app/bot/admin.py
import os
from aiogram import Router, F
from aiogram.types import Message
from loguru import logger
from app.core.db import db

router = Router()
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

def _is_owner(m: Message) -> bool:
    return m.from_user and m.from_user.id == OWNER_ID

@router.message(F.text.startswith("/track"))
async def cmd_track(m: Message):
    if not _is_owner(m):
        return await m.answer("Команда доступна только владельцу.")
    arg = (m.text or "").split(" ", 1)
    if len(arg) < 2 or not arg[1].strip():
        return await m.answer("Использование: /track <ссылка|@username|id>")
    source = arg[1].strip()

    # Если прислали числовой id — помечаем сразу active=true (бот уже внутри)
    active = source.lstrip("-").isdigit()
    chat_id = int(source) if active else None

    async with db() as conn:
        if active:
            await conn.execute(
                """insert into tracked_chats(chat_id, label, active, source)
                   values($1,$2,true,$3)
                   on conflict (chat_id) do update set active=true, label=excluded.label, source=excluded.source""",
                chat_id, f"chat {chat_id}", source
            )
        else:
            # ждём вступления; активируем при первом апдейте
            await conn.execute(
                """insert into tracked_chats(chat_id, label, active, source)
                   values($1,$2,false,$3)
                   on conflict (chat_id) do update set source=excluded.source""",
                0, "pending", source
            )

    help_text = (
        "Ок. Чтобы бот начал индексировать чат:\n"
        "1) Добавь бота в группу/канал (по ссылке/юзернейму, который прислал).\n"
        "2) Для групп: в BotFather → /setprivacy → Disable.\n"
        "3) Для каналов: дай боту права Администратора (иначе Telegram не шлёт посты).\n"
        "Как только бот получит первое сообщение из чата — он автоматически пометит его как активный."
    )
    await m.answer(f"Принял: <code>{source}</code>\n{help_text}", parse_mode="HTML")

@router.message(F.text == "/tracked")
async def cmd_tracked(m: Message):
    if not _is_owner(m):
        return
    async with db() as conn:
        rows = await conn.fetch("select chat_id, label, active, source, added_at from tracked_chats order by added_at desc limit 50")
    if not rows:
        return await m.answer("Список пуст. Используй /track <ссылка|@username|id>.")
    lines = []
    for r in rows:
        cid = r["chat_id"]
        lines.append(f"• {r['label']}  id={cid}  active={'✅' if r['active'] else '⏳'}  src={r['source']}")
    await m.answer("Трекаю чаты:\n" + "\n".join(lines))

@router.message(F.text.startswith("/untrack"))
async def cmd_untrack(m: Message):
    if not _is_owner(m):
        return
    parts = m.text.split(" ", 1)
    if len(parts) < 2:
        return await m.answer("Использование: /untrack <chat_id>")
    try:
        cid = int(parts[1].strip())
    except ValueError:
        return await m.answer("chat_id должен быть числом.")
    async with db() as conn:
        await conn.execute("delete from tracked_chats where chat_id=$1", cid)
    await m.answer(f"Готово. Чат {cid} удалён из списка.")

@router.message(F.text == "/status")
async def cmd_status(m: Message):
    if not _is_owner(m):
        return
    async with db() as conn:
        total = await conn.fetchval("select count(*) from messages")
        tracked = await conn.fetchval("select count(*) from tracked_chats where active=true")
    await m.answer(f"Сообщений в базе: {total or 0}\nАктивных чатов: {tracked or 0}")
