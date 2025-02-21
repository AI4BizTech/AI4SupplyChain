# Inventory Management Simulation Project Specification
## Business Context
We operate a laptop distribution business managing inventory across three warehouses. We stock various laptop models from different manufacturers (e.g., Dell, HP, Lenovo, Apple). Each laptop model has specific stock requirements due to varying demand patterns and price points. Premium models require lower minimum stock levels but higher value tracking, while popular mid-range models need larger stock buffers.
## Overview
This project simulates our laptop inventory management system with an AI assistant that monitors stock levels and generates reports. The simulation operates on a day-by-day basis with automated inventory movements.

## Core Components
### Initial Stock Simulation
- Initial laptop inventory setup at system start
- For each laptop model:
    - Generate random quantities within model-specific ranges
        - Premium models (e.g., MacBook Pro): 20-50 units
        - Mid-range models (e.g., Dell Latitude): 50-100 units
        - Budget models (e.g., Lenovo IdeaPad): 100-200 units
    - Distribute across warehouses A, B, C based on regional demand
    - Ensure minimum stock levels per model
    - Calculate and record initial inventory value

### Time Management System
- Each simulation step represents one day
- At the start of each day, the simulation engine calculates random inventory movements
- Daily cycle: Initial check → Random transactions → End of day report

### Inventory Structure
- Laptop Properties
    - Model ID (unique identifier)
    - Brand and Model Name
    - Quantity
    - Unit Price
    - Minimum Stock Level
    - Category (Premium/Mid-range/Budget)

2. Storage System
    - Three warehouses (A, B, C)
    - Each laptop model stored across locations
    - Total model quantity is sum across warehouses

### Transaction System
- Purchase transactions only in initial phase
- Transaction records include:
    - Date
    - Laptop Model ID
    - Quantity
    - Warehouse Location
    - Transaction Type (Purchase)
    - Transaction ID
    - Purchase Value

#### Inventory Assistant
- Performs daily morning inventory check
- Generates daily report containing:
    - Current stock levels per laptop model
    - Stock levels per warehouse
    - Models below minimum stock level
    - Total inventory value by category
    - High-value items tracking (Premium models)

### Implementation Phases
#### Phase 1: Core Setup
    1. Implement laptop inventory data structures
    2. Set up warehouse system
    3. Create initial stock simulation
    4. Create time management loop

#### Phase 2: Transaction System
    1. Implement purchase transaction logging
    2. Create random transaction generator
    3. Add transaction validation

#### Phase 3: Assistant Implementation
    1. Create daily report generator
    2. Implement stock level monitoring
    3. Add basic alerting for low stock

## Technical Structure
```
INVENTORY-ASSISTANT/
├── inventory_assistant/
│   ├── assistent/
│   │   ├── __init__.py
│   │   └── reporter.py        # Inventory reporting functionality
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py             # SQLModel database setup and operations
│   ├── models/
│   │   ├── __init__.py
│   │   └── lap.py            # Laptop and warehouse stock models
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── engine.py         # Simulation core logic
│   │   └── generator.py      # Random data generation
│   ├── config.py             # Configuration settings
│   └── main.py               # Application entry point
├── nbs/                      # Notebooks for testing/development
├── .env.sample              # Environment variables template
├── pyproject.toml           # Project dependencies and metadata
└── README.md                # Project documentation
```