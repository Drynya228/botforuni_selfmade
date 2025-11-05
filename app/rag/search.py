from __future__ import annotations
import math
import numpy as np
from typing import Any
from app.core.db import db
from app.rag.indexer import embed_batch


def _cosine(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    if va.size != vb.size:
        # для dummy размера 1 просто сравним как числа
        va = np.array([va.mean()])
        vb = np.array([vb.mean()])
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))

async def semantic_search(query: str, chat_id: int, limit: int = 8, allow_fulltext: bool = False) -> list[dict[str, Any]]:
    if not query:
        return []
    q_emb = (await embed_batch([query]))[0]
    async with db() as conn:
        rows = await conn.fetch("""
            select c.id, c.content, c.embedding, m.kind, m.sent_at, m.id as message_id
            from chunks c join messages m on m.id = c.message_id
            where (m.chat_id = $1)
            order by m.sent_at desc limit 400
        """, chat_id)
    scored = []
    for r in rows:
        emb = r["embedding"] or [0.0]
        score = _cosine(emb, q_emb)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for s, r in scored[:limit]:
        out.append({
            "score": s,
            "preview": (r["content"][:180] + "…") if r["content"] and len(r["content"]) > 180 else (r["content"] or ""),
            "kind": r["kind"],
            "sent_at": r["sent_at"].isoformat() if r["sent_at"] else "",
            "message_id": r["message_id"],
            "chunk_id": r["id"],
        })
    return out