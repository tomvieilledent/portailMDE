.PHONY: up down logs build ps test

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
