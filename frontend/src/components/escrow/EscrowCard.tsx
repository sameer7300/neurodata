import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

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

interface EscrowCardProps {
  escrow: EscrowTransaction;
  onConfirmReceipt: (escrowId: string) => void;
  onDispute: (escrow: EscrowTransaction) => void;
  onAutoRelease: (escrowId: string) => void;
  compact?: boolean;
}

const EscrowCard: React.FC<EscrowCardProps> = ({
  escrow,
  onConfirmReceipt,
  onDispute,
  onAutoRelease,
  compact = false
}) => {
  const getStatusBadge = (status: string) => {
    const badges = {
      active: 'bg-blue-100 text-blue-800 border-blue-200',
      completed: 'bg-green-100 text-green-800 border-green-200',
      disputed: 'bg-red-100 text-red-800 border-red-200',
      refunded: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
      auto_released: 'bg-purple-100 text-purple-800 border-purple-200',
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

  const formatCurrency = (amount: string) => {
    return parseFloat(amount).toFixed(2);
  };

  if (compact) {
    return (
      <div className="border border-gray-200 rounded-lg p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h4 className="font-medium text-gray-900">{escrow.dataset_title}</h4>
              <span className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${getStatusBadge(escrow.status)}`}>
                {getStatusIcon(escrow.status)}
                <span className="ml-1 capitalize">{escrow.status.replace('_', ' ')}</span>
              </span>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-600 mb-3">
              <span>Amount: {formatCurrency(escrow.amount)} NCR</span>
              <span>Fee: {formatCurrency(escrow.escrow_fee)} NCR</span>
              <span>Created: {new Date(escrow.created_at).toLocaleDateString()}</span>
            </div>

            <div className="flex items-center space-x-4 text-sm">
              <span className={`flex items-center ${escrow.seller_delivered ? 'text-green-600' : 'text-gray-400'}`}>
                {escrow.seller_delivered ? <CheckCircleIcon className="h-4 w-4 mr-1" /> : <ClockIcon className="h-4 w-4 mr-1" />}
                Seller Delivered
              </span>
              <span className={`flex items-center ${escrow.buyer_confirmed ? 'text-green-600' : 'text-gray-400'}`}>
                {escrow.buyer_confirmed ? <CheckCircleIcon className="h-4 w-4 mr-1" /> : <ClockIcon className="h-4 w-4 mr-1" />}
                Buyer Confirmed
              </span>
            </div>

            {escrow.auto_release_time && escrow.status === 'active' && (
              <div className="mt-2 text-sm text-orange-600">
                <ClockIcon className="h-4 w-4 inline mr-1" />
                Auto-release: {new Date(escrow.auto_release_time).toLocaleString()}
              </div>
            )}

            {escrow.dispute_reason && (
              <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-800">
                <ExclamationTriangleIcon className="h-4 w-4 inline mr-1" />
                Dispute: {escrow.dispute_reason}
              </div>
            )}
          </div>

          <div className="flex flex-col space-y-2 ml-4">
            {escrow.can_confirm && (
              <button
                onClick={() => onConfirmReceipt(escrow.id)}
                className="btn-success btn-sm"
              >
                Confirm Receipt
              </button>
            )}
            
            {escrow.can_dispute && (
              <button
                onClick={() => onDispute(escrow)}
                className="btn-error btn-sm"
              >
                Dispute
              </button>
            )}
            
            {escrow.can_auto_release && (
              <button
                onClick={() => onAutoRelease(escrow.id)}
                className="btn-secondary btn-sm"
              >
                Auto Release
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center space-x-3 mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {escrow.dataset_title}
              </h3>
              <span className={`inline-flex items-center px-3 py-1 text-sm rounded-full border ${getStatusBadge(escrow.status)}`}>
                {getStatusIcon(escrow.status)}
                <span className="ml-2 capitalize">{escrow.status.replace('_', ' ')}</span>
              </span>
            </div>

            {/* Transaction Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-sm font-medium text-gray-600">Amount</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatCurrency(escrow.amount)} NCR
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Escrow Fee</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatCurrency(escrow.escrow_fee)} NCR
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Created</p>
                <p className="text-lg font-semibold text-gray-900">
                  {new Date(escrow.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Progress Indicators */}
            <div className="flex items-center space-x-6 mb-4">
              <div className={`flex items-center text-sm ${escrow.seller_delivered ? 'text-green-600' : 'text-gray-400'}`}>
                {escrow.seller_delivered ? 
                  <CheckCircleIcon className="h-5 w-5 mr-2" /> : 
                  <ClockIcon className="h-5 w-5 mr-2" />
                }
                Seller Delivered
              </div>
              <div className={`flex items-center text-sm ${escrow.buyer_confirmed ? 'text-green-600' : 'text-gray-400'}`}>
                {escrow.buyer_confirmed ? 
                  <CheckCircleIcon className="h-5 w-5 mr-2" /> : 
                  <ClockIcon className="h-5 w-5 mr-2" />
                }
                Buyer Confirmed
              </div>
            </div>

            {/* Auto-release Timer */}
            {escrow.auto_release_time && escrow.status === 'active' && (
              <div className="mb-4 p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center text-orange-800">
                  <ClockIcon className="h-5 w-5 mr-2" />
                  <span className="text-sm font-medium">
                    Auto-release: {new Date(escrow.auto_release_time).toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            {/* Dispute Information */}
            {escrow.dispute_reason && (
              <div className="mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-start text-red-800">
                  <ExclamationTriangleIcon className="h-5 w-5 mr-2 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium">🚨 Dispute Filed</p>
                      {escrow.disputed_at && (
                        <span className="text-xs text-red-600">
                          {new Date(escrow.disputed_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <p className="text-sm mb-2">
                      <strong>By:</strong> {escrow.is_seller ? escrow.buyer_username : 'You'}
                    </p>
                    <p className="text-sm mb-2">
                      <strong>Reason:</strong> {escrow.dispute_reason}
                    </p>
                    {escrow.validator && (
                      <p className="text-sm mb-2">
                        <strong>Assigned Validator:</strong> {escrow.validator}
                      </p>
                    )}
                    {escrow.resolution_notes && (
                      <div className="mt-2 p-2 bg-white rounded border">
                        <p className="text-sm font-medium text-gray-900">Resolution:</p>
                        <p className="text-sm text-gray-700">{escrow.resolution_notes}</p>
                        {escrow.resolved_at && (
                          <p className="text-xs text-gray-500 mt-1">
                            Resolved: {new Date(escrow.resolved_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col space-y-2 ml-6">
            <Link
              to={`/datasets/${escrow.dataset_id}`}
              className="btn-outline btn-sm flex items-center"
            >
              <EyeIcon className="h-4 w-4 mr-2" />
              View Dataset
            </Link>

            {escrow.can_confirm && (
              <button
                onClick={() => onConfirmReceipt(escrow.id)}
                className="btn-success btn-sm"
              >
                <CheckCircleIcon className="h-4 w-4 mr-2" />
                Confirm Receipt
              </button>
            )}
            
            {escrow.can_dispute && (
              <button
                onClick={() => onDispute(escrow)}
                className="btn-error btn-sm"
              >
                <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                Dispute
              </button>
            )}
            
            {escrow.can_auto_release && (
              <button
                onClick={() => onAutoRelease(escrow.id)}
                className="btn-secondary btn-sm"
              >
                <ShieldCheckIcon className="h-4 w-4 mr-2" />
                Auto Release
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EscrowCard;
