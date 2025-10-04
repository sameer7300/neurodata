import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CpuChipIcon,
  BeakerIcon,
  ChartBarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  PlayIcon,
  StopIcon,
  EyeIcon,
  DocumentTextIcon,
  AcademicCapIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { api } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface MLAlgorithm {
  id: number;
  name: string;
  slug: string;
  algorithm_type: 'classification' | 'regression' | 'clustering' | 'dimensionality_reduction' | 'deep_learning';
  description: string;
  library: string;
  class_name: string;
  parameters_schema: any;
  default_parameters: any;
  min_memory_mb: number;
  min_cpu_cores: number;
  supports_gpu: boolean;
  cost_per_hour: string;
  is_active: boolean;
  created_at: string;
}

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

interface Dataset {
  id: string;
  title: string;
  slug: string;
  description: string;
  file_type: string;
  file_size_human: string;
}

const MLTrainingPage: React.FC = () => {
    const navigate = useNavigate();
  const [algorithms, setAlgorithms] = useState<MLAlgorithm[]>([]);
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingJob, setCreatingJob] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<MLAlgorithm | null>(null);
  const [algorithmType, setAlgorithmType] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    algorithm: '',
    dataset: '',
    parameters: {},
    train_test_split: 0.8,
    random_seed: 42,
    max_runtime_hours: 24,
    memory_limit_mb: 2048,
    cpu_cores: 2,
    use_gpu: false,
    priority: 'normal'
  });

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (algorithmType) {
      fetchAlgorithms();
    }
  }, [algorithmType]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [algorithmsRes, jobsRes, datasetsRes] = await Promise.all([
        api.get('/ml/algorithms/'),
        api.get('/ml/jobs/'),
        api.get('/datasets/datasets/')
      ]);

      setAlgorithms(algorithmsRes.data.results || []);
      setTrainingJobs(jobsRes.data.results || []);
      setDatasets(datasetsRes.data.results || []);
    } catch (error) {
      console.error('Error fetching ML data:', error);
      toast.error('Failed to load ML training data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAlgorithms = async () => {
    try {
      const params = algorithmType ? `?type=${algorithmType}` : '';
      const response = await api.get(`/ml/algorithms/${params}`);
      setAlgorithms(response.data.results || []);
    } catch (error) {
      console.error('Error fetching algorithms:', error);
    }
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingJob(true);
    
    try {
      const response = await api.post('/ml/jobs/', formData);
      console.log('Job creation response:', response.data); // Debug log
      
      // Extract job ID from response
      let jobId = response.data.id;
      
      // Fallback: check for other possible ID fields
      if (!jobId) {
        jobId = response.data.job_id || response.data.uuid || response.data.pk || response.data.training_job_id;
      }
      
      // If still no ID, try to get it from a success wrapper
      if (!jobId && response.data.success && response.data.data) {
        jobId = response.data.data.id;
      }
      
      if (jobId) {
        console.log('Job created successfully, ID:', jobId); // Debug log
        toast.success('Training job created successfully! Redirecting to job details...');
        
        // Close modal and reset form first
        setShowCreateModal(false);
        resetForm();
        
        // Navigate immediately without delay
        console.log('Navigating to:', `/ml/jobs/${jobId}`); // Debug log
        try {
          navigate(`/ml/jobs/${jobId}`);
        } catch (navError) {
          console.error('Navigation failed, trying window.location:', navError);
          window.location.href = `/ml/jobs/${jobId}`;
        }
      } else {
        console.error('No job ID found in response:', response.data);
        toast.error('Job created but unable to redirect. Please check the ML Training page.');
        setShowCreateModal(false);
        resetForm();
        fetchData(); // Refresh the jobs list
      }
    } catch (error: any) {
      console.error('Error creating training job:', error);
      toast.error(error.response?.data?.message || 'Failed to create training job');
    } finally {
      setCreatingJob(false);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      const response = await api.post(`/ml/jobs/${jobId}/cancel/`);
      
      if (response.data.success) {
        toast.success('Training job cancelled');
        fetchData();
      }
    } catch (error: any) {
      console.error('Error cancelling job:', error);
      toast.error(error.response?.data?.message || 'Failed to cancel job');
    }
  };

  const resetForm = () => {
    console.log('Resetting form...'); // Debug log
    setFormData({
      name: '',
      description: '',
      algorithm: '',
      dataset: '',
      parameters: {},
      train_test_split: 0.8,
      random_seed: 42,
      max_runtime_hours: 24,
      memory_limit_mb: 2048,
      cpu_cores: 2,
      use_gpu: false,
      priority: 'normal'
    });
    setSelectedAlgorithm(null);
    setCreatingJob(false); // Ensure loading state is reset
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-300 bg-green-500/20 border-green-400/30';
      case 'running': return 'text-blue-300 bg-blue-500/20 border-blue-400/30';
      case 'queued': return 'text-yellow-300 bg-yellow-500/20 border-yellow-400/30';
      case 'failed': return 'text-red-300 bg-red-500/20 border-red-400/30';
      case 'cancelled': return 'text-gray-300 bg-gray-500/20 border-gray-400/30';
      default: return 'text-gray-300 bg-gray-500/20 border-gray-400/30';
    }
  };

  const getAlgorithmTypeColor = (type: string) => {
    switch (type) {
      case 'classification': return 'text-blue-300 bg-blue-500/20 border-blue-400/30';
      case 'regression': return 'text-green-300 bg-green-500/20 border-green-400/30';
      case 'clustering': return 'text-purple-300 bg-purple-500/20 border-purple-400/30';
      case 'dimensionality_reduction': return 'text-orange-300 bg-orange-500/20 border-orange-400/30';
      case 'deep_learning': return 'text-red-300 bg-red-500/20 border-red-400/30';
      default: return 'text-gray-300 bg-gray-500/20 border-gray-400/30';
    }
  };

  const formatRuntime = (seconds: number) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between">
            <div className="mb-6 lg:mb-0">
              <h1 className="text-4xl lg:text-5xl font-black bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-3 flex items-center">
                <BeakerIcon className="h-12 w-12 mr-4 text-cyan-400" />
                🧪 ML Training Lab
              </h1>
              <p className="text-gray-300 text-lg">
                Train machine learning models on your datasets with our integrated AI platform
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25 flex items-center"
            >
              <PlayIcon className="h-6 w-6 mr-3" />
              Start Training
            </button>
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Enhanced Algorithm Types Filter */}
        <div className="mb-12">
          <div className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <CpuChipIcon className="h-6 w-6 mr-2 text-cyan-400" />
              Algorithm Types
            </h3>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setAlgorithmType('')}
                className={`px-4 py-3 rounded-xl text-sm font-bold transition-all duration-300 border ${
                  algorithmType === '' 
                    ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white border-cyan-400/50 shadow-lg shadow-cyan-500/25' 
                    : 'bg-black/20 text-gray-300 border-gray-600/30 hover:border-cyan-400/50 hover:text-white'
                }`}
              >
                🔬 All Algorithms
              </button>
              {[
                { type: 'classification', icon: '🎯', label: 'Classification' },
                { type: 'regression', icon: '📈', label: 'Regression' },
                { type: 'clustering', icon: '🔗', label: 'Clustering' },
                { type: 'dimensionality_reduction', icon: '📊', label: 'Dimensionality Reduction' },
                { type: 'deep_learning', icon: '🧠', label: 'Deep Learning' }
              ].map(({ type, icon, label }) => (
                <button
                  key={type}
                  onClick={() => setAlgorithmType(type)}
                  className={`px-4 py-3 rounded-xl text-sm font-bold transition-all duration-300 border ${
                    algorithmType === type 
                      ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white border-cyan-400/50 shadow-lg shadow-cyan-500/25' 
                      : 'bg-black/20 text-gray-300 border-gray-600/30 hover:border-cyan-400/50 hover:text-white'
                  }`}
                >
                  <span className="mr-2">{icon}</span>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Enhanced Available Algorithms */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2 flex items-center justify-center">
              <CpuChipIcon className="h-8 w-8 mr-3 text-cyan-400" />
              🤖 Available Algorithms
            </h2>
            <p className="text-gray-300">Choose from our collection of state-of-the-art ML algorithms</p>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 animate-pulse">
                  <div className="h-6 bg-gray-600/30 rounded mb-4"></div>
                  <div className="h-4 bg-gray-600/30 rounded mb-3"></div>
                  <div className="h-4 bg-gray-600/30 rounded w-20 mb-6"></div>
                  <div className="h-10 bg-gray-600/30 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {algorithms.map((algorithm) => (
                <div key={algorithm.id} className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-6 hover:border-cyan-400/50 transition-all duration-300 group">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-xl font-bold text-white group-hover:text-cyan-400 transition-colors">
                      {algorithm.name}
                    </h3>
                    <span className={`px-3 py-1 text-xs font-bold rounded-full border ${getAlgorithmTypeColor(algorithm.algorithm_type)}`}>
                      {algorithm.algorithm_type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  
                  <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                    {algorithm.description}
                  </p>
                  
                  <div className="space-y-3 mb-6">
                    <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">Library</span>
                        <span className="text-white font-medium">{algorithm.library}</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                        <div className="text-gray-400 text-xs mb-1">Min Memory</div>
                        <div className="text-white font-bold">{algorithm.min_memory_mb} MB</div>
                      </div>
                      <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                        <div className="text-gray-400 text-xs mb-1">Min CPU</div>
                        <div className="text-white font-bold">{algorithm.min_cpu_cores} cores</div>
                      </div>
                    </div>
                    <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm flex items-center">
                          <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                          Cost per Hour
                        </span>
                        <span className="text-cyan-400 font-bold">{parseFloat(algorithm.cost_per_hour).toFixed(4)} NRC</span>
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => {
                      setSelectedAlgorithm(algorithm);
                      setFormData(prev => ({ ...prev, algorithm: algorithm.id.toString() }));
                      setShowCreateModal(true);
                    }}
                    className="w-full bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
                  >
                    🚀 Use Algorithm
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Enhanced Training Jobs */}
        <div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2 flex items-center justify-center">
              <ChartBarIcon className="h-8 w-8 mr-3 text-cyan-400" />
              📊 Your Training Jobs
            </h2>
            <p className="text-gray-300">Monitor and manage your ML training experiments</p>
          </div>
          
          {trainingJobs.length === 0 ? (
            <div className="text-center py-20 bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20">
              <BeakerIcon className="h-24 w-24 text-cyan-400 mx-auto mb-8" />
              <h3 className="text-3xl font-bold text-white mb-4">
                No training jobs yet
              </h3>
              <p className="text-gray-300 text-lg mb-8 max-w-md mx-auto">
                Start your first ML training job to see results and monitor progress here.
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
              >
                🚀 Start Training
              </button>
            </div>
          ) : (
            <div className="space-y-8">
              {trainingJobs.map((job) => (
                <div key={job.id} className="bg-black/20 backdrop-blur-lg rounded-2xl border border-purple-500/20 p-8 hover:border-cyan-400/50 transition-all duration-300">
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between mb-6">
                    <div className="flex-1 mb-4 lg:mb-0">
                      <h3 className="text-2xl font-bold text-white mb-2">
                        {job.name}
                      </h3>
                      <p className="text-gray-300 text-lg mb-4">
                        {job.description}
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                        <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                          <div className="text-gray-400 mb-1">Algorithm</div>
                          <div className="text-white font-bold">{job.algorithm_name}</div>
                        </div>
                        <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                          <div className="text-gray-400 mb-1">Dataset</div>
                          <div className="text-white font-bold">{job.dataset_title}</div>
                        </div>
                        <div className="bg-black/20 rounded-xl p-3 border border-gray-600/30">
                          <div className="text-gray-400 mb-1">Created</div>
                          <div className="text-white font-bold">{new Date(job.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
                      <span className={`px-4 py-2 text-sm font-bold rounded-full border ${getStatusColor(job.status)}`}>
                        {job.status.toUpperCase()}
                      </span>
                      
                      {job.is_running && (
                        <button
                          onClick={() => handleCancelJob(job.id)}
                          className="bg-gradient-to-r from-red-500 to-pink-600 text-white px-4 py-2 rounded-xl font-bold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-red-500/25 flex items-center"
                        >
                          <StopIcon className="h-4 w-4 mr-2" />
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {/* Enhanced Progress Bar */}
                  {job.status === 'running' && (
                    <div className="mb-6">
                      <div className="flex items-center justify-between text-sm text-gray-300 mb-2">
                        <span className="font-medium">Training Progress</span>
                        <span className="font-bold text-cyan-400">{job.progress_percentage}%</span>
                      </div>
                      <div className="w-full bg-black/20 rounded-full h-3 border border-gray-600/30">
                        <div 
                          className="bg-gradient-to-r from-cyan-500 to-purple-600 h-3 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress_percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  {/* Enhanced Job Stats */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                      <div className="flex items-center mb-2">
                        <ClockIcon className="h-5 w-5 mr-2 text-cyan-400" />
                        <div className="text-gray-400 text-sm">Runtime</div>
                      </div>
                      <div className="text-white font-bold text-lg">{formatRuntime(job.actual_runtime_seconds)}</div>
                    </div>
                    
                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                      <div className="flex items-center mb-2">
                        <CurrencyDollarIcon className="h-5 w-5 mr-2 text-purple-400" />
                        <div className="text-gray-400 text-sm">Cost</div>
                      </div>
                      <div className="text-white font-bold text-lg">
                        {job.actual_cost ? `${parseFloat(job.actual_cost).toFixed(4)} NRC` : 'Estimating...'}
                      </div>
                    </div>
                    
                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30">
                      <div className="flex items-center mb-2">
                        <AcademicCapIcon className="h-5 w-5 mr-2 text-green-400" />
                        <div className="text-gray-400 text-sm">Accuracy</div>
                      </div>
                      <div className="text-white font-bold text-lg">
                        {job.model_metrics?.accuracy ? `${(job.model_metrics.accuracy * 100).toFixed(2)}%` : 'N/A'}
                      </div>
                    </div>
                    
                    <div className="bg-black/20 rounded-xl p-4 border border-gray-600/30 flex items-center justify-center">
                      <Link
                        to={`/ml/jobs/${job.id}`}
                        className="bg-gradient-to-r from-cyan-500/20 to-purple-600/20 text-cyan-300 px-4 py-2 rounded-lg font-bold hover:from-cyan-500/30 hover:to-purple-600/30 transition-all duration-300 border border-cyan-400/30 flex items-center"
                      >
                        <EyeIcon className="h-4 w-4 mr-2" />
                        View Details
                      </Link>
                    </div>
                  </div>
                  
                  {/* Enhanced Error Message */}
                  {job.status === 'failed' && job.error_message && (
                    <div className="bg-red-500/20 border border-red-400/30 rounded-xl p-4">
                      <div className="text-red-300 text-sm">
                        <div className="font-bold mb-2">❌ Training Failed</div>
                        <div className="bg-black/20 p-3 rounded-lg border border-red-400/20">
                          {job.error_message}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Training Job Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <SparklesIcon className="h-6 w-6 mr-2 text-primary-600" />
                  Create Training Job
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <form onSubmit={handleCreateJob} className={`space-y-6 ${creatingJob ? 'opacity-75 pointer-events-none' : ''}`}>
                {/* Loading Indicator */}
                {creatingJob && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                      <div>
                        <p className="text-sm font-medium text-blue-900">Creating Training Job...</p>
                        <p className="text-xs text-blue-700">Please wait while we set up your ML training job.</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="My ML Training Job"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Priority
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    rows={3}
                    placeholder="Describe your training job..."
                  />
                </div>
                
                {/* Algorithm and Dataset Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Algorithm *
                    </label>
                    <select
                      required
                      value={formData.algorithm}
                      onChange={(e) => {
                        const algoId = e.target.value;
                        const algo = algorithms.find(a => a.id.toString() === algoId);
                        setFormData(prev => ({ ...prev, algorithm: algoId }));
                        setSelectedAlgorithm(algo || null);
                      }}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select Algorithm</option>
                      {algorithms.map((algo) => (
                        <option key={algo.id} value={algo.id}>
                          {algo.name} ({algo.algorithm_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Dataset *
                    </label>
                    <select
                      required
                      value={formData.dataset}
                      onChange={(e) => setFormData(prev => ({ ...prev, dataset: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select Dataset</option>
                      {datasets.map((dataset) => (
                        <option key={dataset.id} value={dataset.id}>
                          {dataset.title} ({dataset.file_type}, {dataset.file_size_human})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                {/* Training Configuration */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Train/Test Split
                    </label>
                    <input
                      type="number"
                      min="0.1"
                      max="0.9"
                      step="0.1"
                      value={formData.train_test_split}
                      onChange={(e) => setFormData(prev => ({ ...prev, train_test_split: parseFloat(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Random Seed
                    </label>
                    <input
                      type="number"
                      value={formData.random_seed}
                      onChange={(e) => setFormData(prev => ({ ...prev, random_seed: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Runtime (hours)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="168"
                      value={formData.max_runtime_hours}
                      onChange={(e) => setFormData(prev => ({ ...prev, max_runtime_hours: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
                
                {/* Resource Configuration */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Memory Limit (MB)
                    </label>
                    <input
                      type="number"
                      min="512"
                      max="32768"
                      step="512"
                      value={formData.memory_limit_mb}
                      onChange={(e) => setFormData(prev => ({ ...prev, memory_limit_mb: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CPU Cores
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="16"
                      value={formData.cpu_cores}
                      onChange={(e) => setFormData(prev => ({ ...prev, cpu_cores: parseInt(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="use_gpu"
                      checked={formData.use_gpu}
                      onChange={(e) => setFormData(prev => ({ ...prev, use_gpu: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <label htmlFor="use_gpu" className="ml-2 text-sm font-medium text-gray-700">
                      Use GPU (if available)
                    </label>
                  </div>
                </div>
                
                {/* Estimated Cost */}
                {selectedAlgorithm && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center text-blue-800">
                      <CurrencyDollarIcon className="h-5 w-5 mr-2" />
                      <span className="font-medium">Estimated Cost:</span>
                      <span className="ml-2">
                        {(parseFloat(selectedAlgorithm.cost_per_hour) * formData.max_runtime_hours).toFixed(4)} NRC
                      </span>
                    </div>
                  </div>
                )}
                
                {/* Form Actions */}
                <div className="flex items-center justify-end space-x-3 pt-6 border-t">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      resetForm();
                    }}
                    className="btn-outline"
                    disabled={creatingJob}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary flex items-center"
                    disabled={creatingJob}
                  >
                    {creatingJob ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Creating Job...
                      </>
                    ) : (
                      <>
                        <PlayIcon className="h-4 w-4 mr-2" />
                        Start Training
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MLTrainingPage;
