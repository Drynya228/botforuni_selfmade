# app/bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message
from app.core.db import db
from app.ingestion.storage import save_telegram_file
from app.ingestion.ocr import ocr_photo
from app.ingestion.asr import transcribe
from app.ingestion.docs import extract_text_from_path
from app.rag.search import semantic_search
from app.rag.summarize import summary, topics

router = Router()

@router.message(F.text)
async def on_text(m: Message):
    async with db() as conn:
        await conn.execute(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full)
            values($1,$2,$3,to_timestamp($4),'text',$5)
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), m.text
        )

@router.message(F.photo)
async def on_photo(m: Message):
    file_id = m.photo[-1].file_id
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id)
    text = await ocr_photo(path)
    async with db() as conn:
        await conn.execute(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_name)
            values($1,$2,$3,to_timestamp($4),'photo',$5,$6,$7)
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), text, file_id, "photo.jpg"
        )

@router.message(F.document)
async def on_document(m: Message):
    file_id = m.document.file_id
    fname = m.document.file_name
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id, filename=fname)
    text = await extract_text_from_path(path)
    async with db() as conn:
        await conn.execute(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_name)
            values($1,$2,$3,to_timestamp($4),'document',$5,$6,$7)
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), text, file_id, fname
        )

@router.message(F.voice | F.video_note | F.video)
async def on_audio_like(m: Message):
    kind = "voice" if m.voice else ("video_note" if m.video_note else "video")
    file_id = (m.voice and m.voice.file_id) or (m.video_note and m.video_note.file_id) or (m.video and m.video.file_id)
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id)
    text = await transcribe(path)
    async with db() as conn:
        await conn.execute(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_name)
            values($1,$2,$3,to_timestamp($4),$5,$6,$7,$8)
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), kind, text, file_id, f"{kind}.ogg"
        )

# Команды
@router.message(F.text.startswith("/summary"))
async def cmd_summary(m: Message):
    period = m.text.replace("/summary", "").strip() or "сегодня"
    txt = await summary(m.chat.id, period)
    await m.answer(txt)

@router.message(F.text.startswith("/ask"))
async def cmd_ask(m: Message):
    q = m.text.split(" ", 1)[1] if " " in m.text else ""
    hits = await semantic_search(m.chat.id, q, limit=8)
    if not hits:
        await m.answer("Не нашёл по истории.")
        return
    out = ["Ответ (контекст):"] + [f"• {h['preview']}" for h in hits]
    await m.answer("\n".join(out))

@router.message(F.text.startswith("/find"))
async def cmd_find(m: Message):
    q = m.text.split(" ", 1)[1] if " " in m.text else ""
    hits = await semantic_search(m.chat.id, q, limit=5)
    if not hits:
        await m.answer("Ничего не нашёл.")
        return
    out = [f"• {h['kind']} @ {h['sent_at']} — {h['preview']}" for h in hits]
    await m.answer("\n".join(out))

@router.message(F.text.startswith("/topics"))
async def cmd_topics(m: Message):
    period = m.text.replace("/topics", "").strip() or "7d"
    await m.answer(await topics(m.chat.id, period))
