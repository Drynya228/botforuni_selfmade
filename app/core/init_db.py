# app/core/init_db.py
from loguru import logger

from app.core.db import DATABASE_URL, db

SCHEMA_SQL = """
create table if not exists messages (
  id bigserial primary key,
  chat_id bigint not null,
  telegram_message_id bigint,
  sender_id bigint,
  sent_at timestamptz not null,
  kind text not null,
  text_full text,
  file_id text,
  file_name text,
  meta jsonb default '{}'::jsonb
);
create index if not exists idx_messages_chat_time on messages(chat_id, sent_at desc);

create table if not exists tracked_chats (
  chat_id bigint primary key,
  label text,               -- человекочитаемое имя/метка
  added_at timestamptz default now(),
  active boolean default false,    -- станет true, когда бот реально в чате
  source text                      -- что ввели: ссылка/@username/id
);
"""

async def ensure_schema():
    if not DATABASE_URL:
        logger.warning("DATABASE_URL missing — skipping schema creation")
        return
    async with db() as conn:
        await conn.execute(SCHEMA_SQL)
        logger.info("DB schema ensured")
