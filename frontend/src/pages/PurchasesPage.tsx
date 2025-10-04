import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import {
  CloudArrowDownIcon,
  ShieldCheckIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowLeftIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';

interface Purchase {
  id: string;
  dataset?: {
    id: string;
    title: string;
    description: string;
    price: string;
    file_size: number;
    category?: {
      name: string;
    };
  };
  amount: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  transaction_hash: string;
  created_at: string;
  updated_at: string;
  can_download: boolean;
  escrow?: {
    id: string;
    status: string;
    buyer_confirmed: boolean;
    seller_delivered: boolean;
  };
}

const PurchasesPage: React.FC = () => {
  const { user } = useAuth();
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    fetchPurchases();
  }, []);

  const fetchPurchases = async () => {
    try {
      setLoading(true);
      const response = await api.get('/marketplace/purchases/');
      console.log('Purchases API response:', response.data);
      
      let purchaseData: Purchase[] = [];
      
      if (response.data.success && Array.isArray(response.data.data)) {
        purchaseData = response.data.data;
        console.log('Using response.data.data:', purchaseData);
      } else if (Array.isArray(response.data.results)) {
        purchaseData = response.data.results;
        console.log('Using response.data.results:', purchaseData);
      } else if (Array.isArray(response.data)) {
        purchaseData = response.data;
        console.log('Using response.data directly:', purchaseData);
      } else {
        console.warn('Unexpected purchase data structure:', response.data);
        purchaseData = [];
      }
      
      // Log first purchase to see structure
      if (purchaseData.length > 0) {
        console.log('First purchase structure:', purchaseData[0]);
      }
      
      setPurchases(purchaseData);
    } catch (error) {
      console.error('Error fetching purchases:', error);
      toast.error('Failed to load purchase history');
      setPurchases([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      completed: 'bg-green-100 text-green-800 border-green-200',
      failed: 'bg-red-100 text-red-800 border-red-200',
      refunded: 'bg-gray-100 text-gray-800 border-gray-200',
    };
    return badges[status as keyof typeof badges] || badges.pending;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4" />;
      case 'failed':
        return <XCircleIcon className="h-4 w-4" />;
      case 'pending':
        return <ClockIcon className="h-4 w-4" />;
      case 'refunded':
        return <CurrencyDollarIcon className="h-4 w-4" />;
      default:
        return <ClockIcon className="h-4 w-4" />;
    }
  };

  const handleDownload = async (purchase: Purchase) => {
    if (!purchase.can_download) {
      toast.error('Download not available for this purchase');
      return;
    }

    if (!purchase.dataset?.id) {
      toast.error('Dataset information not available');
      return;
    }

    setDownloading(purchase.id);
    try {
      // Remove hyphens from UUID for backend compatibility
      const cleanId = purchase.dataset.id.replace(/-/g, '');
      const response = await api.get(`/datasets/datasets/${cleanId}/download/`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${purchase.dataset?.title || 'dataset'}.zip`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Download started successfully');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download dataset');
    } finally {
      setDownloading(null);
    }
  };

  const filteredPurchases = Array.isArray(purchases) ? purchases.filter(purchase => {
    if (filter === 'all') return true;
    return purchase.status === filter;
  }) : [];

  const formatCurrency = (amount: string) => {
    return parseFloat(amount).toFixed(2);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading purchase history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to="/dashboard"
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5 mr-2" />
                Back to Dashboard
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Purchase History</h1>
                <p className="text-gray-600 mt-1">
                  View and manage your dataset purchases
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'All Purchases', count: Array.isArray(purchases) ? purchases.length : 0 },
              { key: 'completed', label: 'Completed', count: Array.isArray(purchases) ? purchases.filter(p => p.status === 'completed').length : 0 },
              { key: 'pending', label: 'Pending', count: Array.isArray(purchases) ? purchases.filter(p => p.status === 'pending').length : 0 },
              { key: 'failed', label: 'Failed', count: Array.isArray(purchases) ? purchases.filter(p => p.status === 'failed').length : 0 },
              { key: 'refunded', label: 'Refunded', count: Array.isArray(purchases) ? purchases.filter(p => p.status === 'refunded').length : 0 },
            ].map(({ key, label, count }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === key
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                }`}
              >
                {label} ({count})
              </button>
            ))}
          </div>
        </div>

        {/* Purchase History */}
        {filteredPurchases.length > 0 ? (
          <div className="space-y-6">
            {filteredPurchases.map((purchase) => (
              <div key={purchase.id} className="card">
                <div className="card-body">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Header */}
                      <div className="flex items-center space-x-3 mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {purchase.dataset?.title || 'Dataset'}
                        </h3>
                        <span className={`inline-flex items-center px-3 py-1 text-sm rounded-full border ${getStatusBadge(purchase.status)}`}>
                          {getStatusIcon(purchase.status)}
                          <span className="ml-2 capitalize">{purchase.status}</span>
                        </span>
                        {purchase.escrow && (
                          <span className="inline-flex items-center px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                            <ShieldCheckIcon className="h-3 w-3 mr-1" />
                            Escrow Protected
                          </span>
                        )}
                      </div>

                      {/* Dataset Info */}
                      <div className="mb-4">
                        <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                          {purchase.dataset?.description || 'No description available'}
                        </p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>Category: {purchase.dataset?.category?.name || 'Unknown'}</span>
                          <span>Size: {formatFileSize(purchase.dataset?.file_size || 0)}</span>
                        </div>
                      </div>

                      {/* Purchase Details */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Amount Paid</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {formatCurrency(purchase.amount)} NCR
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">Purchase Date</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {new Date(purchase.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">Transaction</p>
                          <p className="text-sm font-mono text-gray-600 truncate">
                            {purchase.transaction_hash || 'N/A'}
                          </p>
                        </div>
                      </div>

                      {/* Escrow Status */}
                      {purchase.escrow && (
                        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4 text-sm">
                              <span className={`flex items-center ${purchase.escrow.seller_delivered ? 'text-green-600' : 'text-gray-500'}`}>
                                {purchase.escrow.seller_delivered ? 
                                  <CheckCircleIcon className="h-4 w-4 mr-1" /> : 
                                  <ClockIcon className="h-4 w-4 mr-1" />
                                }
                                Seller Delivered
                              </span>
                              <span className={`flex items-center ${purchase.escrow.buyer_confirmed ? 'text-green-600' : 'text-gray-500'}`}>
                                {purchase.escrow.buyer_confirmed ? 
                                  <CheckCircleIcon className="h-4 w-4 mr-1" /> : 
                                  <ClockIcon className="h-4 w-4 mr-1" />
                                }
                                Buyer Confirmed
                              </span>
                            </div>
                            <Link
                              to="/marketplace/escrows"
                              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                            >
                              Manage Escrow →
                            </Link>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col space-y-2 ml-6">
                      {purchase.dataset?.id && (
                        <Link
                          to={`/datasets/${purchase.dataset.id}`}
                          className="btn-outline btn-sm flex items-center"
                        >
                          <EyeIcon className="h-4 w-4 mr-2" />
                          View Dataset
                        </Link>
                      )}

                      {purchase.can_download && (
                        <button
                          onClick={() => handleDownload(purchase)}
                          disabled={downloading === purchase.id}
                          className="btn-primary btn-sm flex items-center"
                        >
                          {downloading === purchase.id ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Downloading...
                            </>
                          ) : (
                            <>
                              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                              Download
                            </>
                          )}
                        </button>
                      )}

                      {purchase.escrow && (
                        <Link
                          to="/marketplace/escrows"
                          className="btn-secondary btn-sm flex items-center"
                        >
                          <ShieldCheckIcon className="h-4 w-4 mr-2" />
                          Manage Escrow
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <CloudArrowDownIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {filter === 'all' ? 'No purchases yet' : `No ${filter} purchases`}
            </h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all' 
                ? 'You haven\'t purchased any datasets yet.'
                : `You don't have any ${filter} purchases.`
              }
            </p>
            <Link to="/datasets" className="btn-primary">
              Browse Datasets
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default PurchasesPage;
