# Sample Data Files

This directory contains CSV files with sample data for testing and development.

## 📋 Available Files

### `products.csv`
Sample product catalog with:
- 10 products across different categories (Electronics, Furniture, Office Supplies)
- Complete product information (SKU, name, description, cost, reorder settings)
- Links to suppliers

### `suppliers.csv`
Sample supplier directory with:
- 5 suppliers with complete contact information
- Performance ratings and business terms
- Different lead times and minimum order quantities

### `locations.csv`
Sample warehouse/store locations with:
- Main warehouse, retail stores, distribution center
- Different location types for multi-location inventory management

### `transactions.csv`
Sample transaction history with:
- Various transaction types (receipts, shipments, transfers, adjustments)
- Realistic timestamps and reference documents
- User tracking and notes

## 🚀 Usage

These files can be imported into the application using:

1. **Simulation Service**:
   ```python
   from ai4supplychain.services.simulation import SimulationService
   sim = SimulationService()
   result = sim.initialize_sample_database()
   ```

2. **Manual Import** (via UI):
   - Navigate to each management section
   - Use the "Import" functionality
   - Upload the respective CSV files

3. **API Import**:
   - Use the bulk import endpoints
   - POST the CSV data to the appropriate endpoints

## 📊 Data Relationships

The sample data is designed with realistic relationships:
- Products are linked to suppliers
- Transactions reference existing products and locations
- Inventory levels reflect transaction history
- Suppliers have realistic business terms

## 🔧 Customization

You can modify these files to:
- Add more products/suppliers/locations
- Change business rules (reorder points, costs)
- Create different transaction patterns
- Test edge cases and scenarios

**Note**: Keep the CSV headers unchanged to ensure compatibility with the import functions.
