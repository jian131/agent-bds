# Makefile for BDS Agent
# Requires Python 3.12

.PHONY: help install dev test build deploy clean lint format

PYTHON = python3.12
VENV = venv
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

help:
	@echo "BDS Agent - Available commands:"
	@echo ""
	@echo "  Setup:"
	@echo "    make setup       - Create venv + install all dependencies"
	@echo "    make install     - Install Python dependencies only"
	@echo "    make playwright  - Install Playwright browsers"
	@echo ""
	@echo "  Development:"
	@echo "    make dev         - Start dev environment (postgres + backend + frontend)"
	@echo "    make backend     - Start backend only"
	@echo "    make frontend    - Start frontend only"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate     - Run database migrations"
	@echo "    make migration   - Create new migration (msg='description')"
	@echo ""
	@echo "  Testing:"
	@echo "    make test        - Run all tests"
	@echo "    make test-cov    - Run tests with coverage"
	@echo "    make lint        - Run linter"
	@echo "    make format      - Format code"
	@echo ""
	@echo "  Docker:"
	@echo "    make build       - Build Docker images"
	@echo "    make up          - Start all services"
	@echo "    make down        - Stop all services"
	@echo "    make logs        - View logs"
	@echo ""

# Setup virtual environment and install dependencies
setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(VENV)/bin/playwright install chromium
	cd frontend && npm install
	@echo "✅ Setup complete! Activate venv: source $(VENV)/bin/activate"

# Install dependencies only
install:
	$(PIP) install -r requirements.txt

# Install Playwright browsers
playwright:
	$(VENV)/bin/playwright install chromium

# Development - start all services
dev:
	docker compose up -d postgres redis
	@sleep 3
	@echo "🚀 Starting backend..."
	$(VENV)/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "🚀 Starting frontend..."
	cd frontend && npm run dev

# Run backend only
backend:
	$(VENV)/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend only
frontend:
	cd frontend && npm run dev

# Database migrations
migrate:
	$(VENV)/bin/alembic upgrade head

# Create new migration
migration:
	$(VENV)/bin/alembic revision --autogenerate -m "$(msg)"

# Testing
test:
	$(PYTEST) tests/ -v

test-cov:
	$(PYTEST) tests/ -v --cov=. --cov-report=html --cov-report=term

# Linting
lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

# Format code
format:
	$(VENV)/bin/ruff format .
	$(VENV)/bin/ruff check --fix .

# Build Docker images
build:
	docker compose build

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Deploy
	docker compose up -d

deploy-prod:
	docker compose --profile production up -d

# Stop all services
stop:
	docker compose down

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf frontend/.next frontend/node_modules
	docker compose down -v

# Logs
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

# Shell access
shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U postgres -d bds_agent

# Pull Ollama model
ollama-setup:
	ollama pull qwen2.5:14b
