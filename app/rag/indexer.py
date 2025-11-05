from datetime import datetime
from typing import List
import numpy as np
from app.core.db import db
from app.core.config import cfg

# Простейший чанкинг по символам

def split_into_chunks(text: str, target_chars: int = 4000, overlap: int = 500) -> list[str]:
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        chunk = text[i : i + target_chars]
        chunks.append(chunk)
        i += max(1, target_chars - overlap)
    return chunks

# Эмбеддинги (dummy или OpenAI)
async def embed_batch(chunks: List[str]) -> list[list[float]]:
    if cfg.EMBEDDINGS_PROVIDER == "openai" and cfg.OPENAI_API_KEY:
        # без реального запроса, чтобы MVP был офлайн-готов
        pass
    # dummy: усредняем кодовые точки
    vecs = []
    for ch in chunks:
        if not ch:
            vecs.append([0.0])
            continue
        arr = np.frombuffer(ch.encode("utf-8"), dtype=np.uint8).astype(np.float32)
        vecs.append([float(arr.mean())])
    return vecs

async def index_text(message_id: int, chat_id: int, sent_at: datetime, kind: str, text: str):
    chunks = split_into_chunks(text)
    if not chunks:
        return
    embs = await embed_batch(chunks)
    async with db() as conn:
        for i, (content, emb) in enumerate(zip(chunks, embs)):
            await conn.execute(
                """
                insert into chunks(message_id, chunk_index, content, embedding, meta)
                values($1,$2,$3,$4,$5)
                """,
                message_id, i, content, emb, {"chat_id": chat_id, "kind": kind, "sent_at": sent_at.isoformat()},
            )