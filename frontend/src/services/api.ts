// API client for AI4SupplyChain backend
import { queuedRequest } from '../utils/requestQueue';

const API_BASE_URL = 'http://localhost:8000/api';

// Error handling utility
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic API request function with queue management
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  return queuedRequest(async () => {
    const url = `${API_BASE_URL}${endpoint}`;

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        // Try to get error message from response body
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // If we can't parse the error body, use the default message
        }

        // Don't retry certain error codes
        if (response.status === 404 || response.status === 401 || response.status === 403 || response.status === 400) {
          throw new ApiError(response.status, errorMessage);
        }
        // Retry server errors (5xx) and some client errors
        throw new ApiError(response.status, errorMessage);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, 2); // Reduce max retries for API calls to 2
}

// Type definitions matching backend models
export interface Product {
  id: number;
  sku: string;
  name: string;
  description?: string;
  category?: string;
  unit_cost: number;
  unit_price?: number;
  weight?: number;
  dimensions?: string;
  reorder_point: number;
  reorder_quantity: number;
  supplier_id?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  sku: string;
  name: string;
  description?: string;
  category?: string;
  unit_cost: number;
  unit_price?: number;
  weight?: number;
  dimensions?: string;
  reorder_point?: number;
  reorder_quantity?: number;
  supplier_id?: number;
}

export interface ProductUpdate {
  name?: string;
  description?: string;
  category?: string;
  unit_cost?: number;
  unit_price?: number;
  weight?: number;
  dimensions?: string;
  reorder_point?: number;
  reorder_quantity?: number;
  supplier_id?: number;
  is_active?: boolean;
}

export interface Supplier {
  id: number;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  lead_time_days: number;
  payment_terms?: string;
  minimum_order_qty: number;
  is_active: boolean;
  performance_rating?: number;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  lead_time_days?: number;
  payment_terms?: string;
  minimum_order_qty?: number;
  performance_rating?: number;
}

export interface SupplierUpdate {
  name?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  lead_time_days?: number;
  payment_terms?: string;
  minimum_order_qty?: number;
  is_active?: boolean;
  performance_rating?: number;
}

