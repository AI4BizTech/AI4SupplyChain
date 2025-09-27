# Software Architecture - AI4SupplyChain

### Document Information
- **Version**: 1.0 
- **Date**: 9/2025
- **Product Name**: AI4SupplyChain
- **Document Owner**: Development Team
- **Contact**: Henry Jiang, AI4BizTech.Team@gmail.com

---

## Overview

This document describes the current architecture of AI4SupplyChain based on the Product Requirements. The implementation is an MVP focusing on inventory master data, supplier/location management, inventory tracking, and transaction processing using a FastAPI + SQLModel backend and a React (Vite) frontend. Advanced features (OCR-driven transaction ingestion, intelligent forecasting, optimization, analytics, and a conversational AI assistant) are planned but not yet implemented.

---

## Tech Stack Summary

| Layer         | Technology |
|---------------|------------|
| Backend       | FastAPI, SQLModel, SQLite (MVP → PostgreSQL) |
| Frontend      | React + Vite (TypeScript, Tailwind CSS 3) |
| Deployment    | Local dev (Vite + Uvicorn), Docker planned |
| Observability | Logging + health/stats endpoints |

---

## High-Level Architecture

- Backend: FastAPI + SQLModel ORM (SQLite for MVP), structured with services and API routers
- Frontend: React + Vite app consuming REST APIs
- Data: SQLModel persisted in SQLite (migration path to PostgreSQL)
- Deployment: Local dev via Vite (Bun) for frontend and Uvicorn for backend; Docker planned
- Observability: Basic logging via settings; health and stats endpoints available


---

## High-Level Architecture Diagram

```text
             [Frontend: React + Vite]
                       |
                       v
        REST API calls over HTTP (JSON)
                       |
                       v
        [Backend: FastAPI + SQLModel ORM]
                       |
                SQLite Database (MVP)
                 (→ PostgreSQL later)
```

---

## Backend Architecture

### Technologies
- FastAPI for HTTP APIs and OpenAPI docs
- SQLModel (SQLAlchemy + Pydantic) for models and validation
- SQLite for persistence in MVP (configurable migration path to PostgreSQL)

### Application Setup
- The backend is initialized by a main application entry point that handles logging, database connections, CORS settings, and API router mounting
- Health and system stats endpoints are provided at: `/health`, `/api/stats`, and a pool status endpoint

### Data Layer
- The data models module defines domain entities and API schemas
  - `Supplier`, `Location`, `Product`, `Inventory`, `Transaction`
  - Enums: `TransactionType`
  - API models: `ProductRead/Create/Update`, etc.
- The database configuration module provides session creation, initialization, and health checks
- Upon first initialization, the data layer will create a new /data directory under the backend directory and generate the SQLite database file with the necessary schema.

### Services Layer
- Service modules implement business operations
  - `InventoryService`: handles quantity calculations and adjustments
  - `SupplierService`, `LocationService`: provides stats and CRUD helpers
  - `TransactionService`: manages transaction processing, validations

### API Layer (Routers)
- The API is organized into logical routers for endppints, such as products, suppliers, locations, inventory, and transactions
- Endpoint prefix: `/api/...`
- Database sessions are managed via dependency injection to these routers
- Upon the first run, the code will create a new /data directory at the project root and generate the SQLite database file with the necessary schema.

### Configuration & Settings
- Configuration module provides application settings (API metadata, CORS, feature flags like `allow_negative_inventory`)

---

## Frontend Architecture

### Technologies
- React 18 with Vite
- TypeScript
- Tailwind CSS 3 (via plugins) and lightweight UI utilities (`clsx`, `lucide-react`)

### Structure & Patterns
- Routing: `react-router-dom`
- Feature pages under `src/pages` for products, suppliers, locations, inventory, transactions
- Forms under `src/components/forms/*`
- Data fetching hooks under `src/hooks/api/*` targeting backend REST APIs
- `src/services/api.ts` centralizes base URL and request helpers
- UI primitives in `src/components/ui/*` and layout in `src/components/layout/*`

---

## Cross-Cutting Concerns

- CORS: Configured for `http://localhost:3000` in backend
- Logging: Python logging configured via `settings.log_level` and `settings.log_format`
- Validation: Pydantic (via SQLModel) schemas for request/response validation
- Security: No authentication/authorization yet (to be added)
- Testing: Not yet implemented; to be added for services and API

---


## Planned Capabilities and Extension Points

The following capabilities are specified in the Product Requirements and planned for subsequent releases. They should be implemented as cohesive modules while preserving current layering.

