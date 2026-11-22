.PHONY: install test test-docker lint up down

install:
	pip install -e ".[dev]"

test:
	pytest -v

test-docker:
	pytest -v -m docker

lint:
	ruff check tools tests

# usage: make up SCENARIO=ledger-drift
up:
	cd scenarios/$(SCENARIO)/environment && docker compose up -d --build

down:
	cd scenarios/$(SCENARIO)/environment && docker compose down -v
