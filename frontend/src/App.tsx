import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/dashboard/Dashboard';
import Products from './pages/products/Products';
import Inventory from './pages/inventory/Inventory';
import Suppliers from './pages/suppliers/Suppliers';
import Locations from './pages/locations/Locations';
import Transactions from './pages/transactions/Transactions';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/products" element={<Products />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/suppliers" element={<Suppliers />} />
        <Route path="/locations" element={<Locations />} />
        <Route path="/transactions" element={<Transactions />} />
      </Routes>
    </Layout>
  );
}

export default App;