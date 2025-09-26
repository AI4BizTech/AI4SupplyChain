import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Search, Loader2, AlertCircle, Package, MapPin, RefreshCw } from 'lucide-react';
import { useInventory } from '../../hooks/api/useInventory';
import { useProducts } from '../../hooks/api/useProducts';
import { useLocations } from '../../hooks/api/useLocations';

const Inventory: React.FC = () => {
  const { inventory, loading, error, refetch } = useInventory();
  const { products } = useProducts();
  const { locations } = useLocations();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLocation, setSelectedLocation] = useState<string>('');

  // Create lookup maps for products and locations
  const productMap = new Map(products.map(p => [p.id, p]));
  const locationMap = new Map(locations.map(l => [l.id, l]));

  // Filter inventory based on search term and location
  const filteredInventory = inventory.filter(item => {
    const product = productMap.get(item.product_id);
    const location = locationMap.get(item.location_id);
    
    const matchesSearch = !searchTerm || 
      product?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product?.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      location?.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesLocation = !selectedLocation || 
      item.location_id.toString() === selectedLocation;
    
    return matchesSearch && matchesLocation;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading inventory...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Inventory</h1>
          <p className="text-muted-foreground">Monitor stock levels and availability</p>
        </div>
        <Button onClick={refetch}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="mb-6 border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-destructive mr-2" />
              <span className="text-destructive">{error}</span>
              <Button variant="outline" size="sm" onClick={refetch} className="ml-auto">
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder="Search by product name, SKU, or location..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring min-w-48"
            >
              <option value="">All Locations</option>
              {locations.map(location => (
                <option key={location.id} value={location.id.toString()}>
                  {location.name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-full">
                <Package className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-muted-foreground">Total Items</p>
                <p className="text-2xl font-bold">{filteredInventory.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-full">
                <Package className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-muted-foreground">Total On Hand</p>
                <p className="text-2xl font-bold">
                  {filteredInventory.reduce((sum, item) => sum + item.quantity_on_hand, 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-full">
                <AlertCircle className="w-6 h-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-muted-foreground">Low Stock Items</p>
                <p className="text-2xl font-bold">
                  {filteredInventory.filter(item => {
                    const product = productMap.get(item.product_id);
                    return product && item.quantity_on_hand <= product.reorder_point;
                  }).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Inventory Table */}
      {filteredInventory.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-muted-foreground">
              {searchTerm || selectedLocation ? 'No inventory items found matching your filters.' : 'No inventory items available.'}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Inventory Items ({filteredInventory.length})</CardTitle>
            <CardDescription>
              Current stock levels and availability
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-4 font-medium">Product</th>
                    <th className="text-left py-2 px-4 font-medium">Location</th>
                    <th className="text-left py-2 px-4 font-medium">On Hand</th>
                    <th className="text-left py-2 px-4 font-medium">Reserved</th>
                    <th className="text-left py-2 px-4 font-medium">Available</th>
                    <th className="text-left py-2 px-4 font-medium">Reorder Point</th>
                    <th className="text-left py-2 px-4 font-medium">Status</th>
                    <th className="text-left py-2 px-4 font-medium">Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInventory.map((item) => {
                    const product = productMap.get(item.product_id);
                    const location = locationMap.get(item.location_id);
                    const isLowStock = product && item.quantity_on_hand <= product.reorder_point;
                    
                    return (
                      <tr key={`${item.product_id}-${item.location_id}`} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium">{product?.name || 'Unknown Product'}</div>
                            <div className="text-sm text-muted-foreground font-mono">{product?.sku}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center">
                            <MapPin className="w-4 h-4 mr-1 text-muted-foreground" />
                            {location?.name || 'Unknown Location'}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm font-medium">
                          {item.quantity_on_hand}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {item.reserved_quantity}
                        </td>
                        <td className="py-3 px-4 text-sm font-medium">
                          {item.available_quantity}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {product?.reorder_point || '-'}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              isLowStock
                                ? 'bg-red-100 text-red-800'
                                : item.available_quantity > 0
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {isLowStock ? 'Low Stock' : item.available_quantity > 0 ? 'In Stock' : 'Out of Stock'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground">
                          {new Date(item.last_updated).toLocaleDateString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Inventory;