from __future__ import annotations
from datetime import datetime, timedelta
from app.core.db import db
from app.rag.search import semantic_search

async def answer_with_context(question: string, hits: list[dict]) -> str:  # type: ignore[name-defined]
    if not hits:
        return "Не нашёл в истории чата. Попробуй сформулировать по-другому."
    bullets = []
    for h in hits:
        bullets.append(f"• {h['preview']} (сообщение #{h['message_id']})")
    return "\n".join([f"Вопрос: {question}", "\nКонтекст:"] + bullets)

async def summarize_period(chat_id: int, period: str = "сегодня") -> str:
    now = datetime.utcnow()
    if period in ("сегодня", "today"):
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period in ("вчера", "yesterday"):
        since = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period.endswith("d"):
        days = int(period[:-1])
        since = now - timedelta(days=days)
    else:
        since = now - timedelta(days=7)
    async with db() as conn:
        rows = await conn.fetch(
            "select kind, sent_at, text_full from messages where chat_id=$1 and sent_at >= $2 order by sent_at",
            chat_id, since,
        )
    if not rows:
        return "За период нет данных."
    items = []
    for r in rows[:200]:
        if r["text_full"]:
            text = r["text_full"].splitlines()[0][:140]
            items.append(f"• [{r['kind']}] {text}")
    head = f"Итоги ({period}): {len(rows)} сообщений\n"
    return head + "\n".join(items[:12])

async def topics_for_period(chat_id: int, period: str = "7d") -> str:
    hits = await semantic_search("тема", chat_id, limit=8)
    if not hits:
        return "Темы не выделены."
    lines = ["Темы периода:"]
    lines += [f"• {h['preview']}" for h in hits]
    return "\n".join(lines)