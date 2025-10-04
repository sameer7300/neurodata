import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  StarIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  TagIcon,
  UserIcon,
  ChevronDownIcon,
  XMarkIcon,
  CloudArrowDownIcon,
  HeartIcon,
  AdjustmentsHorizontalIcon,
  Squares2X2Icon,
  ListBulletIcon,
  SparklesIcon,
  FireIcon,
  TrophyIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { api } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface Dataset {
  id: string;
  title: string;
  slug: string;
  description: string;
  owner_name: string;
  category_name: string;
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
  download_count: number;
  view_count: number;
  rating_average: number;
  rating_count: number;
  status: string;
  created_at: string;
  published_at: string;
  review_stats?: {
    total_reviews: number;
    average_rating: number;
    verified_percentage: number;
  };
}

interface Category {
  id: number;
  name: string;
  description: string;
}

const DatasetsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Initialize search from URL params
  useEffect(() => {
    const search = searchParams.get('search');
    if (search) {
      setSearchQuery(search);
    } else {
      setSearchQuery('');
    }
  }, [searchParams]);

  // Fetch datasets from API
  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        ordering: sortOrder === 'desc' ? `-${sortBy}` : sortBy,
        ...(searchQuery && { search: searchQuery }),
        ...(selectedCategory && { category: selectedCategory.toString() }),
        ...(priceRange.min && { price_min: priceRange.min }),
        ...(priceRange.max && { price_max: priceRange.max }),
      });

      const response = await api.get(`/datasets/datasets/?${params}`);
      setDatasets(response.data.results || []);
      setTotalPages(Math.ceil(response.data.count / 12));
    } catch (error) {
      console.error('Error fetching datasets:', error);
      toast.error('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  // Fetch categories
  const fetchCategories = async () => {
    try {
      const response = await api.get('/datasets/categories/');
      setCategories(response.data.results || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchDatasets();
  }, [currentPage, sortBy, sortOrder, selectedCategory, searchQuery, priceRange]);

  // Update URL params when search query changes
  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    if (searchQuery.trim()) {
      params.set('search', searchQuery.trim());
    } else {
      params.delete('search');
    }
    setSearchParams(params, { replace: true });
  }, [searchQuery, setSearchParams]);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatPrice = (price: string) => {
    return parseFloat(price).toFixed(2);
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

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <StarIcon
        key={i}
        className={`h-4 w-4 ${
          i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'
        }`}
      />
    ));
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory(null);
    setPriceRange({ min: '', max: '' });
    setSortBy('created_at');
    setSortOrder('desc');
    setCurrentPage(1);
    // Update URL params to clear search
    setSearchParams({});
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div 
          className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"
          style={{ transform: `translateY(${scrollY * 0.1}px)` }}
        />
        <div 
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"
          style={{ transform: `translateY(${-scrollY * 0.1}px)` }}
        />
        <div 
          className="absolute top-1/2 left-1/2 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse"
          style={{ transform: `translate(-50%, -50%) translateY(${scrollY * 0.05}px)` }}
        />
      </div>

      {/* Responsive Hero Header Section */}
      <section className="relative py-12 sm:py-16 md:py-20 px-4 sm:px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto text-center z-10 relative">
          <div 
            className="mb-6 sm:mb-8 transform transition-all duration-1000 ease-out"
            style={{ transform: `translateY(${Math.max(0, scrollY * 0.1)}px)` }}
          >
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-black bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-4 sm:mb-6 leading-tight px-2">
               Dataset Marketplace
            </h1>
            <div className="h-1.5 sm:h-2 w-20 sm:w-32 bg-gradient-to-r from-cyan-400 to-purple-500 mx-auto mb-6 sm:mb-8 rounded-full"></div>
          </div>
          
          <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-300 mb-8 sm:mb-12 leading-relaxed font-light max-w-4xl mx-auto px-4">
            Discover and purchase high-quality AI datasets from our global community
            <br className="hidden sm:block" />
            <span className="text-cyan-400 font-semibold block sm:inline mt-2 sm:mt-0">Premium Quality • Verified Data • Instant Access</span>
          </p>


          {/* Responsive Quick Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 max-w-4xl mx-auto px-4">
            {[
              { icon: <TagIcon className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />, label: 'Categories', value: categories.length || '10+' },
              { icon: <SparklesIcon className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />, label: 'Datasets', value: datasets.length || '1,250+' },
              { icon: <FireIcon className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />, label: 'Featured', value: '50+' },
              { icon: <TrophyIcon className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />, label: 'Premium', value: '200+' }
            ].map((stat, idx) => (
              <div key={idx} className="bg-black/20 backdrop-blur-lg rounded-lg sm:rounded-xl p-3 sm:p-4 border border-purple-500/20 hover:border-cyan-400/50 transition-all duration-300">
                <div className="text-cyan-400 mb-1 sm:mb-2 flex justify-center">{stat.icon}</div>
                <div className="text-white font-bold text-sm sm:text-base md:text-lg">{stat.value}</div>
                <div className="text-gray-400 text-xs sm:text-sm">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Responsive Main Content Area */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pb-12 sm:pb-20">
        <div className="flex flex-col lg:flex-row gap-4 sm:gap-6 lg:gap-8">
          {/* Responsive Enhanced Filters Sidebar */}
          <div className="w-full lg:w-80 flex-shrink-0">
            <div className={`bg-black/30 backdrop-blur-lg rounded-xl sm:rounded-2xl border border-purple-500/20 p-4 sm:p-6 ${showFilters ? 'block' : 'hidden lg:block'} lg:sticky lg:top-6`}>
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <h3 className="text-lg sm:text-xl font-bold text-white flex items-center">
                  <AdjustmentsHorizontalIcon className="h-5 w-5 sm:h-6 sm:w-6 mr-2 text-cyan-400" />
                  Search & Filters
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={clearFilters}
                    className="text-xs sm:text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    Clear All
                  </button>
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="lg:hidden text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Search Bar in Filters */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2 sm:mb-3">
                  Search Datasets
                </label>
                <div className="relative">
                  <form onSubmit={(e) => { e.preventDefault(); fetchDatasets(); }}>
                    <input
                      type="text"
                      placeholder="Search datasets, categories, keywords..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-black/20 border border-purple-500/30 rounded-lg px-3 sm:px-4 py-2 sm:py-3 pl-10 sm:pl-12 text-white placeholder-gray-400 text-sm sm:text-base focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all duration-300 hover:border-purple-400/50"
                    />
                  </form>
                  <MagnifyingGlassIcon className="absolute left-3 sm:left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                </div>
              </div>

              {/* Responsive View Mode Toggle */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2 sm:mb-3">
                  View Mode
                </label>
                <div className="flex bg-black/20 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`flex-1 flex items-center justify-center py-2 px-2 sm:px-3 rounded-md transition-all text-xs sm:text-sm ${
                      viewMode === 'grid' 
                        ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white' 
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <Squares2X2Icon className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                    Grid
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`flex-1 flex items-center justify-center py-2 px-2 sm:px-3 rounded-md transition-all text-xs sm:text-sm ${
                      viewMode === 'list' 
                        ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white' 
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <ListBulletIcon className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                    List
                  </button>
                </div>
              </div>

              {/* Responsive Category Filter */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2 sm:mb-3">
                  Category
                </label>
                <select
                  value={selectedCategory || ''}
                  onChange={(e) => setSelectedCategory(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full bg-black/20 border border-purple-500/30 rounded-lg px-3 sm:px-4 py-2 sm:py-3 text-white text-sm sm:text-base focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all"
                >
                  <option value="">All Categories</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Fully Responsive Price Range Filter */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2 sm:mb-3">
                  Price Range (NCR)
                </label>
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <div className="flex-1">
                    <input
                      type="number"
                      placeholder="Min Price"
                      value={priceRange.min}
                      onChange={(e) => setPriceRange({ ...priceRange, min: e.target.value })}
                      className="w-full bg-black/20 border border-purple-500/30 rounded-lg px-3 sm:px-4 lg:px-3 xl:px-4 py-2 sm:py-3 lg:py-2 xl:py-3 text-white placeholder-gray-400 text-sm sm:text-base lg:text-sm xl:text-base focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all duration-300 hover:border-purple-400/50"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="flex-1">
                    <input
                      type="number"
                      placeholder="Max Price"
                      value={priceRange.max}
                      onChange={(e) => setPriceRange({ ...priceRange, max: e.target.value })}
                      className="w-full bg-black/20 border border-purple-500/30 rounded-lg px-3 sm:px-4 lg:px-3 xl:px-4 py-2 sm:py-3 lg:py-2 xl:py-3 text-white placeholder-gray-400 text-sm sm:text-base lg:text-sm xl:text-base focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all duration-300 hover:border-purple-400/50"
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Enter price range in NCR tokens
                </div>
              </div>

              {/* Responsive Sort Options */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2 sm:mb-3">
                  Sort By
                </label>
                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={(e) => {
                    const [field, order] = e.target.value.split('-');
                    setSortBy(field);
                    setSortOrder(order);
                  }}
                  className="w-full bg-black/20 border border-purple-500/30 rounded-lg px-3 sm:px-4 py-2 sm:py-3 text-white text-sm sm:text-base focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all"
                >
                  <option value="created_at-desc">🆕 Newest First</option>
                  <option value="created_at-asc">📅 Oldest First</option>
                  <option value="price-asc">💰 Price: Low to High</option>
                  <option value="price-desc">💎 Price: High to Low</option>
                  <option value="rating-desc">⭐ Highest Rated</option>
                  <option value="download_count-desc">🔥 Most Downloaded</option>
                </select>
              </div>
            </div>
          </div>

          {/* Responsive Main Content */}
          <div className="flex-1 w-full lg:w-auto">
            {/* Responsive Enhanced Results Header */}
            <div className="bg-black/20 backdrop-blur-lg rounded-xl sm:rounded-2xl border border-purple-500/20 p-4 sm:p-6 mb-6 sm:mb-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex-1">
                  <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-white mb-1 sm:mb-2">
                    {loading ? 'Loading Datasets...' : `${datasets.length} Datasets Found`}
                  </h2>
                  <p className="text-gray-400 text-sm sm:text-base">
                    {searchQuery && `Results for "${searchQuery}"`}
                    {selectedCategory && ` in ${categories.find(c => c.id === selectedCategory)?.name}`}
                  </p>
                </div>
                <div className="flex items-center justify-between sm:justify-end gap-3 sm:gap-4">
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="lg:hidden bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-3 sm:px-4 py-2 rounded-lg hover:scale-105 transition-all duration-300 flex items-center text-sm"
                  >
                    <FunnelIcon className="h-4 w-4 mr-1 sm:mr-2" />
                    Filters
                  </button>
                  <div className="flex items-center text-gray-400 text-xs sm:text-sm">
                    <span>Page {currentPage} of {totalPages}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Responsive Enhanced Loading State */}
            {loading ? (
              <div className={`grid gap-4 sm:gap-6 ${
                viewMode === 'grid' 
                  ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3' 
                  : 'grid-cols-1'
              }`}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="bg-black/20 backdrop-blur-lg rounded-xl sm:rounded-2xl border border-purple-500/20 animate-pulse overflow-hidden">
                    <div className="h-32 sm:h-40 md:h-48 bg-gradient-to-br from-purple-500/20 to-cyan-500/20"></div>
                    <div className="p-4 sm:p-6">
                      <div className="h-4 sm:h-6 bg-gray-600/30 rounded mb-2 sm:mb-3"></div>
                      <div className="h-3 sm:h-4 bg-gray-600/20 rounded mb-3 sm:mb-4"></div>
                      <div className="flex justify-between">
                        <div className="h-3 sm:h-4 bg-gray-600/20 rounded w-16 sm:w-20"></div>
                        <div className="h-3 sm:h-4 bg-gray-600/20 rounded w-12 sm:w-16"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <>
                {/* Responsive Enhanced Dataset Grid */}
                <div className={`grid gap-4 sm:gap-6 ${
                  viewMode === 'grid' 
                    ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3' 
                    : 'grid-cols-1'
                }`}>
                  {datasets.map((dataset) => (
                    <Link
                      key={dataset.id}
                      to={`/datasets/${dataset.id}`}
                      className="group bg-black/30 backdrop-blur-lg rounded-xl sm:rounded-2xl border border-gray-700 hover:border-cyan-400/50 transition-all duration-500 hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/20 overflow-hidden"
                    >
                      {/* Responsive Enhanced Dataset Header */}
                      <div className="relative h-32 sm:h-40 md:h-48 bg-gradient-to-br from-purple-600/20 via-cyan-600/20 to-pink-600/20 flex items-center justify-center">
                        <div className="absolute inset-0 bg-black/20"></div>
                        <div className="relative text-center z-10">
                          <TagIcon className="h-8 w-8 sm:h-12 sm:w-12 md:h-16 md:w-16 text-cyan-400 mx-auto mb-2 sm:mb-3 group-hover:scale-110 transition-transform duration-300" />
                          <span className="text-white font-bold text-sm sm:text-base md:text-lg bg-black/30 px-2 sm:px-3 md:px-4 py-1 sm:py-2 rounded-full backdrop-blur-sm">
                            {dataset.category_name}
                          </span>
                        </div>
                        <div className="absolute top-2 sm:top-4 right-2 sm:right-4">
                          <HeartIcon className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6 text-gray-400 hover:text-red-400 transition-colors cursor-pointer" />
                        </div>
                      </div>

                      <div className="p-4 sm:p-5 md:p-6">
                        {/* Responsive Title and Description */}
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2 sm:mb-3 group-hover:text-cyan-400 transition-colors duration-300 line-clamp-2">
                          {dataset.title}
                        </h3>
                        <p className="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-4 line-clamp-2 sm:line-clamp-3">
                          {dataset.description}
                        </p>

                        {/* Responsive Enhanced Tags */}
                        <div className="flex flex-wrap gap-1 sm:gap-2 mb-3 sm:mb-4">
                          {dataset.tags.slice(0, viewMode === 'list' ? 5 : 3).map((tag) => (
                            <span
                              key={tag.id}
                              className="px-2 sm:px-3 py-0.5 sm:py-1 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 text-xs rounded-full border border-cyan-500/30"
                            >
                              {tag.name}
                            </span>
                          ))}
                          {dataset.tags.length > (viewMode === 'list' ? 5 : 3) && (
                            <span className="px-2 sm:px-3 py-0.5 sm:py-1 bg-gray-600/20 text-gray-400 text-xs rounded-full border border-gray-600/30">
                              +{dataset.tags.length - (viewMode === 'list' ? 5 : 3)} more
                            </span>
                          )}
                        </div>

                        {/* Responsive Enhanced Stats */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs sm:text-sm text-gray-400 mb-3 sm:mb-4 gap-2 sm:gap-4">
                          <div className="flex items-center gap-3 sm:gap-4">
                            <div className="flex items-center">
                              <CloudArrowDownIcon className="h-3 w-3 sm:h-4 sm:w-4 mr-1 text-green-400" />
                              <span className="text-white font-medium">{dataset.download_count}</span>
                            </div>
                            <div className="flex items-center">
                              <div className="flex">
                                {renderStars(dataset.review_stats?.average_rating || dataset.rating_average)}
                              </div>
                              <span className="ml-1 sm:ml-2 text-white">({dataset.review_stats?.total_reviews || dataset.rating_count})</span>
                            </div>
                          </div>
                          <div className="text-xs bg-black/30 px-2 py-1 rounded-full self-start sm:self-auto">
                            {formatFileSize(dataset.file_size)}
                          </div>
                        </div>

                        {/* Responsive Enhanced Price and Owner */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
                          <div className="flex items-center">
                            {dataset.is_free ? (
                              <span className="text-green-400 font-bold text-base sm:text-lg">FREE</span>
                            ) : (
                              <div className="flex items-center text-white font-bold text-base sm:text-lg">
                                <CurrencyDollarIcon className="h-4 w-4 sm:h-5 sm:w-5 mr-1 text-yellow-400" />
                                {formatPrice(dataset.price)} NCR
                              </div>
                            )}
                          </div>
                          <div className="flex items-center text-xs sm:text-sm text-gray-400">
                            <UserIcon className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                            <span className="text-cyan-300 truncate">{dataset.owner_name}</span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>

                {/* Responsive Enhanced Empty State */}
                {datasets.length === 0 && !loading && (
                  <div className="text-center py-12 sm:py-16 md:py-20">
                    <div className="bg-black/20 backdrop-blur-lg rounded-xl sm:rounded-2xl border border-purple-500/20 p-6 sm:p-8 md:p-12 max-w-sm sm:max-w-md mx-auto">
                      <TagIcon className="h-12 w-12 sm:h-16 sm:w-16 md:h-20 md:w-20 text-gray-500 mx-auto mb-4 sm:mb-6" />
                      <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-3 sm:mb-4">
                        No Datasets Found
                      </h3>
                      <p className="text-gray-400 mb-4 sm:mb-6 leading-relaxed text-sm sm:text-base">
                        We couldn't find any datasets matching your criteria. Try adjusting your filters or search terms.
                      </p>
                      <button
                        onClick={clearFilters}
                        className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 sm:px-8 py-2 sm:py-3 rounded-full font-bold hover:scale-105 transition-all duration-300 text-sm sm:text-base"
                      >
                        Clear All Filters
                      </button>
                    </div>
                  </div>
                )}

                {/* Responsive Enhanced Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-center mt-8 sm:mt-12 px-4">
                    <div className="bg-black/20 backdrop-blur-lg rounded-xl sm:rounded-2xl border border-purple-500/20 p-3 sm:p-4">
                      <div className="flex items-center space-x-1 sm:space-x-2">
                        <button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          className="px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 bg-black/30 text-white rounded-md sm:rounded-lg border border-gray-600 hover:border-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 text-xs sm:text-sm"
                        >
                          <span className="hidden sm:inline">Previous</span>
                          <span className="sm:hidden">Prev</span>
                        </button>
                        
                        {Array.from({ length: Math.min(window.innerWidth < 640 ? 3 : 5, totalPages) }, (_, i) => {
                          const page = i + 1;
                          return (
                            <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded-md sm:rounded-lg transition-all duration-300 text-xs sm:text-sm ${
                                currentPage === page 
                                  ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white' 
                                  : 'bg-black/30 text-gray-300 border border-gray-600 hover:border-cyan-400 hover:text-white'
                              }`}
                            >
                              {page}
                            </button>
                          );
                        })}
                        
                        <button
                          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                          disabled={currentPage === totalPages}
                          className="px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 bg-black/30 text-white rounded-md sm:rounded-lg border border-gray-600 hover:border-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 text-xs sm:text-sm"
                        >
                          <span className="hidden sm:inline">Next</span>
                          <span className="sm:hidden">→</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatasetsPage;
