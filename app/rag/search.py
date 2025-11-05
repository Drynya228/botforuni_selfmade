# app/rag/search.py
from typing import List, Dict, Any
from app.core.db import db
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

async def recent_corpus(chat_id: int, limit: int = 400) -> List[Dict[str, Any]]:
    async with db() as conn:
        rows = await conn.fetch(
            "select id, kind, sent_at, text_full from messages where chat_id=$1 and text_full is not null order by sent_at desc limit $2",
            chat_id, limit
        )
    return [dict(r) for r in rows]

async def semantic_search(chat_id: int, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    docs = await recent_corpus(chat_id)
    texts = [d["text_full"] or "" for d in docs]
    if not texts:
        return []
    vec = TfidfVectorizer(max_features=8000)
    X = vec.fit_transform(texts + [query])
    sims = cosine_similarity(X[-1], X[:-1]).ravel()
    scored = sorted(zip(sims, docs), key=lambda x: x[0], reverse=True)[:limit]
    out = []
    for score, d in scored:
        preview = (d["text_full"][:180] + "…") if d["text_full"] and len(d["text_full"]) > 180 else (d["text_full"] or "")
        out.append({
            "score": float(score),
            "id": d["id"],
            "kind": d["kind"],
            "sent_at": d["sent_at"].isoformat() if d["sent_at"] else "",
            "preview": preview
        })
    return out
