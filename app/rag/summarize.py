# app/rag/summarize.py
from datetime import datetime, timedelta
from app.core.db import db

def _period_bounds(now: datetime, period: str):
    if period in ("сегодня","today"):
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period in ("вчера","yesterday"):
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period.endswith("d"):
        days = int(period[:-1])
        start = now - timedelta(days=days)
    else:
        start = now - timedelta(days=7)
    return start

async def summary(chat_id: int, period: str = "сегодня") -> str:
    now = datetime.utcnow()
    start = _period_bounds(now, period)
    async with db() as conn:
        rows = await conn.fetch(
            "select kind, sent_at, text_full from messages where chat_id=$1 and sent_at >= $2 order by sent_at",
            chat_id, start
        )
    if not rows:
        return f"За период «{period}» нет данных."
    lines = []
    for r in rows[:200]:
        text = (r["text_full"] or "").splitlines()[0][:140]
        if text:
            lines.append(f"• [{r['kind']}] {text}")
    head = f"Итоги ({period}): {len(rows)} сообщений\n"
    return head + "\n".join(lines[:12])

async def topics(chat_id: int, period: str = "7d") -> str:
    # Простейшая заглушка: первые 8 «самолучших» предложений по длине
    now = datetime.utcnow()
    start = _period_bounds(now, period)
    async with db() as conn:
        rows = await conn.fetch(
            "select text_full from messages where chat_id=$1 and sent_at >= $2 and text_full is not null order by sent_at desc limit 400",
            chat_id, start
        )
    texts = [(t or "") for (t,) in rows]
    if not texts:
        return "Темы не выделены."
    texts.sort(key=lambda s: len(s), reverse=True)
    out = ["Темы периода:"] + [f"• {t[:180]}{'…' if len(t)>180 else ''}" for t in texts[:8]]
    return "\n".join(out)
