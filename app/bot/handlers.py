# app/bot/handlers.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from app.core.db import db
from app.ingestion.storage import save_telegram_file
from app.ingestion.ocr import ocr_photo
from app.ingestion.asr import transcribe
from app.ingestion.docs import extract_text_from_path
from app.rag.search import semantic_search
from app.rag.summarize import summary, topics
from app.bot.filters import IsOwnerPM

# -----------------------------------------------------------------------------
# РОУТЕРЫ:
# - router_ingest: бесшумная индексация в группах/каналах (не отвечает)
# - router_owner: команды только владельцу в ЛС
# -----------------------------------------------------------------------------

router_ingest = Router()
router_owner = Router()
router_owner.message.filter(IsOwnerPM())  # отвечает только OWNER_ID и только в private

# -----------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНО: доступ к чату (список трекаемых), запись событий
# -----------------------------------------------------------------------------

async def _tracked_table_empty() -> bool:
    async with db() as conn:
        total = await conn.fetchval("select count(*) from tracked_chats")
    return (total or 0) == 0

async def _is_allowed(chat_id: int) -> bool:
    # если список пуст — разрешаем индексацию всех чатов
    if await _tracked_table_empty():
        return True
    async with db() as conn:
        row = await conn.fetchrow("select active from tracked_chats where chat_id=$1", chat_id)
    return bool(row and row["active"])

async def _ensure_tracked_active(chat_id: int):
    # если таблица пустая — автоматически разрешим все чаты
    if await _tracked_table_empty():
        return
    async with db() as conn:
        row = await conn.fetchrow("select active from tracked_chats where chat_id=$1", chat_id)
        if row is None:
            # чат ещё не занесён -> игнорируем (пока его не добавят через /track)
            return
        if not row["active"]:
            await conn.execute(
                "update tracked_chats set active=true, label=$2 where chat_id=$1",
                chat_id, f"chat {chat_id}"
            )

async def _store_text(m: Message):
    async with db() as conn:
        await conn.execute(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full)
            values($1,$2,$3,to_timestamp($4),'text',$5)
            """,
            m.chat.id, m.message_id, (m.from_user.id if m.from_user else None),
            m.date.timestamp(), (m.text or "")
        )

async def _store_generic(m: Message, kind: str, text: str, file_id: str, file_name: str):
    async with db() as conn:
        await conn.execute(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_name)
            values($1,$2,$3,to_timestamp($4),$5,$6,$7,$8)
            """,
            m.chat.id, m.message_id, (m.from_user.id if m.from_user else None),
            m.date.timestamp(), kind, (text or ""), file_id, file_name
        )

# -----------------------------------------------------------------------------
# ИНДЕКСАЦИЯ (бесшумно в чатах/каналах). НИКОГДА не отвечаем в группах!
# -----------------------------------------------------------------------------

@router_ingest.message(F.text)
async def ingest_text(m: Message):
    # разрешён ли чат?
    if not await _is_allowed(m.chat.id):
        return
    # пометим чат активным при первом апдейте (если уже в списке)
    await _ensure_tracked_active(m.chat.id)
    await _store_text(m)

@router_ingest.message(F.photo)
async def ingest_photo(m: Message):
    if not await _is_allowed(m.chat.id):
        return
    await _ensure_tracked_active(m.chat.id)
    file_id = m.photo[-1].file_id
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id)
    text = await ocr_photo(path)
    await _store_generic(m, kind="photo", text=text, file_id=file_id, file_name="photo.jpg")

@router_ingest.message(F.document)
async def ingest_document(m: Message):
    if not await _is_allowed(m.chat.id):
        return
    await _ensure_tracked_active(m.chat.id)
    file_id = m.document.file_id
    fname = m.document.file_name or "document"
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id, filename=fname)
    text = await extract_text_from_path(path)
    await _store_generic(m, kind="document", text=text, file_id=file_id, file_name=fname)

