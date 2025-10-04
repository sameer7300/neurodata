import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useActivityTracker } from '../hooks/useActivityTracker';
import api from '../services/api';
import toast from 'react-hot-toast';
import {
  ChartBarIcon,
  DocumentIcon,
  CurrencyDollarIcon,
  StarIcon,
  HeartIcon,
  EyeIcon,
  CloudArrowDownIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  GlobeAltIcon,
  CpuChipIcon,
  LockClosedIcon,
  MagnifyingGlassIcon,
  ArrowRightIcon,
  PlayIcon,
  CheckCircleIcon,
  TrophyIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface Dataset {
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
  view_count: number;
  created_at: string;
  file_size: number;
  file_type: string;
}

interface Stats {
  total_datasets: number;
  total_users: number;
  total_volume: string;
  total_downloads: number;
  active_countries: number;
}

const EnhancedNeuroDataHomepage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { trackSearch } = useActivityTracker();
  
  const [currentFeature, setCurrentFeature] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [isVisible, setIsVisible] = useState<{ [key: string]: boolean }>({});
  const [featuredDatasets, setFeaturedDatasets] = useState<Dataset[]>([]);
  const [recentDatasets, setRecentDatasets] = useState<Dataset[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Fetch homepage data
  useEffect(() => {
    fetchHomepageData();
  }, []);

  const fetchHomepageData = async () => {
    try {
      setLoading(true);
      
      // Fetch featured datasets
      const datasetsResponse = await api.get('/datasets/datasets/?limit=6&featured=true');
      if (datasetsResponse.data.results) {
        setFeaturedDatasets(datasetsResponse.data.results);
      }
      
      // Fetch recent datasets
      const recentResponse = await api.get('/datasets/datasets/?limit=8&ordering=-created_at');
      if (recentResponse.data.results) {
        setRecentDatasets(recentResponse.data.results);
      }
      
      // Fetch platform stats (mock for now, can be replaced with real API)
      setStats({
        total_datasets: datasetsResponse.data.count || 1250,
        total_users: 5420,
        total_volume: '2.4M',
        total_downloads: 15680,
        active_countries: 52
      });
      
    } catch (error) {
      console.error('Error fetching homepage data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Search form submitted with query:', searchQuery);
    
    // Track search activity
    if (searchQuery.trim()) {
      trackSearch();
    }
    
    try {
      if (searchQuery.trim()) {
        const url = `/datasets?search=${encodeURIComponent(searchQuery.trim())}`;
        console.log('Navigating to:', url);
        navigate(url);
      } else {
        console.log('Navigating to datasets page without search');
        navigate('/datasets');
      }
    } catch (error) {
      console.error('Navigation error:', error);
      // Fallback to window.location if navigate fails
      if (searchQuery.trim()) {
        window.location.href = `/datasets?search=${encodeURIComponent(searchQuery.trim())}`;
      } else {
        window.location.href = '/datasets';
      }
    }
  };

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

  const features = [
    { icon: <LockClosedIcon className="h-8 w-8" />, title: 'Decentralized Storage', desc: 'IPFS + Encryption', color: 'from-blue-500 to-cyan-500' },
    { icon: <CurrencyDollarIcon className="h-8 w-8" />, title: 'Smart Contracts', desc: 'NeuroCoin (NCR) Payments', color: 'from-green-500 to-emerald-500' },
    { icon: <CheckCircleIcon className="h-8 w-8" />, title: 'Quality Assurance', desc: 'Community Reviews', color: 'from-purple-500 to-pink-500' },
    { icon: <CpuChipIcon className="h-8 w-8" />, title: 'ML Training', desc: 'Built-in Capabilities', color: 'from-orange-500 to-red-500' },
    { icon: <MagnifyingGlassIcon className="h-8 w-8" />, title: 'Advanced Search', desc: 'AI-Powered Discovery', color: 'from-violet-500 to-purple-500' },
    { icon: <GlobeAltIcon className="h-8 w-8" />, title: 'Global Network', desc: '50+ Countries', color: 'from-teal-500 to-cyan-500' }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentFeature(prev => (prev + 1) % features.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleIntersection = (entries: IntersectionObserverEntry[]) => {
    entries.forEach((entry: IntersectionObserverEntry) => {
      if (entry.isIntersecting) {
        setIsVisible(prev => ({ ...prev, [entry.target.id]: true }));
      }
    });
  };

  useEffect(() => {
    const observer = new IntersectionObserver(handleIntersection, {
      threshold: 0.1,
      rootMargin: '50px'
    });

    const elements = document.querySelectorAll('[data-animate]');
    elements.forEach(el => observer.observe(el));

    return () => observer.disconnect();
  }, []);

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

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 overflow-hidden">
        <div className="text-center z-10 max-w-6xl mx-auto">
          <div 
            className="mb-8 transform transition-all duration-1000 ease-out"
            style={{ transform: `translateY(${Math.max(0, scrollY * 0.2)}px)` }}
          >
            <h1 className="text-6xl md:text-8xl font-black bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-6 leading-tight">
              🧠 NeuroData
            </h1>
            <div className="h-2 w-32 bg-gradient-to-r from-cyan-400 to-purple-500 mx-auto mb-8 rounded-full"></div>
          </div>
          
          <p className="text-xl md:text-2xl text-gray-300 mb-8 leading-relaxed font-light">
            The Future of AI Data Trading
            <br />
            <span className="text-cyan-400 font-semibold">Decentralized • Secure • Intelligent</span>
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-12">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search datasets, categories, or keywords..."
                className="w-full px-6 py-4 pl-14 bg-black/30 backdrop-blur-lg border border-purple-500/30 rounded-full text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all duration-300"
              />
              <MagnifyingGlassIcon className="absolute left-5 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <button
                type="submit"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-gradient-to-r from-cyan-500 to-purple-600 text-white px-6 py-2 rounded-full hover:scale-105 transition-all duration-300"
              >
                Search
              </button>
            </div>
          </form>

          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="group relative px-8 py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-full text-white font-bold text-lg overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/25"
                >
                  <span className="relative z-10 flex items-center gap-2">
                    <ChartBarIcon className="h-5 w-5" />
                    Go to Dashboard
                  </span>
                </Link>
                <Link
                  to="/upload"
                  className="group px-8 py-4 border-2 border-cyan-400 text-cyan-400 rounded-full font-bold text-lg hover:bg-cyan-400 hover:text-black transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cyan-400/25"
                >
                  <DocumentIcon className="h-5 w-5 inline mr-2" />
                  Upload Dataset
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/datasets"
                  className="group relative px-8 py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-full text-white font-bold text-lg overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/25"
                >
                  <span className="relative z-10 flex items-center gap-2">
                    <MagnifyingGlassIcon className="h-5 w-5" />
                    Explore Datasets
                  </span>
                </Link>
                <Link
                  to="/register"
                  className="group px-8 py-4 border-2 border-cyan-400 text-cyan-400 rounded-full font-bold text-lg hover:bg-cyan-400 hover:text-black transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cyan-400/25"
                >
                  <UserGroupIcon className="h-5 w-5 inline mr-2" />
                  Join Now
                </Link>
              </>
            )}
          </div>

          {/* Floating Feature Showcase */}
          <div className="relative">
            <div className="bg-black/30 backdrop-blur-lg rounded-2xl p-6 border border-purple-500/20 max-w-md mx-auto">
              <div className="flex items-center justify-center mb-4">
                <div className="text-cyan-400 mr-4">{features[currentFeature].icon}</div>
                <div>
                  <h3 className="text-cyan-400 font-bold">{features[currentFeature].title}</h3>
                  <p className="text-gray-400 text-sm">{features[currentFeature].desc}</p>
                </div>
              </div>
              <div className="flex justify-center space-x-2">
                {features.map((_, idx) => (
                  <div
                    key={idx}
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      idx === currentFeature ? 'bg-cyan-400 w-8' : 'bg-gray-600'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-gray-400">
          <div className="animate-bounce">
            <div className="w-6 h-10 border-2 border-gray-400 rounded-full flex justify-center">
              <div className="w-1 h-3 bg-gray-400 rounded-full mt-2 animate-pulse"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Real-time Stats Section */}
      <section 
        id="stats"
        data-animate
        className={`relative py-16 transition-all duration-1000 ${
          isVisible.stats ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-black text-white mb-4">
              Platform <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">Statistics</span>
            </h2>
            <p className="text-gray-300">Real-time data from our growing ecosystem</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            {[
              { 
                number: stats?.total_datasets?.toLocaleString() || '1,250+', 
                label: 'Datasets', 
                icon: <DocumentIcon className="h-8 w-8" />,
                color: 'from-blue-500 to-cyan-500'
              },
              { 
                number: stats?.total_users?.toLocaleString() || '5,420+', 
                label: 'Active Users', 
                icon: <UserGroupIcon className="h-8 w-8" />,
                color: 'from-green-500 to-emerald-500'
              },
              { 
                number: `$${stats?.total_volume || '2.4M'}`, 
                label: 'Volume Traded', 
                icon: <CurrencyDollarIcon className="h-8 w-8" />,
                color: 'from-yellow-500 to-orange-500'
              },
              { 
                number: stats?.total_downloads?.toLocaleString() || '15,680+', 
                label: 'Downloads', 
                icon: <CloudArrowDownIcon className="h-8 w-8" />,
                color: 'from-purple-500 to-pink-500'
              },
              { 
                number: `${stats?.active_countries || 52}+`, 
                label: 'Countries', 
                icon: <GlobeAltIcon className="h-8 w-8" />,
                color: 'from-teal-500 to-cyan-500'
              }
            ].map((stat, idx) => (
              <div 
                key={idx}
                className="group text-center p-6 bg-black/20 backdrop-blur-lg rounded-xl border border-purple-500/20 hover:border-cyan-400/50 transition-all duration-300 hover:scale-105"
              >
                <div className={`inline-flex p-3 rounded-full bg-gradient-to-br ${stat.color} text-white mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  {stat.icon}
                </div>
                <div className="text-3xl font-bold text-white mb-1">{stat.number}</div>
                <div className="text-gray-400 text-sm">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

     

      {/* Features Grid */}
      <section 
        id="features"
        data-animate
        className={`py-16 transition-all duration-1000 delay-200 ${
          isVisible.features ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-black text-white mb-4">
              Why Choose <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">NeuroData?</span>
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Revolutionary blockchain technology meets AI/ML capabilities in a secure, decentralized ecosystem
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: <LockClosedIcon className="h-12 w-12" />,
                title: 'Decentralized Storage',
                desc: 'IPFS-based storage with enterprise-grade encryption ensures your data remains secure and always accessible.',
                gradient: 'from-blue-500 to-cyan-500',
                features: ['IPFS Integration', 'End-to-End Encryption', '99.9% Uptime']
              },
              {
                icon: <CurrencyDollarIcon className="h-12 w-12" />,
                title: 'Smart Contract Payments',
                desc: 'Secure transactions using NeuroCoin (NCR) with automated escrow and instant settlement.',
                gradient: 'from-green-500 to-emerald-500',
                features: ['Automated Escrow', 'Instant Settlement', 'Dispute Resolution']
              },
              {
                icon: <CheckCircleIcon className="h-12 w-12" />,
                title: 'Quality Assurance',
                desc: 'Community-driven verification and AI-powered quality scoring for premium datasets.',
                gradient: 'from-purple-500 to-pink-500',
                features: ['Peer Review System', 'AI Quality Scoring', 'Verified Purchases']
              },
              {
                icon: <CpuChipIcon className="h-12 w-12" />,
                title: 'Integrated ML Training',
                desc: 'Built-in Jupyter environments and GPU clusters for immediate model development.',
                gradient: 'from-orange-500 to-red-500',
                features: ['Jupyter Notebooks', 'GPU Acceleration', 'Model Deployment']
              },
              {
                icon: <MagnifyingGlassIcon className="h-12 w-12" />,
                title: 'AI-Powered Discovery',
                desc: 'Semantic search and recommendation engine to find the perfect datasets for your needs.',
                gradient: 'from-violet-500 to-purple-500',
                features: ['Semantic Search', 'Smart Recommendations', 'Advanced Filters']
              },
              {
                icon: <GlobeAltIcon className="h-12 w-12" />,
                title: 'Global Ecosystem',
                desc: 'Connect with researchers and data scientists from 50+ countries worldwide.',
                gradient: 'from-teal-500 to-cyan-500',
                features: ['Global Community', 'Multi-language Support', 'Regional Compliance']
              }
            ].map((feature, idx) => (
              <div
                key={idx}
                className="group relative p-8 bg-black/30 backdrop-blur-lg rounded-2xl border border-gray-700 hover:border-cyan-400/50 transition-all duration-500 hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/20"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-5 rounded-2xl group-hover:opacity-10 transition-opacity duration-300`}></div>
                <div className="relative z-10">
                  <div className={`text-cyan-400 mb-4 group-hover:scale-110 transition-transform duration-300 inline-flex p-3 rounded-full bg-gradient-to-br ${feature.gradient}`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3 group-hover:text-cyan-400 transition-colors duration-300">
                    {feature.title}
                  </h3>
                  <p className="text-gray-400 leading-relaxed mb-4">
                    {feature.desc}
                  </p>
                  <ul className="space-y-2">
                    {feature.features.map((item, itemIdx) => (
                      <li key={itemIdx} className="flex items-center text-sm text-gray-300">
                        <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section 
        id="how-it-works"
        data-animate
        className={`py-16 transition-all duration-1000 delay-400 ${
          isVisible['how-it-works'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-4xl font-black text-center text-white mb-12">
            How It <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">Works</span>
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Connect Wallet',
                desc: 'Link your MetaMask or Web3 wallet to access the decentralized marketplace.',
                color: 'from-cyan-400 to-blue-500'
              },
              {
                step: '2',
                title: 'Discover & Trade',
                desc: 'Browse premium datasets and trade securely using NeuroCoin (NCR) tokens.',
                color: 'from-purple-400 to-pink-500'
              },
              {
                step: '3',
                title: 'Build & Train',
                desc: 'Access integrated ML tools and GPU clusters to build cutting-edge AI models.',
                color: 'from-green-400 to-emerald-500'
              }
            ].map((step, idx) => (
              <div key={idx} className="relative">
                <div className="text-center group hover:scale-105 transition-all duration-300">
                  <div className={`w-20 h-20 bg-gradient-to-br ${step.color} rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl group-hover:shadow-2xl transition-shadow duration-300`}>
                    <span className="text-2xl font-black text-white">{step.step}</span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4 group-hover:text-cyan-400 transition-colors duration-300">
                    {step.title}
                  </h3>
                  <p className="text-gray-400 leading-relaxed">
                    {step.desc}
                  </p>
                </div>
                
                {idx < 2 && (
                  <div className="hidden md:block absolute top-10 -right-4 w-8 h-0.5 bg-gradient-to-r from-gray-600 to-transparent"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Datasets Section */}
    

      {/* CTA Section */}
      <section className="py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-purple-600 to-pink-600 opacity-90"></div>
        <div className="relative z-10 max-w-4xl mx-auto text-center px-6">
          <h2 className="text-5xl md:text-6xl font-black text-white mb-8">
            {isAuthenticated ? 'Ready to Contribute?' : 'Ready to Transform AI?'}
          </h2>
          <p className="text-xl text-white/90 mb-12 leading-relaxed">
            {isAuthenticated 
              ? `Welcome back, ${user?.username || 'User'}! Upload your datasets and start earning NCR tokens.`
              : 'Join the revolution in decentralized AI data trading. Build the future with NeuroData.'
            }
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            {isAuthenticated ? (
              <>
                <Link
                  to="/upload"
                  className="group px-10 py-5 bg-white text-purple-600 rounded-full font-black text-lg hover:scale-105 transition-all duration-300 hover:shadow-2xl flex items-center justify-center gap-2"
                >
                  <DocumentIcon className="h-6 w-6" />
                  Upload Dataset
                  <ArrowRightIcon className="w-0 group-hover:w-6 transition-all duration-300 overflow-hidden" />
                </Link>
                <Link
                  to="/dashboard"
                  className="group px-10 py-5 border-2 border-white text-white rounded-full font-bold text-lg hover:bg-white hover:text-purple-600 transition-all duration-300 hover:scale-105"
                >
                  <ChartBarIcon className="h-6 w-6 inline mr-2" />
                  View Dashboard
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/register"
                  className="group px-10 py-5 bg-white text-purple-600 rounded-full font-black text-lg hover:scale-105 transition-all duration-300 hover:shadow-2xl flex items-center justify-center gap-2"
                >
                  <SparklesIcon className="h-6 w-6" />
                  Start Building Now
                  <ArrowRightIcon className="w-0 group-hover:w-6 transition-all duration-300 overflow-hidden" />
                </Link>
                <Link
                  to="/datasets"
                  className="group px-10 py-5 border-2 border-white text-white rounded-full font-bold text-lg hover:bg-white hover:text-purple-600 transition-all duration-300 hover:scale-105"
                >
                  <MagnifyingGlassIcon className="h-6 w-6 inline mr-2" />
                  Explore Datasets
                </Link>
              </>
            )}
          </div>

          <div className="mt-16 grid grid-cols-3 md:grid-cols-6 gap-8 text-white/70">
            {[
              { icon: <LockClosedIcon className="h-8 w-8" />, label: 'Secure' },
              { icon: <CpuChipIcon className="h-8 w-8" />, label: 'Fast' },
              { icon: <GlobeAltIcon className="h-8 w-8" />, label: 'Decentralized' },
              { icon: <ShieldCheckIcon className="h-8 w-8" />, label: 'Verified' },
              { icon: <TrophyIcon className="h-8 w-8" />, label: 'Quality' },
              { icon: <PlayIcon className="h-8 w-8" />, label: 'Ready' }
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="text-white/80 mb-2 flex justify-center">
                  {item.icon}
                </div>
                <div className="text-sm font-medium">{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default EnhancedNeuroDataHomepage;