import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type { InventoryItem } from '../../services/api';

export function useInventory() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.inventory.getAll();
      setInventory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch inventory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const updateInventory = async (productId: number, locationId: number, update: Partial<InventoryItem>): Promise<InventoryItem | null> => {
    try {
      setError(null);
      const updatedItem = await api.inventory.update(productId, locationId, update);
      setInventory(prev => prev.map(item => 
        item.product_id === productId && item.location_id === locationId 
          ? updatedItem 
          : item
      ));
      return updatedItem;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update inventory');
      return null;
    }
  };

  const getAlerts = async (): Promise<InventoryItem[]> => {
    try {
      setError(null);
      return await api.inventory.getAlerts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
      return [];
    }
  };

  return {
    inventory,
    loading,
    error,
    refetch: fetchInventory,
    updateInventory,
    getAlerts,
  };
}