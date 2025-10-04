import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  EyeIcon,
  EyeSlashIcon,
  WalletIcon,
  EnvelopeIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { useWeb3 } from '../contexts/Web3Context';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, connectWalletAuth, isLoading } = useAuth();
  const { connectWallet, isConnected, account } = useWeb3();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loginMethod, setLoginMethod] = useState<'email' | 'wallet'>('email');
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const success = await login(formData.email, formData.password);
      if (success) {
        toast.success('Login successful!');
        navigate('/datasets');
      }
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWalletLogin = async () => {
    setLoading(true);
    
    // Add timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      setLoading(false);
      toast.error('Authentication timed out. Please try again.');
    }, 30000); // 30 seconds timeout
    
    try {
      if (!isConnected) {
        await connectWallet();
      }
      
      if (account) {
        const success = await connectWalletAuth();
        if (success) {
          clearTimeout(timeout);
          toast.success('Wallet authentication successful!');
          navigate('/datasets');
        } else {
          clearTimeout(timeout);
          toast.error('Wallet authentication failed');
        }
      } else {
        clearTimeout(timeout);
        toast.error('No wallet account found');
      }
    } catch (error) {
      clearTimeout(timeout);
      console.error('Wallet login error:', error);
      toast.error('Wallet authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">N</span>
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
          Sign in to NeuroData
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <Link
            to="/register"
            className="font-medium text-primary-600 hover:text-primary-500"
          >
            create a new account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-soft sm:rounded-lg sm:px-10">
          {/* Login Method Toggle */}
          <div className="mb-6">
            <div className="flex rounded-lg bg-gray-100 p-1">
              <button
                onClick={() => setLoginMethod('email')}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                  loginMethod === 'email'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <EnvelopeIcon className="h-4 w-4 inline mr-2" />
                Email
              </button>
              <button
                onClick={() => setLoginMethod('wallet')}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                  loginMethod === 'wallet'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <WalletIcon className="h-4 w-4 inline mr-2" />
                Wallet
              </button>
            </div>
          </div>

          {/* Email Login Form */}
          {loginMethod === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <div className="mt-1 relative">
                  <EnvelopeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="input pl-10"
                    placeholder="Enter your email"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <div className="mt-1 relative">
                  <LockClosedIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    className="input pl-10 pr-10"
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <Link
                    to="/forgot-password"
                    className="font-medium text-primary-600 hover:text-primary-500"
                  >
                    Forgot your password?
                  </Link>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={loading || isLoading}
                  className="btn-primary w-full disabled:opacity-50"
                >
                  {loading || isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Signing in...
                    </div>
                  ) : (
                    'Sign in'
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Wallet Login */}
          {loginMethod === 'wallet' && (
            <div className="space-y-6">
              <div className="text-center">
                <WalletIcon className="h-16 w-16 text-primary-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Connect Your Wallet
                </h3>
                <p className="text-sm text-gray-500 mb-6">
                  Sign in securely using your Web3 wallet. No password required.
                </p>
              </div>

              {isConnected && account ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                    <div>
                      <p className="text-sm font-medium text-green-800">
                        Wallet Connected
                      </p>
                      <p className="text-xs text-green-600">
                        {account.slice(0, 6)}...{account.slice(-4)}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-yellow-800">
                    Please connect your wallet to continue
                  </p>
                </div>
              )}

              <button
                onClick={handleWalletLogin}
                disabled={loading}
                className="btn-primary w-full disabled:opacity-50"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {isConnected ? 'Authenticating...' : 'Connecting...'}
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <WalletIcon className="h-5 w-5 mr-2" />
                    {isConnected ? 'Sign in with Wallet' : 'Connect Wallet'}
                  </div>
                )}
              </button>

              <div className="text-center text-xs text-gray-500">
                <p>Supported wallets: MetaMask, WalletConnect</p>
              </div>
            </div>
          )}

          {/* Divider */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">New to NeuroData?</span>
              </div>
            </div>
          </div>

          {/* Register Link */}
          <div className="mt-6">
            <Link
              to="/register"
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-lg shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Create a new account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
