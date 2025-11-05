import asyncio
import asyncpg
from app.core.config import cfg

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
  file_path text,
  meta jsonb default '{}'::jsonb
);

create table if not exists chunks (
  id bigserial primary key,
  message_id bigint references messages(id) on delete cascade,
  chunk_index int not null,
  content text not null,
  embedding double precision[], -- храним массив; для простоты вместо pgvector
  meta jsonb default '{}'::jsonb
);

create index if not exists idx_messages_chat_time on messages(chat_id, sent_at);
"""

async def main():
    conn = await asyncpg.connect(cfg.DATABASE_URL)
    try:
        await conn.execute(SCHEMA_SQL)
        print("DB schema ready")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())