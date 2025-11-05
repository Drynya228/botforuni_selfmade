from aiogram import Router, F
from aiogram.types import Message
from app.core.db import db
from app.core.logging import logger
from app.ingestion.storage import save_telegram_file
from app.ingestion.asr import transcribe_message
from app.ingestion.ocr import ocr_photo
from app.ingestion.docs import extract_document_text
from app.rag.indexer import index_text

router = Router()

def register_handlers(dp):
    dp.include_router(router)

@router.message(F.text)
async def on_text(m: Message):
    async with db() as conn:
        rec = await conn.fetchrow(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full)
            values($1,$2,$3, to_timestamp($4), 'text', $5) returning id
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), m.text,
        )
    await index_text(rec["id"], m.chat.id, m.date, "text", m.text)

@router.message(F.photo)
async def on_photo(m: Message):
    file_id = m.photo[-1].file_id
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id)
    text = await ocr_photo(path)
    async with db() as conn:
        rec = await conn.fetchrow(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_path)
            values($1,$2,$3, to_timestamp($4), 'photo', $5, $6, $7) returning id
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), text, file_id, path,
        )
    if text:
        await index_text(rec["id"], m.chat.id, m.date, "photo", text)

@router.message(F.document)
async def on_doc(m: Message):
    file_id = m.document.file_id
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id, filename=m.document.file_name)
    text = await extract_document_text(path)
    async with db() as conn:
        rec = await conn.fetchrow(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_path)
            values($1,$2,$3, to_timestamp($4), 'document', $5, $6, $7) returning id
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), text, file_id, path,
        )
    if text:
        await index_text(rec["id"], m.chat.id, m.date, "document", text)

@router.message(F.voice | F.video_note | F.video)
async def on_audio_like(m: Message):
    file_id = (m.voice and m.voice.file_id) or (m.video_note and m.video_note.file_id) or (m.video and m.video.file_id)
    kind = "voice" if m.voice else ("video_note" if m.video_note else "video")
    path = await save_telegram_file(m.bot, file_id, m.chat.id, m.message_id)
    text = await transcribe_message(path)
    async with db() as conn:
        rec = await conn.fetchrow(
            """
            insert into messages(chat_id, telegram_message_id, sender_id, sent_at, kind, text_full, file_id, file_path)
            values($1,$2,$3, to_timestamp($4), $5, $6, $7, $8) returning id
            """,
            m.chat.id, m.message_id, m.from_user.id, m.date.timestamp(), kind, text, file_id, path,
        )
    if text:
        await index_text(rec["id"], m.chat.id, m.date, kind, text)
    else:
        logger.warning("ASR produced empty text")