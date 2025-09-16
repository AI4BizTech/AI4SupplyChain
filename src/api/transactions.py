"""
Transaction processing API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from src.services.transactions import TransactionService
from src.data.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Pydantic models for API
class TransactionCreate(BaseModel):
    product_sku: str = Field(..., description="Product SKU")
    location_id: str = Field(..., description="Location ID")
    transaction_type: str = Field(..., description="Transaction type")
    quantity: int = Field(..., description="Quantity (positive for inbound, negative for outbound)")
    unit_cost: Optional[float] = Field(None, description="Unit cost for this transaction")
    reference_document: Optional[str] = Field(None, description="Reference document number")
    notes: Optional[str] = Field(None, description="Additional notes")
    user_id: str = Field(default="api", description="User ID")

class TransactionResponse(BaseModel):
    transaction_id: str
    product_sku: str
    location_id: str
    transaction_type: str
    quantity: int
    unit_cost: Optional[float]
    reference_document: Optional[str]
    timestamp: str
    user_id: str
    notes: Optional[str]

class OCRProcessingResult(BaseModel):
    success: bool
    ocr_data: Dict[str, Any]
    transactions_created: int
    transactions: List[Dict[str, Any]]
    errors: Optional[List[str]] = None

# Dependency to get transaction service
def get_transaction_service() -> TransactionService:
    return TransactionService(get_database())

@router.post("/", response_model=Dict[str, Any])
async def create_transaction(
    transaction: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Create a new inventory transaction"""
    try:
        # Convert SKU to product ID and location_id to internal ID
        from src.services.inventory import InventoryService
        inventory_service = InventoryService()
        
        product = inventory_service.get_product_by_sku(transaction.product_sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{transaction.product_sku}' not found")
        
        location = inventory_service.get_location_by_id(transaction.location_id)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location '{transaction.location_id}' not found")
        
        # Prepare transaction data
        transaction_data = {
            "product_id": product.id,
            "location_id": location.id,
            "transaction_type": transaction.transaction_type,
            "quantity": transaction.quantity,
            "unit_cost": transaction.unit_cost,
            "reference_document": transaction.reference_document,
            "notes": transaction.notes,
            "user_id": transaction.user_id,
            "processed": 1  # Process immediately for manual transactions
        }
        
        created_transaction = service.create_transaction(transaction_data)
        
        return {
            "success": True,
            "transaction": {
                "transaction_id": created_transaction.transaction_id,
                "product_sku": transaction.product_sku,
                "location_id": transaction.location_id,
                "transaction_type": created_transaction.transaction_type,
                "quantity": created_transaction.quantity,
                "timestamp": created_transaction.timestamp.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-document", response_model=OCRProcessingResult)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, JPG, PNG)"),
    document_type: str = Form(..., description="Document type: purchase_order or delivery_order"),
    location_id: str = Form(..., description="Location ID for processing"),
    user_id: str = Form(default="api", description="User ID"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Upload and process a document using OCR"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not supported. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate document type
        if document_type not in ["purchase_order", "delivery_order"]:
            raise HTTPException(
                status_code=400,
                detail="Document type must be 'purchase_order' or 'delivery_order'"
            )
        
        # Get location internal ID
        from src.services.inventory import InventoryService
        inventory_service = InventoryService()
        location = inventory_service.get_location_by_id(location_id)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location '{location_id}' not found")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Process document
        result = service.process_uploaded_document(
            file_content=file_content,
            filename=file.filename or "uploaded_document",
            document_type=document_type,
            location_id=location.id,
            user_id=user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Document processing failed"))
        
        return OCRProcessingResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.get("/pending-receipts")
async def get_pending_receipts(
    service: TransactionService = Depends(get_transaction_service)
):
    """Get all pending expected receipts"""
    try:
        pending_receipts = service.get_pending_receipts()
        
        return {
            "pending_receipts": pending_receipts,
            "count": len(pending_receipts)
        }
    except Exception as e:
        logger.error(f"Error getting pending receipts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/process-receipt/{transaction_id}")
async def process_expected_receipt(
    transaction_id: str,
    actual_quantity: int = Query(..., description="Actual quantity received"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Convert an expected receipt to an actual receipt"""
    try:
        success = service.process_expected_receipt(transaction_id, actual_quantity)
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Expected receipt transaction '{transaction_id}' not found"
            )
        
        return {
            "success": True,
            "message": f"Processed receipt for transaction {transaction_id}",
            "transaction_id": transaction_id,
            "actual_quantity": actual_quantity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing expected receipt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_transaction_history(
    product_sku: Optional[str] = Query(None, description="Filter by product SKU"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction history with optional filters"""
    try:
        from src.services.inventory import InventoryService
        inventory_service = InventoryService()
        
        # Convert filters to internal IDs
        product_pk = None
        if product_sku:
            product = inventory_service.get_product_by_sku(product_sku)
            if product:
                product_pk = product.id
        
        location_pk = None
        if location_id:
            location = inventory_service.get_location_by_id(location_id)
            if location:
                location_pk = location.id
        
        transactions = inventory_service.get_transaction_history(
            product_id=product_pk,
            location_id=location_pk,
            limit=limit
        )
        
        # Filter by transaction type if specified
        if transaction_type:
            transactions = [t for t in transactions if t['transaction_type'] == transaction_type]
        
        return {
            "transactions": transactions,
            "count": len(transactions),
            "filters": {
                "product_sku": product_sku,
                "location_id": location_id,
                "transaction_type": transaction_type
            }
        }
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_transaction_types():
    """Get available transaction types"""
    return {
        "transaction_types": [
            {
                "type": "receipt",
                "description": "Goods received into inventory",
                "quantity_sign": "positive"
            },
            {
                "type": "shipment", 
                "description": "Goods shipped out of inventory",
                "quantity_sign": "negative"
            },
            {
                "type": "adjustment",
                "description": "Inventory adjustments (cycle counts, damage, etc.)",
                "quantity_sign": "positive or negative"
            },
            {
                "type": "transfer",
                "description": "Transfer between locations",
                "quantity_sign": "negative at source, positive at destination"
            },
            {
                "type": "expected_receipt",
                "description": "Expected receipt from purchase order",
                "quantity_sign": "positive"
            }
        ]
    }

@router.get("/summary")
async def get_transaction_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days for summary"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction summary statistics"""
    try:
        from src.services.inventory import InventoryService
        from datetime import datetime, timedelta
        
        inventory_service = InventoryService()
        
        # Get recent transactions
        transactions = inventory_service.get_transaction_history(limit=1000)
        
        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_transactions = [
            t for t in transactions 
            if t['timestamp'] >= cutoff_date
        ]
        
        # Calculate summary statistics
        total_transactions = len(recent_transactions)
        
        by_type = {}
        total_inbound = 0
        total_outbound = 0
        
        for transaction in recent_transactions:
            trans_type = transaction['transaction_type']
            quantity = transaction['quantity']
            
            # Count by type
            by_type[trans_type] = by_type.get(trans_type, 0) + 1
            
            # Sum quantities
            if quantity > 0:
                total_inbound += quantity
            else:
                total_outbound += abs(quantity)
        
        return {
            "period_days": days,
            "total_transactions": total_transactions,
            "total_inbound_quantity": total_inbound,
            "total_outbound_quantity": total_outbound,
            "net_quantity_change": total_inbound - total_outbound,
            "transactions_by_type": by_type,
            "average_transactions_per_day": round(total_transactions / days, 1) if days > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting transaction summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
