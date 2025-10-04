import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  StarIcon,
  ArrowDownTrayIcon,
  CurrencyDollarIcon,
  UserIcon,
  CalendarIcon,
  DocumentIcon,
  TagIcon,
  ShieldCheckIcon,
  HeartIcon,
  ShareIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartIconSolid } from '@heroicons/react/24/solid';
import { useAuth } from '../contexts/AuthContext';
import { useWeb3 } from '../contexts/Web3Context';
import api from '../services/api';
import toast from 'react-hot-toast';
import ContractService from '../services/contracts';
import { ethers } from 'ethers';

interface Dataset {
  id: string;
  title: string;
  slug: string;
  description: string;
  owner: {
    id: string;
    username: string;
    reputation_score?: number;
  };
  category: {
    id: number;
    name: string;
    slug: string;
    description: string;
    icon: string;
  };
  tags: Array<{
    id: number;
    name: string;
    slug: string;
    color: string;
  }>;
  price: string;
  is_free: boolean;
  file_size: number;
  file_size_human: string;
  file_type: string;
  file_name: string;
  download_count: number;
  view_count: number;
  rating_average: number;
  rating_count: number;
  status: string;
  created_at: string;
  published_at: string;
  keywords: string;
  sample_data?: any;
  schema_info?: any;
  statistics?: any;
  data_format: string;
  data_size: string;
  collection_method: string;
  license: string;
  privacy_level: string;
  file_url?: string;
  has_purchased: boolean;
  can_download: boolean;
  is_favorited: boolean;
  escrow?: {
    id: string;
    status: 'active' | 'completed' | 'disputed' | 'refunded' | 'cancelled' | 'auto_released';
    buyer_confirmed: boolean;
    seller_delivered: boolean;
    created_at: string;
    auto_release_time: string;
    dispute_reason?: string;
    can_confirm: boolean;
    can_dispute: boolean;
    can_auto_release: boolean;
    dispute_status?: 'open' | 'closed';
  };
}

interface Review {
  id: string;
  reviewer: {
    id: string;
    username: string;
    email: string;
  };
  rating: number;
  title: string;
  comment: string;
  is_verified_purchase: boolean;
  helpful_count: number;
  report_count: number;
  is_helpful_by_user: boolean;
  can_report: boolean;
  can_edit: boolean;
  created_at: string;
}

interface ReviewStats {
  total_reviews: number;
  average_rating: number;
  rating_distribution: { [key: number]: number };
  verified_percentage: number;
  five_star_count: number;
  four_star_count: number;
  three_star_count: number;
  two_star_count: number;
  one_star_count: number;
  five_star_percentage: number;
  four_star_percentage: number;
  three_star_percentage: number;
  two_star_percentage: number;
  one_star_percentage: number;
}

