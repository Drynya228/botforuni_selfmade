from aiogram import Router, F
from aiogram.types import Message
from app.core.config import cfg
from app.rag.search import semantic_search
from app.rag.llm import answer_with_context, summarize_period, topics_for_period

router = Router()

def register_commands(dp):
    dp.include_router(router)

@router.message(F.text.startswith("/start"))
async def cmd_start(m: Message):
    await m.reply(
        "Привет! Я помогу собрать важное из чатов: /summary, /ask, /find, /file, /topics, /notify.\n"
        "Добавь меня в группу и отключи privacy у бота в BotFather."
    )

@router.message(F.text.startswith("/help"))
async def cmd_help(m: Message):
    await m.reply(
        "Команды:\n"
        "/summary сегодня|вчера|7d — сводка\n"
        "/ask <вопрос> — ответ по базе чата\n"
        "/find <ключевые слова> — поиск\n"
        "/file <описание> — найти и прислать файл\n"
        "/topics — темы/кластеры за период\n"
        "/notify add|list|remove — алерты по словам\n"
        "/optout — не индексировать мои сообщения"
    )

@router.message(F.text.startswith("/ask"))
async def cmd_ask(m: Message):
    q = m.text.split(" ", 1)[1] if " " in m.text else ""
    hits = await semantic_search(q, chat_id=m.chat.id, limit=8)
    reply = await answer_with_context(q, hits)
    await m.reply(reply)

@router.message(F.text.startswith("/summary"))
async def cmd_summary(m: Message):
    period = m.text.replace("/summary", "").strip() or "сегодня"
    reply = await summarize_period(chat_id=m.chat.id, period=period)
    await m.reply(reply)

@router.message(F.text.startswith("/topics"))
async def cmd_topics(m: Message):
    period = m.text.replace("/topics", "").strip() or "7d"
    reply = await topics_for_period(chat_id=m.chat.id, period=period)
    await m.reply(reply)

@router.message(F.text.startswith("/find"))
async def cmd_find(m: Message):
    q = m.text.split(" ", 1)[1] if " " in m.text else ""
    hits = await semantic_search(q, chat_id=m.chat.id, limit=5, allow_fulltext=True)
    if not hits:
        await m.reply("Ничего не найдено")
        return
    lines = []
    for h in hits:
        lines.append(f"• {h['kind']} @ {h['sent_at']} — {h['preview']}")
    await m.reply("\n".join(lines))