import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { X } from 'lucide-react';
import type { Product, ProductCreate, ProductUpdate } from '../../services/api';

interface ProductFormProps {
  product?: Product;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  title: string;
}

const ProductForm: React.FC<ProductFormProps> = ({
  product,
  onSubmit,
  onCancel,
  isLoading = false,
  title
}) => {
  const [formData, setFormData] = useState({
    sku: product?.sku || '',
    name: product?.name || '',
    description: product?.description || '',
    category: product?.category || '',
    unit_cost: product?.unit_cost?.toString() || '',
    unit_price: product?.unit_price?.toString() || '',
    weight: product?.weight?.toString() || '',
    dimensions: product?.dimensions || '',
    reorder_point: product?.reorder_point?.toString() || '10',
    reorder_quantity: product?.reorder_quantity?.toString() || '50',
    supplier_id: product?.supplier_id?.toString() || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.sku.trim()) {
      newErrors.sku = 'SKU is required';
    }
    if (!formData.name.trim()) {
      newErrors.name = 'Product name is required';
    }
    if (!formData.unit_cost || parseFloat(formData.unit_cost) < 0) {
      newErrors.unit_cost = 'Valid unit cost is required';
    }
    if (formData.unit_price && parseFloat(formData.unit_price) < 0) {
      newErrors.unit_price = 'Unit price must be positive';
    }
    if (formData.weight && parseFloat(formData.weight) < 0) {
      newErrors.weight = 'Weight must be positive';
    }
    if (!formData.reorder_point || parseInt(formData.reorder_point) < 0) {
      newErrors.reorder_point = 'Valid reorder point is required';
    }
    if (!formData.reorder_quantity || parseInt(formData.reorder_quantity) < 1) {
      newErrors.reorder_quantity = 'Reorder quantity must be at least 1';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const submitData: ProductCreate | ProductUpdate = {
      sku: formData.sku.trim(),
      name: formData.name.trim(),
      description: formData.description.trim() || undefined,
      category: formData.category.trim() || undefined,
      unit_cost: parseFloat(formData.unit_cost),
      unit_price: formData.unit_price ? parseFloat(formData.unit_price) : undefined,
      weight: formData.weight ? parseFloat(formData.weight) : undefined,
      dimensions: formData.dimensions.trim() || undefined,
      reorder_point: parseInt(formData.reorder_point),
      reorder_quantity: parseInt(formData.reorder_quantity),
      supplier_id: formData.supplier_id ? parseInt(formData.supplier_id) : undefined,
    };

    await onSubmit(submitData);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>
                {product ? 'Update product information' : 'Add a new product to your catalog'}
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  SKU <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.sku}
                  onChange={(e) => handleInputChange('sku', e.target.value)}
                  placeholder="PROD-001"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.sku ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.sku && <p className="text-red-500 text-xs mt-1">{errors.sku}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Product Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Product Name"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.name ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Product description..."
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Category</label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => handleInputChange('category', e.target.value)}
                placeholder="Electronics, Tools, etc."
                className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Pricing */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Unit Cost <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.unit_cost}
                  onChange={(e) => handleInputChange('unit_cost', e.target.value)}
                  placeholder="0.00"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.unit_cost ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.unit_cost && <p className="text-red-500 text-xs mt-1">{errors.unit_cost}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Unit Price</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.unit_price}
                  onChange={(e) => handleInputChange('unit_price', e.target.value)}
                  placeholder="0.00"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.unit_price ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.unit_price && <p className="text-red-500 text-xs mt-1">{errors.unit_price}</p>}
              </div>
            </div>

            {/* Physical Properties */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Weight (kg)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.weight}
                  onChange={(e) => handleInputChange('weight', e.target.value)}
                  placeholder="0.00"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.weight ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.weight && <p className="text-red-500 text-xs mt-1">{errors.weight}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Dimensions</label>
                <input
                  type="text"
                  value={formData.dimensions}
                  onChange={(e) => handleInputChange('dimensions', e.target.value)}
                  placeholder="L x W x H"
                  className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>

            {/* Inventory Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Reorder Point <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.reorder_point}
                  onChange={(e) => handleInputChange('reorder_point', e.target.value)}
                  placeholder="10"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.reorder_point ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.reorder_point && <p className="text-red-500 text-xs mt-1">{errors.reorder_point}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Reorder Quantity <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.reorder_quantity}
                  onChange={(e) => handleInputChange('reorder_quantity', e.target.value)}
                  placeholder="50"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.reorder_quantity ? 'border-red-500' : 'border-input'
                  }`}
                />
                {errors.reorder_quantity && <p className="text-red-500 text-xs mt-1">{errors.reorder_quantity}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Supplier ID</label>
              <input
                type="number"
                min="1"
                value={formData.supplier_id}
                onChange={(e) => handleInputChange('supplier_id', e.target.value)}
                placeholder="Leave empty if no supplier"
                className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Saving...' : product ? 'Update Product' : 'Add Product'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProductForm;