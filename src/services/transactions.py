"""
Transaction processing service with OCR support
"""

import pytesseract
from PIL import Image
import io
import re
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import uuid

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from src.data.database import get_database
from src.data.inventory import Product, Location, Transaction, Inventory
from src.config import OCR_PROVIDER, AWS_REGION

logger = logging.getLogger(__name__)

class OCRService:
    """Service for processing Purchase Orders and Delivery Orders using OCR"""
    
    def __init__(self, ocr_provider: str = OCR_PROVIDER):
        self.provider = ocr_provider.lower()
        
        if self.provider == "google" and GOOGLE_VISION_AVAILABLE:
            try:
                self.vision_client = vision.ImageAnnotatorClient()
            except Exception as e:
                logger.warning(f"Google Vision API not configured: {e}")
                self.provider = "tesseract"
        elif self.provider == "aws" and AWS_AVAILABLE:
            try:
                self.textract = boto3.client('textract', region_name=AWS_REGION)
            except Exception as e:
                logger.warning(f"AWS Textract not configured: {e}")
                self.provider = "tesseract"
        else:
            self.provider = "tesseract"
    
    def process_document(self, file_content: bytes, document_type: str) -> Dict[str, Any]:
        """Process uploaded document and extract relevant information"""
        try:
            if self.provider == "tesseract":
                return self._process_with_tesseract(file_content, document_type)
            elif self.provider == "google":
                return self._process_with_google_vision(file_content, document_type)
            elif self.provider == "aws":
                return self._process_with_aws_textract(file_content, document_type)
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {"error": f"OCR processing failed: {str(e)}"}
    
    def _process_with_tesseract(self, file_content: bytes, document_type: str) -> Dict[str, Any]:
        """Process document using Tesseract OCR"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(file_content))
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Parse based on document type
            if document_type.lower() == "purchase_order":
                return self._parse_purchase_order(text)
            elif document_type.lower() == "delivery_order":
                return self._parse_delivery_order(text)
            else:
                return {"raw_text": text, "parsed_data": {}, "document_type": document_type}
                
        except Exception as e:
            logger.error(f"Tesseract processing failed: {e}")
            return {"error": f"Tesseract processing failed: {str(e)}"}
    
    def _process_with_google_vision(self, file_content: bytes, document_type: str) -> Dict[str, Any]:
        """Process document using Google Vision API"""
        try:
            image = vision.Image(content=file_content)
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                text = texts[0].description
            else:
                text = ""
            
            if document_type.lower() == "purchase_order":
                return self._parse_purchase_order(text)
            elif document_type.lower() == "delivery_order":
                return self._parse_delivery_order(text)
            else:
                return {"raw_text": text, "parsed_data": {}, "document_type": document_type}
                
        except Exception as e:
            logger.error(f"Google Vision processing failed: {e}")
            return {"error": f"Google Vision processing failed: {str(e)}"}
    
    def _process_with_aws_textract(self, file_content: bytes, document_type: str) -> Dict[str, Any]:
        """Process document using AWS Textract"""
        try:
            response = self.textract.detect_document_text(
                Document={'Bytes': file_content}
            )
            
            text_lines = []
            for item in response['Blocks']:
                if item['BlockType'] == 'LINE':
                    text_lines.append(item['Text'])
            
            text = '\n'.join(text_lines)
            
            if document_type.lower() == "purchase_order":
                return self._parse_purchase_order(text)
            elif document_type.lower() == "delivery_order":
                return self._parse_delivery_order(text)
            else:
                return {"raw_text": text, "parsed_data": {}, "document_type": document_type}
                
        except Exception as e:
            logger.error(f"AWS Textract processing failed: {e}")
            return {"error": f"AWS Textract processing failed: {str(e)}"}
    
    def _parse_purchase_order(self, text: str) -> Dict[str, Any]:
        """Parse Purchase Order text and extract structured data"""
        parsed_data = {
            "document_type": "purchase_order",
            "po_number": None,
            "supplier": None,
            "date": None,
            "items": [],
            "raw_text": text
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract PO Number
            po_match = re.search(r'(?:PO|Purchase Order|P\.O\.)\s*[#:]?\s*(\w+)', line, re.IGNORECASE)
            if po_match and not parsed_data["po_number"]:
                parsed_data["po_number"] = po_match.group(1)
            
            # Extract supplier information
            if any(word in line.lower() for word in ['vendor', 'supplier', 'from']) and not parsed_data["supplier"]:
                parsed_data["supplier"] = line
            
            # Extract date
            date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', line)
            if date_match and not parsed_data["date"]:
                parsed_data["date"] = date_match.group(0)
            
            # Extract item information (basic pattern matching)
            # Look for patterns like: SKU123 Description 10 $25.00
            item_match = re.search(r'([A-Z0-9-]+)\s+(.+?)\s+(\d+)\s+\$?(\d+\.?\d*)', line)
            if item_match:
                parsed_data["items"].append({
                    "sku": item_match.group(1),
                    "description": item_match.group(2).strip(),
                    "quantity": int(item_match.group(3)),
                    "price": float(item_match.group(4))
                })
        
        return parsed_data
    
    def _parse_delivery_order(self, text: str) -> Dict[str, Any]:
        """Parse Delivery Order text and extract structured data"""
        parsed_data = {
            "document_type": "delivery_order",
            "do_number": None,
            "supplier": None,
            "date": None,
            "items": [],
            "raw_text": text
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract DO Number
            do_match = re.search(r'(?:DO|Delivery Order|D\.O\.)\s*[#:]?\s*(\w+)', line, re.IGNORECASE)
            if do_match and not parsed_data["do_number"]:
                parsed_data["do_number"] = do_match.group(1)
            
            # Extract supplier information
            if any(word in line.lower() for word in ['vendor', 'supplier', 'from']) and not parsed_data["supplier"]:
                parsed_data["supplier"] = line
            
            # Extract date
            date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', line)
            if date_match and not parsed_data["date"]:
                parsed_data["date"] = date_match.group(0)
            
            # Extract delivered items
            item_match = re.search(r'([A-Z0-9-]+)\s+(.+?)\s+(\d+)', line)
            if item_match:
                parsed_data["items"].append({
                    "sku": item_match.group(1),
                    "description": item_match.group(2).strip(),
                    "quantity_delivered": int(item_match.group(3))
                })
        
        return parsed_data

class TransactionService:
    """Service for processing inventory transactions with OCR support"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
        self.ocr_service = OCRService()
    
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Transaction:
        """Create a new transaction"""
        with self.db.session() as session:
            # Generate unique transaction ID if not provided
            if 'transaction_id' not in transaction_data:
                transaction_data['transaction_id'] = f"{transaction_data['transaction_type']}_{uuid.uuid4().hex[:8]}"
            
            transaction = Transaction(**transaction_data)
            session.add(transaction)
            session.flush()
            session.refresh(transaction)
            
            # Update inventory if this is a processed transaction
            if transaction.processed == 1 and transaction.transaction_type in ['receipt', 'shipment', 'adjustment']:
                self._update_inventory_from_transaction(session, transaction)
            
            return transaction
    
    def _update_inventory_from_transaction(self, session, transaction: Transaction):
        """Update inventory levels based on transaction"""
        try:
            # Get or create inventory record
            inventory = session.query(Inventory).filter(
                Inventory.product_id == transaction.product_id,
                Inventory.location_id == transaction.location_id
            ).first()
            
            if not inventory:
                inventory = Inventory(
                    product_id=transaction.product_id,
                    location_id=transaction.location_id,
                    quantity_on_hand=0,
                    reserved_quantity=0,
                    available_quantity=0
                )
                session.add(inventory)
            
            # Update quantities based on transaction type
            if transaction.transaction_type in ['receipt', 'adjustment']:
                inventory.quantity_on_hand += transaction.quantity
            elif transaction.transaction_type == 'shipment':
                inventory.quantity_on_hand += transaction.quantity  # quantity is negative for shipments
            
            # Recalculate available quantity
            inventory.available_quantity = inventory.quantity_on_hand - inventory.reserved_quantity
            inventory.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating inventory from transaction: {e}")
            raise
    
    def process_uploaded_document(self, file_content: bytes, filename: str, 
                                 document_type: str, location_id: int, user_id: str = "system") -> Dict[str, Any]:
        """Process uploaded document and create transactions"""
        try:
            # Extract data using OCR
            ocr_result = self.ocr_service.process_document(file_content, document_type)
            
            if "error" in ocr_result:
                return ocr_result
            
            # Process extracted items
            transactions_created = []
            errors = []
            
            for item in ocr_result.get("items", []):
                try:
                    # Look up product by SKU
                    with self.db.session() as session:
                        product = session.query(Product).filter(Product.sku == item["sku"]).first()
                        if not product:
                            errors.append(f"Product with SKU '{item['sku']}' not found")
                            continue
                        
                        # Create transaction based on document type
                        if document_type == "purchase_order":
                            # For PO, create expected receipt transaction (not processed yet)
                            transaction_data = {
                                "product_id": product.id,
                                "location_id": location_id,
                                "transaction_type": "expected_receipt",
                                "quantity": item["quantity"],
                                "unit_cost": item.get("price"),
                                "reference_document": f"PO-{ocr_result.get('po_number', 'UNKNOWN')}",
                                "notes": f"From OCR processing of {filename}",
                                "user_id": user_id,
                                "processed": 0  # Not processed yet - just expectation
                            }
                        elif document_type == "delivery_order":
                            # For DO, create actual receipt transaction
                            transaction_data = {
                                "product_id": product.id,
                                "location_id": location_id,
                                "transaction_type": "receipt",
                                "quantity": item["quantity_delivered"],
                                "reference_document": f"DO-{ocr_result.get('do_number', 'UNKNOWN')}",
                                "notes": f"From OCR processing of {filename}",
                                "user_id": user_id,
                                "processed": 1  # Process immediately for deliveries
                            }
                        
                        # Create the transaction
                        transaction = self.create_transaction(transaction_data)
                        transactions_created.append({
                            "transaction_id": transaction.transaction_id,
                            "sku": item["sku"],
                            "quantity": transaction.quantity,
                            "type": transaction.transaction_type
                        })
                        
                except Exception as e:
                    errors.append(f"Error processing item {item.get('sku', 'unknown')}: {str(e)}")
                    logger.error(f"Error processing OCR item: {e}")
            
            return {
                "success": True,
                "ocr_data": ocr_result,
                "transactions_created": len(transactions_created),
                "transactions": transactions_created,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {"error": f"Document processing failed: {str(e)}"}
    
    def get_pending_receipts(self) -> List[Dict[str, Any]]:
        """Get all pending expected receipts"""
        with self.db.session() as session:
            transactions = session.query(
                Transaction,
                Product.sku,
                Product.name.label('product_name'),
                Location.location_id,
                Location.name.label('location_name')
            ).join(Product).join(Location).filter(
                Transaction.transaction_type == 'expected_receipt',
                Transaction.processed == 0
            ).all()
            
            results = []
            for trans, sku, product_name, loc_id, loc_name in transactions:
                results.append({
                    'transaction_id': trans.transaction_id,
                    'sku': sku,
                    'product_name': product_name,
                    'location_id': loc_id,
                    'location_name': loc_name,
                    'expected_quantity': trans.quantity,
                    'reference_document': trans.reference_document,
                    'timestamp': trans.timestamp,
                    'notes': trans.notes
                })
            
            return results
    
    def process_expected_receipt(self, transaction_id: str, actual_quantity: int) -> bool:
        """Convert expected receipt to actual receipt"""
        with self.db.session() as session:
            transaction = session.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()
            
            if not transaction or transaction.transaction_type != 'expected_receipt':
                return False
            
            # Update the transaction
            transaction.transaction_type = 'receipt'
            transaction.quantity = actual_quantity
            transaction.processed = 1
            transaction.notes = (transaction.notes or '') + f" | Processed on {datetime.utcnow()}"
            
            # Update inventory
            self._update_inventory_from_transaction(session, transaction)
            
            session.flush()
            return True
