import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import {
  ShieldCheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  BanknotesIcon,
  ArrowLeftIcon,
  EyeIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

interface EscrowTransaction {
  id: string;
  purchase_id: string;
  dataset_title: string;
  dataset_id: string;
  amount: string;
  status: 'active' | 'completed' | 'disputed' | 'refunded' | 'cancelled' | 'auto_released';
  buyer_confirmed: boolean;
  seller_delivered: boolean;
  created_at: string;
  updated_at: string;
  auto_release_time: string;
  dispute_reason?: string;
  escrow_fee: string;
  can_confirm: boolean;
  can_dispute: boolean;
  can_auto_release: boolean;
  buyer: {
    id: string;
    username: string;
    email: string;
  };
  seller: {
    id: string;
    username: string;
    email: string;
  };
}

const EscrowPage: React.FC = () => {
  const { user } = useAuth();
  const [escrows, setEscrows] = useState<EscrowTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [selectedEscrow, setSelectedEscrow] = useState<EscrowTransaction | null>(null);
  const [showDisputeModal, setShowDisputeModal] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'confirm' | 'auto-release';
    escrowId: string;
    title: string;
    message: string;
  } | null>(null);

  useEffect(() => {
    fetchEscrows();
  }, []);

  const fetchEscrows = async () => {
    try {
      setLoading(true);
      const response = await api.get('/marketplace/escrows/');
      console.log('Escrow API response:', response.data);
      
      let escrowData: EscrowTransaction[] = [];
      
      if (response.data.success && Array.isArray(response.data.data)) {
        escrowData = response.data.data;
      } else if (Array.isArray(response.data.results)) {
        escrowData = response.data.results;
      } else if (Array.isArray(response.data)) {
        escrowData = response.data;
      } else {
        console.warn('Unexpected escrow data structure:', response.data);
        escrowData = [];
      }
      
      setEscrows(escrowData);
    } catch (error) {
      console.error('Error fetching escrows:', error);
      toast.error('Failed to load escrow transactions');
      setEscrows([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      active: 'bg-blue-500/20 text-blue-300 border-blue-400/30',
      completed: 'bg-green-500/20 text-green-300 border-green-400/30',
      disputed: 'bg-red-500/20 text-red-300 border-red-400/30',
      refunded: 'bg-yellow-500/20 text-yellow-300 border-yellow-400/30',
      cancelled: 'bg-gray-500/20 text-gray-300 border-gray-400/30',
      auto_released: 'bg-purple-500/20 text-purple-300 border-purple-400/30',
    };
    return badges[status as keyof typeof badges] || badges.active;
  };

  const getStatusIcon = (status: string) => {
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
    setConfirmAction({
      type: 'confirm',
      escrowId,
      title: 'Confirm Receipt',
      message: 'Are you sure you want to confirm receipt of this dataset? This action cannot be undone and will release the payment to the seller.'
    });
    setShowConfirmModal(true);
  };

  const executeConfirmReceipt = async (escrowId: string) => {
    try {
      await api.post(`/marketplace/escrows/${escrowId}/confirm-receipt/`);
      toast.success('Receipt confirmed successfully');
      fetchEscrows();
    } catch (error) {
      console.error('Error confirming receipt:', error);
      toast.error('Failed to confirm receipt');
    }
  };

  const handleDispute = async () => {
    if (!selectedEscrow || !disputeReason.trim()) {
      toast.error('Please provide a reason for the dispute');
      return;
    }

    try {
      await api.post(`/marketplace/escrows/${selectedEscrow.id}/dispute/`, { 
        reason: disputeReason 
      });
      toast.success('Dispute submitted successfully');
      setShowDisputeModal(false);
      setDisputeReason('');
      setSelectedEscrow(null);
      fetchEscrows();
    } catch (error) {
      console.error('Error submitting dispute:', error);
      toast.error('Failed to submit dispute');
    }
  };

  const handleAutoRelease = async (escrowId: string) => {
    setConfirmAction({
      type: 'auto-release',
      escrowId,
      title: 'Auto-Release Payment',
      message: 'Are you sure you want to auto-release this payment? This will immediately release the funds to the seller.'
    });
    setShowConfirmModal(true);
  };

  const executeAutoRelease = async (escrowId: string) => {
    try {
      await api.post(`/marketplace/escrows/${escrowId}/auto-release/`);
      toast.success('Payment auto-released successfully');
      fetchEscrows();
    } catch (error) {
      console.error('Error auto-releasing payment:', error);
      toast.error('Failed to auto-release payment');
    }
  };

  const handleConfirmAction = async () => {
    if (!confirmAction) return;

    if (confirmAction.type === 'confirm') {
      await executeConfirmReceipt(confirmAction.escrowId);
    } else if (confirmAction.type === 'auto-release') {
      await executeAutoRelease(confirmAction.escrowId);
    }

    setShowConfirmModal(false);
    setConfirmAction(null);
  };

  const filteredEscrows = Array.isArray(escrows) ? escrows.filter(escrow => {
    if (filter === 'all') return true;
    return escrow.status === filter;
  }) : [];

  const formatCurrency = (amount: string) => {
    return parseFloat(amount).toFixed(2);
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
          <p className="text-white text-xl font-medium">Loading escrow transactions...</p>
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
                <Link
                  to="/dashboard"
                  className="inline-flex items-center text-cyan-400 hover:text-cyan-300 transition-colors mb-4"
                >
                  <ArrowLeftIcon className="h-5 w-5 mr-2" />
                  Back to Dashboard
                </Link>
                <h1 className="text-4xl lg:text-5xl font-black bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-3">
                  🛡️ Escrow Transactions
                </h1>
                <p className="text-gray-300 text-lg">
                  Manage your secure dataset transactions with blockchain protection
                </p>
              </div>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <Link
                  to="/test-escrow"
                  className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-purple-300 px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 border border-purple-400/30"
                >
                  Test Escrow System
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Filters */}
        <div className="mb-8">
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <DocumentTextIcon className="h-6 w-6 mr-2 text-cyan-400" />
              Filter Transactions
            </h3>
            <div className="flex flex-wrap gap-3">
              {[
                { key: 'all', label: 'All Transactions', count: Array.isArray(escrows) ? escrows.length : 0, icon: '📋' },
                { key: 'active', label: 'Active', count: Array.isArray(escrows) ? escrows.filter(e => e.status === 'active').length : 0, icon: '🔄' },
                { key: 'completed', label: 'Completed', count: Array.isArray(escrows) ? escrows.filter(e => e.status === 'completed').length : 0, icon: '✅' },
                { key: 'disputed', label: 'Disputed', count: Array.isArray(escrows) ? escrows.filter(e => e.status === 'disputed').length : 0, icon: '⚠️' },
                { key: 'auto_released', label: 'Auto Released', count: Array.isArray(escrows) ? escrows.filter(e => e.status === 'auto_released').length : 0, icon: '🚀' },
              ].map(({ key, label, count, icon }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`px-4 py-3 rounded-xl text-sm font-bold transition-all duration-300 border ${
                    filter === key
                      ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white border-cyan-400/50 shadow-lg shadow-cyan-500/25'
                      : 'bg-black/20 text-gray-300 border-gray-600/30 hover:border-cyan-400/50 hover:text-white'
                  }`}
                >
                  <span className="mr-2">{icon}</span>
                  {label} ({count})
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Enhanced Escrow Transactions */}
        {filteredEscrows.length > 0 ? (
          <div className="space-y-8">
            {filteredEscrows.map((escrow) => (
              <div key={escrow.id} className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden hover:border-cyan-400/50 transition-all duration-300">
                <div className="p-8">
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between">
                    <div className="flex-1 mb-6 lg:mb-0">
                      {/* Enhanced Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 mb-6">
                        <h3 className="text-2xl font-bold text-white mb-2 sm:mb-0">
                          {escrow.dataset_title}
                        </h3>
                        <span className={`inline-flex items-center px-4 py-2 text-sm font-bold rounded-full border ${getStatusBadge(escrow.status)}`}>
                          {getStatusIcon(escrow.status)}
                          <span className="ml-2 capitalize">{escrow.status.replace('_', ' ')}</span>
                        </span>
                      </div>

                      {/* Enhanced Transaction Details */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                          <p className="text-sm font-medium text-gray-400 mb-2">💰 Amount</p>
                          <p className="text-2xl font-black text-cyan-400">
                            {formatCurrency(escrow.amount)} <span className="text-lg">NCR</span>
                          </p>
                        </div>
                        <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                          <p className="text-sm font-medium text-gray-400 mb-2">🏦 Escrow Fee</p>
                          <p className="text-2xl font-black text-purple-400">
                            {formatCurrency(escrow.escrow_fee)} <span className="text-lg">NCR</span>
                          </p>
                        </div>
                        <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                          <p className="text-sm font-medium text-gray-400 mb-2">📅 Created</p>
                          <p className="text-2xl font-black text-white">
                            {new Date(escrow.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      {/* Enhanced Progress Indicators */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
                        <div className={`bg-black/20 rounded-xl p-4 border transition-all duration-300 ${
                          escrow.seller_delivered 
                            ? 'border-green-400/30 bg-green-500/10' 
                            : 'border-gray-600/30'
                        }`}>
                          <div className={`flex items-center ${escrow.seller_delivered ? 'text-green-300' : 'text-gray-400'}`}>
                            {escrow.seller_delivered ? 
                              <CheckCircleIcon className="h-6 w-6 mr-3" /> : 
                              <ClockIcon className="h-6 w-6 mr-3" />
                            }
                            <div>
                              <div className="font-bold">Seller Delivered</div>
                              <div className="text-xs">
                                {escrow.seller_delivered ? 'Dataset delivered' : 'Waiting for delivery'}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className={`bg-black/20 rounded-xl p-4 border transition-all duration-300 ${
                          escrow.buyer_confirmed 
                            ? 'border-green-400/30 bg-green-500/10' 
                            : 'border-gray-600/30'
                        }`}>
                          <div className={`flex items-center ${escrow.buyer_confirmed ? 'text-green-300' : 'text-gray-400'}`}>
                            {escrow.buyer_confirmed ? 
                              <CheckCircleIcon className="h-6 w-6 mr-3" /> : 
                              <ClockIcon className="h-6 w-6 mr-3" />
                            }
                            <div>
                              <div className="font-bold">Buyer Confirmed</div>
                              <div className="text-xs">
                                {escrow.buyer_confirmed ? 'Receipt confirmed' : 'Waiting for confirmation'}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Enhanced Auto-release Timer */}
                      {escrow.auto_release_time && escrow.status === 'active' && (
                        <div className="mb-6 p-4 bg-orange-500/20 rounded-xl border border-orange-400/30">
                          <div className="flex items-center text-orange-300">
                            <ClockIcon className="h-6 w-6 mr-3" />
                            <div>
                              <div className="font-bold">⏰ Auto-release Timer</div>
                              <div className="text-sm">
                                {new Date(escrow.auto_release_time).toLocaleString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Enhanced Dispute Reason */}
                      {escrow.dispute_reason && (
                        <div className="mb-6 p-4 bg-red-500/20 rounded-xl border border-red-400/30">
                          <div className="flex items-start text-red-300">
                            <ExclamationTriangleIcon className="h-6 w-6 mr-3 mt-1" />
                            <div className="flex-1">
                              <div className="font-bold mb-2">🚨 Dispute Filed</div>
                              <div className="bg-black/20 p-3 rounded-lg border border-red-400/20">
                                <p className="text-sm">{escrow.dispute_reason}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Enhanced Action Buttons */}
                    <div className="flex flex-col space-y-4 lg:ml-8 lg:w-64">
                      <Link
                        to={`/datasets/${escrow.dataset_id}`}
                        className="bg-black/20 text-cyan-300 px-4 py-3 rounded-xl font-bold hover:bg-cyan-500/20 transition-all duration-300 border border-cyan-400/30 flex items-center justify-center"
                      >
                        <EyeIcon className="h-5 w-5 mr-2" />
                        View Dataset
                      </Link>

                      {escrow.can_confirm && (
                        <button
                          onClick={() => handleConfirmReceipt(escrow.id)}
                          className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-green-500/25 flex items-center justify-center"
                        >
                          <CheckCircleIcon className="h-5 w-5 mr-2" />
                          Confirm Receipt
                        </button>
                      )}
                      
                      {escrow.can_dispute && (
                        <button
                          onClick={() => {
                            setSelectedEscrow(escrow);
                            setShowDisputeModal(true);
                          }}
                          className="bg-gradient-to-r from-red-500 to-pink-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-red-500/25 flex items-center justify-center"
                        >
                          <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                          File Dispute
                        </button>
                      )}
                      
                      {escrow.can_auto_release && (
                        <button
                          onClick={() => handleAutoRelease(escrow.id)}
                          className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-purple-500/25 flex items-center justify-center"
                        >
                          <ShieldCheckIcon className="h-5 w-5 mr-2" />
                          Auto Release
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20">
            <ShieldCheckIcon className="h-24 w-24 text-cyan-400 mx-auto mb-8" />
            <h3 className="text-3xl font-bold text-white mb-4">
              {filter === 'all' ? 'No escrow transactions' : `No ${filter} transactions`}
            </h3>
            <p className="text-gray-300 text-lg mb-8 max-w-md mx-auto">
              {filter === 'all' 
                ? 'You haven\'t made any purchases with escrow protection yet. Start exploring datasets!'
                : `You don't have any ${filter} escrow transactions at the moment.`
              }
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/datasets" className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25">
                Browse Datasets
              </Link>
              <Link to="/test-escrow" className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-purple-300 px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all duration-300 border border-purple-400/30">
                Test Escrow System
              </Link>
            </div>
          </div>
        )}

        {/* Enhanced Dispute Modal */}
        {showDisputeModal && selectedEscrow && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-gradient-to-br from-slate-900 to-purple-900 rounded-2xl max-w-md w-full p-8 border border-red-500/30">
              <div className="text-center mb-6">
                <ExclamationTriangleIcon className="h-16 w-16 text-red-400 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-white mb-2">
                  🚨 File Dispute
                </h3>
                <p className="text-gray-300">
                  Report an issue with this transaction
                </p>
              </div>
              
              <div className="mb-6">
                <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30 mb-4">
                  <div className="text-sm text-gray-400 mb-1">Dataset</div>
                  <div className="font-bold text-white">{selectedEscrow.dataset_title}</div>
                </div>
                
                <p className="text-sm text-gray-300 mb-4">
                  Please provide a detailed reason for disputing this transaction. This will be reviewed by our validators.
                </p>
                
                <textarea
                  value={disputeReason}
                  onChange={(e) => setDisputeReason(e.target.value)}
                  placeholder="Describe the issue with this dataset or transaction..."
                  className="w-full p-4 bg-black/20 border border-gray-600/30 rounded-xl resize-none h-32 focus:ring-2 focus:ring-red-500 focus:border-red-500 text-white placeholder-gray-400"
                  maxLength={500}
                />
                <p className="text-xs text-gray-400 mt-2">
                  {disputeReason.length}/500 characters
                </p>
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => {
                    setShowDisputeModal(false);
                    setDisputeReason('');
                    setSelectedEscrow(null);
                  }}
                  className="flex-1 bg-black/20 text-gray-300 px-4 py-3 rounded-xl font-bold hover:bg-gray-600/20 transition-all duration-300 border border-gray-600/30"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDispute}
                  disabled={!disputeReason.trim()}
                  className="flex-1 bg-gradient-to-r from-red-500 to-pink-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-red-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Submit Dispute
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Confirmation Modal */}
        {showConfirmModal && confirmAction && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-gradient-to-br from-slate-900 to-purple-900 rounded-2xl max-w-md w-full p-8 border border-cyan-500/30">
              <div className="text-center mb-6">
                {confirmAction.type === 'confirm' ? (
                  <CheckCircleIcon className="h-16 w-16 text-green-400 mx-auto mb-4" />
                ) : (
                  <ShieldCheckIcon className="h-16 w-16 text-purple-400 mx-auto mb-4" />
                )}
                <h3 className="text-2xl font-bold text-white mb-2">
                  {confirmAction.type === 'confirm' ? '✅ Confirm Receipt' : '🚀 Auto Release'}
                </h3>
                <p className="text-gray-300">
                  {confirmAction.title}
                </p>
              </div>
              
              <div className="mb-6">
                <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                  <p className="text-gray-300 text-center">
                    {confirmAction.message}
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => {
                    setShowConfirmModal(false);
                    setConfirmAction(null);
                  }}
                  className="flex-1 bg-black/20 text-gray-300 px-4 py-3 rounded-xl font-bold hover:bg-gray-600/20 transition-all duration-300 border border-gray-600/30"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmAction}
                  className={`flex-1 px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg ${
                    confirmAction.type === 'confirm' 
                      ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-green-500/25' 
                      : 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white hover:shadow-purple-500/25'
                  }`}
                >
                  {confirmAction.type === 'confirm' ? 'Confirm Receipt' : 'Auto Release'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EscrowPage;
