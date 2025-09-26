"""
FastAPI main application for AI4SupplyChain inventory management.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from ..config import settings
from ..data.database import init_database
from .products import router as products_router
from .inventory import router as inventory_router
from .suppliers import router as suppliers_router
from .locations import router as locations_router
from .transactions import router as transactions_router

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting AI4SupplyChain backend...")
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI4SupplyChain backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
app.include_router(suppliers_router, prefix="/api/suppliers", tags=["suppliers"])
app.include_router(locations_router, prefix="/api/locations", tags=["locations"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])


@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI4SupplyChain Inventory Management API",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }


@app.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    from ..data.database import check_database_health
    
    db_healthy = check_database_health()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.api_version
    }


@app.get("/api/stats", summary="System statistics")
async def system_stats():
    """Get overall system statistics."""
    from ..data.database import get_session
    from ..services.inventory_service import InventoryService
    from ..services.supplier_service import SupplierService
    from ..services.location_service import LocationService
    from sqlmodel import select, func
    from ..data.models import Product, Transaction

    try:
        # Use proper session management with dependency injection pattern
        session_gen = get_session()
        session = next(session_gen)
        try:
            # Get basic counts
            total_products = session.exec(select(func.count(Product.id))).first()
            active_products = session.exec(
                select(func.count(Product.id)).where(Product.is_active == True)
            ).first()
            total_transactions = session.exec(select(func.count(Transaction.id))).first()

            # Get service statistics
            supplier_service = SupplierService(session)
            location_service = LocationService(session)

            supplier_stats = supplier_service.get_supplier_statistics()
            location_stats = location_service.get_location_statistics()

            return {
                "products": {
                    "total": total_products or 0,
                    "active": active_products or 0,
                },
                "transactions": {
                    "total": total_transactions or 0,
                },
                "suppliers": supplier_stats,
                "locations": location_stats,
                "system": {
                    "version": settings.api_version,
                    "database_type": "SQLite",
                    "allow_negative_inventory": settings.allow_negative_inventory,
                }
            }
        finally:
            # Ensure session is properly closed
            try:
                next(session_gen)
            except StopIteration:
                pass
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system statistics")


@app.get("/api/system/pool-status", summary="Database connection pool status")
async def get_pool_status():
    """Get database connection pool status for monitoring."""
    from ..data.database import get_connection_pool_status
    try:
        return get_connection_pool_status()
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving pool status")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )