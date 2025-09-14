"""
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.data.database import get_database
from src.config import validate_config
from src.api.inventory import router as inventory_router
from src.api.suppliers import router as suppliers_router
from src.api.transactions import router as transactions_router
from src.api.forecast import router as forecast_router
from src.api.chat import router as chat_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AI4SupplyChain API...")
    
    # Validate configuration
    if not validate_config():
        logger.warning("Configuration validation failed - some features may not work")
    
    # Initialize database
    try:
        db = get_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI4SupplyChain API...")

# Create FastAPI app
app = FastAPI(
    title="AI4SupplyChain API",
    description="AI-Powered Dynamic Inventory and Demand Planning System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(suppliers_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(forecast_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI4SupplyChain API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_database()
        with db.session() as session:
            session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-01-13T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
