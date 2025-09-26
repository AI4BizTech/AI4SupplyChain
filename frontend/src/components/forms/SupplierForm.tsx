import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { X } from 'lucide-react';
import type { Supplier, SupplierCreate, SupplierUpdate } from '../../services/api';

interface SupplierFormProps {
  supplier?: Supplier;
  title: string;
  onSubmit: (data: SupplierCreate | SupplierUpdate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const SupplierForm: React.FC<SupplierFormProps> = ({
  supplier,
  title,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const [formData, setFormData] = useState({
    name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    lead_time_days: 7,
    payment_terms: '',
    minimum_order_qty: 1,
    performance_rating: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (supplier) {
      setFormData({
        name: supplier.name || '',
        contact_person: supplier.contact_person || '',
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        lead_time_days: supplier.lead_time_days || 7,
        payment_terms: supplier.payment_terms || '',
        minimum_order_qty: supplier.minimum_order_qty || 1,
        performance_rating: supplier.performance_rating?.toString() || '',
      });
    }
  }, [supplier]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Supplier name is required';
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (formData.lead_time_days < 0) {
      newErrors.lead_time_days = 'Lead time must be 0 or greater';
    }

    if (formData.minimum_order_qty < 1) {
      newErrors.minimum_order_qty = 'Minimum order quantity must be at least 1';
    }

    if (formData.performance_rating &&
        (parseFloat(formData.performance_rating) < 0 || parseFloat(formData.performance_rating) > 5)) {
      newErrors.performance_rating = 'Performance rating must be between 0 and 5';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const submitData: SupplierCreate | SupplierUpdate = {
      name: formData.name.trim(),
      contact_person: formData.contact_person.trim() || undefined,
      email: formData.email.trim() || undefined,
      phone: formData.phone.trim() || undefined,
      address: formData.address.trim() || undefined,
      lead_time_days: formData.lead_time_days,
      payment_terms: formData.payment_terms.trim() || undefined,
      minimum_order_qty: formData.minimum_order_qty,
      performance_rating: formData.performance_rating ? parseFloat(formData.performance_rating) : undefined,
    };

    await onSubmit(submitData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>
                {supplier ? 'Update supplier information' : 'Enter supplier details'}
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
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-muted-foreground">Basic Information</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium mb-1">
                    Supplier Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.name ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="Enter supplier name"
                    disabled={isLoading}
                  />
                  {errors.name && (
                    <p className="text-sm text-destructive mt-1">{errors.name}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="contact_person" className="block text-sm font-medium mb-1">
                    Contact Person
                  </label>
                  <input
                    type="text"
                    id="contact_person"
                    name="contact_person"
                    value={formData.contact_person}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Enter contact person name"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.email ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="supplier@example.com"
                    disabled={isLoading}
                  />
                  {errors.email && (
                    <p className="text-sm text-destructive mt-1">{errors.email}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium mb-1">
                    Phone
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="+1 (555) 123-4567"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="address" className="block text-sm font-medium mb-1">
                  Address
                </label>
                <textarea
                  id="address"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Enter full address"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Business Terms */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-muted-foreground">Business Terms</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="lead_time_days" className="block text-sm font-medium mb-1">
                    Lead Time (Days)
                  </label>
                  <input
                    type="number"
                    id="lead_time_days"
                    name="lead_time_days"
                    value={formData.lead_time_days}
                    onChange={handleInputChange}
                    min="0"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.lead_time_days ? 'border-destructive' : 'border-input'
                    }`}
                    disabled={isLoading}
                  />
                  {errors.lead_time_days && (
                    <p className="text-sm text-destructive mt-1">{errors.lead_time_days}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="minimum_order_qty" className="block text-sm font-medium mb-1">
                    Minimum Order Quantity
                  </label>
                  <input
                    type="number"
                    id="minimum_order_qty"
                    name="minimum_order_qty"
                    value={formData.minimum_order_qty}
                    onChange={handleInputChange}
                    min="1"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.minimum_order_qty ? 'border-destructive' : 'border-input'
                    }`}
                    disabled={isLoading}
                  />
                  {errors.minimum_order_qty && (
                    <p className="text-sm text-destructive mt-1">{errors.minimum_order_qty}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="payment_terms" className="block text-sm font-medium mb-1">
                    Payment Terms
                  </label>
                  <input
                    type="text"
                    id="payment_terms"
                    name="payment_terms"
                    value={formData.payment_terms}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="e.g., Net 30, COD"
                    disabled={isLoading}
                  />
                </div>

                <div>
                  <label htmlFor="performance_rating" className="block text-sm font-medium mb-1">
                    Performance Rating (0-5)
                  </label>
                  <input
                    type="number"
                    id="performance_rating"
                    name="performance_rating"
                    value={formData.performance_rating}
                    onChange={handleInputChange}
                    min="0"
                    max="5"
                    step="0.1"
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                      errors.performance_rating ? 'border-destructive' : 'border-input'
                    }`}
                    placeholder="0.0"
                    disabled={isLoading}
                  />
                  {errors.performance_rating && (
                    <p className="text-sm text-destructive mt-1">{errors.performance_rating}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button variant="outline" type="button" onClick={onCancel} disabled={isLoading}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Saving...' : supplier ? 'Update Supplier' : 'Add Supplier'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default SupplierForm;