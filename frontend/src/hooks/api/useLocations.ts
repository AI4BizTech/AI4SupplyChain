import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type { Location, LocationCreate, LocationUpdate } from '../../services/api';

export function useLocations() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.locations.getAll();
      setLocations(data);
    } catch (err) {
      console.error('Failed to fetch locations:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch locations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  const createLocation = async (location: LocationCreate): Promise<Location | null> => {
    try {
      setError(null);
      const newLocation = await api.locations.create(location);
      setLocations(prev => [...prev, newLocation]);
      return newLocation;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create location');
      return null;
    }
  };

  const updateLocation = async (id: number, location: LocationUpdate): Promise<Location | null> => {
    try {
      setError(null);
      const updatedLocation = await api.locations.update(id, location);
      setLocations(prev => prev.map(l => l.id === id ? updatedLocation : l));
      return updatedLocation;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update location');
      return null;
    }
  };

  const deleteLocation = async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.locations.delete(id);
      // For soft delete, update the location status instead of removing
      setLocations(prev => prev.map(l => l.id === id ? { ...l, is_active: false } : l));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deactivate location');
      return false;
    }
  };

  const deleteLocationPermanently = async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.locations.deletePermanently(id);
      setLocations(prev => prev.filter(l => l.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to permanently delete location');
      return false;
    }
  };

  return {
    locations,
    loading,
    error,
    refetch: fetchLocations,
    createLocation,
    updateLocation,
    deleteLocation,
    deleteLocationPermanently,
  };
}