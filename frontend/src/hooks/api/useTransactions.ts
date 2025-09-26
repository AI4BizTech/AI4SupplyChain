import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type {
  Transaction,
  TransactionCreate,
  StockReceiptRequest,
  StockShipmentRequest,
  StockTransferRequest,
  StockAdjustmentRequest
} from '../../services/api';

export function useTransactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.transactions.getAll();
      setTransactions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const createTransaction = async (transaction: TransactionCreate): Promise<Transaction | null> => {
    try {
      setError(null);
      const newTransaction = await api.transactions.create(transaction);
      setTransactions(prev => [newTransaction, ...prev]);
      return newTransaction;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create transaction');
      return null;
    }
  };

  const createBatchTransactions = async (transactions: TransactionCreate[]): Promise<Transaction[] | null> => {
    try {
      setError(null);
      const newTransactions = await api.transactions.createBatch(transactions);
      setTransactions(prev => [...newTransactions, ...prev]);
      return newTransactions;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create batch transactions');
      return null;
    }
  };

  // Specialized transaction operations
  const processReceipt = async (data: StockReceiptRequest): Promise<Transaction | null> => {
    try {
      setError(null);
      const newTransaction = await api.transactions.processReceipt(data);
      setTransactions(prev => [newTransaction, ...prev]);
      return newTransaction;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process stock receipt');
      return null;
    }
  };

  const processShipment = async (data: StockShipmentRequest): Promise<Transaction | null> => {
    try {
      setError(null);
      const newTransaction = await api.transactions.processShipment(data);
      setTransactions(prev => [newTransaction, ...prev]);
      return newTransaction;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process stock shipment');
      return null;
    }
  };

  const processTransfer = async (data: StockTransferRequest): Promise<Transaction[] | null> => {
    try {
      setError(null);
      const newTransactions = await api.transactions.processTransfer(data);
      setTransactions(prev => [...newTransactions, ...prev]);
      return newTransactions;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process stock transfer');
      return null;
    }
  };

  const processAdjustment = async (data: StockAdjustmentRequest): Promise<Transaction | null> => {
    try {
      setError(null);
      const newTransaction = await api.transactions.processAdjustment(data);
      setTransactions(prev => [newTransaction, ...prev]);
      return newTransaction;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process stock adjustment');
      return null;
    }
  };

  return {
    transactions,
    loading,
    error,
    refetch: fetchTransactions,
    createTransaction,
    createBatchTransactions,
    processReceipt,
    processShipment,
    processTransfer,
    processAdjustment,
  };
}