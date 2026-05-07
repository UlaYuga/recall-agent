.PHONY: dev backend dashboard landing seed test lint demo

dev:
	docker compose up --build

backend:
	cd backend && uvicorn app.main:app --reload

dashboard:
	cd dashboard && npm run dev

landing:
	cd landing && npm run dev

seed:
	cd backend && python seeds/seed.py

test:
	cd backend && pytest

lint:
	cd backend && ruff check .

demo:
	@echo "Run backend, dashboard and landing, then follow docs/DEMO.md"

