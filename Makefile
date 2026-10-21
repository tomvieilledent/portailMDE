.PHONY: up down logs build ps test seed e2e

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

ps:
	docker compose ps

test:
	docker compose exec api pytest

seed:
	docker compose exec api python -m app.cli seed-demo

e2e:
	docker compose up -d --build --wait db api web
	docker compose exec -T api python -m app.cli seed-demo
	cd e2e && npm ci && npx playwright install chromium && npx playwright test
