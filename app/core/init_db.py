# app/core/init_db.py
from app.core.db import db

SCHEMA_SQL = """
create table if not exists messages (
  id bigserial primary key,
  chat_id bigint not null,
  telegram_message_id bigint,
  sender_id bigint,
  sent_at timestamptz not null,
  kind text not null,               -- text|photo|document|voice|video_note|video
  text_full text,
  file_id text,
  file_name text,
  meta jsonb default '{}'::jsonb
);
create index if not exists idx_messages_chat_time on messages(chat_id, sent_at desc);
"""

async def ensure_schema():
    async with db() as conn:
        await conn.execute(SCHEMA_SQL)

        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
