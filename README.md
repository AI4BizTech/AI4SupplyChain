# AI4SupplyChain

AI-Powered Dynamic Inventory and Demand Planning System

## Development Commands

### Quick Development Setup
```bash
# Install all dependencies (backend + frontend)
make install

# Run both backend and frontend in development
make dev

# Or run individually
make dev-backend    # Backend only (http://localhost:8000)
make dev-frontend   # Frontend only (http://localhost:3000)

# Populate database with some sample data(must run the following command from the backend directory to use the correct .venv environment):
cd backend 
uv run python scripts/generate_sample_data.py

# Navigate to the following URL to see the UI of the system
http://localhost:3000

```

### Backend Development
```bash
# Install UV package manager first (one time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Backend specific commands
make install-backend
make dev-backend
make test-backend

# Manual commands if needed
cd backend && uv sync
cd backend && uv run uvicorn src.api.main:app --reload
```

### Frontend Development
```bash
# Frontend specific commands
make install-frontend
make dev-frontend
make test-frontend

# Manual commands if needed
cd frontend && bun install
cd frontend && bun run dev    # Uses Bun's built-in dev server
cd frontend && bun run build  # Uses Bun's built-in bundler
```

## Features

- Product Master Data Management
- Smart Inventory Management
- Supplier Management  
- Transaction Processing with OCR
- AI-Powered Demand Forecasting
- Inventory Optimization
- Conversational AI Assistant


## **Core Documents**
- **[Product Requirements](docs/PRODUCT_REQUIREMENTS.md)** - Complete business requirements, market research, and feature specifications
- **[Software Architecture](docs/Software_Architecture.md)** - Technical architecture, system design, and implementation details


## Acknowledgement
The first version of this project incorporates portion of the code from https://github.com/moarshy/supplychain/, which followed the same core documents as mentioned above (see [Core Documents](#core-documents) section). It implements basic operations of an inventory management system (product, supplier, and location management, inventory tracking, and transaction processing) with a FastAPI + SQLModel backend and a React frontend. It serves as a foundation upon which we can build more advanced features, such as Intelligent Demand Forecasting, Advanced Analytics and Optimization, Conversational AI Assistant, etc.