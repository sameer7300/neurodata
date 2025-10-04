import React from 'react';
import { 
  WrenchScrewdriverIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const SettingsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Manage your account preferences and platform settings
          </p>
        </div>

        {/* Under Construction Card */}
        <div className="card">
          <div className="card-body text-center py-16">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <WrenchScrewdriverIcon className="h-24 w-24 text-yellow-500" />
                <div className="absolute -top-2 -right-2 bg-yellow-100 rounded-full p-2">
                  <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Settings Page Under Construction
            </h2>
            
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              We're working hard to bring you a comprehensive settings page. 
              This feature will be available soon with exciting customization options!
            </p>

            {/* Coming Soon Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-primary-600 mb-3">
                  <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Account Settings</h3>
                <p className="text-sm text-gray-600">
                  Update your profile, email preferences, and security settings
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-primary-600 mb-3">
                  <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Privacy & Security</h3>
                <p className="text-sm text-gray-600">
                  Manage your privacy settings, two-factor authentication, and API keys
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-primary-600 mb-3">
                  <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM9 7H4l5-5v5zm6 10V7a1 1 0 00-1-1H5a1 1 0 00-1 1v10a1 1 0 001 1h9a1 1 0 001-1z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Wallet & Payments</h3>
                <p className="text-sm text-gray-600">
                  Configure your wallet connections and payment preferences
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-primary-600 mb-3">
                  <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM9 7H4l5-5v5zm6 10V7a1 1 0 00-1-1H5a1 1 0 00-1 1v10a1 1 0 001 1h9a1 1 0 001-1z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Notifications</h3>
                <p className="text-sm text-gray-600">
                  Control email notifications, push alerts, and communication preferences
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-primary-600 mb-3">
                  <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 00-2-2z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Data & Analytics</h3>
                <p className="text-sm text-gray-600">
                  View your usage statistics and download your data
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-primary-600 mb-3">
                  <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Platform Preferences</h3>
                <p className="text-sm text-gray-600">
                  Customize your dashboard, themes, and user interface preferences
                </p>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-blue-50 rounded-lg p-6 mb-8">
              <div className="flex items-center justify-center mb-4">
                <ClockIcon className="h-6 w-6 text-blue-600 mr-2" />
                <h3 className="text-lg font-semibold text-blue-900">Development Timeline</h3>
              </div>
              <div className="text-sm text-blue-800">
                <p className="mb-2">🚀 <strong>Phase 1:</strong> Basic account settings (Coming Soon)</p>
                <p className="mb-2">🔐 <strong>Phase 2:</strong> Security & privacy controls</p>
                <p className="mb-2">💰 <strong>Phase 3:</strong> Wallet & payment management</p>
                <p>🎨 <strong>Phase 4:</strong> Advanced customization options</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={() => window.history.back()}
                className="btn-secondary"
              >
                Go Back
              </button>
              <button 
                onClick={() => window.location.href = '/dashboard'}
                className="btn-primary"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Temporary Quick Settings */}
        <div className="mt-8">
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
              <p className="text-sm text-gray-600">Available now while we build the full settings page</p>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button 
                  onClick={() => window.location.href = '/profile'}
                  className="flex items-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-left"
                >
                  <div className="flex-shrink-0 mr-4">
                    <svg className="h-8 w-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Edit Profile</h4>
                    <p className="text-sm text-gray-600">Update your profile information and preferences</p>
                  </div>
                </button>

                <button 
                  onClick={() => window.location.href = '/dashboard'}
                  className="flex items-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-left"
                >
                  <div className="flex-shrink-0 mr-4">
                    <svg className="h-8 w-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 00-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">View Dashboard</h4>
                    <p className="text-sm text-gray-600">Check your stats and recent activity</p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
