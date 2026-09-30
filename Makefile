install:
	uv sync
	cd frontend && npm install

build:
	cd frontend && npm run build

run: build
	uv run labcloud

dev-api:
	uv run uvicorn labcloud.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev

test:
	uv run pytest -q
	cd frontend && npm run typecheck

reset-db:
	rm -f labcloud.db

.PHONY: install build run dev-api dev-web test reset-db
