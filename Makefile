.PHONY: dev stop backend dashboard landing seed test lint public-check install-hooks demo demo-backend clean

dev:
	docker compose up --build

stop:
	docker compose down

backend:
	cd backend && PYTHONPATH=. python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	cd dashboard && npm install && npm run dev

landing:
	cd landing && npm install && npm run dev

seed:
	cd backend && PYTHONPATH=. python seeds/seed.py

test:
	cd backend && PYTHONPATH=. uv run --python 3.11 --extra dev pytest -q

lint:
	cd backend && PYTHONPATH=. uv run --python 3.11 --extra dev ruff check .

public-check:
	scripts/check-public-repo-safety.sh

install-hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit scripts/check-public-repo-safety.sh

demo:
	@echo "=== Recall Local Demo ==="
	@echo ""
	@echo "Backend API:  http://localhost:8000/docs"
	@echo "Dashboard:    http://localhost:3000"
	@echo "Landing:      http://localhost:3001"
	@echo ""
	@echo "Start all services:"
	@echo "  make dev              # Docker Compose (all services)"
	@echo ""
	@echo "Start individually:"
	@echo "  make backend          # FastAPI on :8000"
	@echo "  make dashboard        # Next.js on :3000"
	@echo "  make landing          # Next.js on :3001"
	@echo ""
	@echo "Demo workflow:"
	@echo "  make seed             # Load 7 players + 96 events"
	@echo "  make demo-backend     # Seed + start backend"

demo-backend:
	@echo "=== Recall Demo: Backend ==="
	@echo ""
	@echo "1. Seeding database with 7 players and 96 events..."
	cd backend && PYTHONPATH=. python seeds/seed.py
	@echo ""
	@echo "2. Starting FastAPI server..."
	@echo "   Health check:  http://localhost:8000/health"
	@echo "   API docs:      http://localhost:8000/docs"
	@echo ""
	@echo "   Demo endpoints:"
	@echo "     curl -X POST http://localhost:8000/agent/scan"
	@echo "     curl http://localhost:8000/agent/decide/p_001"
	@echo "     curl http://localhost:8000/approval/queue"
	@echo ""
	cd backend && PYTHONPATH=. python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf backend/__pycache__ backend/app/**/__pycache__ backend/tests/__pycache__ backend/seeds/__pycache__
	rm -rf backend/.pytest_cache backend/.ruff_cache
	rm -rf backend/*.db backend/*.sqlite
	rm -rf storage/
	rm -rf dashboard/node_modules dashboard/.next
	rm -rf landing/node_modules landing/.next
	@echo "Cleaned caches, databases, node_modules, and storage."