export interface Location {
  id: number;
  name: string;
  code?: string;
  address?: string;
  warehouse_type?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LocationCreate {
  name: string;
  code?: string;
  address?: string;
  warehouse_type?: string;
}

export interface LocationUpdate {
  name?: string;
  code?: string;
  address?: string;
  warehouse_type?: string;
  is_active?: boolean;
}

export interface InventoryItem {
  id: number;
  product_id: number;
  location_id: number;
  quantity_on_hand: number;
  reserved_quantity: number;
  available_quantity: number;
  last_updated: string;
}

export interface Transaction {
  id: number;
  product_id: number;
  location_id: number;
  transaction_type: 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';
  quantity: number;
  reference_number?: string;
  notes?: string;
  user_id?: string;
  created_at: string;
}

export interface TransactionCreate {
  product_id: number;
  location_id: number;
  transaction_type: 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';
  quantity: number;
  reference_number?: string;
  notes?: string;
  user_id?: string;
}

export interface StockReceiptRequest {
  product_id: number;
  location_id: number;
  quantity: number;
  reference_number?: string;
  notes?: string;
  user_id?: string;
}

export interface StockShipmentRequest {
  product_id: number;
  location_id: number;
  quantity: number;
  reference_number?: string;
  notes?: string;
  user_id?: string;
}

export interface StockTransferRequest {
  product_id: number;
  from_location_id: number;
  to_location_id: number;
  quantity: number;
  reference_number?: string;
  notes?: string;
  user_id?: string;
}

export interface StockAdjustmentRequest {
  product_id: number;
  location_id: number;
  adjustment_quantity: number;
  reason: string;
  user_id?: string;
}

export interface SystemStats {
  products: {
    total: number;
    active: number;
  };
  transactions: {
    total: number;
  };
  suppliers: any;
  locations: any;
  system: {
    version: string;
    database_type: string;
    allow_negative_inventory: boolean;
  };
}

// API functions
export const api = {
  // Products
  products: {
    getAll: (): Promise<Product[]> => apiRequest('/products/'),
    getById: (id: number): Promise<Product> => apiRequest(`/products/${id}`),
    create: (product: ProductCreate): Promise<Product> => 
      apiRequest('/products', {
        method: 'POST',
        body: JSON.stringify(product),
      }),
    update: (id: number, product: ProductUpdate): Promise<Product> =>
      apiRequest(`/products/${id}`, {
        method: 'PUT',
        body: JSON.stringify(product),
      }),
    delete: (id: number): Promise<void> =>
      apiRequest(`/products/${id}`, {
        method: 'DELETE',
      }),
    deletePermanently: (id: number): Promise<void> =>
      apiRequest(`/products/${id}/permanent`, {
        method: 'DELETE',
      }),
  },

  // Suppliers
  suppliers: {
    getAll: (): Promise<Supplier[]> => apiRequest('/suppliers/'),
    getById: (id: number): Promise<Supplier> => apiRequest(`/suppliers/${id}`),
    create: (supplier: Partial<Supplier>): Promise<Supplier> =>
      apiRequest('/suppliers', {
        method: 'POST',
        body: JSON.stringify(supplier),
      }),
    update: (id: number, supplier: Partial<Supplier>): Promise<Supplier> =>
      apiRequest(`/suppliers/${id}`, {
        method: 'PUT',
        body: JSON.stringify(supplier),
      }),
    delete: (id: number): Promise<void> =>
      apiRequest(`/suppliers/${id}`, {
        method: 'DELETE',
      }),
    deletePermanently: (id: number): Promise<void> =>
      apiRequest(`/suppliers/${id}/permanent`, {
        method: 'DELETE',
      }),
  },

  // Locations
  locations: {
    getAll: (): Promise<Location[]> => apiRequest('/locations/'),
    getById: (id: number): Promise<Location> => apiRequest(`/locations/${id}`),
    create: (location: Partial<Location>): Promise<Location> =>
      apiRequest('/locations', {
        method: 'POST',
        body: JSON.stringify(location),
      }),
    update: (id: number, location: Partial<Location>): Promise<Location> =>
      apiRequest(`/locations/${id}`, {
        method: 'PUT',
        body: JSON.stringify(location),
      }),
    delete: (id: number): Promise<void> =>
      apiRequest(`/locations/${id}`, {
        method: 'DELETE',
      }),
    deletePermanently: (id: number): Promise<void> =>
      apiRequest(`/locations/${id}/permanent`, {
        method: 'DELETE',
      }),
  },

  // Inventory
  inventory: {
    getAll: (): Promise<InventoryItem[]> => apiRequest('/inventory/'),
    getByLocation: (locationId: number): Promise<InventoryItem[]> =>
      apiRequest(`/inventory/location/${locationId}`),
    update: (productId: number, locationId: number, update: Partial<InventoryItem>): Promise<InventoryItem> =>
      apiRequest(`/inventory/${productId}/${locationId}`, {
        method: 'PUT',
        body: JSON.stringify(update),
      }),
    getAlerts: (): Promise<InventoryItem[]> => apiRequest('/inventory/alerts'),
  },

  // Transactions
  transactions: {
    getAll: (): Promise<Transaction[]> => apiRequest('/transactions/'),
    getById: (id: number): Promise<Transaction> => apiRequest(`/transactions/${id}`),
    create: (transaction: TransactionCreate): Promise<Transaction> =>
      apiRequest('/transactions', {
        method: 'POST',
        body: JSON.stringify(transaction),
      }),
    createBatch: (transactions: TransactionCreate[]): Promise<Transaction[]> =>
      apiRequest('/transactions/batch', {
        method: 'POST',
        body: JSON.stringify(transactions),
      }),
    getSummary: (params?: {
      product_id?: number;
      location_id?: number;
      start_date?: string;
      end_date?: string;
    }): Promise<any> => {
      const searchParams = new URLSearchParams();
      if (params?.product_id) searchParams.append('product_id', params.product_id.toString());
      if (params?.location_id) searchParams.append('location_id', params.location_id.toString());
      if (params?.start_date) searchParams.append('start_date', params.start_date);
      if (params?.end_date) searchParams.append('end_date', params.end_date);
      return apiRequest(`/transactions/summary?${searchParams.toString()}`);
    },
    // Specialized transaction operations
    processReceipt: (data: StockReceiptRequest): Promise<Transaction> =>
      apiRequest(`/transactions/receipt?${new URLSearchParams({
        product_id: data.product_id.toString(),
        location_id: data.location_id.toString(),
        quantity: data.quantity.toString(),
        ...(data.reference_number && { reference_number: data.reference_number }),
        ...(data.notes && { notes: data.notes }),
        ...(data.user_id && { user_id: data.user_id }),
      }).toString()}`, {
        method: 'POST',
      }),
    processShipment: (data: StockShipmentRequest): Promise<Transaction> =>
      apiRequest(`/transactions/shipment?${new URLSearchParams({
        product_id: data.product_id.toString(),
        location_id: data.location_id.toString(),
        quantity: data.quantity.toString(),
        ...(data.reference_number && { reference_number: data.reference_number }),
        ...(data.notes && { notes: data.notes }),
        ...(data.user_id && { user_id: data.user_id }),
      }).toString()}`, {
        method: 'POST',
      }),
    processTransfer: (data: StockTransferRequest): Promise<Transaction[]> =>
      apiRequest(`/transactions/transfer?${new URLSearchParams({
        product_id: data.product_id.toString(),
        from_location_id: data.from_location_id.toString(),
        to_location_id: data.to_location_id.toString(),
        quantity: data.quantity.toString(),
        ...(data.reference_number && { reference_number: data.reference_number }),
        ...(data.notes && { notes: data.notes }),
        ...(data.user_id && { user_id: data.user_id }),
      }).toString()}`, {
        method: 'POST',
      }),
    processAdjustment: (data: StockAdjustmentRequest): Promise<Transaction> =>
      apiRequest(`/transactions/adjustment?${new URLSearchParams({
        product_id: data.product_id.toString(),
        location_id: data.location_id.toString(),
        adjustment_quantity: data.adjustment_quantity.toString(),
        reason: data.reason,
        ...(data.user_id && { user_id: data.user_id }),
      }).toString()}`, {
        method: 'POST',
      }),
    getProductHistory: (productId: number, limit: number = 100): Promise<Transaction[]> =>
      apiRequest(`/transactions/product/${productId}/history?limit=${limit}`),
    getLocationHistory: (locationId: number, limit: number = 100): Promise<Transaction[]> =>
      apiRequest(`/transactions/location/${locationId}/history?limit=${limit}`),
  },

  // System
  system: {
    getStats: (): Promise<SystemStats> => apiRequest('/stats/'),
    healthCheck: (): Promise<{ status: string; database: string; version: string }> =>
      apiRequest('/health'),
  },
};