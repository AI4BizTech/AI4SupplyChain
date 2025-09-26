import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Plus, Search, Loader2, AlertCircle, Edit, Trash2, Eye, Power, MoreVertical } from 'lucide-react';
import { useProducts } from '../../hooks/api/useProducts';
import ProductForm from '../../components/forms/ProductForm';
import DeleteConfirmDialog from '../../components/ui/DeleteConfirmDialog';
import type { Product, ProductCreate, ProductUpdate } from '../../services/api';

const Products: React.FC = () => {
  const { products, loading, error, refetch, createProduct, updateProduct, deleteProduct, deleteProductPermanently } = useProducts();
  const [searchTerm, setSearchTerm] = useState('');

  // Modal states
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [inactivatingProduct, setInactivatingProduct] = useState<Product | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setOpenDropdown(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // Filter products based on search term
  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  // CRUD handlers
  const handleAddProduct = async (data: ProductCreate) => {
    setFormLoading(true);
    try {
      await createProduct(data);
      setShowAddForm(false);
      refetch();
    } catch (err) {
      console.error('Failed to add product:', err);
    } finally {
      setFormLoading(false);
    }
  };

  const handleEditProduct = async (data: ProductUpdate) => {
    if (!editingProduct) return;

    setFormLoading(true);
    try {
      await updateProduct(editingProduct.id, data);
      setEditingProduct(null);
      refetch();
    } catch (err) {
      console.error('Failed to update product:', err);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!deletingProduct) return;

    setFormLoading(true);
    setDeleteError(null);
    try {
      const success = await deleteProductPermanently(deletingProduct.id);
      if (success) {
        setDeletingProduct(null);
        refetch();
      }
    } catch (err) {
      console.error('Failed to permanently delete product:', err);
      setDeleteError(err instanceof Error ? err.message : 'Failed to permanently delete product');
    } finally {
      setFormLoading(false);
    }
  };

  const handleInactivateProduct = async () => {
    if (!inactivatingProduct) return;

    setFormLoading(true);
    try {
      if (inactivatingProduct.is_active) {
        // Deactivating - use the soft delete endpoint
        await deleteProduct(inactivatingProduct.id);
      } else {
        // Activating - use the update endpoint
        await updateProduct(inactivatingProduct.id, { is_active: true });
      }
      setInactivatingProduct(null);
      refetch();
    } catch (err) {
      console.error('Failed to update product status:', err);
    } finally {
      setFormLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading products...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Products</h1>
          <p className="text-muted-foreground">Manage your product catalog</p>
        </div>
        <Button onClick={() => setShowAddForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Product
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

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder="Search products by name, SKU, or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Products Grid */}
      {filteredProducts.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-muted-foreground">
              {searchTerm ? 'No products found matching your search.' : 'No products available.'}
            </div>
            {!searchTerm && (
              <Button className="mt-4" onClick={() => setShowAddForm(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Product
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {/* Products Table */}
          <Card>
            <CardHeader>
              <CardTitle>Products ({filteredProducts.length})</CardTitle>
              <CardDescription>
                Showing {filteredProducts.length} of {products.length} products
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4 font-medium">SKU</th>
                      <th className="text-left py-2 px-4 font-medium">Name</th>
                      <th className="text-left py-2 px-4 font-medium">Category</th>
                      <th className="text-left py-2 px-4 font-medium">Cost</th>
                      <th className="text-left py-2 px-4 font-medium">Price</th>
                      <th className="text-left py-2 px-4 font-medium">Stock</th>
                      <th className="text-left py-2 px-4 font-medium">Status</th>
                      <th className="text-left py-2 px-4 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredProducts.map((product) => (
                      <tr key={product.id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4 font-mono text-sm">{product.sku}</td>
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium">{product.name}</div>
                            {product.description && (
                              <div className="text-sm text-muted-foreground truncate max-w-xs">
                                {product.description}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {product.category || '-'}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {formatCurrency(product.unit_cost)}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {product.unit_price ? formatCurrency(product.unit_price) : '-'}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          <div className="text-sm">
                            <div>Reorder: {product.reorder_point}</div>
                            <div className="text-muted-foreground">Qty: {product.reorder_quantity}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              product.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {product.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingProduct(product)}
                              title="Edit product"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <div className="relative">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdown(openDropdown === product.id ? null : product.id);
                                }}
                                title="More actions"
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                              {openDropdown === product.id && (
                                <div
                                  className="absolute right-0 top-8 bg-background border border-border rounded-md shadow-lg z-10 min-w-48"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <div className="py-1">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setInactivatingProduct(product);
                                        setOpenDropdown(null);
                                      }}
                                      className="flex items-center w-full px-3 py-2 text-sm hover:bg-muted"
                                    >
                                      <Power className="w-4 h-4 mr-2" />
                                      {product.is_active ? 'Deactivate' : 'Activate'}
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setDeletingProduct(product);
                                        setOpenDropdown(null);
                                      }}
                                      className="flex items-center w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                                    >
                                      <Trash2 className="w-4 h-4 mr-2" />
                                      Delete Permanently
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Product Modal */}
      {showAddForm && (
        <ProductForm
          title="Add New Product"
          onSubmit={handleAddProduct}
          onCancel={() => setShowAddForm(false)}
          isLoading={formLoading}
        />
      )}

      {/* Edit Product Modal */}
      {editingProduct && (
        <ProductForm
          title="Edit Product"
          product={editingProduct}
          onSubmit={handleEditProduct}
          onCancel={() => setEditingProduct(null)}
          isLoading={formLoading}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {deletingProduct && (
        <DeleteConfirmDialog
          isOpen={true}
          onClose={() => {
            setDeletingProduct(null);
            setDeleteError(null);
          }}
          onConfirm={handleDeleteProduct}
          title="Delete Product Permanently"
          description="Are you sure you want to permanently delete"
          itemName={deletingProduct.name}
          isLoading={formLoading}
          errorMessage={deleteError}
        />
      )}

      {/* Inactivate Confirmation Dialog */}
      {inactivatingProduct && (
        <DeleteConfirmDialog
          isOpen={true}
          onClose={() => setInactivatingProduct(null)}
          onConfirm={handleInactivateProduct}
          title={`${inactivatingProduct.is_active ? 'Deactivate' : 'Activate'} Product`}
          description={`Are you sure you want to ${inactivatingProduct.is_active ? 'deactivate' : 'activate'}`}
          itemName={inactivatingProduct.name}
          isLoading={formLoading}
          confirmText={inactivatingProduct.is_active ? 'Deactivate' : 'Activate'}
          isDestructive={false}
        />
      )}
    </div>
  );
};

export default Products;