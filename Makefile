.PHONY: help dev backend frontend test lint clean migrate seed docker docker-down install

help:
	@echo "Titanium - Enterprise AI Platform"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  dev          Start development servers (backend + frontend)"
	@echo "  backend      Start backend only"
	@echo "  frontend     Start frontend only"
	@echo "  test         Run all tests"
	@echo "  test-backend  Run backend tests"
	@echo "  test-frontend Run frontend tests"
	@echo "  e2e          Run E2E tests (Playwright)"
	@echo "  lint         Run linters"
	@echo "  typecheck    Run type checks"
	@echo "  clean        Remove generated files"
	@echo "  migrate      Run database migrations"
	@echo "  seed         Seed memory system"
	@echo "  seed-demo    Seed demo data"
	@echo "  load-test    Run load tests"
	@echo "  security-scan Run security scans"
	@echo "  docker       Start Docker Compose stack"
	@echo "  docker-down  Stop Docker Compose stack"
	@echo "  docker-build Rebuild Docker images"
	@echo "  docker-logs  View Docker logs"
	@echo "  docker-ps    View Docker status"
	@echo "  install      Install all dependencies"
	@echo "  format       Format code"
	@echo "  health       Check backend health"
	@echo "  status       Check all services"

dev:
	@echo "Starting development servers..."
	@TITANIUM_TESTING=true .venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
	@cd frontend && npm run dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "API Docs: http://localhost:8000/docs"
	@wait

backend:
	@TITANIUM_TESTING=true .venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	@TITANIUM_TESTING=true .venv/bin/pytest backend/tests/ -v --cov=backend --cov=memory --cov=agents --cov-report=term-missing --ignore=backend/tests/e2e

test-frontend:
	@cd frontend && npm test -- --run

lint: lint-backend lint-frontend

lint-backend:
	@.venv/bin/ruff check backend/ memory/ agents/ --select F,E9,W6 || true
	@.venv/bin/ruff format --check backend/ memory/ agents/ || true
	@echo "=== Lint complete (use 'make format' to auto-fix) ==="

lint-frontend:
	@cd frontend && npx eslint src --ext ts,tsx
	@cd frontend && npx tsc --noEmit

typecheck:
	@cd frontend && npx tsc --noEmit
	@echo "=== TypeScript ==="
	@echo "Passed"
	@echo "=== Python (mypy - informational) ==="
	@.venv/bin/mypy backend/ memory/ agents/ --ignore-missing-imports --explicit-package-bases --follow-imports=skip --no-strict-optional 2>&1 | grep "error:" | head -20 || true
	@echo "=== Type check complete ==="

clean:
	@echo "Cleaning generated files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .mypy_cache/ .pytest_cache/ htmlcov/ coverage.xml
	@rm -rf backend/titanium.db
	@rm -rf frontend/node_modules/ frontend/dist/
	@rm -rf agent_memory/
	@echo "Clean complete"

migrate:
	@.venv/bin/python -m alembic -c backend/migrations/alembic.ini upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	.venv/bin/python -m alembic -c backend/migrations/alembic.ini revision --autogenerate -m "$$name"

seed:
	@.venv/bin/python deployment/scripts/seed_memory.py

seed-demo:
	@.venv/bin/python deployment/scripts/seed_demo.py

load-test:
	@.venv/bin/python backend/tests/load_test.py

docker:
	@docker compose up -d

docker-down:
	@docker compose down

docker-build:
	@docker compose build --no-cache

docker-logs:
	@docker compose logs -f

docker-ps:
	@docker compose ps

install: install-backend install-frontend

install-backend:
	@python3 -m venv .venv
	@.venv/bin/pip install -r backend/requirements.txt
	@.venv/bin/pip install -r memory/requirements.txt
	@.venv/bin/pip install pytest pytest-asyncio pytest-cov ruff mypy -q

install-frontend:
	@cd frontend && npm install

format: format-backend format-frontend

format-backend:
	@.venv/bin/ruff format backend/ memory/ agents/
	@.venv/bin/ruff check --fix backend/ memory/ agents/

format-frontend:
	@cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

health:
	@curl -s http://localhost:8000/api/health | python3 -m json.tool

status:
	@echo "=== Titanium System Status ==="
	@echo ""
	@echo "Backend:  $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/health 2>/dev/null || echo 'down')"
	@echo "Frontend: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5173 2>/dev/null || echo 'down')"
	@echo "Ollama:   $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/api/tags 2>/dev/null || echo 'down')"
	@echo "Qdrant:   $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:6333/ 2>/dev/null || echo 'down')"
	@echo "Redis:    $$(redis-cli ping 2>/dev/null || echo 'down')"
	@echo ""

e2e:
	@cd frontend && npx playwright install --with-deps
	@TITANIUM_TESTING=true .venv/bin/pytest backend/tests/e2e/ -v

security-scan:
	@.venv/bin/pip install bandit safety -q
	@.venv/bin/bandit -r backend/ memory/ agents/ -f json -o bandit-report.json || true
	@.venv/bin/safety check -r backend/requirements.txt || true