@router_ingest.message(F.voice | F.video_note | F.video)
async def ingest_audio_like(m: Message):
    if not await _is_allowed(m.chat.id):
        return
    await _ensure_tracked_active(m.chat.id)
    kind = "voice" if m.voice else ("video_note" if m.video_note else "video")
    file_id = (m.voice and m.voice.file_id) or (m.video_note and m.video_note.file_id) or (m.video and m.video.file_id)
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id)
    text = await transcribe(path)
    await _store_generic(m, kind=kind, text=text, file_id=file_id, file_name=f"{kind}.ogg")

# -----------------------------------------------------------------------------
# КОМАНДЫ ТОЛЬКО В ЛИЧКЕ ВЛАДЕЛЬЦА (IsOwnerPM)
# Формат аргументов (требуют chat_id целевого чата):
#   /summary <chat_id> [period]
#   /ask <chat_id> <вопрос>
#   /find <chat_id> <запрос>
#   /topics <chat_id> [period]
# -----------------------------------------------------------------------------

def _parse_first_int_arg(s: str) -> tuple[int | None, str]:
    """
    Парсит первую часть как chat_id (int), возвращает (chat_id, rest).
    Пример: "/summary -100123 7d" -> (-100123, "7d")
    """
    parts = (s or "").strip().split(maxsplit=2)
    if not parts:
        return None, ""
    # убираем саму команду
    if parts[0].startswith("/"):
        parts = parts[1:]
    if not parts:
        return None, ""
    # первая оставшаяся — chat_id
    try:
        cid = int(parts[0])
    except ValueError:
        return None, " ".join(parts)
    rest = " ".join(parts[1:]) if len(parts) > 1 else ""
    return cid, rest

@router_owner.message(F.text == "/start")
async def owner_start(m: Message):
    await m.answer(
        "Готов. Я молча индексирую чаты, где меня добавили.\n"
        "Команды (использовать в ЛС):\n"
        "/summary <chat_id> [period]\n"
        "/ask <chat_id> <вопрос>\n"
        "/find <chat_id> <запрос>\n"
        "/topics <chat_id> [period]\n"
        "Примеры:\n"
        "/summary -1001234567890 сегодня\n"
        "/ask -1001234567890 дедлайн по презентации?\n"
        "/find -1001234567890 смета\n"
        "/topics -1001234567890 7d"
    )

@router_owner.message(F.text.startswith("/summary"))
async def cmd_summary(m: Message):
    chat_id, rest = _parse_first_int_arg(m.text or "")
    period = (rest or "").strip() or "сегодня"
    if chat_id is None:
        return await m.answer("Формат: /summary <chat_id> [period]")
    txt = await summary(chat_id, period)
    await m.answer(txt)

@router_owner.message(F.text.startswith("/ask"))
async def cmd_ask(m: Message):
    chat_id, rest = _parse_first_int_arg(m.text or "")
    if chat_id is None or not rest:
        return await m.answer("Формат: /ask <chat_id> <вопрос>")
    q = rest.strip()
    hits = await semantic_search(chat_id, q, limit=8)
    if not hits:
        return await m.answer("Не нашёл по истории.")
    out = ["Ответ (контекст):"] + [f"• {h['preview']}" for h in hits]
    await m.answer("\n".join(out))

@router_owner.message(F.text.startswith("/find"))
async def cmd_find(m: Message):
    chat_id, rest = _parse_first_int_arg(m.text or "")
    if chat_id is None or not rest:
        return await m.answer("Формат: /find <chat_id> <запрос>")
    hits = await semantic_search(chat_id, rest.strip(), limit=6)
    if not hits:
        return await m.answer("Пусто.")
    out = [f"• {h['kind']} @ {h['sent_at']} — {h['preview']}" for h in hits]
    await m.answer("\n".join(out))

@router_owner.message(F.text.startswith("/topics"))
async def cmd_topics(m: Message):
    chat_id, rest = _parse_first_int_arg(m.text or "")
    period = (rest or "").strip() or "7d"
    if chat_id is None:
        return await m.answer("Формат: /topics <chat_id> [period]")
    await m.answer(await topics(chat_id, period))

# Глушилка на любые прочие личные сообщения владельца (если захочешь что-то ещё)
@router_owner.message(F.text)
async def owner_fallback(m: Message):
    # чтобы было тихо, если команда не распознана
    pass
