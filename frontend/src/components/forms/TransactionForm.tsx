import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { X, ArrowDown, ArrowUp, ArrowLeftRight, Settings } from 'lucide-react';
import { useProducts } from '../../hooks/api/useProducts';
import { useLocations } from '../../hooks/api/useLocations';
import type {
  TransactionCreate,
  StockReceiptRequest,
  StockShipmentRequest,
  StockTransferRequest,
  StockAdjustmentRequest
} from '../../services/api';

type TransactionType = 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';

interface TransactionFormProps {
  title: string;
  transactionType?: TransactionType;
  onSubmit: (data: TransactionCreate | StockReceiptRequest | StockShipmentRequest | StockTransferRequest | StockAdjustmentRequest, transactionType: TransactionType) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const TransactionForm: React.FC<TransactionFormProps> = ({
  title,
  transactionType: initialType,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const { products } = useProducts();
  const { locations } = useLocations();

  const [transactionType, setTransactionType] = useState<TransactionType>(initialType || 'IN');
  const [formData, setFormData] = useState({
    product_id: '',
    location_id: '',
    from_location_id: '',
    to_location_id: '',
    quantity: '',
    adjustment_quantity: '',
    reference_number: '',
    notes: '',
    reason: '',
    user_id: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when transaction type changes
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      quantity: '',
      adjustment_quantity: '',
      from_location_id: '',
      to_location_id: '',
      reason: '',
    }));
    setErrors({});
  }, [transactionType]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Common validations
    if (!formData.product_id) {
      newErrors.product_id = 'Product is required';
    }

