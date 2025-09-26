import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type { Supplier, SupplierCreate, SupplierUpdate } from '../../services/api';

export function useSuppliers() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.suppliers.getAll();
      setSuppliers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch suppliers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const createSupplier = async (supplier: SupplierCreate): Promise<Supplier | null> => {
    try {
      setError(null);
      const newSupplier = await api.suppliers.create(supplier);
      setSuppliers(prev => [...prev, newSupplier]);
      return newSupplier;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create supplier');
      return null;
    }
  };

  const updateSupplier = async (id: number, supplier: SupplierUpdate): Promise<Supplier | null> => {
    try {
      setError(null);
      const updatedSupplier = await api.suppliers.update(id, supplier);
      setSuppliers(prev => prev.map(s => s.id === id ? updatedSupplier : s));
      return updatedSupplier;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update supplier');
      return null;
    }
  };

  const deleteSupplier = async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.suppliers.delete(id);
      // For soft delete, update the supplier status instead of removing
      setSuppliers(prev => prev.map(s => s.id === id ? { ...s, is_active: false } : s));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deactivate supplier');
      return false;
    }
  };

  const deleteSupplierPermanently = async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.suppliers.deletePermanently(id);
      setSuppliers(prev => prev.filter(s => s.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to permanently delete supplier');
      return false;
    }
  };

  return {
    suppliers,
    loading,
    error,
    refetch: fetchSuppliers,
    createSupplier,
    updateSupplier,
    deleteSupplier,
    deleteSupplierPermanently,
  };
}