import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import EscrowCard from '../components/escrow/EscrowCard';
import {
  ChartBarIcon,
  DocumentIcon,
  CurrencyDollarIcon,
  StarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PlusIcon,
  EyeIcon,
  CloudArrowDownIcon,
  ShieldCheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  BanknotesIcon,
  HeartIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

interface UserStats {
  datasets_uploaded: number;
  datasets_purchased: number;
  total_earnings: string;
  total_spent: string;
  reputation_score: string;
  verification_status: string;
  wallet_connected: boolean;
  account_age_days: number;
  // Escrow-related stats
  active_escrows: number;
  completed_escrows: number;
  disputed_escrows: number;
  total_escrow_fees: string;
  escrow_success_rate: string;
}

interface RecentDataset {
  id: string;
  title: string;
  status: string;
  created_at: string;
  download_count: number;
  view_count: number;
  price: string;
}

interface PurchasedDataset {
  id: string;
  dataset: {
    id: string;
    title: string;
    price: string;
  };
  amount: string;
  status: string;
  created_at: string;
}

interface EscrowTransaction {
  id: string;
  purchase_id: string;
  dataset_id: string;
  dataset_title: string;
  amount: string;
  status: 'active' | 'completed' | 'disputed' | 'refunded' | 'cancelled' | 'auto_released';
  buyer_confirmed: boolean;
  seller_delivered: boolean;
  created_at: string;
  auto_release_time?: string;
  dispute_reason?: string;
  disputed_at?: string;
  validator?: string;
  resolution_notes?: string;
  resolved_at?: string;
  buyer_username: string;
  seller_username: string;
  escrow_fee: string;
  can_confirm: boolean;
  can_dispute: boolean;
  can_auto_release: boolean;
  is_buyer: boolean;
  is_seller: boolean;
}

interface FavoriteDataset {
  id: string;
  title: string;
  description: string;
  owner_name: string;
  category_name: string;
  price: string;
  is_free: boolean;
  rating_average: number;
  rating_count: number;
  download_count: number;
  created_at: string;
  review_stats?: {
    total_reviews: number;
    average_rating: number;
    verified_percentage: number;
  };
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [recentDatasets, setRecentDatasets] = useState<RecentDataset[]>([]);
  const [purchasedDatasets, setPurchasedDatasets] = useState<PurchasedDataset[]>([]);
  const [escrowTransactions, setEscrowTransactions] = useState<EscrowTransaction[]>([]);
  const [favoriteDatasets, setFavoriteDatasets] = useState<FavoriteDataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Refresh data when component becomes visible (user navigates back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchDashboardData();
      }
    };

    const handleFocus = () => {
      fetchDashboardData();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch user stats
      const statsResponse = await api.get('/auth/stats/');
      console.log('Stats response:', statsResponse.data);
      
      if (statsResponse.data.success) {
        setStats(statsResponse.data.data);
      } else {
        setStats(statsResponse.data);
      }

      // Fetch recent datasets (user's uploads) - backend already filters for user's datasets
      try {
        const datasetsResponse = await api.get('/datasets/datasets/?limit=5');
        console.log('Datasets response:', datasetsResponse.data);
        
        if (datasetsResponse.data.results) {
          setRecentDatasets(datasetsResponse.data.results);
        } else {
          setRecentDatasets([]);
        }
      } catch (datasetError) {
        console.error('Error fetching datasets:', datasetError);
        setRecentDatasets([]);
      }

      // Fetch purchased datasets
      try {
        const purchasesResponse = await api.get('/marketplace/purchases/?limit=5');
        console.log('Purchases response:', purchasesResponse.data);
        
        if (purchasesResponse.data.success && purchasesResponse.data.data) {
          setPurchasedDatasets(purchasesResponse.data.data.slice(0, 5));
        } else if (purchasesResponse.data.results) {
          setPurchasedDatasets(purchasesResponse.data.results.slice(0, 5));
        } else {
          setPurchasedDatasets([]);
        }
      } catch (purchaseError) {
        console.error('Error fetching purchases:', purchaseError);
        setPurchasedDatasets([]);
      }

      // Fetch escrow transactions
      try {
        const escrowResponse = await api.get('/marketplace/escrows/?limit=10');
        console.log('Escrow response:', escrowResponse.data);
        
        if (escrowResponse.data.success && escrowResponse.data.data && escrowResponse.data.data.escrows) {
          setEscrowTransactions(escrowResponse.data.data.escrows);
        } else if (escrowResponse.data.success && escrowResponse.data.data && Array.isArray(escrowResponse.data.data)) {
          setEscrowTransactions(escrowResponse.data.data);
        } else if (escrowResponse.data.results && Array.isArray(escrowResponse.data.results)) {
          setEscrowTransactions(escrowResponse.data.results);
        } else {
          setEscrowTransactions([]);
        }
      } catch (escrowError) {
        console.error('Error fetching escrow transactions:', escrowError);
        setEscrowTransactions([]);
      }

      // Fetch favorite datasets
      try {
        const favoritesResponse = await api.get('/datasets/datasets/favorites/');
        console.log('Favorites response:', favoritesResponse.data);
        console.log('Favorites response structure:', {
          success: favoritesResponse.data.success,
          data: favoritesResponse.data.data,
          dataType: typeof favoritesResponse.data.data,
          isArray: Array.isArray(favoritesResponse.data.data),
          length: favoritesResponse.data.data?.length
        });
        
        if (favoritesResponse.data.success && favoritesResponse.data.data) {
          setFavoriteDatasets(favoritesResponse.data.data.slice(0, 5));
        } else {
          console.log('No favorites found or invalid response structure');
          setFavoriteDatasets([]);
        }
      } catch (favoritesError) {
        console.error('Error fetching favorites:', favoritesError);
        setFavoriteDatasets([]);
      }
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getVerificationBadge = (status: string) => {
    const badges = {
      verified: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      unverified: 'bg-gray-100 text-gray-800',
    };
    return badges[status as keyof typeof badges] || badges.unverified;
  };

  const formatCurrency = (amount: string) => {
    return parseFloat(amount).toFixed(2);
  };

  const refreshFavorites = async () => {
    try {
      const favoritesResponse = await api.get('/datasets/datasets/favorites/');
      console.log('Refreshed favorites response:', favoritesResponse.data);
      
      if (favoritesResponse.data.success && favoritesResponse.data.data) {
        setFavoriteDatasets(favoritesResponse.data.data.slice(0, 5));
        toast.success('Favorites refreshed!');
      } else {
        setFavoriteDatasets([]);
      }
    } catch (error) {
      console.error('Error refreshing favorites:', error);
      toast.error('Failed to refresh favorites');
    }
  };

  const getEscrowStatusBadge = (status: string) => {
    const badges = {
      active: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      disputed: 'bg-red-100 text-red-800',
      refunded: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-gray-100 text-gray-800',
      auto_released: 'bg-purple-100 text-purple-800',
    };
    return badges[status as keyof typeof badges] || badges.active;
  };

  const getEscrowStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <ClockIcon className="h-4 w-4" />;
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4" />;
      case 'disputed':
        return <ExclamationTriangleIcon className="h-4 w-4" />;
      case 'refunded':
        return <XCircleIcon className="h-4 w-4" />;
      case 'auto_released':
        return <ShieldCheckIcon className="h-4 w-4" />;
      default:
        return <ClockIcon className="h-4 w-4" />;
    }
  };

  const handleConfirmReceipt = async (escrowId: string) => {
    try {
      await api.post(`/marketplace/escrows/${escrowId}/confirm-receipt/`);
      toast.success('Receipt confirmed successfully');
      fetchDashboardData(); // Refresh data
    } catch (error) {
      console.error('Error confirming receipt:', error);
      toast.error('Failed to confirm receipt');
    }
  };

  const handleDispute = async (escrowId: string, reason: string) => {
    try {
      await api.post(`/marketplace/escrows/${escrowId}/dispute/`, { reason });
      toast.success('Dispute submitted successfully');
      fetchDashboardData(); // Refresh data
    } catch (error) {
      console.error('Error submitting dispute:', error);
      toast.error('Failed to submit dispute');
    }
  };

  const handleAutoRelease = async (escrowId: string) => {
    try {
      await api.post(`/marketplace/escrows/${escrowId}/auto-release/`);
      toast.success('Payment auto-released successfully');
      fetchDashboardData(); // Refresh data
    } catch (error) {
      console.error('Error auto-releasing payment:', error);
      toast.error('Failed to auto-release payment');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        {/* Animated Background Elements */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" />
        </div>
        <div className="relative text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-2 border-cyan-400 border-t-transparent mx-auto mb-6"></div>
          <p className="text-white text-xl font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse" />
      </div>
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Enhanced Header */}
        <div className="mb-12">
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-8">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between">
              <div className="mb-6 lg:mb-0">
                <h1 className="text-4xl lg:text-5xl font-black bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-3">
                  Welcome back, {user?.username}! 👋
                </h1>
                <p className="text-gray-300 text-lg">
                  Here's what's happening with your datasets and marketplace activity
                </p>
              </div>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <span className={`px-4 py-2 rounded-full text-sm font-bold border ${
                  stats?.verification_status === 'verified' 
                    ? 'bg-green-500/20 text-green-300 border-green-400/30' :
                  stats?.verification_status === 'pending' 
                    ? 'bg-yellow-500/20 text-yellow-300 border-yellow-400/30' : 
                    'bg-red-500/20 text-red-300 border-red-400/30'
                }`}>
                  {stats?.verification_status === 'verified' ? '✓ Verified User' : 
                   stats?.verification_status === 'pending' ? '⏳ Verification Pending' : '❌ Unverified'}
                </span>
                <Link
                  to="/upload"
                  className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25 flex items-center space-x-2"
                >
                  <PlusIcon className="h-5 w-5" />
                  <span>Upload Dataset</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {/* Datasets Uploaded */}
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-400/30">
                  <DocumentIcon className="h-8 w-8 text-blue-400" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Datasets Uploaded</p>
                <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{stats?.datasets_uploaded || 0}</p>
              </div>
            </div>
          </div>

          {/* Datasets Purchased */}
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-green-500/20 rounded-xl border border-green-400/30">
                  <CloudArrowDownIcon className="h-8 w-8 text-green-400" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Datasets Purchased</p>
                <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{stats?.datasets_purchased || 0}</p>
              </div>
            </div>
          </div>

          {/* Total Earnings */}
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-emerald-500/20 rounded-xl border border-emerald-400/30">
                  <ArrowUpIcon className="h-8 w-8 text-emerald-400" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Earnings</p>
                <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{formatCurrency(stats?.total_earnings || '0')} <span className="text-lg text-cyan-400">NCR</span></p>
              </div>
            </div>
          </div>

          {/* Total Spent */}
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-red-500/20 rounded-xl border border-red-400/30">
                  <ArrowDownIcon className="h-8 w-8 text-red-400" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Spent</p>
                <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{formatCurrency(stats?.total_spent || '0')} <span className="text-lg text-cyan-400">NCR</span></p>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Escrow Stats Grid */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">🛡️ Escrow Protection</h2>
            <p className="text-gray-300">Secure transaction management and statistics</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Active Escrows */}
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-400/30">
                    <ShieldCheckIcon className="h-8 w-8 text-blue-400" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Active Escrows</p>
                  <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{stats?.active_escrows || 0}</p>
                </div>
              </div>
            </div>

            {/* Completed Escrows */}
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-3 bg-green-500/20 rounded-xl border border-green-400/30">
                    <CheckCircleIcon className="h-8 w-8 text-green-400" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Completed Escrows</p>
                  <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{stats?.completed_escrows || 0}</p>
                </div>
              </div>
            </div>

            {/* Disputed Escrows */}
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-3 bg-red-500/20 rounded-xl border border-red-400/30">
                    <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Disputed Escrows</p>
                  <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{stats?.disputed_escrows || 0}</p>
                </div>
              </div>
            </div>

            {/* Escrow Success Rate */}
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="p-3 bg-yellow-500/20 rounded-xl border border-yellow-400/30">
                    <StarIcon className="h-8 w-8 text-yellow-400" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Success Rate</p>
                  <p className="text-3xl font-black text-white group-hover:text-cyan-400 transition-colors">{parseFloat(stats?.escrow_success_rate || '0').toFixed(1)}<span className="text-lg text-yellow-400">%</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Enhanced Recent Datasets */}
          <div>
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
              <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-white flex items-center">
                    <DocumentIcon className="h-6 w-6 mr-2 text-cyan-400" />
                    📊 Your Recent Datasets
                  </h3>
                  <Link to="/datasets?owner=me" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition-colors">
                    View all →
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {recentDatasets.length > 0 ? (
                  <div className="space-y-4">
                    {recentDatasets.map((dataset) => (
                      <div key={dataset.id} className="bg-black/20 backdrop-blur-sm rounded-xl p-4 border border-gray-600/30 hover:border-cyan-400/50 transition-all duration-300">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex-1">
                            <h4 className="font-bold text-white text-lg mb-2">{dataset.title}</h4>
                            <div className="flex items-center space-x-3">
                              <span className={`px-3 py-1 text-xs font-medium rounded-full border ${
                                dataset.status === 'approved' ? 'bg-green-500/20 text-green-300 border-green-400/30' :
                                dataset.status === 'pending' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-400/30' :
                                'bg-red-500/20 text-red-300 border-red-400/30'
                              }`}>
                                {dataset.status === 'approved' ? '✅ Approved' : 
                                 dataset.status === 'pending' ? '⏳ Pending' : '❌ Rejected'}
                              </span>
                              <span className="text-sm text-gray-400">
                                {new Date(dataset.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4 text-sm">
                            <div className="flex items-center space-x-1 text-gray-300">
                              <EyeIcon className="h-4 w-4 text-blue-400" />
                              <span>{dataset.view_count}</span>
                            </div>
                            <div className="flex items-center space-x-1 text-gray-300">
                              <CloudArrowDownIcon className="h-4 w-4 text-green-400" />
                              <span>{dataset.download_count}</span>
                            </div>
                            <div className="font-bold text-cyan-400">
                              {parseFloat(dataset.price) > 0 ? `${formatCurrency(dataset.price)} NCR` : 'Free'}
                            </div>
                          </div>
                          
                          <Link
                            to={`/datasets/${dataset.id}`}
                            className="bg-gradient-to-r from-cyan-500/20 to-purple-600/20 text-cyan-300 px-4 py-2 rounded-lg font-medium hover:from-cyan-500/30 hover:to-purple-600/30 transition-all duration-300 border border-cyan-400/30"
                          >
                            View Details →
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <DocumentIcon className="h-16 w-16 text-purple-400 mx-auto mb-6" />
                    <h3 className="text-xl font-bold text-white mb-4">No datasets yet</h3>
                    <p className="text-gray-300 mb-6">Start sharing your data with the community</p>
                    <Link to="/upload" className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25">
                      Upload Your First Dataset
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enhanced Recent Purchases */}
          <div>
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
              <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-white flex items-center">
                    <CloudArrowDownIcon className="h-6 w-6 mr-2 text-cyan-400" />
                    🛒 Recent Purchases
                  </h3>
                  <Link to="/marketplace/purchases" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition-colors">
                    View all →
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {purchasedDatasets.length > 0 ? (
                  <div className="space-y-4">
                    {purchasedDatasets.map((purchase) => (
                      <div key={purchase.id} className="bg-black/20 backdrop-blur-sm rounded-xl p-4 border border-gray-600/30 hover:border-cyan-400/50 transition-all duration-300">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="font-bold text-white text-lg mb-2">{purchase.dataset?.title || 'Dataset'}</h4>
                            <div className="flex items-center space-x-3">
                              <span className={`px-3 py-1 text-xs font-medium rounded-full border ${
                                purchase.status === 'completed' ? 'bg-green-500/20 text-green-300 border-green-400/30' :
                                purchase.status === 'pending' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-400/30' :
                                'bg-red-500/20 text-red-300 border-red-400/30'
                              }`}>
                                {purchase.status === 'completed' ? '✅ Completed' : 
                                 purchase.status === 'pending' ? '⏳ Pending' : '❌ Failed'}
                              </span>
                              <span className="text-sm text-gray-400">
                                {new Date(purchase.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-black text-2xl text-cyan-400 mb-1">
                              {formatCurrency(purchase.amount)} <span className="text-lg">NCR</span>
                            </div>
                            <div className="text-xs text-gray-400">Purchase Amount</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <CloudArrowDownIcon className="h-16 w-16 text-purple-400 mx-auto mb-6" />
                    <h3 className="text-xl font-bold text-white mb-4">No purchases yet</h3>
                    <p className="text-gray-300 mb-6">Discover amazing datasets from the community</p>
                    <Link to="/datasets" className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25">
                      Browse Datasets
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Favorite Datasets */}
        <div className="mb-12">
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
            <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <HeartIcon className="h-6 w-6 mr-2 text-red-400" />
                  ❤️ Your Favorite Datasets
                </h3>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={refreshFavorites}
                    className="text-gray-400 hover:text-cyan-400 p-2 rounded-lg hover:bg-black/20 transition-all duration-300"
                    title="Refresh favorites"
                  >
                    <ArrowPathIcon className="h-5 w-5" />
                  </button>
                  <Link to="/datasets?favorites=true" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition-colors">
                    View all →
                  </Link>
                </div>
              </div>
            </div>
            <div className="p-6">
              {favoriteDatasets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {favoriteDatasets.map((dataset) => (
                    <Link
                      key={dataset.id}
                      to={`/datasets/${dataset.id}`}
                      className="block bg-black/20 backdrop-blur-sm rounded-xl p-4 border border-gray-600/30 hover:border-cyan-400/50 transition-all duration-300 group"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="font-bold text-white text-lg line-clamp-2 group-hover:text-cyan-400 transition-colors">{dataset.title}</h4>
                        <HeartIcon className="h-5 w-5 text-red-400 fill-current flex-shrink-0 ml-2" />
                      </div>
                      
                      <p className="text-sm text-gray-300 line-clamp-2 mb-4">{dataset.description}</p>
                      
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          {Array.from({ length: 5 }, (_, i) => (
                            <StarIcon
                              key={i}
                              className={`h-4 w-4 ${
                                i < Math.floor(dataset.review_stats?.average_rating || dataset.rating_average)
                                  ? 'text-yellow-400 fill-current'
                                  : 'text-gray-600'
                              }`}
                            />
                          ))}
                          <span className="ml-2 text-xs text-gray-400">
                            ({dataset.review_stats?.total_reviews || dataset.rating_count})
                          </span>
                        </div>
                        
                        <div className="font-bold text-cyan-400">
                          {dataset.is_free ? 'Free' : `${formatCurrency(dataset.price)} NCR`}
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>by {dataset.owner_name}</span>
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full border border-purple-400/30">
                          {dataset.category_name}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16">
                  <HeartIcon className="h-20 w-20 text-red-400 mx-auto mb-6" />
                  <h3 className="text-2xl font-bold text-white mb-4">No favorites yet</h3>
                  <p className="text-gray-300 mb-2">
                    Browse datasets and click the heart icon to add them to your favorites
                  </p>
                  <p className="text-sm text-gray-400 mb-8">
                    Build your personal collection of amazing datasets
                  </p>
                  <Link to="/datasets" className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25">
                    Browse Datasets
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Disputed Escrows - Seller Attention Required */}
        {Array.isArray(escrowTransactions) && escrowTransactions.filter(escrow => escrow.status === 'disputed' && escrow.is_seller).length > 0 && (
          <div className="mb-8">
            <div className="card border-red-200">
              <div className="card-header bg-red-50">
                <h3 className="text-lg font-semibold text-red-900 flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                  🚨 Disputed Transactions - Your Attention Required
                </h3>
                <span className="text-sm text-red-700">
                  {Array.isArray(escrowTransactions) ? escrowTransactions.filter(escrow => escrow.status === 'disputed' && escrow.is_seller).length : 0} dispute(s) on your datasets
                </span>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  {Array.isArray(escrowTransactions) && escrowTransactions
                    .filter(escrow => escrow.status === 'disputed' && escrow.is_seller)
                    .map((escrow) => (
                      <div key={escrow.id} className="border border-red-200 rounded-lg p-4 bg-red-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-red-900 mb-2">{escrow.dataset_title}</h4>
                            <div className="text-sm text-red-800 space-y-1">
                              <p><strong>Disputed by:</strong> {escrow.buyer_username}</p>
                              <p><strong>Reason:</strong> {escrow.dispute_reason}</p>
                              {escrow.disputed_at && (
                                <p><strong>Date:</strong> {new Date(escrow.disputed_at).toLocaleDateString()}</p>
                              )}
                              {escrow.validator && (
                                <p><strong>Validator:</strong> {escrow.validator}</p>
                              )}
                              {escrow.resolution_notes && (
                                <div className="mt-2 p-2 bg-white rounded border">
                                  <p><strong>Resolution:</strong> {escrow.resolution_notes}</p>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="ml-4">
                            <Link
                              to={`/datasets/${escrow.dataset_id}`}
                              className="btn-outline btn-sm text-red-700 border-red-300 hover:bg-red-100"
                            >
                              View Dataset
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Active Escrow Transactions */}
        <div className="mb-12">
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
            <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <ShieldCheckIcon className="h-6 w-6 mr-2 text-cyan-400" />
                  🛡️ Active Escrow Transactions
                </h3>
                <div className="flex items-center space-x-4">
                  <Link to="/test-escrow" className="text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors">
                    Test Escrow →
                  </Link>
                  <Link to="/marketplace/escrows" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition-colors">
                    View all →
                  </Link>
                </div>
              </div>
            </div>
            <div className="p-6">
              {Array.isArray(escrowTransactions) && escrowTransactions.length > 0 ? (
                <div className="space-y-6">
                  {escrowTransactions.map((escrow) => (
                    <div key={escrow.id} className="bg-black/20 backdrop-blur-sm rounded-xl border border-gray-600/30 hover:border-cyan-400/50 transition-all duration-300">
                      <EscrowCard
                        escrow={escrow}
                        onConfirmReceipt={handleConfirmReceipt}
                        onDispute={(escrow) => {
                          // For dashboard, we'll redirect to the full escrow page for disputes
                          navigate('/marketplace/escrows');
                        }}
                        onAutoRelease={handleAutoRelease}
                        compact={true}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16">
                  <ShieldCheckIcon className="h-20 w-20 text-cyan-400 mx-auto mb-6" />
                  <h3 className="text-2xl font-bold text-white mb-4">No active escrow transactions</h3>
                  <p className="text-gray-300 mb-6">Your secure transactions will appear here</p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link to="/datasets" className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25">
                      Browse Datasets
                    </Link>
                    <Link to="/test-escrow" className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-purple-300 px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 border border-purple-400/30">
                      Test Escrow System
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Enhanced Profile Summary & Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          <div className="lg:col-span-2">
            {/* Quick Actions */}
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
              <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <BanknotesIcon className="h-6 w-6 mr-2 text-cyan-400" />
                  ⚡ Quick Actions
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Link
                    to="/upload"
                    className="bg-gradient-to-r from-cyan-500/20 to-purple-600/20 text-white p-4 rounded-xl border border-cyan-400/30 hover:border-cyan-400/50 transition-all duration-300 text-center group"
                  >
                    <PlusIcon className="h-8 w-8 text-cyan-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                    <div className="font-bold text-sm">Upload Dataset</div>
                  </Link>
                  
                  <Link
                    to="/datasets"
                    className="bg-gradient-to-r from-purple-500/20 to-pink-600/20 text-white p-4 rounded-xl border border-purple-400/30 hover:border-purple-400/50 transition-all duration-300 text-center group"
                  >
                    <DocumentIcon className="h-8 w-8 text-purple-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                    <div className="font-bold text-sm">Browse Datasets</div>
                  </Link>
                  
                  <Link
                    to="/marketplace/escrows"
                    className="bg-gradient-to-r from-emerald-500/20 to-teal-600/20 text-white p-4 rounded-xl border border-emerald-400/30 hover:border-emerald-400/50 transition-all duration-300 text-center group"
                  >
                    <ShieldCheckIcon className="h-8 w-8 text-emerald-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                    <div className="font-bold text-sm">Manage Escrows</div>
                  </Link>
                  
                  <Link
                    to="/test-escrow"
                    className="bg-gradient-to-r from-yellow-500/20 to-orange-600/20 text-white p-4 rounded-xl border border-yellow-400/30 hover:border-yellow-400/50 transition-all duration-300 text-center group"
                  >
                    <ChartBarIcon className="h-8 w-8 text-yellow-400 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                    <div className="font-bold text-sm">Test Escrow</div>
                  </Link>
                </div>
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            {/* Enhanced Profile Card */}
            <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
              <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-white flex items-center">
                    <StarIcon className="h-6 w-6 mr-2 text-yellow-400" />
                    👤 Profile Summary
                  </h3>
                  <Link to="/profile" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition-colors">
                    Edit →
                  </Link>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-2xl font-black text-white">{user?.username?.charAt(0).toUpperCase()}</span>
                    </div>
                    <h4 className="font-bold text-white text-lg">{user?.username}</h4>
                    <p className="text-gray-400 text-sm">{user?.email}</p>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                      <p className="text-sm font-medium text-gray-400 mb-2">Reputation Score</p>
                      <div className="flex items-center">
                        <StarIcon className="h-6 w-6 text-yellow-400 fill-current mr-2" />
                        <span className="text-2xl font-black text-white">
                          {parseFloat(stats?.reputation_score || '0').toFixed(1)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                      <p className="text-sm font-medium text-gray-400 mb-2">Account Age</p>
                      <p className="text-2xl font-black text-white">
                        {stats?.account_age_days || 0} <span className="text-lg text-cyan-400">days</span>
                      </p>
                    </div>

                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                      <p className="text-sm font-medium text-gray-400 mb-2">Wallet Status</p>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                        stats?.wallet_connected 
                          ? 'bg-green-500/20 text-green-300 border-green-400/30' 
                          : 'bg-red-500/20 text-red-300 border-red-400/30'
                      }`}>
                        {stats?.wallet_connected ? '✓ Connected' : '❌ Not Connected'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
