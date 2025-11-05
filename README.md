# tg-knowledge-bot
Бот для Telegram: читает текст/фото/документы/голос/кружки из групп, где он добавлен, делает ASR/OCR/парсинг, индексирует и по запросу выдаёт сводки, поиск, файлы и темы.

## Быстрый старт
1) Создай бота в BotFather → получи BOT_TOKEN. Отключи privacy: `/setprivacy` → **Disable**.
2) Скопируй `.env.example` в `.env`, заполни `BOT_TOKEN` и `WEBHOOK_URL` (например, `https://<домен>/tg-webhook`).
3) Запусти: