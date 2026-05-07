.PHONY: dev backend dashboard landing seed test lint public-check install-hooks demo

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
	cd backend && PYTHONPATH=. uv run --python 3.11 --extra dev pytest

lint:
	cd backend && PYTHONPATH=. uv run --python 3.11 --extra dev ruff check .

public-check:
	scripts/check-public-repo-safety.sh

install-hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit scripts/check-public-repo-safety.sh

demo:
	@echo "Run backend, dashboard and landing, then follow docs/DEMO.md"
