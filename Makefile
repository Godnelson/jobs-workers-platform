.PHONY: up down logs fmt lint test

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

fmt:
	ruff format .

lint:
	ruff check . && mypy .

test:
	pytest -q
