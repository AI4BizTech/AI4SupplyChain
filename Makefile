# AI4SupplyChain Development Makefile

.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend test test-backend lint format clean sample-data reset-db status

# Default target
help:
	@echo "AI4SupplyChain Development Commands"
	@echo "==================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          - Install all dependencies (backend + frontend)"
	@echo "  install-backend  - Install backend dependencies only"
	@echo "  install-frontend - Install frontend dependencies only"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev              - Run both backend and frontend in development"
	@echo "  dev-backend      - Run backend only (http://localhost:8000)"
	@echo "  dev-frontend     - Run frontend only (http://localhost:3000)"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test             - Run all tests"
	@echo "  test-backend     - Run backend tests only"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint             - Run linting"
	@echo "  format           - Format code"
	@echo "  clean            - Clean build artifacts"
	@echo ""
	@echo "Data Commands:"
	@echo "  sample-data      - Generate sample data"
	@echo "  reset-db         - Reset database (WARNING: deletes all data)"
	@echo "  status           - Show project status"

# Installation Commands
install: install-backend install-frontend
	@echo "✅ All dependencies installed successfully!"

install-backend:
	@echo "📦 Installing backend dependencies..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing UV package manager..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	cd backend && uv sync
	@echo "✅ Backend dependencies installed!"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@if ! command -v bun >/dev/null 2>&1; then \
		echo "⚠️  Bun not found. Please install Bun first:"; \
		echo "   curl -fsSL https://bun.sh/install | bash"; \
		exit 1; \
	fi
	@if [ -d "frontend" ]; then \
		cd frontend && bun install; \
		echo "✅ Frontend dependencies installed!"; \
	else \
		echo "ℹ️  Frontend directory not found (will be created in next feature)"; \
	fi

# Development Commands
dev: dev-backend dev-frontend

dev-backend:
	@echo "🚀 Starting backend development server..."
	@if [ ! -f ".env" ]; then \
		echo "Creating .env from template..."; \
		cp .env.example .env; \
	fi
	cd backend && uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

dev-frontend:
	@if [ -d "frontend" ]; then \
		echo "🚀 Starting frontend development server..."; \
		cd frontend && bun run dev; \
	else \
		echo "ℹ️  Frontend not implemented yet (next feature)"; \
		echo "   Backend running at: http://localhost:8000"; \
		echo "   API docs at: http://localhost:8000/docs"; \
	fi

# Quality Commands
lint:
	@echo "🔍 Running linting..."
	@if [ -d "backend" ]; then \
		cd backend && uv run flake8 src/ || true; \
		cd backend && uv run mypy src/ || true; \
	fi

format:
	@echo "🎨 Formatting code..."
	@if [ -d "backend" ]; then \
		cd backend && uv run black src/ tests/ || true; \
		cd backend && uv run isort src/ tests/ || true; \
	fi

# Data Commands
sample-data:
	@echo "📊 Generating sample data..."
	cd backend && uv run python scripts/generate_sample_data.py

reset-db:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "🗑️  Removing database files..."
	rm -f data/*.db data/*.sqlite
	@echo "📊 Regenerating sample data..."
	cd backend && uv run python scripts/generate_sample_data.py

# Utility Commands
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
	find . -type f -name "*.pyo" -delete || true
	find . -type f -name ".coverage" -delete || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + || true
	@if [ -d "frontend" ]; then \
		cd frontend && rm -rf node_modules .next out dist || true; \
	fi
	@echo "✅ Cleanup completed!"

# Status and Info
status:
	@echo "📊 AI4SupplyChain Project Status"
	@echo "==============================="
	@echo ""
	@echo "Backend:"
	@if [ -d "backend" ]; then \
		echo "  ✅ Backend structure created"; \
		if [ -f "backend/pyproject.toml" ]; then echo "  ✅ Dependencies configured"; fi; \
		if [ -f "data/inventory.db" ]; then echo "  ✅ Database exists"; else echo "  ⚠️  Database not found (run 'make sample-data')"; fi; \
	else \
		echo "  ❌ Backend not found"; \
	fi
	@echo ""
	@echo "Frontend:"
	@if [ -d "frontend" ]; then \
		echo "  ✅ Frontend structure created"; \
	else \
		echo "  ⏳ Frontend pending (next feature)"; \
	fi
	@echo ""
	@echo "Tools:"
	@if command -v uv >/dev/null 2>&1; then echo "  ✅ UV package manager"; else echo "  ❌ UV not installed"; fi
	@if command -v bun >/dev/null 2>&1; then echo "  ✅ Bun package manager"; else echo "  ⚠️  Bun not installed (needed for frontend)"; fi
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make install-backend    # Install dependencies"
	@echo "  2. make sample-data        # Generate test data"  
	@echo "  3. make dev-backend        # Start API server"
	@echo "  4. Visit http://localhost:8000/docs"
