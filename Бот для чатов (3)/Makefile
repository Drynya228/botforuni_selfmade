.PHONY: up down logs set-webhook drop-webhook bootstrap test lint fmt

up:
	docker compose -f infra/docker-compose.yml up -d --build

down:
	docker compose -f infra/docker-compose.yml down -v

logs:
	docker compose -f infra/docker-compose.yml logs -f app

set-webhook:
	@[ -z "$$BOT_TOKEN" ] && echo "Set BOT_TOKEN env var" && exit 1 || true
	@[ -z "$$WEBHOOK_URL" ] && echo "Set WEBHOOK_URL env var" && exit 1 || true
	curl -s -X POST "https://api.telegram.org/bot$$BOT_TOKEN/setWebhook" -d "url=$$WEBHOOK_URL" | jq .

drop-webhook:
	@[ -z "$$BOT_TOKEN" ] && echo "Set BOT_TOKEN env var" && exit 1 || true
	curl -s "https://api.telegram.org/bot$$BOT_TOKEN/deleteWebhook" | jq .

bootstrap: up
	# создаём таблицы, если их ещё нет
	docker compose -f infra/docker-compose.yml exec -T app python -m app.core.init_db
	# ставим webhook
	BOT_TOKEN=$$BOT_TOKEN WEBHOOK_URL=$$WEBHOOK_URL make set-webhook || true
	@echo "\n✅ Bootstrap complete. Test: curl http://localhost:8000/healthz\n"

test:
	docker compose -f infra/docker-compose.yml exec -T app pytest -q || true

lint:
	docker compose -f infra/docker-compose.yml exec -T app ruff check .

fmt:
	docker compose -f infra/docker-compose.yml exec -T app ruff check . --fix