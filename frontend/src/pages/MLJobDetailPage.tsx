import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  BeakerIcon,
  ChartBarIcon,
  ClockIcon,
  CpuChipIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  EyeIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CloudArrowDownIcon
} from '@heroicons/react/24/outline';
import { api } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface TrainingJob {
  id: string;
  name: string;
  description: string;
  user_email: string;
  algorithm: number;
  algorithm_name: string;
  dataset: string;
  dataset_title: string;
  parameters: any;
  train_test_split: number;
  random_seed: number;
  max_runtime_hours: number;
  memory_limit_mb: number;
  cpu_cores: number;
  use_gpu: boolean;
  status: 'created' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  progress_percentage: number;
  model_file: string;
  model_metrics: any;
  training_logs: string;
  actual_runtime_seconds: number;
  peak_memory_usage_mb: number;
  estimated_cost: string;
  actual_cost: string;
  error_message: string;
  runtime_hours: number;
  is_running: boolean;
  is_completed: boolean;
  created_at: string;
  started_at: string;
  completed_at: string;
}

const MLJobDetailPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<TrainingJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [showModelDetails, setShowModelDetails] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId]);

  useEffect(() => {
    // Auto-refresh for running jobs
    if (job?.is_running) {
      const interval = setInterval(() => {
        fetchJobDetails();
      }, 5000); // Refresh every 5 seconds
      setRefreshInterval(interval);
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [job?.is_running]);

  const fetchJobDetails = async () => {
    try {
      const response = await api.get(`/ml/jobs/${jobId}/`);
      setJob(response.data);
    } catch (error) {
      console.error('Error fetching job details:', error);
      toast.error('Failed to load job details');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await api.get(`/ml/jobs/${jobId}/logs/`);
      setLogs(response.data.logs || 'No logs available');
      setShowLogs(true);
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error('Failed to load logs');
    }
  };

  const handleDownloadModel = async () => {
    if (!job) {
      toast.error('Job information not available');
      return;
    }

    if (job.status !== 'completed') {
      toast.error('Job must be completed before downloading the model');
      return;
    }

    try {
      // Make API request to download model
      const response = await api.get(`/ml/jobs/${job.id}/download_model/`, {
        responseType: 'blob'
      });
      
      // Create blob URL and trigger download
      const blob = new Blob([response.data], { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${job.name}_model.pkl`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Model downloaded successfully');
    } catch (error: any) {
      console.error('Error downloading model:', error);
      if (error.response?.status === 404) {
        toast.error('Model file not found. It may have been deleted.');
      } else if (error.response?.status === 400) {
        toast.error('Job is not ready for download yet.');
      } else {
        toast.error('Failed to download model. Please try again.');
      }
    }
  };


  const handleCancelJob = async () => {
    if (!job) return;
    
    try {
      const response = await api.post(`/ml/jobs/${job.id}/cancel/`);
      
      if (response.data.success) {
        toast.success('Training job cancelled');
        fetchJobDetails();
      }
    } catch (error: any) {
      console.error('Error cancelling job:', error);
      toast.error(error.response?.data?.message || 'Failed to cancel job');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-6 w-6 text-green-600" />;
      case 'running':
        return <PlayIcon className="h-6 w-6 text-blue-600" />;
      case 'queued':
        return <ClockIcon className="h-6 w-6 text-yellow-600" />;
      case 'failed':
        return <XCircleIcon className="h-6 w-6 text-red-600" />;
      case 'cancelled':
        return <StopIcon className="h-6 w-6 text-gray-600" />;
      default:
        return <ExclamationTriangleIcon className="h-6 w-6 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'queued': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'cancelled': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatRuntime = (seconds: number | null | undefined): string => {
    if (!seconds || seconds === 0) return 'N/A';
    
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const formatMemory = (mb: number | null | undefined): string => {
    if (!mb || mb === 0) return 'N/A';
    
    if (mb < 1024) {
      return `${mb.toFixed(1)} MB`;
    } else {
      const gb = mb / 1024;
      return `${gb.toFixed(2)} GB`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <BeakerIcon className="h-12 w-12 text-gray-400 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Loading training job details...</p>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-600">Training job not found</p>
          <Link to="/ml/training" className="btn-primary mt-4">
            Back to ML Training
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Link
                to="/ml/training"
                className="mr-4 p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </Link>
              <div className="flex items-center">
                {getStatusIcon(job.status)}
                <div className="ml-3">
                  <h1 className="text-2xl font-bold text-gray-900">
                    {job.name}
                  </h1>
                  <p className="text-gray-600">
                    {job.algorithm_name} • {job.dataset_title}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 text-sm rounded-full font-medium ${getStatusColor(job.status)}`}>
                {job.status.toUpperCase()}
              </span>
              
              {job.is_running && (
                <button
                  onClick={handleCancelJob}
                  className="btn-error"
                >
                  <StopIcon className="h-4 w-4 mr-2" />
                  Cancel Job
                </button>
              )}
              
              <button
                onClick={fetchLogs}
                className="btn-outline"
              >
                <DocumentTextIcon className="h-4 w-4 mr-2" />
                View Logs
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Progress */}
            {(job.status === 'created' || job.status === 'queued' || job.status === 'running' || job.status === 'completed') && (
              <div className="card">
                <div className="card-header">
                  <h2 className="text-lg font-semibold flex items-center">
                    <BeakerIcon className="h-5 w-5 mr-2" />
                    Training Progress
                  </h2>
                </div>
                <div className="card-body">
                  {/* Progress Bar */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Progress</span>
                    <span className="text-sm text-gray-600">{job.progress_percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                    <div 
                      className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500 relative overflow-hidden"
                      style={{ width: `${job.progress_percentage}%` }}
                    >
                      {job.status === 'running' && (
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
                      )}
                    </div>
                  </div>
                  
                  {/* Training Stages */}
                  <div className="space-y-3">
                    {/* Stage 1: Queue */}
                    <div className={`flex items-center space-x-3 ${
                      job.status === 'created' ? 'text-yellow-600' : 
                      job.status === 'queued' ? 'text-blue-600' : 'text-green-600'
                    }`}>
                      <div className={`w-3 h-3 rounded-full ${
                        job.status === 'created' ? 'bg-yellow-500 animate-pulse' :
                        job.status === 'queued' ? 'bg-blue-500 animate-pulse' : 'bg-green-500'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {job.status === 'created' ? 'Job Created' : 
                         job.status === 'queued' ? 'In Queue (Position in queue)' : 'Queued ✓'}
                      </span>
                    </div>
                    
                    {/* Stage 2: Data Loading */}
                    <div className={`flex items-center space-x-3 ${
                      job.status === 'running' && job.progress_percentage >= 10 ? 'text-blue-600' :
                      job.status === 'running' && job.progress_percentage < 10 ? 'text-yellow-600' :
                      job.status === 'completed' ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      <div className={`w-3 h-3 rounded-full ${
                        job.status === 'running' && job.progress_percentage >= 10 ? 'bg-blue-500' :
                        job.status === 'running' && job.progress_percentage < 10 ? 'bg-yellow-500 animate-pulse' :
                        job.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {job.status === 'running' && job.progress_percentage < 10 ? 'Loading Dataset...' :
                         job.status === 'running' && job.progress_percentage >= 10 ? 'Dataset Loaded ✓' :
                         job.status === 'completed' ? 'Dataset Loaded ✓' : 'Load Dataset'}
                      </span>
                    </div>
                    
                    {/* Stage 3: Data Preprocessing */}
                    <div className={`flex items-center space-x-3 ${
                      job.status === 'running' && job.progress_percentage >= 30 ? 'text-blue-600' :
                      job.status === 'running' && job.progress_percentage >= 10 && job.progress_percentage < 30 ? 'text-yellow-600' :
                      job.status === 'completed' ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      <div className={`w-3 h-3 rounded-full ${
                        job.status === 'running' && job.progress_percentage >= 30 ? 'bg-blue-500' :
                        job.status === 'running' && job.progress_percentage >= 10 && job.progress_percentage < 30 ? 'bg-yellow-500 animate-pulse' :
                        job.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {job.status === 'running' && job.progress_percentage >= 10 && job.progress_percentage < 30 ? 'Preprocessing Data...' :
                         job.status === 'running' && job.progress_percentage >= 30 ? 'Data Preprocessed ✓' :
                         job.status === 'completed' ? 'Data Preprocessed ✓' : 'Preprocess Data'}
                      </span>
                    </div>
                    
                    {/* Stage 4: Model Training */}
                    <div className={`flex items-center space-x-3 ${
                      job.status === 'running' && job.progress_percentage >= 80 ? 'text-blue-600' :
                      job.status === 'running' && job.progress_percentage >= 30 && job.progress_percentage < 80 ? 'text-yellow-600' :
                      job.status === 'completed' ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      <div className={`w-3 h-3 rounded-full ${
                        job.status === 'running' && job.progress_percentage >= 80 ? 'bg-blue-500' :
                        job.status === 'running' && job.progress_percentage >= 30 && job.progress_percentage < 80 ? 'bg-yellow-500 animate-pulse' :
                        job.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {job.status === 'running' && job.progress_percentage >= 30 && job.progress_percentage < 80 ? 'Training Model...' :
                         job.status === 'running' && job.progress_percentage >= 80 ? 'Model Trained ✓' :
                         job.status === 'completed' ? 'Model Trained ✓' : 'Train Model'}
                      </span>
                    </div>
                    
                    {/* Stage 5: Saving Results */}
                    <div className={`flex items-center space-x-3 ${
                      job.status === 'completed' ? 'text-green-600' :
                      job.status === 'running' && job.progress_percentage >= 80 ? 'text-yellow-600' : 'text-gray-400'
                    }`}>
                      <div className={`w-3 h-3 rounded-full ${
                        job.status === 'completed' ? 'bg-green-500' :
                        job.status === 'running' && job.progress_percentage >= 80 ? 'bg-yellow-500 animate-pulse' : 'bg-gray-300'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {job.status === 'completed' ? 'Results Saved ✓' :
                         job.status === 'running' && job.progress_percentage >= 80 ? 'Saving Results...' : 'Save Results'}
                      </span>
                    </div>
                  </div>
                  
                  {/* Status Message */}
                  <div className={`mt-4 p-3 rounded-lg border ${
                    job.status === 'completed' ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'
                  }`}>
                    <p className={`text-sm ${
                      job.status === 'completed' ? 'text-green-800' : 'text-blue-800'
                    }`}>
                      {job.status === 'created' && '🚀 Job created successfully! Waiting to be queued...'}
                      {job.status === 'queued' && '⏳ Job is queued and waiting for available resources...'}
                      {job.status === 'running' && '🔥 Training in progress! This page will update automatically.'}
                      {job.status === 'completed' && '✅ Training completed successfully! Your model is ready.'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Model Metrics */}
            {job.model_metrics && Object.keys(job.model_metrics).length > 0 && (
              <div className="card">
                <div className="card-header">
                  <h2 className="text-lg font-semibold flex items-center">
                    <ChartBarIcon className="h-5 w-5 mr-2" />
                    Model Performance
                  </h2>
                </div>
                <div className="card-body">
                  {/* Visualization */}
                  {job.model_metrics.visualization && (
                    <div className="mb-6">
                      <img 
                        src={`data:image/png;base64,${job.model_metrics.visualization}`}
                        alt="Training Results Visualization"
                        className="w-full max-w-2xl mx-auto rounded-lg shadow-sm"
                      />
                    </div>
                  )}
                  
                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {job.model_metrics.accuracy && (
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {(job.model_metrics.accuracy * 100).toFixed(2)}%
                        </div>
                        <div className="text-sm text-green-700">Accuracy</div>
                      </div>
                    )}
                    
                    {job.model_metrics.precision && (
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {(job.model_metrics.precision * 100).toFixed(2)}%
                        </div>
                        <div className="text-sm text-blue-700">Precision</div>
                      </div>
                    )}
                    
                    {job.model_metrics.recall && (
                      <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {(job.model_metrics.recall * 100).toFixed(2)}%
                        </div>
                        <div className="text-sm text-purple-700">Recall</div>
                      </div>
                    )}
                    
                    {job.model_metrics.f1_score && (
                      <div className="text-center p-4 bg-orange-50 rounded-lg">
                        <div className="text-2xl font-bold text-orange-600">
                          {(job.model_metrics.f1_score * 100).toFixed(2)}%
                        </div>
                        <div className="text-sm text-orange-700">F1-Score</div>
                      </div>
                    )}
                    
                    {job.model_metrics.mse && (
                      <div className="text-center p-4 bg-red-50 rounded-lg">
                        <div className="text-2xl font-bold text-red-600">
                          {job.model_metrics.mse.toFixed(4)}
                        </div>
                        <div className="text-sm text-red-700">MSE</div>
                      </div>
                    )}
                    
                    {job.model_metrics.r2_score && (
                      <div className="text-center p-4 bg-indigo-50 rounded-lg">
                        <div className="text-2xl font-bold text-indigo-600">
                          {job.model_metrics.r2_score.toFixed(4)}
                        </div>
                        <div className="text-sm text-indigo-700">R² Score</div>
                      </div>
                    )}
                    
                    {job.model_metrics.silhouette_score && (
                      <div className="text-center p-4 bg-teal-50 rounded-lg">
                        <div className="text-2xl font-bold text-teal-600">
                          {job.model_metrics.silhouette_score.toFixed(4)}
                        </div>
                        <div className="text-sm text-teal-700">Silhouette Score</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Error Message */}
            {job.status === 'failed' && job.error_message && (
              <div className="card border-red-200">
                <div className="card-header bg-red-50">
                  <h2 className="text-lg font-semibold text-red-900 flex items-center">
                    <XCircleIcon className="h-5 w-5 mr-2" />
                    Training Failed
                  </h2>
                </div>
                <div className="card-body">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-800 font-medium mb-2">Error Details:</p>
                    <p className="text-red-700 text-sm font-mono">
                      {job.error_message}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Job Configuration */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold">Configuration</h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Training Parameters</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Train/Test Split:</span>
                        <span className="font-medium">{(job.train_test_split * 100).toFixed(0)}% / {((1 - job.train_test_split) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Random Seed:</span>
                        <span className="font-medium">{job.random_seed}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Priority:</span>
                        <span className="font-medium capitalize">{job.priority}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Resource Allocation</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">CPU Cores:</span>
                        <span className="font-medium">{job.cpu_cores}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Memory Limit:</span>
                        <span className="font-medium">{formatMemory(job.memory_limit_mb)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">GPU Enabled:</span>
                        <span className="font-medium">{job.use_gpu ? 'Yes' : 'No'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Max Runtime:</span>
                        <span className="font-medium">{job.max_runtime_hours}h</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Algorithm Parameters */}
                {job.parameters && Object.keys(job.parameters).length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-medium text-gray-900 mb-3">Algorithm Parameters</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <pre className="text-sm text-gray-700 overflow-x-auto">
                        {JSON.stringify(job.parameters, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Job Stats */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold">Job Statistics</h2>
              </div>
              <div className="card-body space-y-4">
                <div className="flex items-center">
                  <ClockIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-600">Runtime</div>
                    <div className="font-medium">{formatRuntime(job.actual_runtime_seconds)}</div>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <CurrencyDollarIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-600">Cost</div>
                    <div className="font-medium">
                      {job.actual_cost ? `${parseFloat(job.actual_cost).toFixed(6)} NRC` : 'Calculating...'}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <CpuChipIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-600">Peak Memory</div>
                    <div className="font-medium">{formatMemory(job.peak_memory_usage_mb)}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold">Timeline</h2>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                    <div className="ml-3">
                      <div className="text-sm font-medium">Created</div>
                      <div className="text-xs text-gray-600">
                        {new Date(job.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  
                  {job.started_at && (
                    <div className="flex items-start">
                      <div className="flex-shrink-0 w-2 h-2 bg-blue-400 rounded-full mt-2"></div>
                      <div className="ml-3">
                        <div className="text-sm font-medium">Started</div>
                        <div className="text-xs text-gray-600">
                          {new Date(job.started_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {job.completed_at && (
                    <div className="flex items-start">
                      <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                        job.status === 'completed' ? 'bg-green-400' : 'bg-red-400'
                      }`}></div>
                      <div className="ml-3">
                        <div className="text-sm font-medium">
                          {job.status === 'completed' ? 'Completed' : 'Failed'}
                        </div>
                        <div className="text-xs text-gray-600">
                          {new Date(job.completed_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            {job.status === 'completed' && (
              <div className="card">
                <div className="card-header">
                  <h2 className="text-lg font-semibold">Actions</h2>
                </div>
                <div className="card-body space-y-3">
                  <button 
                    onClick={handleDownloadModel}
                    className="btn-primary w-full flex items-center justify-center"
                  >
                    <CloudArrowDownIcon className="h-4 w-4 mr-2" />
                    Download Model
                  </button>
                  <button 
                    onClick={() => setShowModelDetails(true)}
                    className="btn-outline w-full flex items-center justify-center"
                  >
                    <EyeIcon className="h-4 w-4 mr-2" />
                    View Model Details
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Logs Modal */}
      {showLogs && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">Training Logs</h2>
              <button
                onClick={() => setShowLogs(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-96">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded-lg">
                {logs || 'No logs available yet.'}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Model Details Modal */}
      {showModelDetails && job && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">Model Details</h2>
              <button
                onClick={() => setShowModelDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-96">
              <div className="space-y-6">
                {/* Model Information */}
                <div>
                  <h3 className="text-md font-semibold text-gray-900 mb-3">Model Information</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-sm font-medium text-gray-600">Algorithm:</span>
                        <p className="text-sm text-gray-900">{job.algorithm_name}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">Model File:</span>
                        <p className="text-sm text-gray-900">{job.model_file || 'Not available'}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">Training Dataset:</span>
                        <p className="text-sm text-gray-900">{job.dataset_title}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">Training Time:</span>
                        <p className="text-sm text-gray-900">{formatRuntime(job.actual_runtime_seconds)}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Training Parameters */}
                <div>
                  <h3 className="text-md font-semibold text-gray-900 mb-3">Training Parameters</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-sm font-medium text-gray-600">Train/Test Split:</span>
                        <p className="text-sm text-gray-900">{(job.train_test_split * 100).toFixed(0)}% / {((1 - job.train_test_split) * 100).toFixed(0)}%</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">Random Seed:</span>
                        <p className="text-sm text-gray-900">{job.random_seed}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">CPU Cores:</span>
                        <p className="text-sm text-gray-900">{job.cpu_cores}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">Memory Limit:</span>
                        <p className="text-sm text-gray-900">{(job.memory_limit_mb / 1024).toFixed(2)} GB</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Model Performance Metrics */}
                {job.model_metrics && Object.keys(job.model_metrics).length > 0 && (
                  <div>
                    <h3 className="text-md font-semibold text-gray-900 mb-3">Performance Metrics</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {job.model_metrics.accuracy && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-green-600">
                              {(job.model_metrics.accuracy * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-gray-600">Accuracy</div>
                          </div>
                        )}
                        {job.model_metrics.precision && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-blue-600">
                              {(job.model_metrics.precision * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-gray-600">Precision</div>
                          </div>
                        )}
                        {job.model_metrics.recall && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">
                              {(job.model_metrics.recall * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-gray-600">Recall</div>
                          </div>
                        )}
                        {job.model_metrics.f1_score && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-orange-600">
                              {(job.model_metrics.f1_score * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-gray-600">F1-Score</div>
                          </div>
                        )}
                        {job.model_metrics.mse && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-red-600">
                              {job.model_metrics.mse.toFixed(4)}
                            </div>
                            <div className="text-xs text-gray-600">MSE</div>
                          </div>
                        )}
                        {job.model_metrics.r2_score && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-indigo-600">
                              {job.model_metrics.r2_score.toFixed(4)}
                            </div>
                            <div className="text-xs text-gray-600">R² Score</div>
                          </div>
                        )}
                        {job.model_metrics.silhouette_score && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-teal-600">
                              {job.model_metrics.silhouette_score.toFixed(4)}
                            </div>
                            <div className="text-xs text-gray-600">Silhouette Score</div>
                          </div>
                        )}
                        {job.model_metrics.n_clusters && (
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">
                              {job.model_metrics.n_clusters}
                            </div>
                            <div className="text-xs text-gray-600">Clusters</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Model Parameters */}
                {job.parameters && Object.keys(job.parameters).length > 0 && (
                  <div>
                    <h3 className="text-md font-semibold text-gray-900 mb-3">Model Parameters</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <pre className="text-sm text-gray-700 overflow-x-auto">
                        {JSON.stringify(job.parameters, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MLJobDetailPage;
