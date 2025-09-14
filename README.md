# AI4SupplyChain

AI-Powered Dynamic Inventory and Demand Planning System

## Quick Start

1. **Install dependencies**
```bash
uv sync  # or pip install -e .
```

2. **Set up environment**
```bash
cp env.example .env
# Edit .env with your API keys
```

3. **Run the application**
```bash
# Streamlit Dashboard
uv run streamlit run src/ui/main.py

# FastAPI Server
uv run uvicorn src.api.main:app --reload
```

## Features

- Product Master Data Management
- Smart Inventory Management
- Supplier Management  
- Transaction Processing with OCR
- AI-Powered Demand Forecasting
- Inventory Optimization
- Conversational AI Assistant

## Architecture

Built with Python 3.11+, FastAPI, SQLite, LangChain, OpenAI GPT-4o mini, and Streamlit.

## 📚 Documentation

### **Core Documents**
- **[Product Requirements](docs/PRODUCT_REQUIREMENTS.md)** - Complete business requirements, market research, and feature specifications
- **[Software Architecture](docs/Software_Architecture.md)** - Technical architecture, system design, and implementation details

For detailed setup instructions and development guidelines, refer to the documentation files above.