const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const { isConnected, account, provider, signer } = useWeb3();
  
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewStats, setReviewStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'reviews' | 'sample' | 'quality'>('overview');
  const [previewData, setPreviewData] = useState<any>(null);
  const [qualityScore, setQualityScore] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingQuality, setLoadingQuality] = useState(false);
  
  // Review state
  const [showAddReview, setShowAddReview] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    rating: 5,
    title: '',
    comment: ''
  });
  const [reviewFilters, setReviewFilters] = useState({
    rating: '',
    verified_only: false,
    sort_by: 'newest'
  });
  const [submittingReview, setSubmittingReview] = useState(false);
  const [showDisputeModal, setShowDisputeModal] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'confirm' | 'auto-release';
    title: string;
    message: string;
  } | null>(null);

  useEffect(() => {
    if (id) {
      fetchDataset();
      fetchReviews();
    }
  }, [id]);

  useEffect(() => {
    if (activeTab === 'sample' && dataset) {
      fetchPreviewData();
    }
  }, [activeTab, dataset]);

  useEffect(() => {
    if (activeTab === 'quality' && dataset) {
      fetchQualityScore();
    }
  }, [activeTab, dataset]);

  useEffect(() => {
    if (activeTab === 'reviews') {
      fetchReviews();
    }
  }, [activeTab, reviewFilters]);

  const fetchDataset = async () => {
    try {
      setLoading(true);
      // Remove hyphens from UUID for backend compatibility
      const cleanId = id?.replace(/-/g, '');
      const response = await api.get(`/datasets/datasets/${cleanId}/`);
      setDataset(response.data.data || response.data);
    } catch (error) {
      console.error('Error fetching dataset:', error);
      toast.error('Failed to load dataset');
      navigate('/datasets');
    } finally {
      setLoading(false);
    }
  };

  const fetchReviews = async () => {
    try {
      // Remove hyphens from UUID for backend compatibility
      const cleanId = id?.replace(/-/g, '');
      
      // Build query parameters
      const params = new URLSearchParams();
      if (reviewFilters.rating) params.append('rating', reviewFilters.rating);
      if (reviewFilters.verified_only) params.append('verified_only', 'true');
      params.append('sort_by', reviewFilters.sort_by);
      
      const response = await api.get(`/reviews/datasets/${cleanId}/reviews/?${params}`);
      
      // Handle different response structures
      if (response.data.success !== false) {
        const responseData = response.data.data || response.data;
        
        // Handle paginated responses (DRF pagination)
        if (responseData.results) {
          setReviews(responseData.results);
          setReviewStats(responseData.stats || null);
        }
        // Handle non-paginated responses
        else if (responseData.reviews) {
          setReviews(responseData.reviews);
          setReviewStats(responseData.stats || null);
        }
        // Handle direct array responses
        else if (Array.isArray(responseData)) {
          setReviews(responseData);
          setReviewStats(response.data.stats || null);
        }
        // Handle empty responses
        else {
          setReviews([]);
          setReviewStats(responseData.stats || null);
        }
      } else {
        setReviews([]);
        setReviewStats(null);
      }
    } catch (error) {
      console.error('Error fetching reviews:', error);
      setReviews([]);
      setReviewStats(null);
    }
  };

  const fetchPreviewData = async () => {
    if (!dataset || previewData) return;
    
    setLoadingPreview(true);
    try {
      const cleanId = id?.replace(/-/g, '');
      const response = await api.get(`/datasets/datasets/${cleanId}/preview/`);
      setPreviewData(response.data.data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Purchase required to view dataset preview');
      } else {
        console.error('Error fetching preview:', error);
        toast.error('Failed to load dataset preview');
      }
    } finally {
      setLoadingPreview(false);
    }
  };

  const fetchQualityScore = async () => {
    if (!dataset || qualityScore) return;
    
    setLoadingQuality(true);
    try {
      const cleanId = id?.replace(/-/g, '');
      const response = await api.get(`/datasets/datasets/${cleanId}/quality_score/`);
      setQualityScore(response.data.data);
    } catch (error) {
      console.error('Error fetching quality score:', error);
    } finally {
      setLoadingQuality(false);
    }
  };

  const handleSubmitReview = async () => {
    if (!dataset || !isAuthenticated) {
      toast.error('Please login to submit a review');
      return;
    }

    if (reviewForm.title.length < 3) {
      toast.error('Review title must be at least 3 characters');
      return;
    }

    if (reviewForm.comment.length < 10) {
      toast.error('Review comment must be at least 10 characters');
      return;
    }

    setSubmittingReview(true);
    try {
      const response = await api.post('/reviews/reviews/', {
        dataset_id: dataset.id,
        rating: reviewForm.rating,
        title: reviewForm.title,
        comment: reviewForm.comment
      });

      if (response.data.success) {
        toast.success('Review submitted successfully');
        setShowAddReview(false);
        setReviewForm({ rating: 5, title: '', comment: '' });
        fetchReviews();
        // Refresh dataset to update rating
        fetchDataset();
      }
    } catch (error: any) {
      console.error('Error submitting review:', error);
      if (error.response?.data?.message) {
        toast.error(error.response.data.message);
      } else {
        toast.error('Failed to submit review');
      }
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleMarkHelpful = async (reviewId: string, isHelpful: boolean) => {
    if (!isAuthenticated) {
      toast.error('Please login to vote');
      return;
    }

    try {
      await api.post(`/reviews/reviews/${reviewId}/helpful/`, {
        is_helpful: isHelpful
      });
      
      // Refresh reviews to show updated helpful count
      fetchReviews();
    } catch (error: any) {
      console.error('Error marking helpful:', error);
      if (error.response?.data?.message) {
        toast.error(error.response.data.message);
      } else {
        toast.error('Failed to update vote');
      }
    }
  };

  const handleReportReview = async (reviewId: string, reason: string, description: string) => {
    if (!isAuthenticated) {
      toast.error('Please login to report');
      return;
    }

    try {
      await api.post(`/reviews/reviews/${reviewId}/report/`, {
        reason,
        description
      });
      
      toast.success('Review reported successfully');
      fetchReviews();
    } catch (error: any) {
      console.error('Error reporting review:', error);
      if (error.response?.data?.message) {
        toast.error(error.response.data.message);
      } else {
        toast.error('Failed to report review');
      }
    }
  };


  const handlePurchase = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to purchase datasets');
      navigate('/login');
      return;
    }

    if (!isConnected || !provider || !signer) {
      toast.error('Please connect your wallet to make purchases');
      return;
    }

    if (!dataset) {
      toast.error('Dataset not found');
      return;
    }

    setPurchasing(true);
    try {
      // Step 1: Create purchase record in backend
      const cleanId = id?.replace(/-/g, '');
      const backendResponse = await api.post(`/datasets/datasets/${cleanId}/purchase/`, {
        payment_method: 'crypto',
        wallet_address: account,
      });

      if (!backendResponse.data.success) {
        throw new Error(backendResponse.data.message || 'Failed to create purchase record');
      }

      const purchaseId = backendResponse.data.data.purchase_id;
      
      // Step 2: Check wallet balance and execute blockchain transaction
      let txHash = null;
      let useSmartContract = false;
      
      // Check if smart contracts are available
      if (provider && signer && process.env.REACT_APP_MARKETPLACE_CONTRACT !== '0x0000000000000000000000000000000000000000') {
        try {
          // Check ETH balance for gas fees
          const ethBalance = await provider.getBalance(account!);
          const ethBalanceFormatted = parseFloat(ethers.formatEther(ethBalance));
          
          if (ethBalanceFormatted < 0.001) { // Need at least 0.001 ETH for gas
            throw new Error(`Insufficient ETH for gas fees. You have ${ethBalanceFormatted.toFixed(4)} ETH, need at least 0.001 ETH`);
          }
          
          // Check NCR balance
          const contractService = new ContractService(provider, signer);
          const ncrBalance = await contractService.getNRCBalance(account!);
          const ncrBalanceFormatted = parseFloat(ncrBalance);
          const requiredNCR = parseFloat(dataset.price);
          
          if (ncrBalanceFormatted < requiredNCR) {
            throw new Error(`Insufficient NCR tokens. You have ${ncrBalanceFormatted.toFixed(2)} NCR, need ${requiredNCR} NCR`);
          }
          
          toast.loading('Executing blockchain transaction...', { id: 'purchase-tx' });
          
          txHash = await contractService.purchaseDataset(cleanId!, dataset.price);
          useSmartContract = true;
          
          toast.dismiss('purchase-tx');
        } catch (contractError: any) {
          console.error('Smart contract transaction failed:', contractError);
          toast.dismiss('purchase-tx');
          
          // Show specific error messages
          if (contractError.message?.includes('Insufficient ETH')) {
            toast.error(contractError.message);
            throw contractError;
          } else if (contractError.message?.includes('Insufficient NCR')) {
            toast.error(contractError.message);
            throw contractError;
          } else if (contractError.message?.includes('rejected') || contractError.code === 4001) {
            toast.error('Transaction cancelled by user');
            throw contractError;
          } else if (contractError.message?.includes('insufficient funds')) {
            toast.error('Insufficient NCR tokens or ETH for gas fees');
            throw contractError;
          } else if (contractError.message?.includes('Insufficient NRC balance')) {
            toast.error('Insufficient NCR tokens for this purchase');
            throw contractError;
          } else {
            toast.error('Blockchain transaction failed. Please check your wallet balance.');
            throw contractError;
          }
        }
      } else {
        // No smart contract available - this should not allow free purchases
        throw new Error('Payment system unavailable. Smart contracts not configured.');
      }
      
      // Step 3: Update backend with transaction status
      toast.loading('Confirming purchase...', { id: 'purchase-confirm' });
      
      await api.patch(`/marketplace/purchases/${purchaseId}/`, {
        transaction_hash: txHash,
        status: 'completed'
      });

      // Step 4: Create escrow for secure transaction
      toast.loading('Setting up escrow protection...', { id: 'escrow-setup' });
      
      try {
        const escrowResponse = await api.post(`/marketplace/purchases/${purchaseId}/escrow/`);
        
        if (escrowResponse.data.success) {
          toast.dismiss('escrow-setup');
          toast.success('Purchase successful with escrow protection! Seller will be notified to deliver the dataset.');
        } else {
          console.warn('Escrow creation failed:', escrowResponse.data.message);
          toast.dismiss('escrow-setup');
          toast.success('Purchase successful! You can now download the dataset.');
        }
      } catch (escrowError) {
        console.warn('Escrow creation failed:', escrowError);
        toast.dismiss('escrow-setup');
        toast.success('Purchase successful! You can now download the dataset.');
      }

      toast.dismiss('purchase-confirm');
      
      // Update local state
      setDataset(prev => prev ? { ...prev, has_purchased: true, can_download: true } : null);
      setShowPurchaseModal(false);

    } catch (error: any) {
      console.error('Purchase error:', error);
      toast.dismiss('purchase-tx');
      toast.dismiss('purchase-confirm');
      
      let errorMessage = 'Purchase failed';
      if (error.message?.includes('insufficient')) {
        errorMessage = 'Insufficient NRC balance';
      } else if (error.message?.includes('rejected') || error.code === 4001) {
        errorMessage = 'Transaction rejected by user';
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setPurchasing(false);
    }
  };

  // Escrow action handlers
  const handleConfirmReceipt = async () => {
    if (!dataset?.escrow?.id) return;

    setConfirmAction({
      type: 'confirm',
      title: 'Confirm Receipt',
      message: 'Are you sure you want to confirm receipt of this dataset? This action cannot be undone and will release the payment to the seller.'
    });
    setShowConfirmModal(true);
  };

  const executeConfirmReceipt = async () => {
    if (!dataset?.escrow?.id) return;

    try {
      await api.post(`/marketplace/escrows/${dataset.escrow.id}/confirm-receipt/`);
      toast.success('Receipt confirmed successfully');
      fetchDataset(); // Refresh dataset data
    } catch (error) {
      console.error('Error confirming receipt:', error);
      toast.error('Failed to confirm receipt');
    }
  };

  const handleDispute = async () => {
    if (!dataset?.escrow?.id || !disputeReason.trim()) {
      toast.error('Please provide a reason for the dispute');
      return;
    }

    try {
      await api.post(`/marketplace/escrows/${dataset.escrow.id}/dispute/`, { 
        reason: disputeReason 
      });
      toast.success('Dispute submitted successfully');
      setShowDisputeModal(false);
      setDisputeReason('');
      fetchDataset(); // Refresh dataset data
    } catch (error) {
      console.error('Error submitting dispute:', error);
      toast.error('Failed to submit dispute');
    }
  };

  const handleAutoRelease = async () => {
    if (!dataset?.escrow?.id) return;

    setConfirmAction({
      type: 'auto-release',
      title: 'Auto-Release Payment',
      message: 'Are you sure you want to auto-release this payment? This will immediately release the funds to the seller.'
    });
    setShowConfirmModal(true);
  };

  const executeAutoRelease = async () => {
    if (!dataset?.escrow?.id) return;

    try {
      await api.post(`/marketplace/escrows/${dataset.escrow.id}/auto-release/`);
      toast.success('Payment auto-released successfully');
      fetchDataset(); // Refresh dataset data
    } catch (error) {
      console.error('Error auto-releasing payment:', error);
      toast.error('Failed to auto-release payment');
    }
  };

  const handleConfirmAction = async () => {
    if (!confirmAction) return;

    if (confirmAction.type === 'confirm') {
      await executeConfirmReceipt();
    } else if (confirmAction.type === 'auto-release') {
      await executeAutoRelease();
    }

    setShowConfirmModal(false);
    setConfirmAction(null);
  };

  const handleDownload = async () => {
    if (!dataset?.can_download) {
      toast.error('You don\'t have permission to download this dataset. Please purchase it first.');
      return;
    }

    setDownloading(true);
    try {
      // Remove hyphens from UUID for backend compatibility
      const cleanId = id?.replace(/-/g, '');
      const response = await api.get(`/datasets/datasets/${cleanId}/download/`, {
        responseType: 'blob',
      });

      // Get filename - prioritize Content-Disposition header, then dataset.file_name
      console.log('Dataset object:', dataset);
      console.log('Dataset file_name:', dataset?.file_name);
      console.log('Dataset title:', dataset?.title);
      
      let filename = dataset?.file_name || `${dataset?.title || 'dataset'}.zip`;
      
      const contentDisposition = response.headers['content-disposition'];
      console.log('Content-Disposition header:', contentDisposition);
      
      if (contentDisposition) {
        // Try different patterns for filename extraction
        const patterns = [
          /filename="([^"]+)"/,  // filename="file.ext"
          /filename=([^;]+)/,    // filename=file.ext
          /filename\*=UTF-8''([^;]+)/ // filename*=UTF-8''file.ext
        ];
        
        for (const pattern of patterns) {
          const match = contentDisposition.match(pattern);
          if (match) {
            filename = decodeURIComponent(match[1]);
            console.log('Extracted filename from header:', filename);
            break;
          }
        }
      }
      
      console.log('Final filename before content-type check:', filename);
      
      // If filename still has wrong extension, fix it based on content-type
      const contentType = response.headers['content-type'];
      if (contentType && contentType !== 'application/octet-stream') {
        const extensionMap: { [key: string]: string } = {
          'image/jpeg': '.jpeg',
          'image/jpg': '.jpg', 
          'image/png': '.png',
          'image/gif': '.gif',
          'text/csv': '.csv',
          'application/json': '.json',
          'text/plain': '.txt',
          'application/pdf': '.pdf',
          'application/zip': '.zip'
        };
        
        const correctExtension = extensionMap[contentType];
        if (correctExtension && !filename.toLowerCase().endsWith(correctExtension)) {
          // Remove any existing extension and add the correct one
          const nameWithoutExt = filename.replace(/\.[^/.]+$/, '');
          filename = nameWithoutExt + correctExtension;
          console.log('Corrected filename based on content-type:', filename);
        }
      }

      // Verify we have actual data
      if (!response.data || response.data.size === 0) {
        throw new Error('Downloaded file is empty');
      }

      console.log('Download response:', {
        size: response.data.size,
        type: response.data.type,
        filename: filename,
        headers: response.headers
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Download started!');
    } catch (error: any) {
      console.error('Download error:', error);
      
      let errorMessage = 'Download failed';
      if (error.message?.includes('empty')) {
        errorMessage = 'Downloaded file is empty or corrupted';
      } else if (error.response?.status === 403) {
        errorMessage = 'You don\'t have permission to download this dataset';
      } else if (error.response?.status === 404) {
        errorMessage = 'Dataset file not found';
      }
      
      toast.error(errorMessage);
    } finally {
      setDownloading(false);
    }
  };

  const toggleFavorite = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to favorite datasets');
      return;
    }

    try {
      // Remove hyphens from UUID for backend compatibility
      const cleanId = id?.replace(/-/g, '');
      const response = await api.post(`/datasets/datasets/${cleanId}/favorite/`);
      setDataset(prev => prev ? { ...prev, is_favorited: !prev.is_favorited } : null);
      toast.success(dataset?.is_favorited ? 'Removed from favorites' : 'Added to favorites');
    } catch (error) {
      console.error('Favorite error:', error);
      toast.error('Failed to update favorites');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getCategoryGradient = (categoryName: string) => {
    const gradients: { [key: string]: string } = {
      'Audio & Speech': 'from-purple-100 to-pink-100',
      'Computer Vision': 'from-blue-100 to-cyan-100',
      'Natural Language': 'from-green-100 to-teal-100',
      'Healthcare': 'from-red-100 to-orange-100',
      'Finance': 'from-yellow-100 to-amber-100',
      'Social Media': 'from-indigo-100 to-purple-100',
      'IoT & Sensors': 'from-gray-100 to-slate-100',
      'Geospatial': 'from-emerald-100 to-green-100',
      'Time Series': 'from-orange-100 to-red-100',
      'Synthetic': 'from-violet-100 to-purple-100',
    };
    return gradients[categoryName] || 'from-primary-100 to-secondary-100';
  };

  const parseDescription = (description: string) => {
    try {
      // Check if description contains "Additional Information:" indicating it has JSON
      if (description.includes('Additional Information:')) {
        const parts = description.split('Additional Information:');
        const userDescription = parts[0].trim();
        
        if (parts.length > 1) {
          const jsonPart = parts[1].trim();
          let additionalInfo = null;
          
          try {
            additionalInfo = JSON.parse(jsonPart);
          } catch {
            // If JSON parsing fails, return the original description
            return { userDescription: description, additionalInfo: null };
          }
          
          return { userDescription, additionalInfo };
        }
      }
      
      // If no "Additional Information:" found, return as is
      return { userDescription: description, additionalInfo: null };
    } catch {
      return { userDescription: description, additionalInfo: null };
    }
  };

  const handleShare = async () => {
    if (!dataset) {
      toast.error('Dataset not loaded');
      return;
    }

    const shareData = {
      title: dataset.title,
      text: `Check out this dataset: ${dataset.title} by ${dataset.owner.username}`,
      url: window.location.href,
    };

    try {
      // Check if Web Share API is available
      if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
        toast.success('Dataset shared successfully!');
      } else {
        // Fallback: Copy to clipboard
        await navigator.clipboard.writeText(window.location.href);
        toast.success('Dataset link copied to clipboard!');
      }
    } catch (error) {
      console.error('Error sharing:', error);
      // Final fallback: Copy to clipboard
      try {
        await navigator.clipboard.writeText(window.location.href);
        toast.success('Dataset link copied to clipboard!');
      } catch (clipboardError) {
        console.error('Clipboard error:', clipboardError);
        toast.error('Unable to share or copy link');
      }
    }
  };

  const formatPrice = (price: string) => {
    return parseFloat(price).toFixed(2);
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <StarIcon
        key={i}
        className={`h-5 w-5 ${
          i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'
        }`}
      />
    ));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Dataset not found</h2>
          <button onClick={() => navigate('/datasets')} className="btn-primary">
            Back to Datasets
          </button>
        </div>
      </div>
    );
  }

  const canDownload = dataset.can_download;
  const needsToPurchase = !dataset.has_purchased && parseFloat(dataset.price) > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse" />
      </div>

      {/* Enhanced Header */}
      <div className="relative z-10 bg-black/20 backdrop-blur-lg border-b border-purple-500/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <button
            onClick={() => navigate('/datasets')}
            className="flex items-center text-gray-300 hover:text-white mb-6 transition-colors duration-300 group"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-2 group-hover:scale-110 transition-transform duration-300" />
            <span className="font-medium">Back to Datasets</span>
          </button>
          
          <div className="flex flex-col lg:flex-row lg:items-start gap-8">
            {/* Enhanced Dataset Image */}
            <div className="lg:w-80 flex-shrink-0">
              <div className="relative bg-black/30 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden group hover:border-cyan-400/50 transition-all duration-500">
                <div className="aspect-video bg-gradient-to-br from-purple-600/20 via-cyan-600/20 to-pink-600/20 flex items-center justify-center relative">
                  <div className="absolute inset-0 bg-black/20"></div>
                  <div className="relative text-center z-10">
                    <TagIcon className="h-20 w-20 text-cyan-400 mx-auto mb-4 group-hover:scale-110 transition-transform duration-300" />
                    <span className="text-white font-bold text-xl bg-black/30 px-4 py-2 rounded-full backdrop-blur-sm">
                      {dataset.category.name}
                    </span>
                    <div className="mt-3 text-cyan-300 text-sm font-medium">
                      {dataset.file_type?.toUpperCase() || 'DATA'} Dataset
                    </div>
                  </div>
                  {/* Enhanced decorative elements */}
                  <div className="absolute top-4 right-4">
                    <div className="bg-black/40 backdrop-blur-sm text-white text-xs font-medium px-3 py-1.5 rounded-full border border-cyan-400/30">
                      {formatFileSize(dataset.file_size)}
                    </div>
                  </div>
                  <div className="absolute bottom-4 left-4">
                    <div className="bg-black/40 backdrop-blur-sm text-cyan-300 text-xs font-medium px-3 py-1.5 rounded-full border border-purple-400/30">
                      ID: {dataset.id.slice(0, 8)}...
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Dataset Info */}
            <div className="flex-1">
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <h1 className="text-4xl font-black bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-4 leading-tight">
                    {dataset.title}
                  </h1>
                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-300 mb-6">
                    <div className="flex items-center bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full border border-purple-500/30">
                      <UserIcon className="h-4 w-4 mr-2 text-cyan-400" />
                      <span className="text-white font-medium">{dataset.owner.username}</span>
                    </div>
                    <div className="flex items-center bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full border border-purple-500/30">
                      <CalendarIcon className="h-4 w-4 mr-2 text-cyan-400" />
                      <span className="text-white">{new Date(dataset.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full border border-purple-500/30">
                      <ArrowDownTrayIcon className="h-4 w-4 mr-2 text-green-400" />
                      <span className="text-white font-medium">{dataset.download_count}</span>
                      <span className="text-gray-300 ml-1">downloads</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 ml-4">
                  <button
                    onClick={toggleFavorite}
                    className="p-3 rounded-xl bg-black/20 backdrop-blur-sm border border-purple-500/30 hover:border-red-400/50 transition-all duration-300 group"
                    title={dataset.is_favorited ? "Remove from favorites" : "Add to favorites"}
                  >
                    {dataset.is_favorited ? (
                      <HeartIconSolid className="h-6 w-6 text-red-500 group-hover:scale-110 transition-transform duration-300" />
                    ) : (
                      <HeartIcon className="h-6 w-6 text-gray-400 group-hover:text-red-400 group-hover:scale-110 transition-all duration-300" />
                    )}
                  </button>
                  <button 
                    onClick={handleShare}
                    className="p-3 rounded-xl bg-black/20 backdrop-blur-sm border border-purple-500/30 hover:border-cyan-400/50 transition-all duration-300 group"
                    title="Share dataset"
                  >
                    <ShareIcon className="h-6 w-6 text-gray-400 group-hover:text-cyan-400 group-hover:scale-110 transition-all duration-300" />
                  </button>
                </div>
              </div>

              {/* Enhanced Rating and Price */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex items-center">
                  <div className="bg-black/20 backdrop-blur-sm rounded-xl px-4 py-3 border border-purple-500/30">
                    <div className="flex items-center">
                      <div className="flex">
                        {renderStars(reviewStats?.average_rating || dataset.rating_average)}
                      </div>
                      <span className="ml-3 text-white font-medium">
                        {Number(reviewStats?.average_rating || dataset.rating_average || 0).toFixed(1)}
                      </span>
                      <span className="ml-2 text-gray-400 text-sm">
                        ({reviewStats?.total_reviews || dataset.rating_count || 0} reviews)
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="bg-black/20 backdrop-blur-sm rounded-xl px-6 py-4 border border-purple-500/30">
                    {dataset.is_free ? (
                      <div className="text-3xl font-bold text-green-400 flex items-center justify-end">
                        <span>FREE</span>
                      </div>
                    ) : (
                      <div className="text-3xl font-bold text-white flex items-center justify-end">
                        <CurrencyDollarIcon className="h-8 w-8 mr-2 text-yellow-400" />
                        <span>{formatPrice(dataset.price)}</span>
                        <span className="text-cyan-400 ml-2">NCR</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Enhanced Tags */}
              <div className="flex flex-wrap gap-2 mb-8">
                {dataset.tags.map((tag) => (
                  <span 
                    key={tag.id} 
                    className="px-4 py-2 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 text-sm rounded-full border border-cyan-500/30 backdrop-blur-sm hover:border-cyan-400/50 transition-all duration-300"
                  >
                    {tag.name}
                  </span>
                ))}
              </div>

              {/* Enhanced Action Buttons */}
              <div className="space-y-6">
                <div className="flex gap-4">
                  {canDownload ? (
                    <button
                      onClick={handleDownload}
                      disabled={downloading}
                      className="flex-1 relative overflow-hidden bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl hover:shadow-emerald-500/30 group"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="relative flex items-center justify-center">
                        {downloading ? (
                          <>
                            <div className="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent mr-3"></div>
                            <span>Downloading...</span>
                          </>
                        ) : (
                          <>
                            <div className="mr-3 p-1 bg-white/20 rounded-full">
                              <ArrowDownTrayIcon className="h-5 w-5" />
                            </div>
                            <span>Download Dataset</span>
                            <div className="ml-3 text-xs bg-white/20 px-2 py-1 rounded-full">
                              {formatFileSize(dataset.file_size)}
                            </div>
                          </>
                        )}
                      </div>
                    </button>
                  ) : (
                    <button
                      onClick={() => setShowPurchaseModal(true)}
                      className="flex-1 bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
                    >
                      <CurrencyDollarIcon className="h-6 w-6 mr-3" />
                      Purchase Dataset
                    </button>
                  )}
                </div>

                {/* Enhanced Escrow Status and Actions */}
                {dataset.escrow && (
                  <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center">
                        <ShieldCheckIcon className="h-6 w-6 text-cyan-400 mr-3" />
                        <span className="font-bold text-white text-lg">Escrow Protection Active</span>
                      </div>
                      <span className={`px-4 py-2 text-sm rounded-full font-medium ${
                        dataset.escrow.status === 'active' ? 'bg-blue-500/20 text-blue-300 border border-blue-400/30' :
                        dataset.escrow.status === 'completed' ? 'bg-green-500/20 text-green-300 border border-green-400/30' :
                        dataset.escrow.status === 'disputed' ? 'bg-red-500/20 text-red-300 border border-red-400/30' :
                        'bg-gray-500/20 text-gray-300 border border-gray-400/30'
                      }`}>
                        {dataset.escrow.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>

                    {/* Enhanced Progress Indicators */}
                    <div className="flex items-center space-x-6 mb-4">
                      <div className={`flex items-center px-3 py-2 rounded-lg ${
                        dataset.escrow.seller_delivered 
                          ? 'bg-green-500/20 text-green-300 border border-green-400/30' 
                          : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                      }`}>
                        <span className="text-lg mr-2">{dataset.escrow.seller_delivered ? '✓' : '○'}</span>
                        <span className="font-medium">Seller Delivered</span>
                      </div>
                      <div className={`flex items-center px-3 py-2 rounded-lg ${
                        dataset.escrow.buyer_confirmed 
                          ? 'bg-green-500/20 text-green-300 border border-green-400/30' 
                          : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                      }`}>
                        <span className="text-lg mr-2">{dataset.escrow.buyer_confirmed ? '✓' : '○'}</span>
                        <span className="font-medium">Buyer Confirmed</span>
                      </div>
                    </div>

                    {/* Enhanced Auto-release Timer */}
                    {dataset.escrow.auto_release_time && dataset.escrow.status === 'active' && (
                      <div className="mb-4 p-4 bg-orange-500/20 border border-orange-400/30 rounded-xl">
                        <div className="flex items-center text-orange-300">
                          <span className="font-medium">Auto-release:</span>
                          <span className="ml-2 text-white">{new Date(dataset.escrow.auto_release_time).toLocaleString()}</span>
                        </div>
                      </div>
                    )}

                    {/* Enhanced Dispute Status */}
                    {dataset.escrow.status === 'disputed' && (
                      <div className="mb-4 p-4 bg-red-500/20 border border-red-400/30 rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-red-300 font-medium">Dispute Status:</span>
                          <span className="px-3 py-1 text-sm rounded-full bg-red-500/30 text-red-200 border border-red-400/50">
                            {dataset.escrow.dispute_status?.toUpperCase() || 'OPEN'}
                          </span>
                        </div>
                        {dataset.escrow.dispute_reason && (
                          <p className="text-red-200 text-sm bg-red-500/10 p-3 rounded-lg border border-red-400/20">
                            {dataset.escrow.dispute_reason}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Enhanced Action Buttons */}
                    <div className="flex gap-3">
                      {dataset.escrow.can_confirm && (
                        <button
                          onClick={handleConfirmReceipt}
                          className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-green-500/25"
                        >
                          Confirm Receipt
                        </button>
                      )}
                      
                      {dataset.escrow.can_dispute && (
                        <button
                          onClick={() => setShowDisputeModal(true)}
                          className="flex-1 bg-gradient-to-r from-red-500 to-pink-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-red-500/25"
                        >
                          Open Dispute
                        </button>
                      )}
                      
                      {dataset.escrow.can_auto_release && (
                        <button
                          onClick={handleAutoRelease}
                          className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-purple-500/25"
                        >
                          Release Funds
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Content Tabs */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-black/30 backdrop-blur-lg rounded-2xl border border-purple-500/20 overflow-hidden">
          {/* Enhanced Tab Navigation */}
          <div className="border-b border-purple-500/20">
            <nav className="flex space-x-0 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: '📋' },
                { id: 'reviews', label: `Reviews (${reviewStats?.total_reviews || dataset.rating_count || 0})`, icon: '⭐' },
                { id: 'sample', label: 'Sample Data', icon: '🔍' },
                { id: 'quality', label: 'Quality Score', icon: '🎯' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-6 font-medium text-sm transition-all duration-300 relative ${
                    activeTab === tab.id
                      ? 'text-cyan-400 bg-cyan-500/10 border-b-2 border-cyan-400'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <span className="flex items-center">
                    <span className="mr-2">{tab.icon}</span>
                    {tab.label}
                  </span>
                </button>
              ))}
            </nav>
          </div>

          {/* Enhanced Tab Content */}
          <div className="p-8">
            {activeTab === 'overview' && (
              <div className="space-y-8">
                {/* Enhanced Description */}
                <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                    <DocumentIcon className="h-6 w-6 mr-2 text-cyan-400" />
                    Description
                  </h3>
                  {(() => {
                    const { userDescription } = parseDescription(dataset.description);
                    return (
                      <p className="text-gray-300 leading-relaxed text-lg">
                        {userDescription || 'No description provided.'}
                      </p>
                    );
                  })()}
                </div>

                {/* Enhanced Dataset Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                      <TagIcon className="h-6 w-6 mr-2 text-cyan-400" />
                      Dataset Information
                    </h3>
                    {(() => {
                      const { additionalInfo } = parseDescription(dataset.description);
                      return (
                        <dl className="space-y-4">
                          <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                            <dt className="text-sm font-medium text-gray-400">Format</dt>
                            <dd className="text-sm text-white font-medium">
                              {additionalInfo?.data_format || dataset.data_format || dataset.file_type}
                            </dd>
                          </div>
                          <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                            <dt className="text-sm font-medium text-gray-400">Size</dt>
                            <dd className="text-sm text-white font-medium">
                              {additionalInfo?.data_size || `${formatFileSize(dataset.file_size)} (${dataset.file_type})`}
                            </dd>
                          </div>
                          <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                            <dt className="text-sm font-medium text-gray-400">License</dt>
                            <dd className="text-sm text-white font-medium">{dataset.license}</dd>
                          </div>
                          <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                            <dt className="text-sm font-medium text-gray-400">Privacy Level</dt>
                            <dd className="text-sm text-white font-medium capitalize">
                              {additionalInfo?.privacy_level || dataset.privacy_level}
                            </dd>
                          </div>
                          {additionalInfo?.collection_method && (
                            <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                              <dt className="text-sm font-medium text-gray-400">Collection Method</dt>
                              <dd className="text-sm text-white font-medium">{additionalInfo.collection_method}</dd>
                            </div>
                          )}
                          {additionalInfo?.sample_data && (
                            <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                              <dt className="text-sm font-medium text-gray-400">Sample Data</dt>
                              <dd className="text-sm text-white font-medium">{additionalInfo.sample_data}</dd>
                            </div>
                          )}
                        </dl>
                      );
                    })()}
                  </div>
                  
                  {/* Additional Stats Card */}
                  <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                      <ArrowDownTrayIcon className="h-6 w-6 mr-2 text-cyan-400" />
                      Usage Statistics
                    </h3>
                    <dl className="space-y-4">
                      <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                        <dt className="text-sm font-medium text-gray-400">Downloads</dt>
                        <dd className="text-sm text-white font-medium">{dataset.download_count}</dd>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                        <dt className="text-sm font-medium text-gray-400">Views</dt>
                        <dd className="text-sm text-white font-medium">{dataset.view_count}</dd>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                        <dt className="text-sm font-medium text-gray-400">Created</dt>
                        <dd className="text-sm text-white font-medium">{new Date(dataset.created_at).toLocaleDateString()}</dd>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-black/20 rounded-lg border border-gray-600/30">
                        <dt className="text-sm font-medium text-gray-400">Status</dt>
                        <dd className="text-sm text-green-400 font-medium capitalize">{dataset.status}</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'reviews' && (
              <div className="space-y-8">
                {/* Enhanced Review Stats */}
                {reviewStats && (
                  <div className="bg-black/20 backdrop-blur-sm rounded-2xl p-8 border border-purple-500/20">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                      {/* Overall Rating */}
                      <div className="text-center">
                        <div className="text-5xl font-black text-white mb-3">
                          {Number(reviewStats.average_rating || 0).toFixed(1)}
                        </div>
                        <div className="flex items-center justify-center mb-3">
                          {renderStars(reviewStats.average_rating)}
                        </div>
                        <div className="text-gray-300 font-medium">
                          {reviewStats.total_reviews} reviews
                        </div>
                        <div className="mt-2 text-sm text-cyan-400">
                          {Number(reviewStats.verified_percentage || 0).toFixed(0)}% verified purchases
                        </div>
                      </div>

                      {/* Enhanced Rating Distribution */}
                      <div className="col-span-2">
                        <h4 className="font-bold text-white mb-6 text-xl">Rating Distribution</h4>
                        <div className="space-y-3">
                          {[5, 4, 3, 2, 1].map((rating) => {
                            const count = reviewStats.rating_distribution[rating] || 0;
                            const percentage = reviewStats.total_reviews > 0 
                              ? (count / reviewStats.total_reviews) * 100 
                              : 0;
                            
                            return (
                              <div key={rating} className="flex items-center">
                                <span className="text-white font-medium w-12 flex items-center">
                                  {rating}
                                  <StarIcon className="h-4 w-4 text-yellow-400 ml-1" />
                                </span>
                                <div className="flex-1 mx-4 bg-gray-700 rounded-full h-3 overflow-hidden">
                                  <div 
                                    className="bg-gradient-to-r from-yellow-400 to-orange-400 h-3 rounded-full transition-all duration-500" 
                                    style={{ width: `${percentage}%` }}
                                  ></div>
                                </div>
                                <span className="text-gray-300 font-medium w-16 text-right">
                                  {count} ({Number(percentage || 0).toFixed(0)}%)
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Enhanced Review Filters */}
                <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <div className="flex flex-wrap gap-4 items-center justify-between">
                    <div className="flex flex-wrap gap-4">
                      {/* Rating Filter */}
                      <select
                        value={reviewFilters.rating}
                        onChange={(e) => setReviewFilters(prev => ({ ...prev, rating: e.target.value }))}
                        className="bg-black/30 border border-gray-600 rounded-lg px-4 py-2 text-white text-sm focus:border-cyan-400 focus:outline-none"
                      >
                        <option value="">All Ratings</option>
                        <option value="5">5 Stars</option>
                        <option value="4">4 Stars</option>
                        <option value="3">3 Stars</option>
                        <option value="2">2 Stars</option>
                        <option value="1">1 Star</option>
                      </select>

                      {/* Verified Filter */}
                      <label className="flex items-center bg-black/30 border border-gray-600 rounded-lg px-4 py-2 cursor-pointer hover:border-cyan-400 transition-colors">
                        <input
                          type="checkbox"
                          checked={reviewFilters.verified_only}
                          onChange={(e) => setReviewFilters(prev => ({ ...prev, verified_only: e.target.checked }))}
                          className="mr-3 w-4 h-4 text-cyan-400 bg-black/30 border-gray-600 rounded focus:ring-cyan-400"
                        />
                        <span className="text-sm text-gray-300">Verified purchases only</span>
                      </label>

                      {/* Sort Filter */}
                      <select
                        value={reviewFilters.sort_by}
                        onChange={(e) => setReviewFilters(prev => ({ ...prev, sort_by: e.target.value }))}
                        className="bg-black/30 border border-gray-600 rounded-lg px-4 py-2 text-white text-sm focus:border-cyan-400 focus:outline-none"
                      >
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="highest_rated">Highest Rated</option>
                        <option value="lowest_rated">Lowest Rated</option>
                        <option value="most_helpful">Most Helpful</option>
                      </select>
                    </div>

                    {/* Add Review Button */}
                    {isAuthenticated && (
                      <button
                        onClick={() => setShowAddReview(true)}
                        className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 py-2 rounded-lg font-medium hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
                      >
                        ✍️ Write a Review
                      </button>
                    )}
                  </div>
                </div>

                {/* Enhanced Reviews List */}
                <div className="space-y-6">
                  {reviews.length > 0 ? (
                    reviews.map((review) => (
                      <div key={review.id} className="bg-black/20 backdrop-blur-sm border border-purple-500/20 rounded-2xl p-6 hover:border-cyan-400/30 transition-all duration-300">
                        {/* Enhanced Review Header */}
                        <div className="flex items-start justify-between mb-6">
                          <div className="flex items-center">
                            <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-full flex items-center justify-center mr-4">
                              <UserIcon className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <div className="flex items-center">
                                <span className="font-bold text-white text-lg">{review.reviewer.username}</span>
                                {review.is_verified_purchase && (
                                  <span className="ml-3 px-3 py-1 text-xs bg-green-500/20 text-green-300 rounded-full border border-green-400/30 flex items-center">
                                    <ShieldCheckIcon className="h-3 w-3 mr-1" />
                                    Verified Purchase
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-gray-400 mt-1">
                                {new Date(review.created_at).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center mb-2">
                              {renderStars(review.rating)}
                            </div>
                            <div className="text-cyan-400 font-bold text-lg">
                              {review.rating}.0
                            </div>
                          </div>
                        </div>

                        {/* Enhanced Review Content */}
                        <div className="mb-6">
                          <h4 className="font-bold text-white text-xl mb-3">{review.title}</h4>
                          <p className="text-gray-300 leading-relaxed text-lg bg-black/20 p-4 rounded-xl border border-gray-600/30">
                            {review.comment}
                          </p>
                        </div>

                        {/* Enhanced Review Actions */}
                        <div className="flex items-center justify-between pt-4 border-t border-purple-500/20">
                          <div className="flex items-center space-x-4">
                            {/* Helpful Button */}
                            <button
                              onClick={() => handleMarkHelpful(review.id, true)}
                              className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                                review.is_helpful_by_user 
                                  ? 'bg-green-500/20 text-green-300 border border-green-400/30' 
                                  : 'bg-black/20 text-gray-400 border border-gray-600/30 hover:border-green-400/50 hover:text-green-300'
                              }`}
                              disabled={!isAuthenticated}
                            >
                              👍 Helpful ({review.helpful_count})
                            </button>
                            
                            {review.can_report && (
                              <button
                                onClick={() => handleReportReview(review.id, 'inappropriate', 'Inappropriate content')}
                                className="px-4 py-2 rounded-lg bg-black/20 text-gray-400 border border-gray-600/30 hover:border-red-400/50 hover:text-red-300 transition-all duration-300"
                              >
                                🚨 Report
                              </button>
                            )}
                          </div>

                          {/* Edit Button for Own Reviews */}
                          {review.can_edit && (
                            <button className="px-4 py-2 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-400/30 hover:bg-cyan-500/30 transition-all duration-300">
                              ✏️ Edit Review
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-16 bg-black/20 backdrop-blur-sm rounded-2xl border border-purple-500/20">
                      <div className="text-gray-400 mb-6">
                        <StarIcon className="h-16 w-16 mx-auto text-purple-400" />
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-4">No reviews yet</h3>
                      <p className="text-gray-300 mb-8 text-lg">Be the first to review this dataset!</p>
                      {isAuthenticated && (
                        <button
                          onClick={() => setShowAddReview(true)}
                          className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
                        >
                          Write the First Review
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'sample' && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h3 className="text-3xl font-bold text-white mb-2">Dataset Preview</h3>
                  <p className="text-gray-300">Explore the structure and sample data</p>
                </div>
                
                {loadingPreview ? (
                  <div className="flex flex-col items-center justify-center py-16 bg-black/20 backdrop-blur-sm rounded-2xl border border-purple-500/20">
                    <div className="animate-spin rounded-full h-12 w-12 border-2 border-cyan-400 border-t-transparent mb-4"></div>
                    <span className="text-white font-medium text-lg">Loading preview...</span>
                  </div>
                ) : previewData ? (
                  <div className="space-y-8">
                    {/* Enhanced File Information */}
                    <div className="bg-black/20 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                      <h4 className="font-bold text-white text-xl mb-6 flex items-center">
                        <DocumentIcon className="h-6 w-6 mr-2 text-cyan-400" />
                        File Information
                      </h4>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="bg-black/30 rounded-xl p-4 border border-gray-600/30">
                          <div className="text-gray-400 text-sm mb-1">Rows</div>
                          <div className="text-white font-bold text-2xl">{previewData.statistics?.total_rows || 'N/A'}</div>
                        </div>
                        <div className="bg-black/30 rounded-xl p-4 border border-gray-600/30">
                          <div className="text-gray-400 text-sm mb-1">Columns</div>
                          <div className="text-white font-bold text-2xl">{previewData.statistics?.total_columns || 'N/A'}</div>
                        </div>
                        <div className="bg-black/30 rounded-xl p-4 border border-gray-600/30">
                          <div className="text-gray-400 text-sm mb-1">Size</div>
                          <div className="text-white font-bold text-2xl">{previewData.file_info?.size_human || 'N/A'}</div>
                        </div>
                        <div className="bg-black/30 rounded-xl p-4 border border-gray-600/30">
                          <div className="text-gray-400 text-sm mb-1">Type</div>
                          <div className="text-cyan-400 font-bold text-2xl">{previewData.file_info?.type || 'N/A'}</div>
                        </div>
                      </div>
                    </div>

                    {/* Enhanced Data Preview Table */}
                    {previewData.sample_data?.data && previewData.sample_data.data.length > 0 ? (
                      <div className="bg-black/20 backdrop-blur-sm border border-purple-500/20 rounded-2xl overflow-hidden">
                        <div className="px-6 py-4 bg-black/30 border-b border-purple-500/20">
                          <h4 className="font-bold text-white text-xl flex items-center">
                            <TagIcon className="h-6 w-6 mr-2 text-cyan-400" />
                            Sample Data (First {previewData.sample_data.total_rows_preview} rows)
                          </h4>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full">
                            <thead className="bg-black/30">
                              <tr>
                                {previewData.sample_data.columns.map((column: string, index: number) => (
                                  <th key={index} className="px-4 py-4 text-left">
                                    <div>
                                      <div className="font-bold text-white">{column}</div>
                                      <div className="text-xs text-cyan-400 mt-1">
                                        {previewData.sample_data.data_types?.[column] || 'unknown'}
                                      </div>
                                    </div>
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {previewData.sample_data.data.slice(0, 10).map((row: any, rowIndex: number) => (
                                <tr key={rowIndex} className={`border-b border-gray-600/30 ${rowIndex % 2 === 0 ? 'bg-black/10' : 'bg-black/20'} hover:bg-black/30 transition-colors`}>
                                  {previewData.sample_data.columns.map((column: string, colIndex: number) => (
                                    <td key={colIndex} className="px-4 py-3 text-sm text-gray-300 max-w-xs truncate">
                                      {row[column] !== null && row[column] !== undefined ? String(row[column]) : <span className="text-gray-500">-</span>}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12 bg-black/20 backdrop-blur-sm rounded-2xl border border-purple-500/20">
                        <DocumentIcon className="h-12 w-12 text-purple-400 mx-auto mb-4" />
                        <p className="text-gray-300 text-lg">No preview data available</p>
                      </div>
                    )}

                    {/* Column Statistics */}
                    {previewData.statistics?.numeric_statistics && Object.keys(previewData.statistics.numeric_statistics).length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">Numeric Column Statistics</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-200">
                                <th className="text-left py-2 font-medium text-gray-900">Column</th>
                                <th className="text-right py-2 font-medium text-gray-900">Mean</th>
                                <th className="text-right py-2 font-medium text-gray-900">Median</th>
                                <th className="text-right py-2 font-medium text-gray-900">Min</th>
                                <th className="text-right py-2 font-medium text-gray-900">Max</th>
                                <th className="text-right py-2 font-medium text-gray-900">Unique</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(previewData.statistics.numeric_statistics).map(([column, stats]: [string, any]) => (
                                <tr key={column} className="border-b border-gray-100">
                                  <td className="py-2 font-medium text-gray-900">{column}</td>
                                  <td className="py-2 text-right text-gray-600">{stats.mean?.toFixed(2) || 'N/A'}</td>
                                  <td className="py-2 text-right text-gray-600">{stats.median?.toFixed(2) || 'N/A'}</td>
                                  <td className="py-2 text-right text-gray-600">{stats.min?.toFixed(2) || 'N/A'}</td>
                                  <td className="py-2 text-right text-gray-600">{stats.max?.toFixed(2) || 'N/A'}</td>
                                  <td className="py-2 text-right text-gray-600">{stats.unique_count || 'N/A'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-16 bg-black/20 backdrop-blur-sm rounded-2xl border border-purple-500/20">
                    <DocumentIcon className="h-16 w-16 text-purple-400 mx-auto mb-6" />
                    <h3 className="text-2xl font-bold text-white mb-4">Preview Not Available</h3>
                    <p className="text-gray-300 text-lg mb-6">Purchase this dataset to view a preview of the data</p>
                    <button 
                      onClick={() => setShowPurchaseModal(true)}
                      className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
                    >
                      Purchase Dataset
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'quality' && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h3 className="text-3xl font-bold text-white mb-2">Data Quality Assessment</h3>
                  <p className="text-gray-300">AI-powered quality analysis and scoring</p>
                </div>
                
                {loadingQuality ? (
                  <div className="flex flex-col items-center justify-center py-16 bg-black/20 backdrop-blur-sm rounded-2xl border border-purple-500/20">
                    <div className="animate-spin rounded-full h-12 w-12 border-2 border-cyan-400 border-t-transparent mb-4"></div>
                    <span className="text-white font-medium text-lg">Analyzing quality...</span>
                  </div>
                ) : qualityScore ? (
                  <div className="space-y-8">
                    {/* Enhanced Overall Quality Score */}
                    <div className="bg-gradient-to-r from-purple-600/20 via-cyan-600/20 to-pink-600/20 backdrop-blur-sm rounded-2xl p-8 border border-purple-500/20 relative overflow-hidden">
                      <div className="absolute inset-0 bg-black/20"></div>
                      <div className="relative text-center">
                        <div className="text-6xl font-black text-white mb-4">
                          {qualityScore.overall_score}%
                        </div>
                        <div className="text-2xl font-bold text-white mb-2">Overall Quality Score</div>
                        <div className={`text-lg font-medium px-4 py-2 rounded-full inline-block ${
                          qualityScore.overall_score >= 80 ? 'bg-green-500/20 text-green-300 border border-green-400/30' : 
                          qualityScore.overall_score >= 60 ? 'bg-blue-500/20 text-blue-300 border border-blue-400/30' : 
                          qualityScore.overall_score >= 40 ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-400/30' : 
                          'bg-red-500/20 text-red-300 border border-red-400/30'
                        }`}>
                          {qualityScore.overall_score >= 80 ? '🌟 Excellent' : 
                           qualityScore.overall_score >= 60 ? '👍 Good' : 
                           qualityScore.overall_score >= 40 ? '⚠️ Fair' : '❌ Needs Improvement'}
                        </div>
                      </div>
                    </div>

                    {/* Quality Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {/* Completeness */}
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium text-gray-900">Completeness</h4>
                          <span className="text-lg font-bold text-green-600">{qualityScore.completeness}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{ width: `${qualityScore.completeness}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-600">Percentage of non-missing values</p>
                      </div>

                      {/* Consistency */}
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium text-gray-900">Consistency</h4>
                          <span className="text-lg font-bold text-blue-600">{qualityScore.consistency}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${qualityScore.consistency}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-600">Data type uniformity and structure</p>
                      </div>

                      {/* Richness */}
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium text-gray-900">Richness</h4>
                          <span className="text-lg font-bold text-purple-600">{qualityScore.richness}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div 
                            className="bg-purple-500 h-2 rounded-full" 
                            style={{ width: `${qualityScore.richness}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-600">Variety of data types and features</p>
                      </div>
                    </div>

                    {/* Detailed Statistics */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-4">Detailed Analysis</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Total Rows:</span>
                          <span className="ml-2 font-medium">{qualityScore.total_rows?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Total Columns:</span>
                          <span className="ml-2 font-medium">{qualityScore.total_columns}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Missing Values:</span>
                          <span className="ml-2 font-medium">{qualityScore.missing_values_count?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Data Types:</span>
                          <span className="ml-2 font-medium">{qualityScore.data_types_variety}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 bg-gray-50 rounded-lg">
                    <ShieldCheckIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">Quality analysis not available</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Purchase Modal */}
      {showPurchaseModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Purchase Dataset
            </h3>
            
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Dataset:</span>
                <span className="font-medium">{dataset.title}</span>
              </div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-gray-600">Price:</span>
                <span className="text-2xl font-bold text-primary-600">
                  {formatPrice(dataset.price)} NRC
                </span>
              </div>
              
              {!isConnected && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
                    <span className="text-sm text-yellow-800">
                      Please connect your wallet to complete the purchase
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowPurchaseModal(false)}
                className="btn-outline flex-1"
              >
                Cancel
              </button>
              <button
                onClick={handlePurchase}
                disabled={purchasing || !isConnected}
                className="btn-primary flex-1 disabled:opacity-50"
              >
                {purchasing ? 'Processing...' : 'Purchase'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dispute Modal */}
      {showDisputeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Open Dispute
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Please provide a detailed reason for disputing this transaction. This will be reviewed by our validators.
            </p>
            <textarea
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              placeholder="Describe the issue with this dataset or transaction..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none h-32 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              maxLength={500}
            />
            <p className="text-xs text-gray-500 mt-1 mb-4">
              {disputeReason.length}/500 characters
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDisputeModal(false);
                  setDisputeReason('');
                }}
                className="btn-outline flex-1"
              >
                Cancel
              </button>
              <button
                onClick={handleDispute}
                disabled={!disputeReason.trim()}
                className="btn-error flex-1 disabled:opacity-50"
              >
                Submit Dispute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && confirmAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {confirmAction.title}
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              {confirmAction.message}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowConfirmModal(false);
                  setConfirmAction(null);
                }}
                className="btn-outline flex-1"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmAction}
                className={confirmAction.type === 'confirm' ? 'btn-success flex-1' : 'btn-secondary flex-1'}
              >
                {confirmAction.type === 'confirm' ? 'Confirm Receipt' : 'Release Funds'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Review Modal */}
      {showAddReview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Write a Review
            </h3>
            
            <div className="space-y-4">
              {/* Rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rating *
                </label>
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setReviewForm(prev => ({ ...prev, rating: star }))}
                      className={`text-2xl ${
                        star <= reviewForm.rating ? 'text-yellow-400' : 'text-gray-300'
                      } hover:text-yellow-400 transition-colors`}
                    >
                      ★
                    </button>
                  ))}
                  <span className="ml-2 text-sm text-gray-600">
                    ({reviewForm.rating}/5)
                  </span>
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Review Title *
                </label>
                <input
                  type="text"
                  value={reviewForm.title}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Summarize your experience..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  maxLength={200}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {reviewForm.title.length}/200 characters
                </div>
              </div>

              {/* Comment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Review *
                </label>
                <textarea
                  value={reviewForm.comment}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, comment: e.target.value }))}
                  placeholder="Share your detailed experience with this dataset..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  maxLength={2000}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {reviewForm.comment.length}/2000 characters (minimum 10)
                </div>
              </div>

              {/* Guidelines */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Review Guidelines</h4>
                <ul className="text-xs text-blue-800 space-y-1">
                  <li>• Be honest and constructive in your feedback</li>
                  <li>• Focus on the dataset quality, accuracy, and usefulness</li>
                  <li>• Avoid inappropriate language or personal attacks</li>
                  <li>• Your review will be automatically filtered for quality</li>
                </ul>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAddReview(false);
                  setReviewForm({ rating: 5, title: '', comment: '' });
                }}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                disabled={submittingReview}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitReview}
                disabled={submittingReview || reviewForm.title.length < 3 || reviewForm.comment.length < 10}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submittingReview ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </div>
                ) : (
                  'Submit Review'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetDetailPage;
