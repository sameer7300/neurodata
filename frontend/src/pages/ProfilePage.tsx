import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWeb3 } from '../contexts/Web3Context';
import api from '../services/api';
import toast from 'react-hot-toast';
import {
  UserIcon,
  EnvelopeIcon,
  WalletIcon,
  ShieldCheckIcon,
  CogIcon,
  BellIcon,
  KeyIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

interface ProfileData {
  user_email: string;
  user_username: string;
  user_first_name: string;
  user_last_name: string;
  wallet_address?: string;
  bio: string;
  website: string;
  location: string;
  verification_status: string;
  email_notifications: boolean;
  marketing_emails: boolean;
}

const ProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { account, isConnected } = useWeb3();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData>({
    user_email: '',
    user_username: '',
    user_first_name: '',
    user_last_name: '',
    wallet_address: '',
    bio: '',
    website: '',
    location: '',
    verification_status: 'unverified',
    email_notifications: true,
    marketing_emails: false,
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/auth/profile/');
      setProfileData(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
      toast.error('Failed to load profile data');
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.patch('/auth/profile/', {
        user_first_name: profileData.user_first_name,
        user_last_name: profileData.user_last_name,
        bio: profileData.bio,
        website: profileData.website,
        location: profileData.location,
        email_notifications: profileData.email_notifications,
        marketing_emails: profileData.marketing_emails,
      });

      toast.success('Profile updated successfully!');
      await refreshUser();
    } catch (error: any) {
      console.error('Profile update error:', error);
      toast.error(error.response?.data?.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleWalletLink = async () => {
    if (!isConnected || !account) {
      toast.error('Please connect your wallet first');
      return;
    }

    try {
      await api.post('/auth/wallet/link/', {
        wallet_address: account,
      });
      
      toast.success('Wallet linked successfully!');
      await fetchProfile();
      await refreshUser();
    } catch (error: any) {
      console.error('Wallet link error:', error);
      toast.error(error.response?.data?.message || 'Failed to link wallet');
    }
  };

  const handleWalletUnlink = async () => {
    try {
      await api.post('/auth/wallet/unlink/');
      toast.success('Wallet unlinked successfully!');
      await fetchProfile();
      await refreshUser();
    } catch (error: any) {
      console.error('Wallet unlink error:', error);
      toast.error(error.response?.data?.message || 'Failed to unlink wallet');
    }
  };

  const getVerificationBadge = (status: string) => {
    const badges = {
      verified: { color: 'bg-green-100 text-green-800', text: '✓ Verified' },
      pending: { color: 'bg-yellow-100 text-yellow-800', text: '⏳ Pending' },
      unverified: { color: 'bg-gray-100 text-gray-800', text: '❌ Unverified' },
    };
    return badges[status as keyof typeof badges] || badges.unverified;
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'wallet', name: 'Wallet', icon: WalletIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
          <p className="text-gray-600 mt-1">
            Manage your account settings and preferences
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="card-body">
                <div className="text-center mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-primary-400 to-secondary-400 rounded-full flex items-center justify-center mx-auto mb-4">
                    <UserIcon className="h-10 w-10 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{user?.username}</h3>
                  <p className="text-sm text-gray-600">{user?.email}</p>
                  <div className="mt-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getVerificationBadge(profileData.verification_status).color}`}>
                      {getVerificationBadge(profileData.verification_status).text}
                    </span>
                  </div>
                </div>

                <nav className="space-y-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        activeTab === tab.id
                          ? 'bg-primary-100 text-primary-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <tab.icon className="h-5 w-5 mr-3" />
                      {tab.name}
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="card">
              <div className="card-body">
                {/* Profile Tab */}
                {activeTab === 'profile' && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile Information</h2>
                    <form onSubmit={handleProfileUpdate} className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            First Name
                          </label>
                          <input
                            type="text"
                            value={profileData.user_first_name}
                            onChange={(e) => setProfileData({ ...profileData, user_first_name: e.target.value })}
                            className="input-field"
                            placeholder="Enter your first name"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Last Name
                          </label>
                          <input
                            type="text"
                            value={profileData.user_last_name}
                            onChange={(e) => setProfileData({ ...profileData, user_last_name: e.target.value })}
                            className="input-field"
                            placeholder="Enter your last name"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Bio
                        </label>
                        <textarea
                          value={profileData.bio}
                          onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                          rows={4}
                          className="input-field"
                          placeholder="Tell us about yourself..."
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Website
                          </label>
                          <input
                            type="url"
                            value={profileData.website}
                            onChange={(e) => setProfileData({ ...profileData, website: e.target.value })}
                            className="input-field"
                            placeholder="https://yourwebsite.com"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Location
                          </label>
                          <input
                            type="text"
                            value={profileData.location}
                            onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
                            className="input-field"
                            placeholder="City, Country"
                          />
                        </div>
                      </div>

                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={loading}
                          className="btn-primary"
                        >
                          {loading ? 'Updating...' : 'Update Profile'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Wallet Tab */}
                {activeTab === 'wallet' && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Wallet Management</h2>
                    
                    <div className="space-y-6">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-start">
                          <WalletIcon className="h-6 w-6 text-blue-600 mt-1 mr-3" />
                          <div>
                            <h3 className="font-medium text-blue-900">Wallet Connection</h3>
                            <p className="text-sm text-blue-700 mt-1">
                              Connect your wallet to enable dataset purchases and earnings
                            </p>
                          </div>
                        </div>
                      </div>

                      {profileData.wallet_address ? (
                        <div className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium text-gray-900">Connected Wallet</h4>
                              <p className="text-sm text-gray-600 font-mono">
                                {profileData.wallet_address}
                              </p>
                            </div>
                            <button
                              onClick={handleWalletUnlink}
                              className="btn-secondary text-red-600 hover:bg-red-50"
                            >
                              Disconnect
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="border border-gray-200 rounded-lg p-4">
                          <div className="text-center">
                            <WalletIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                            <h4 className="font-medium text-gray-900 mb-2">No Wallet Connected</h4>
                            <p className="text-sm text-gray-600 mb-4">
                              Connect your wallet to start buying and selling datasets
                            </p>
                            <button
                              onClick={handleWalletLink}
                              disabled={!isConnected}
                              className="btn-primary"
                            >
                              {isConnected ? 'Link Wallet' : 'Connect Wallet First'}
                            </button>
                          </div>
                        </div>
                      )}

                      {isConnected && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-start">
                            <ShieldCheckIcon className="h-6 w-6 text-green-600 mt-1 mr-3" />
                            <div>
                              <h3 className="font-medium text-green-900">Wallet Status: Connected</h3>
                              <p className="text-sm text-green-700 mt-1">
                                Current wallet: {account}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Notifications Tab */}
                {activeTab === 'notifications' && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Notification Preferences</h2>
                    
                    <form onSubmit={handleProfileUpdate} className="space-y-6">
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Email Notifications</h4>
                            <p className="text-sm text-gray-600">
                              Receive notifications about your datasets and purchases
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={profileData.email_notifications}
                              onChange={(e) => setProfileData({ ...profileData, email_notifications: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                          </label>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Marketing Emails</h4>
                            <p className="text-sm text-gray-600">
                              Receive updates about new features and promotions
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={profileData.marketing_emails}
                              onChange={(e) => setProfileData({ ...profileData, marketing_emails: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                          </label>
                        </div>
                      </div>

                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={loading}
                          className="btn-primary"
                        >
                          {loading ? 'Updating...' : 'Save Preferences'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Security Tab */}
                {activeTab === 'security' && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Security Settings</h2>
                    
                    <div className="space-y-6">
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex items-start">
                          <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600 mt-1 mr-3" />
                          <div>
                            <h3 className="font-medium text-yellow-900">Account Security</h3>
                            <p className="text-sm text-yellow-700 mt-1">
                              Keep your account secure by using strong passwords and enabling two-factor authentication
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Password</h4>
                            <p className="text-sm text-gray-600">
                              Last updated: Never
                            </p>
                          </div>
                          <button className="btn-secondary">
                            Change Password
                          </button>
                        </div>
                      </div>

                      <div className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">Two-Factor Authentication</h4>
                            <p className="text-sm text-gray-600">
                              Add an extra layer of security to your account
                            </p>
                          </div>
                          <button className="btn-secondary" disabled>
                            Enable 2FA (Coming Soon)
                          </button>
                        </div>
                      </div>

                      <div className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">API Keys</h4>
                            <p className="text-sm text-gray-600">
                              Manage API keys for programmatic access
                            </p>
                          </div>
                          <button className="btn-secondary" disabled>
                            Manage Keys (Coming Soon)
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