1) Transaction Processing with OCR
- A new OCR service module will be introduced to handle document ingestion, supporting both local and cloud-based providers
- New endpoints will be added to the transactions API for document upload and parsing
- A dedicated storage location will be required for uploads (local in development, configurable to use various cloud storage providers in production)

2) Intelligent Demand Forecasting
- A new forecasting service will be created with pluggable algorithms (e.g., moving average, ETS)
- API endpoints will be added for training, inference, and backtesting
- Results will be persisted in new database tables

3) Optimization & Recommendations
- An optimization service module will be added to handle business logic for EOQ, reorder points, and safety stock
- This will be exposed via a new set of API endpoints
- Outputs will be integrated into the dashboard and reorder suggestions

4) Advanced Analytics & Reporting
- New API endpoints will be created for aggregations and KPIs
- A report generation module will be added, with export endpoints for formats like CSV and PDF
- A dedicated storage location for generated artifacts will be added

5) Conversational AI Assistant
- An agent module will be added to handle LLM interaction
- A chat API will expose endpoints (websocket or HTTP) for the assistant
- This module will include components for memory, guardrails, and cost controls

6) Authentication & Authorization
- JWT-based authentication will be introduced, along with RBAC roles (Admin, Manager, Clerk)
- This will secure endpoints and add user context to transactions.

---

## Agentic Workflow Plan (Future Releases)

Goal: Enable an LLM-powered assistant that can orchestrate inventory operations safely and cost-effectively.

### Architectural Components
- LLM client abstraction to support multiple providers (OpenAI, Anthropic)
- Tool interfaces safely map to service-layer functions (CRUD, queries, analytics)
- Agent orchestrator implements a tool-using workflow with planning and reflection
- Conversational memory component provides short-term memory, with optional vector store for retrieval
- Policy and guardrail component enforces rate limits, role permissions, and schema validation

### Agent Capabilities (Iterative)
- v0: Read-only Q&A (system stats, product lookups, inventory positions)
- v1: Action proposals (create transactions as drafts requiring human confirm)
- v2: Autonomous routines (e.g., nightly reorder proposals), with audit logs

### Tooling Contracts
- Tools wrap service-layer functions with:
  - Input/Output pydantic schemas
  - Idempotency keys for safe retries
  - Permission checks per role
 
### Execution Modes
- Human-in-the-loop approval for state-changing actions via frontend modals
- Background jobs for long-running tasks (OCR batches, forecasting runs)

### Observability
- Structured logs for each agent step (tool calls, prompts, outputs)
- Correlation IDs across frontend request → backend → agent tool calls

### Safety & Risk Controls
- Sandbox: Agent executes only via approved tools (no arbitrary code or DB access)
- Quotas: Daily limits per user/organization for costly operations
- Rollback: Transactions drafted first; require explicit commit

---

## Non-Functional Requirements & Roadmap Considerations

- Performance: Keep endpoints simple and bounded; add pagination and filtering for lists
- Reliability: Add retries for transient DB/IO errors; adopt migrations (Alembic) when moving to Postgres
- Security: Add authentication and RBAC; validate uploads; sanitize OCR content
- Compliance: Log and audit user actions; configurable data retention
- Dev Experience: Add linting, tests, pre-commit; Docker dev environment

---

## API Surface (Current)

- Products: `/api/products` CRUD
- Suppliers: `/api/suppliers` CRUD
- Locations: `/api/locations` CRUD
- Inventory: `/api/inventory` view/update
- Transactions: `/api/transactions` create/list
- System: `/`, `/health`, `/api/stats`, `/api/system/pool-status`

---

## Frontend-Backend Contract

- REST JSON over HTTP; consistent resource shapes via SQLModel schemas
- Errors surfaced as HTTP status codes with `detail`
- CORS: allow `http://localhost:3000` (will be updated for deployments)

---

## Migration Path

- Database: Prepare for PostgreSQL by avoiding SQLite-specific constraints and adding Alembic migrations
- Storage: Introduce A pluggable storage interface for uploads and exports when OCR and reporting capabilities are added
- Auth: Add JWT/OIDC and role-based permissions before enabling write-capable agent tools
- Observability: Centralize structured logging; add metrics and tracing later

---

## Appendix: Alignment with Product Requirements

- Implemented now: product, supplier, location CRUD; inventory tracking; transaction processing; basic dashboard stats
- Planned next: OCR ingestion, forecasting, optimization, analytics, conversational assistant, authentication, exports


