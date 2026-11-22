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
# Always starts from a clean container, so one run never sees another run's files.
up:
	cd scenarios/$(SCENARIO)/environment && docker compose down -v && docker compose up -d --build --wait

down:
	cd scenarios/$(SCENARIO)/environment && docker compose down -v
