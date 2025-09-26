import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type { Product, ProductCreate, ProductUpdate } from '../../services/api';

export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.products.getAll();
      setProducts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const createProduct = async (product: ProductCreate): Promise<Product | null> => {
    try {
      setError(null);
      const newProduct = await api.products.create(product);
      setProducts(prev => [...prev, newProduct]);
      return newProduct;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create product');
      return null;
    }
  };

  const updateProduct = async (id: number, product: ProductUpdate): Promise<Product | null> => {
    try {
      setError(null);
      const updatedProduct = await api.products.update(id, product);
      setProducts(prev => prev.map(p => p.id === id ? updatedProduct : p));
      return updatedProduct;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update product');
      return null;
    }
  };

  const deleteProduct = async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.products.delete(id);
      // For soft delete, update the product status instead of removing
      setProducts(prev => prev.map(p => p.id === id ? { ...p, is_active: false } : p));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deactivate product');
      return false;
    }
  };

  const deleteProductPermanently = async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.products.deletePermanently(id);
      setProducts(prev => prev.filter(p => p.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to permanently delete product');
      return false;
    }
  };

  return {
    products,
    loading,
    error,
    refetch: fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    deleteProductPermanently,
  };
}