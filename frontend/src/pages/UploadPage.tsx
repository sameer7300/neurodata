import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
  InformationCircleIcon,
  CurrencyDollarIcon,
  TagIcon,
  PhotoIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { api } from '../contexts/AuthContext';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface Category {
  id: number;
  name: string;
  description: string;
}

interface UploadFormData {
  title: string;
  description: string;
  category: number | null;
  tags: number[];
  price: string;
  file: File | null;
  thumbnail: File | null;
  license_type: string;
  license_text: string;
  keywords: string;
  sample_data: string;
  data_format: string;
  data_size: string;
  collection_method: string;
  privacy_level: string;
}

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<UploadFormData>({
    title: '',
    description: '',
    category: null,
    tags: [],
    price: '',
    file: null,
    thumbnail: null,
    license_type: 'mit',
    license_text: '',
    keywords: '',
    sample_data: '',
    data_format: '',
    data_size: '',
    collection_method: '',
    privacy_level: 'public'
  });

  const [tagInput, setTagInput] = useState('');
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please login to upload datasets');
      navigate('/login');
      return;
    }
    fetchCategories();
  }, [isAuthenticated, navigate]);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/datasets/categories/');
      // Handle both paginated and non-paginated responses
      const categoriesData = response.data.results || response.data.data || response.data;
      setCategories(Array.isArray(categoriesData) ? categoriesData : []);
    } catch (error) {
      console.error('Error fetching categories:', error);
      toast.error('Failed to load categories');
    }
  };

  const handleInputChange = (field: keyof UploadFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFileUpload = (file: File, type: 'file' | 'thumbnail') => {
    if (type === 'file') {
      // Validate file size (max 500MB to match backend)
      if (file.size > 500 * 1024 * 1024) {
        toast.error('File size must be less than 500MB');
        return;
      }
      
      // Validate file type
      const allowedExtensions = [
        'csv', 'json', 'parquet', 'xlsx', 'xls', 'tsv', 'txt',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp',
        'zip', 'tar', 'gz', 'rar',
        'xml', 'yaml', 'yml', 'h5', 'hdf5', 'pkl', 'pickle'
      ];
      
      const fileExt = file.name.split('.').pop()?.toLowerCase();
      if (!fileExt || !allowedExtensions.includes(fileExt)) {
        toast.error(`Unsupported file type. Allowed: ${allowedExtensions.join(', ')}`);
        return;
      }
      
      handleInputChange('file', file);
    } else {
      // Validate thumbnail (max 5MB, images only)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Thumbnail size must be less than 5MB');
        return;
      }
      if (!file.type.startsWith('image/')) {
        toast.error('Thumbnail must be an image file');
        return;
      }
      handleInputChange('thumbnail', file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0], 'file');
    }
  };

  const addTag = () => {
    if (tagInput.trim()) {
      // For now, we'll store tag names as strings and convert to IDs later
      const tagName = tagInput.trim();
      if (!formData.keywords.split(',').map(t => t.trim()).includes(tagName)) {
        const currentKeywords = formData.keywords ? formData.keywords.split(',').map(t => t.trim()) : [];
        handleInputChange('keywords', [...currentKeywords, tagName].join(', '));
        setTagInput('');
      }
    }
  };

  const removeTag = (tagToRemove: string) => {
    const currentKeywords = formData.keywords.split(',').map(t => t.trim());
    const updatedKeywords = currentKeywords.filter(tag => tag !== tagToRemove);
    handleInputChange('keywords', updatedKeywords.join(', '));
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        return !!(formData.title && formData.description && formData.category);
      case 2:
        return !!(formData.file && formData.price);
      case 3:
        return !!(formData.data_format && formData.collection_method);
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    } else {
      toast.error('Please fill in all required fields');
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const submitData = new FormData();
      
      // Add all form fields
      submitData.append('title', formData.title);
      submitData.append('description', formData.description);
      submitData.append('category', formData.category!.toString());
      submitData.append('price', formData.price);
      submitData.append('license_type', formData.license_type);
      submitData.append('license_text', formData.license_text);
      submitData.append('keywords', formData.keywords);
      
      // Tags field - leave empty for now since we're using keywords
      // The backend expects individual tag IDs, but we'll use keywords instead
      
      // Note: These fields are not in the backend model, so we'll store them in keywords or description
      const additionalInfo = {
        sample_data: formData.sample_data,
        data_format: formData.data_format,
        data_size: formData.data_size,
        collection_method: formData.collection_method,
        privacy_level: formData.privacy_level
      };
      
      // Append additional info to description
      const fullDescription = `${formData.description}\n\nAdditional Information:\n${JSON.stringify(additionalInfo, null, 2)}`;
      submitData.set('description', fullDescription);
      
      // Add files
      if (formData.file) {
        submitData.append('file', formData.file);
      }
      if (formData.thumbnail) {
        submitData.append('thumbnail', formData.thumbnail);
      }

      const response = await api.post('/datasets/datasets/', submitData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setUploadProgress(progress);
        },
      });

      toast.success('Dataset uploaded successfully!');
      
      // The backend returns: { success: true, message: "...", data: { id: "...", ... } }
      const datasetId = response.data.data?.id || response.data.id;
      if (datasetId) {
        navigate(`/datasets/${datasetId}`);
      } else {
        // Fallback to datasets list if no ID
        navigate('/datasets');
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      console.error('Error response:', error.response?.data);
      
      // Show detailed error message
      let errorMessage = 'Failed to upload dataset';
      if (error.response?.data) {
        // Handle Django error pages (HTML response)
        if (typeof error.response.data === 'string' && error.response.data.includes('IntegrityError')) {
          if (error.response.data.includes('UNIQUE constraint failed: datasets.file_hash')) {
            errorMessage = 'This file has already been uploaded. Please select a different file or check your existing datasets.';
          } else {
            errorMessage = 'Database error occurred. Please try again.';
          }
        }
        // Handle JSON error responses
        else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else if (error.response.data.errors) {
          // Handle field-specific errors
          const errors = error.response.data.errors;
          const errorMessages = Object.entries(errors).map(([field, msgs]: [string, any]) => {
            const messages = Array.isArray(msgs) ? msgs : [msgs];
            return `${field}: ${messages.join(', ')}`;
          });
          errorMessage = errorMessages.join('\n');
        } else if (error.response.data.file) {
          // Handle file-specific validation errors
          const fileErrors = Array.isArray(error.response.data.file) ? error.response.data.file : [error.response.data.file];
          errorMessage = fileErrors.join(', ');
        } else if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const steps = [
    { number: 1, title: 'Basic Information', description: 'Dataset title, description, and category' },
    { number: 2, title: 'File & Pricing', description: 'Upload your dataset and set pricing' },
    { number: 3, title: 'Metadata', description: 'Additional details about your dataset' },
    { number: 4, title: 'Review', description: 'Review and submit your dataset' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Upload Dataset
          </h1>
          <p className="text-xl text-gray-600">
            Share your valuable data with the AI community
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  currentStep >= step.number
                    ? 'bg-primary-600 border-primary-600 text-white'
                    : 'border-gray-300 text-gray-500'
                }`}>
                  {currentStep > step.number ? (
                    <CheckCircleIcon className="h-6 w-6" />
                  ) : (
                    step.number
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-4 ${
                    currentStep > step.number ? 'bg-primary-600' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 text-center">
            <h3 className="text-lg font-medium text-gray-900">
              {steps[currentStep - 1].title}
            </h3>
            <p className="text-sm text-gray-500">
              {steps[currentStep - 1].description}
            </p>
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white rounded-lg shadow-sm border p-8">
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dataset Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="Enter a descriptive title for your dataset"
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Provide a detailed description of your dataset, including what it contains and potential use cases"
                  rows={4}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  value={formData.category || ''}
                  onChange={(e) => handleInputChange('category', parseInt(e.target.value))}
                  className="input"
                  required
                >
                  <option value="">Select a category</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.keywords.split(',').filter(tag => tag.trim()).map((tag) => (
                    <span
                      key={tag.trim()}
                      className="badge-primary flex items-center gap-1"
                    >
                      {tag.trim()}
                      <button
                        onClick={() => removeTag(tag.trim())}
                        className="hover:text-primary-300"
                      >
                        <XMarkIcon className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    placeholder="Add tags to help others find your dataset"
                    className="input flex-1"
                  />
                  <button
                    type="button"
                    onClick={addTag}
                    className="btn-outline"
                  >
                    Add Tag
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: File & Pricing */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dataset File *
                </label>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center ${
                    dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {formData.file ? (
                    <div className="flex items-center justify-center">
                      <DocumentIcon className="h-12 w-12 text-primary-600 mr-4" />
                      <div>
                        <p className="text-lg font-medium text-gray-900">
                          {formData.file.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {(formData.file.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        onClick={() => handleInputChange('file', null)}
                        className="ml-4 text-red-600 hover:text-red-700"
                      >
                        <XMarkIcon className="h-6 w-6" />
                      </button>
                    </div>
                  ) : (
                    <div>
                      <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-lg text-gray-600 mb-2">
                        Drag and drop your dataset file here
                      </p>
                      <p className="text-sm text-gray-500 mb-4">
                        Supports: CSV, JSON, Excel, Images, Archives, and more (Max 500MB)
                      </p>
                      <input
                        type="file"
                        onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'file')}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="btn-primary cursor-pointer"
                      >
                        Choose File
                      </label>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Thumbnail (Optional)
                </label>
                <div className="flex items-center gap-4">
                  {formData.thumbnail ? (
                    <div className="flex items-center">
                      <img
                        src={URL.createObjectURL(formData.thumbnail)}
                        alt="Thumbnail preview"
                        className="h-16 w-16 object-cover rounded-lg"
                      />
                      <button
                        onClick={() => handleInputChange('thumbnail', null)}
                        className="ml-2 text-red-600 hover:text-red-700"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <PhotoIcon className="h-8 w-8 text-gray-400" />
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'thumbnail')}
                        className="hidden"
                        id="thumbnail-upload"
                      />
                      <label
                        htmlFor="thumbnail-upload"
                        className="btn-outline cursor-pointer"
                      >
                        Upload Thumbnail
                      </label>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Price (NRC) *
                </label>
                <div className="relative">
                  <CurrencyDollarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.price}
                    onChange={(e) => handleInputChange('price', e.target.value)}
                    placeholder="0.00"
                    className="input pl-10"
                    required
                  />
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Set to 0 for free datasets
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Metadata */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Data Format *
                  </label>
                  <select
                    value={formData.data_format}
                    onChange={(e) => handleInputChange('data_format', e.target.value)}
                    className="input"
                    required
                  >
                    <option value="">Select format</option>
                    <option value="CSV">CSV</option>
                    <option value="JSON">JSON</option>
                    <option value="XML">XML</option>
                    <option value="Parquet">Parquet</option>
                    <option value="HDF5">HDF5</option>
                    <option value="Images">Images</option>
                    <option value="Audio">Audio</option>
                    <option value="Video">Video</option>
                    <option value="Text">Text</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Data Size
                  </label>
                  <input
                    type="text"
                    value={formData.data_size}
                    onChange={(e) => handleInputChange('data_size', e.target.value)}
                    placeholder="e.g., 10,000 rows, 1M images"
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Collection Method *
                </label>
                <textarea
                  value={formData.collection_method}
                  onChange={(e) => handleInputChange('collection_method', e.target.value)}
                  placeholder="Describe how this data was collected"
                  rows={3}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sample Data
                </label>
                <textarea
                  value={formData.sample_data}
                  onChange={(e) => handleInputChange('sample_data', e.target.value)}
                  placeholder="Provide a sample of your data (first few rows, example entries, etc.)"
                  rows={4}
                  className="input"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    License
                  </label>
                  <select
                    value={formData.license_type}
                    onChange={(e) => handleInputChange('license_type', e.target.value)}
                    className="input"
                  >
                    <option value="cc0">CC0 - Public Domain</option>
                    <option value="cc_by">CC BY - Attribution</option>
                    <option value="cc_by_sa">CC BY-SA - Attribution-ShareAlike</option>
                    <option value="cc_by_nc">CC BY-NC - Attribution-NonCommercial</option>
                    <option value="mit">MIT License</option>
                    <option value="apache">Apache License 2.0</option>
                    <option value="custom">Custom License</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Privacy Level
                  </label>
                  <select
                    value={formData.privacy_level}
                    onChange={(e) => handleInputChange('privacy_level', e.target.value)}
                    className="input"
                  >
                    <option value="public">Public</option>
                    <option value="private">Private</option>
                    <option value="restricted">Restricted</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Review Your Dataset
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
                    <p><strong>Title:</strong> {formData.title}</p>
                    <p><strong>Category:</strong> {categories.find(c => c.id === formData.category)?.name}</p>
                    <p><strong>Price:</strong> {formData.price} NRC</p>
                    <p><strong>Tags:</strong> {formData.keywords || 'None'}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">File Details</h4>
                    <p><strong>File:</strong> {formData.file?.name}</p>
                    <p><strong>Size:</strong> {formData.file ? (formData.file.size / (1024 * 1024)).toFixed(2) + ' MB' : 'N/A'}</p>
                    <p><strong>Format:</strong> {formData.data_format}</p>
                    <p><strong>License:</strong> {formData.license_type}</p>
                  </div>
                </div>
                
                <div className="mt-4">
                  <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                  <p className="text-gray-600">{formData.description}</p>
                </div>
              </div>

              {loading && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                    <span className="text-blue-800">
                      Uploading... {uploadProgress}%
                    </span>
                  </div>
                  <div className="mt-2 bg-blue-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t">
            <button
              onClick={prevStep}
              disabled={currentStep === 1}
              className="btn-outline disabled:opacity-50"
            >
              Previous
            </button>
            
            {currentStep < 4 ? (
              <button
                onClick={nextStep}
                className="btn-primary"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="btn-primary disabled:opacity-50"
              >
                {loading ? 'Uploading...' : 'Upload Dataset'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
