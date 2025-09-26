import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Plus, Search, Loader2, AlertCircle, ArrowUp, ArrowDown, ArrowLeftRight, Settings, Calendar } from 'lucide-react';
import { useTransactions } from '../../hooks/api/useTransactions';
import { useProducts } from '../../hooks/api/useProducts';
import { useLocations } from '../../hooks/api/useLocations';
import TransactionForm from '../../components/forms/TransactionForm';
import type {
  TransactionCreate,
  StockReceiptRequest,
  StockShipmentRequest,
  StockTransferRequest,
  StockAdjustmentRequest
} from '../../services/api';

const Transactions: React.FC = () => {
  const {
    transactions,
    loading,
    error,
    refetch,
    processReceipt,
    processShipment,
    processTransfer,
    processAdjustment
  } = useTransactions();
  const { products } = useProducts();
  const { locations } = useLocations();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedLocation, setSelectedLocation] = useState<string>('');

  // Modal states
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);

  // Create lookup maps
  const productMap = new Map(products.map(p => [p.id, p]));
  const locationMap = new Map(locations.map(l => [l.id, l]));

  // Filter transactions
  const filteredTransactions = transactions.filter(transaction => {
    const product = productMap.get(transaction.product_id);
    const location = locationMap.get(transaction.location_id);
    
    const matchesSearch = !searchTerm || 
      product?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product?.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.reference_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.notes?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = !selectedType || transaction.transaction_type === selectedType;
    const matchesLocation = !selectedLocation || transaction.location_id.toString() === selectedLocation;
    
    return matchesSearch && matchesType && matchesLocation;
  });

  // Get transaction type icon and styling
  const getTransactionDisplay = (type: string) => {
    switch (type) {
      case 'IN':
        return {
          icon: ArrowDown,
          label: 'Stock In',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
        };
      case 'OUT':
        return {
          icon: ArrowUp,
          label: 'Stock Out',
          color: 'text-red-600',
          bgColor: 'bg-red-100',
        };
      case 'TRANSFER':
        return {
          icon: ArrowLeftRight,
          label: 'Transfer',
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
        };
      case 'ADJUSTMENT':
        return {
          icon: Settings,
          label: 'Adjustment',
          color: 'text-purple-600',
          bgColor: 'bg-purple-100',
        };
      default:
        return {
          icon: Settings,
          label: 'Unknown',
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
        };
    }
  };

  // Handle transaction submission with type-specific routing
  const handleTransactionSubmit = async (data: any, transactionType: string) => {
    setFormLoading(true);
    try {
      switch (transactionType) {
        case 'IN':
          await processReceipt(data as StockReceiptRequest);
          break;
        case 'OUT':
          await processShipment(data as StockShipmentRequest);
          break;
        case 'TRANSFER':
          await processTransfer(data as StockTransferRequest);
          break;
        case 'ADJUSTMENT':
          await processAdjustment(data as StockAdjustmentRequest);
          break;
        default:
          console.error('Unknown transaction type:', transactionType);
          return;
      }
      setShowTransactionForm(false);
      refetch();
    } catch (err) {
      console.error('Failed to process transaction:', err);
    } finally {
      setFormLoading(false);
    }
  };

  // Calculate stats
  const transactionStats = {
    total: transactions.length, // Note: This shows paginated count, not total DB count
    today: transactions.filter(t => 
      new Date(t.created_at).toDateString() === new Date().toDateString()
    ).length,
    thisWeek: transactions.filter(t => {
      const transactionDate = new Date(t.created_at);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return transactionDate >= weekAgo;
    }).length,
    byType: {
      IN: transactions.filter(t => t.transaction_type === 'IN').length,
      OUT: transactions.filter(t => t.transaction_type === 'OUT').length,
      TRANSFER: transactions.filter(t => t.transaction_type === 'TRANSFER').length,
      ADJUSTMENT: transactions.filter(t => t.transaction_type === 'ADJUSTMENT').length,
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading transactions...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Transactions</h1>
          <p className="text-muted-foreground">Track inventory movements and adjustments</p>
        </div>
        <Button onClick={() => setShowTransactionForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Transaction
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-full">
                <Calendar className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-muted-foreground">Total Transactions</p>
                <p className="text-2xl font-bold">{transactionStats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-full">
                <Calendar className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-muted-foreground">Today</p>
                <p className="text-2xl font-bold">{transactionStats.today}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-full">
                <Calendar className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-muted-foreground">This Week</p>
                <p className="text-2xl font-bold">{transactionStats.thisWeek}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">By Type</p>
              <div className="grid grid-cols-2 gap-1 text-xs">
                <div className="flex justify-between">
                  <span>In:</span>
                  <span className="font-medium text-green-600">{transactionStats.byType.IN}</span>
                </div>
                <div className="flex justify-between">
                  <span>Out:</span>
                  <span className="font-medium text-red-600">{transactionStats.byType.OUT}</span>
                </div>
                <div className="flex justify-between">
                  <span>Transfer:</span>
                  <span className="font-medium text-blue-600">{transactionStats.byType.TRANSFER}</span>
                </div>
                <div className="flex justify-between">
                  <span>Adj:</span>
                  <span className="font-medium text-purple-600">{transactionStats.byType.ADJUSTMENT}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder="Search by product, SKU, reference, or notes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All Types</option>
              <option value="IN">Stock In</option>
              <option value="OUT">Stock Out</option>
              <option value="TRANSFER">Transfer</option>
              <option value="ADJUSTMENT">Adjustment</option>
            </select>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
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

      {/* Transactions Table */}
      {filteredTransactions.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-muted-foreground">
              {searchTerm || selectedType || selectedLocation 
                ? 'No transactions found matching your filters.' 
                : 'No transactions available.'
              }
            </div>
            {!searchTerm && !selectedType && !selectedLocation && (
              <Button className="mt-4" onClick={() => setShowTransactionForm(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Transaction
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Transaction History ({filteredTransactions.length})</CardTitle>
            <CardDescription>
              Showing {filteredTransactions.length} of {transactions.length} transactions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-4 font-medium">Date</th>
                    <th className="text-left py-2 px-4 font-medium">Type</th>
                    <th className="text-left py-2 px-4 font-medium">Product</th>
                    <th className="text-left py-2 px-4 font-medium">Location</th>
                    <th className="text-left py-2 px-4 font-medium">Quantity</th>
                    <th className="text-left py-2 px-4 font-medium">Reference</th>
                    <th className="text-left py-2 px-4 font-medium">User</th>
                    <th className="text-left py-2 px-4 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTransactions.map((transaction) => {
                    const product = productMap.get(transaction.product_id);
                    const location = locationMap.get(transaction.location_id);
                    const typeDisplay = getTransactionDisplay(transaction.transaction_type);
                    const Icon = typeDisplay.icon;
                    
                    return (
                      <tr key={transaction.id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4 text-sm">
                          {new Date(transaction.created_at).toLocaleDateString()}
                          <div className="text-xs text-muted-foreground">
                            {new Date(transaction.created_at).toLocaleTimeString()}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center">
                            <div className={`p-1 rounded-full ${typeDisplay.bgColor} mr-2`}>
                              <Icon className={`w-3 h-3 ${typeDisplay.color}`} />
                            </div>
                            <span className="text-sm font-medium">{typeDisplay.label}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium text-sm">{product?.name || 'Unknown Product'}</div>
                            <div className="text-xs text-muted-foreground font-mono">{product?.sku}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {location?.name || 'Unknown Location'}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`font-medium ${
                            transaction.transaction_type === 'IN' ? 'text-green-600' :
                            transaction.transaction_type === 'OUT' ? 'text-red-600' :
                            'text-blue-600'
                          }`}>
                            {transaction.transaction_type === 'OUT' ? '-' : '+'}{transaction.quantity}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm font-mono">
                          {transaction.reference_number || '-'}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {transaction.user_id || '-'}
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground max-w-xs">
                          <div className="truncate" title={transaction.notes || ''}>
                            {transaction.notes || '-'}
                          </div>
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

      {/* Transaction Form Modal */}
      {showTransactionForm && (
        <TransactionForm
          title="New Transaction"
          onSubmit={handleTransactionSubmit}
          onCancel={() => setShowTransactionForm(false)}
          isLoading={formLoading}
        />
      )}
    </div>
  );
};

export default Transactions;