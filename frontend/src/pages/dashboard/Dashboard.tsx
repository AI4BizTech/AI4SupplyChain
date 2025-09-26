import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import {
  Package,
  AlertTriangle,
  Activity,
  Loader2,
  Users,
  MapPin,
  Plus,
  TrendingUp,
  BarChart,
  Clock,
  ArrowDown,
  ArrowUp,
  ArrowLeftRight,
  Settings
} from 'lucide-react';
import { useSystemStats } from '../../hooks/api/useSystemStats';
import { useTransactions } from '../../hooks/api/useTransactions';
import { useSuppliers } from '../../hooks/api/useSuppliers';
import { useLocations } from '../../hooks/api/useLocations';
import { useInventory } from '../../hooks/api/useInventory';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { stats, loading, error } = useSystemStats();
  const { transactions } = useTransactions();
  const { suppliers } = useSuppliers();
  const { locations } = useLocations();
  const { inventory } = useInventory();

  // Calculate additional stats
  const lowStockItems = inventory.filter(item =>
    item.available_quantity <= 10 // Simple threshold for demo
  ).length;

  const activeSuppliers = suppliers.filter(s => s.is_active).length;
  const activeLocations = locations.filter(l => l.is_active).length;

  // Get recent transactions (last 5)
  const recentTransactions = transactions
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  // Get transaction type display
  const getTransactionDisplay = (type: string) => {
    switch (type) {
      case 'IN':
        return { icon: ArrowDown, label: 'Stock In', color: 'text-green-600' };
      case 'OUT':
        return { icon: ArrowUp, label: 'Stock Out', color: 'text-red-600' };
      case 'TRANSFER':
        return { icon: ArrowLeftRight, label: 'Transfer', color: 'text-blue-600' };
      case 'ADJUSTMENT':
        return { icon: Settings, label: 'Adjustment', color: 'text-purple-600' };
      default:
        return { icon: Activity, label: 'Unknown', color: 'text-gray-600' };
    }
  };

  const StatCard = ({ 
    icon: Icon, 
    title, 
    value, 
    iconColor, 
    bgColor 
  }: {
    icon: React.ElementType;
    title: string;
    value: string | number;
    iconColor: string;
    bgColor: string;
  }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center">
          <div className={`p-2 ${bgColor} rounded-full`}>
            <Icon className={`w-6 h-6 ${iconColor}`} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">
              {loading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : error ? (
                "Error"
              ) : (
                value
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      {error && (
        <Card className="mb-6 border-destructive">
          <CardContent className="p-4">
            <p className="text-destructive">Failed to load dashboard data: {error}</p>
          </CardContent>
        </Card>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={Package}
          title="Total Products"
          value={stats?.products?.total || 0}
          iconColor="text-blue-600"
          bgColor="bg-blue-100"
        />

        <StatCard
          icon={Users}
          title="Active Suppliers"
          value={activeSuppliers}
          iconColor="text-purple-600"
          bgColor="bg-purple-100"
        />

        <StatCard
          icon={MapPin}
          title="Active Locations"
          value={activeLocations}
          iconColor="text-green-600"
          bgColor="bg-green-100"
        />

        <StatCard
          icon={AlertTriangle}
          title="Low Stock Items"
          value={lowStockItems}
          iconColor="text-yellow-600"
          bgColor="bg-yellow-100"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={Activity}
          title="Total Transactions"
          value={transactions.length}
          iconColor="text-red-600"
          bgColor="bg-red-100"
        />

        <StatCard
          icon={TrendingUp}
          title="This Week"
          value={transactions.filter(t => {
            const transactionDate = new Date(t.created_at);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return transactionDate >= weekAgo;
          }).length}
          iconColor="text-indigo-600"
          bgColor="bg-indigo-100"
        />

        <StatCard
          icon={BarChart}
          title="Reports"
          value="Coming Soon"
          iconColor="text-gray-600"
          bgColor="bg-gray-100"
        />

        <StatCard
          icon={Clock}
          title="Forecasting"
          value="Coming Soon"
          iconColor="text-gray-600"
          bgColor="bg-gray-100"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest inventory movements and updates</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/transactions')}>
              View All
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentTransactions.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  No recent activity to display
                </div>
              ) : (
                recentTransactions.map((transaction) => {
                  const typeDisplay = getTransactionDisplay(transaction.transaction_type);
                  const Icon = typeDisplay.icon;

                  return (
                    <div key={transaction.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center">
                        <div className="p-2 bg-background rounded-full mr-3">
                          <Icon className={`w-4 h-4 ${typeDisplay.color}`} />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{typeDisplay.label}</p>
                          <p className="text-xs text-muted-foreground">
                            Quantity: {transaction.quantity} • {new Date(transaction.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">
                          {transaction.reference_number || 'No ref'}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button
                className="w-full"
                variant="default"
                onClick={() => navigate('/products')}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add New Product
              </Button>
              <Button
                className="w-full"
                variant="secondary"
                onClick={() => navigate('/transactions')}
              >
                <Activity className="w-4 h-4 mr-2" />
                Record Transaction
              </Button>
              <Button
                className="w-full"
                variant="outline"
                onClick={() => navigate('/suppliers')}
              >
                <Users className="w-4 h-4 mr-2" />
                Add Supplier
              </Button>
              <Button
                className="w-full"
                variant="outline"
                onClick={() => navigate('/locations')}
              >
                <MapPin className="w-4 h-4 mr-2" />
                Manage Locations
              </Button>
              <Button
                className="w-full"
                variant="ghost"
                disabled
              >
                <BarChart className="w-4 h-4 mr-2" />
                View Reports (Coming Soon)
              </Button>
              <Button
                className="w-full"
                variant="ghost"
                disabled
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                AI Assistant (Coming Soon)
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Low Stock Alerts */}
      {lowStockItems > 0 && (
        <Card className="mt-6 border-yellow-200 bg-yellow-50">
          <CardHeader>
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
              <CardTitle className="text-yellow-800">Low Stock Alert</CardTitle>
            </div>
            <CardDescription className="text-yellow-700">
              {lowStockItems} items are running low on stock
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-center">
              <p className="text-sm text-yellow-700">
                Items with 10 or fewer units available need attention
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/inventory')}
                className="border-yellow-300 text-yellow-700 hover:bg-yellow-100"
              >
                View Inventory
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Info */}
      {stats && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Version</p>
                <p className="font-medium">{stats.system.version}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Database</p>
                <p className="font-medium">{stats.system.database_type}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Negative Inventory</p>
                <p className="font-medium">{stats.system.allow_negative_inventory ? 'Allowed' : 'Not Allowed'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p className="font-medium text-green-600">Online</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;