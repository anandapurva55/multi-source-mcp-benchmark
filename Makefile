.PHONY: install test lint up down

install:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check tools tests

# usage: make up SCENARIO=ledger-drift
up:
	cd scenarios/$(SCENARIO)/environment && docker compose up -d --build

down:
	cd scenarios/$(SCENARIO)/environment && docker compose down -v