    // Type-specific validations
    switch (transactionType) {
      case 'IN':
      case 'OUT':
        if (!formData.location_id) {
          newErrors.location_id = 'Location is required';
        }
        if (!formData.quantity || Number(formData.quantity) <= 0) {
          newErrors.quantity = 'Quantity must be greater than 0';
        }
        break;

      case 'TRANSFER':
        if (!formData.from_location_id) {
          newErrors.from_location_id = 'From location is required';
        }
        if (!formData.to_location_id) {
          newErrors.to_location_id = 'To location is required';
        }
        if (formData.from_location_id === formData.to_location_id) {
          newErrors.to_location_id = 'To location must be different from from location';
        }
        if (!formData.quantity || Number(formData.quantity) <= 0) {
          newErrors.quantity = 'Quantity must be greater than 0';
        }
        break;

      case 'ADJUSTMENT':
        if (!formData.location_id) {
          newErrors.location_id = 'Location is required';
        }
        if (!formData.adjustment_quantity || Number(formData.adjustment_quantity) === 0) {
          newErrors.adjustment_quantity = 'Adjustment quantity cannot be zero';
        }
        if (!formData.reason.trim()) {
          newErrors.reason = 'Reason is required for adjustments';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Prepare data based on transaction type
    let submitData: any;

    switch (transactionType) {
      case 'IN':
        submitData = {
          product_id: Number(formData.product_id),
          location_id: Number(formData.location_id),
          quantity: Number(formData.quantity),
          reference_number: formData.reference_number.trim() || undefined,
          notes: formData.notes.trim() || undefined,
          user_id: formData.user_id.trim() || undefined,
        } as StockReceiptRequest;
        break;

      case 'OUT':
        submitData = {
          product_id: Number(formData.product_id),
          location_id: Number(formData.location_id),
          quantity: Number(formData.quantity),
          reference_number: formData.reference_number.trim() || undefined,
          notes: formData.notes.trim() || undefined,
          user_id: formData.user_id.trim() || undefined,
        } as StockShipmentRequest;
        break;

      case 'TRANSFER':
        submitData = {
          product_id: Number(formData.product_id),
          from_location_id: Number(formData.from_location_id),
          to_location_id: Number(formData.to_location_id),
          quantity: Number(formData.quantity),
          reference_number: formData.reference_number.trim() || undefined,
          notes: formData.notes.trim() || undefined,
          user_id: formData.user_id.trim() || undefined,
        } as StockTransferRequest;
        break;

      case 'ADJUSTMENT':
        submitData = {
          product_id: Number(formData.product_id),
          location_id: Number(formData.location_id),
          adjustment_quantity: Number(formData.adjustment_quantity),
          reason: formData.reason.trim(),
          user_id: formData.user_id.trim() || undefined,
        } as StockAdjustmentRequest;
        break;
    }

    await onSubmit(submitData, transactionType);
  };

  const getTransactionTypeDisplay = (type: TransactionType) => {
    switch (type) {
      case 'IN':
        return {
          icon: ArrowDown,
          label: 'Stock Receipt',
          description: 'Add inventory to a location',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
        };
      case 'OUT':
        return {
          icon: ArrowUp,
          label: 'Stock Shipment',
          description: 'Remove inventory from a location',
          color: 'text-red-600',
          bgColor: 'bg-red-100',
        };
      case 'TRANSFER':
        return {
          icon: ArrowLeftRight,
          label: 'Stock Transfer',
          description: 'Move inventory between locations',
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
        };
      case 'ADJUSTMENT':
        return {
          icon: Settings,
          label: 'Stock Adjustment',
          description: 'Adjust inventory quantities',
          color: 'text-purple-600',
          bgColor: 'bg-purple-100',
        };
    }
  };

  const activeLocations = locations.filter(l => l.is_active);
  const activeProducts = products.filter(p => p.is_active);
  const typeDisplay = getTransactionTypeDisplay(transactionType);
  const Icon = typeDisplay.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className={`p-2 rounded-full ${typeDisplay.bgColor} mr-3`}>
                <Icon className={`w-5 h-5 ${typeDisplay.color}`} />
              </div>
              <div>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{typeDisplay.description}</CardDescription>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Transaction Type Selection (if not pre-selected) */}
            {!initialType && (
              <div>
                <label className="block text-sm font-medium mb-2">Transaction Type</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {(['IN', 'OUT', 'TRANSFER', 'ADJUSTMENT'] as TransactionType[]).map((type) => {
                    const display = getTransactionTypeDisplay(type);
                    const TypeIcon = display.icon;
                    return (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setTransactionType(type)}
                        className={`p-3 border rounded-lg text-left transition-colors ${
                          transactionType === type
                            ? 'border-primary bg-primary/5'
                            : 'border-input hover:bg-muted'
                        }`}
                      >
                        <div className="flex items-center mb-2">
                          <div className={`p-1 rounded-full ${display.bgColor} mr-2`}>
                            <TypeIcon className={`w-4 h-4 ${display.color}`} />
                          </div>
                          <span className="font-medium text-sm">{display.label}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Product Selection */}
            <div>
              <label htmlFor="product_id" className="block text-sm font-medium mb-1">
                Product *
              </label>
              <select
                id="product_id"
                name="product_id"
                value={formData.product_id}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                  errors.product_id ? 'border-destructive' : 'border-input'
                }`}
                disabled={isLoading}
              >
                <option value="">Select a product...</option>
                {activeProducts.map(product => (
                  <option key={product.id} value={product.id}>
                    {product.name} ({product.sku})
                  </option>
                ))}
              </select>
              {errors.product_id && (
                <p className="text-sm text-destructive mt-1">{errors.product_id}</p>
              )}
            </div>

            {/* Location Fields */}
            {transactionType === 'TRANSFER' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="from_location_id" className="block text-sm font-medium mb-1">
                    From Location *
                  </label>
                  <select
                    id="from_location_id"
                    name="from_location_id"
                    value={formData.from_location_id}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.from_location_id ? 'border-destructive' : 'border-input'
                    }`}
                    disabled={isLoading}
                  >
                    <option value="">Select from location...</option>
                    {activeLocations.map(location => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                  {errors.from_location_id && (
                    <p className="text-sm text-destructive mt-1">{errors.from_location_id}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="to_location_id" className="block text-sm font-medium mb-1">
                    To Location *
                  </label>
                  <select
                    id="to_location_id"
                    name="to_location_id"
                    value={formData.to_location_id}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.to_location_id ? 'border-destructive' : 'border-input'
                    }`}
                    disabled={isLoading}
                  >
                    <option value="">Select to location...</option>
                    {activeLocations.map(location => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                  {errors.to_location_id && (
                    <p className="text-sm text-destructive mt-1">{errors.to_location_id}</p>
                  )}
                </div>
              </div>
            ) : (
              <div>
                <label htmlFor="location_id" className="block text-sm font-medium mb-1">
                  Location *
                </label>
                <select
                  id="location_id"
                  name="location_id"
                  value={formData.location_id}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.location_id ? 'border-destructive' : 'border-input'
                  }`}
                  disabled={isLoading}
                >
                  <option value="">Select a location...</option>
                  {activeLocations.map(location => (
                    <option key={location.id} value={location.id}>
                      {location.name}
                    </option>
                  ))}
                </select>
                {errors.location_id && (
                  <p className="text-sm text-destructive mt-1">{errors.location_id}</p>
                )}
              </div>
            )}

            {/* Quantity Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {transactionType === 'ADJUSTMENT' ? (
                <div>
                  <label htmlFor="adjustment_quantity" className="block text-sm font-medium mb-1">
                    Adjustment Quantity *
                  </label>
                  <input
                    type="number"
                    id="adjustment_quantity"
                    name="adjustment_quantity"
                    value={formData.adjustment_quantity}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.adjustment_quantity ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="e.g., -5 or +10"
                    disabled={isLoading}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Use negative values to decrease, positive to increase
                  </p>
                  {errors.adjustment_quantity && (
                    <p className="text-sm text-destructive mt-1">{errors.adjustment_quantity}</p>
                  )}
                </div>
              ) : (
                <div>
                  <label htmlFor="quantity" className="block text-sm font-medium mb-1">
                    Quantity *
                  </label>
                  <input
                    type="number"
                    id="quantity"
                    name="quantity"
                    value={formData.quantity}
                    onChange={handleInputChange}
                    min="1"
                    step="1"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.quantity ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="Enter quantity"
                    disabled={isLoading}
                  />
                  {errors.quantity && (
                    <p className="text-sm text-destructive mt-1">{errors.quantity}</p>
                  )}
                </div>
              )}

              <div>
                <label htmlFor="reference_number" className="block text-sm font-medium mb-1">
                  Reference Number
                </label>
                <input
                  type="text"
                  id="reference_number"
                  name="reference_number"
                  value={formData.reference_number}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="PO-123, DO-456, etc."
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Adjustment Reason (only for adjustments) */}
            {transactionType === 'ADJUSTMENT' && (
              <div>
                <label htmlFor="reason" className="block text-sm font-medium mb-1">
                  Reason *
                </label>
                <input
                  type="text"
                  id="reason"
                  name="reason"
                  value={formData.reason}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.reason ? 'border-destructive' : 'border-input'
                  }`}
                  placeholder="e.g., Physical count correction, Damaged goods"
                  disabled={isLoading}
                />
                {errors.reason && (
                  <p className="text-sm text-destructive mt-1">{errors.reason}</p>
                )}
              </div>
            )}

            {/* Optional Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="user_id" className="block text-sm font-medium mb-1">
                  User ID
                </label>
                <input
                  type="text"
                  id="user_id"
                  name="user_id"
                  value={formData.user_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Enter user identifier"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="notes" className="block text-sm font-medium mb-1">
                Notes
              </label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Additional notes about this transaction"
                disabled={isLoading}
              />
            </div>

            {/* Form Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button variant="outline" type="button" onClick={onCancel} disabled={isLoading}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Processing...' : `Process ${typeDisplay.label}`}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default TransactionForm;