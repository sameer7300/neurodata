import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ChartBarIcon, 
  ShieldCheckIcon, 
  CurrencyDollarIcon,
  CloudArrowUpIcon,
  MagnifyingGlassIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';

const HomePage: React.FC = () => {
  const features = [
    {
      name: 'Decentralized Storage',
      description: 'Your datasets are stored securely on IPFS with encryption, ensuring data integrity and availability.',
      icon: CloudArrowUpIcon,
    },
    {
      name: 'Blockchain Payments',
      description: 'Secure transactions using NeuroCoin (NRC) with smart contract escrow protection.',
      icon: CurrencyDollarIcon,
    },
    {
      name: 'Data Quality Assurance',
      description: 'Community-driven reviews and ratings help you find the highest quality datasets.',
      icon: ShieldCheckIcon,
    },
    {
      name: 'Advanced Analytics',
      description: 'Built-in ML training capabilities and comprehensive dataset analytics.',
      icon: ChartBarIcon,
    },
    {
      name: 'Easy Discovery',
      description: 'Powerful search and filtering tools to find exactly the data you need.',
      icon: MagnifyingGlassIcon,
    },
    {
      name: 'Global Community',
      description: 'Connect with data scientists and researchers from around the world.',
      icon: UserGroupIcon,
    },
  ];

  const stats = [
    { name: 'Datasets Available', value: '10,000+' },
    { name: 'Active Users', value: '5,000+' },
    { name: 'Total Transactions', value: '$2M+' },
    { name: 'Countries Served', value: '50+' },
  ];

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 to-secondary-50"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              The Future of{' '}
              <span className="text-gradient-primary">AI Data Trading</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Buy, sell, and discover high-quality AI datasets on the world's first 
              decentralized data marketplace. Powered by blockchain technology and NeuroCoin.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/datasets"
                className="btn-primary btn-lg"
              >
                Explore Datasets
              </Link>
              <Link
                to="/upload"
                className="btn-outline btn-lg"
              >
                Upload Your Data
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.name} className="text-center">
                <div className="text-3xl font-bold text-primary-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600">{stat.name}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose NeuroData?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              We're revolutionizing how AI datasets are bought, sold, and shared 
              with cutting-edge blockchain technology.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.name}
                className="card hover-lift hover-glow transition-all duration-300"
              >
                <div className="card-body">
                  <div className="flex items-center mb-4">
                    <div className="flex-shrink-0">
                      <feature.icon className="h-8 w-8 text-primary-600" />
                    </div>
                    <h3 className="ml-3 text-lg font-semibold text-gray-900">
                      {feature.name}
                    </h3>
                  </div>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-white py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Getting started with NeuroData is simple and secure.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Connect Your Wallet
              </h3>
              <p className="text-gray-600">
                Connect your MetaMask or other Web3 wallet to get started with secure transactions.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Browse & Purchase
              </h3>
              <p className="text-gray-600">
                Discover high-quality datasets and purchase them securely using NeuroCoin (NRC).
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Start Building
              </h3>
              <p className="text-gray-600">
                Download your datasets and start building amazing AI models with confidence.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-primary py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join thousands of data scientists and researchers who trust NeuroData 
            for their AI dataset needs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="btn bg-white text-primary-600 hover:bg-gray-100 btn-lg"
            >
              Create Account
            </Link>
            <Link
              to="/datasets"
              className="btn border-white text-white hover:bg-white/10 btn-lg"
            >
              Browse Datasets
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
