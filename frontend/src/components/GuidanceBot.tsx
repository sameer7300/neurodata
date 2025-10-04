import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { activityTracker } from '../services/activityTracker';
import {
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
  SparklesIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  QuestionMarkCircleIcon,
  EyeSlashIcon,
  FireIcon,
  TrophyIcon,
  HeartIcon
} from '@heroicons/react/24/outline';

interface GuidanceStep {
  id: number;
  title: string;
  content: string;
  action?: string;
  highlight?: string;
}

interface PageGuidance {
  greeting: string;
  steps: GuidanceStep[];
  tips?: string[];
}

const GuidanceBot: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [showBanner, setShowBanner] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isGuidanceEnabled, setIsGuidanceEnabled] = useState(true);
  const [showHelpButton, setShowHelpButton] = useState(true);
  const [userActivity, setUserActivity] = useState(activityTracker.getActivity());
  const [personalizedMessage, setPersonalizedMessage] = useState('');

  // Generate personalized greeting based on user activity and context
  const getPersonalizedGreeting = (path: string): string => {
    const timeGreeting = activityTracker.getTimeBasedGreeting();
    const userName = user?.username || user?.first_name || 'there';
    const engagementLevel = activityTracker.getUserEngagementLevel();
    const isReturning = activityTracker.isReturningUser();
    const insights = activityTracker.getPersonalizedInsights();
    
    let greeting = '';
    
    if (isAuthenticated) {
      if (isReturning) {
        greeting = `${timeGreeting}, ${userName}! Welcome back to NeuroData! `;
        
        // Add activity-based messages
        if (userActivity.currentStreak >= 3) {
          greeting += `🔥 ${userActivity.currentStreak} day streak - you're amazing! `;
        }
        
        if (insights.length > 0) {
          greeting += insights[0] + ' ';
        }
        
        // Add engagement-specific messages
        switch (engagementLevel) {
          case 'expert':
            greeting += "As an expert user, you're making great progress! ";
            break;
          case 'power_user':
            greeting += "You're a power user! Thanks for being such an active member! ";
            break;
          case 'active':
            greeting += "Great to see you staying active on the platform! ";
            break;
        }
      } else {
        greeting = `${timeGreeting}, ${userName}! Welcome to NeuroData! `;
        greeting += "I'm excited to help you get started with AI datasets! ";
      }
    } else {
      greeting = `${timeGreeting}! Welcome to NeuroData! `;
      greeting += "Ready to explore the world's largest AI dataset marketplace? ";
    }
    
    return greeting.trim();
  };

  // Action handlers for interactive guidance
  const handleAction = (action: string) => {
    switch (action) {
      case 'Explore the homepage features':
        scrollToSection('features');
        break;
      case 'Try searching for a dataset':
        focusSearchInput();
        break;
      case 'Scroll down to see stats':
        scrollToSection('stats');
        break;
      case 'Go to Datasets':
        navigate('/datasets');
        break;
      case 'Sign Up Now':
        navigate('/register');
        break;
      case 'Try using the search or filters':
        focusSearchInput();
        break;
      case 'Click on a dataset card':
        highlightDatasetCards();
        break;
      case 'Browse available datasets':
        scrollToSection('recent-datasets');
        break;
      case 'Look for highly rated datasets':
        highlightRatedDatasets();
        break;
      case 'Fill out the dataset details form':
        focusElement('dataset-title');
        break;
      case 'Set your dataset price in NCR':
        focusElement('dataset-price');
        break;
      case 'Choose appropriate tags and category':
        focusElement('dataset-category');
        break;
      case 'Select and upload your files':
        focusElement('file-upload');
        break;
      case 'Submit your dataset for review':
        scrollToSection('submit-section');
        break;
      case 'Browse available algorithms':
        scrollToSection('algorithms');
        break;
      case 'Select a training dataset':
        scrollToSection('dataset-selection');
        break;
      case 'Configure training settings':
        scrollToSection('training-config');
        break;
      case 'Start the training process':
        focusElement('start-training');
        break;
      case 'Monitor your training job':
        scrollToSection('training-monitor');
        break;
      default:
        console.log('Action not implemented:', action);
    }
  };

  // Utility functions for actions
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
      // Add highlight effect
      element.classList.add('ring-4', 'ring-cyan-400', 'ring-opacity-50');
      setTimeout(() => {
        element.classList.remove('ring-4', 'ring-cyan-400', 'ring-opacity-50');
      }, 3000);
    }
  };

  const focusSearchInput = () => {
    const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement;
    if (searchInput) {
      searchInput.focus();
      searchInput.classList.add('ring-4', 'ring-cyan-400', 'ring-opacity-50');
      setTimeout(() => {
        searchInput.classList.remove('ring-4', 'ring-cyan-400', 'ring-opacity-50');
      }, 3000);
    }
  };

  const focusElement = (elementId: string) => {
    const element = document.getElementById(elementId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
        (element as HTMLInputElement).focus();
      }
      element.classList.add('ring-4', 'ring-cyan-400', 'ring-opacity-50');
      setTimeout(() => {
        element.classList.remove('ring-4', 'ring-cyan-400', 'ring-opacity-50');
      }, 3000);
    }
  };

  const highlightDatasetCards = () => {
    const cards = document.querySelectorAll('[data-dataset-card]');
    cards.forEach((card, index) => {
      setTimeout(() => {
        card.classList.add('ring-4', 'ring-cyan-400', 'ring-opacity-50', 'scale-105');
        setTimeout(() => {
          card.classList.remove('ring-4', 'ring-cyan-400', 'ring-opacity-50', 'scale-105');
        }, 2000);
      }, index * 200);
    });
  };

  const highlightRatedDatasets = () => {
    const ratedCards = document.querySelectorAll('[data-rating]');
    ratedCards.forEach((card, index) => {
      const rating = parseFloat(card.getAttribute('data-rating') || '0');
      if (rating >= 4.0) {
        setTimeout(() => {
          card.classList.add('ring-4', 'ring-yellow-400', 'ring-opacity-50');
          setTimeout(() => {
            card.classList.remove('ring-4', 'ring-yellow-400', 'ring-opacity-50');
          }, 2000);
        }, index * 150);
      }
    });
  };

  // Get current page guidance
  const getCurrentPageGuidance = (): PageGuidance => {
    const path = location.pathname;
    
    switch (path) {
      case '/':
        return {
          greeting: getPersonalizedGreeting(path),
          steps: [
            {
              id: 1,
              title: "🏠 Welcome Home",
              content: "This is your gateway to the world's largest decentralized AI dataset marketplace. Here you can discover, buy, and sell high-quality datasets.",
              action: "Explore the homepage features"
            },
            {
              id: 2,
              title: "🔍 Search Datasets",
              content: "Use the search bar above to find specific datasets, categories, or keywords. Try searching for 'computer vision' or 'NLP'.",
              action: "Try searching for a dataset"
            },
            {
              id: 3,
              title: "📊 Platform Stats",
              content: "Check out our real-time platform statistics showing total datasets, users, and transactions.",
              action: "Scroll down to see stats"
            },
            {
              id: 4,
              title: "📋 Recent Datasets",
              content: "Explore our latest datasets uploaded by the community. Click on any dataset to view details.",
              action: "Browse available datasets"
            },
            {
              id: 5,
              title: "🚀 Get Started",
              content: isAuthenticated 
                ? "You're all set! Visit the datasets page to browse, or upload your own data to start earning."
                : "Ready to join? Sign up to start buying datasets or upload your own to earn NCR tokens.",
              action: isAuthenticated ? "Go to Datasets" : "Sign Up Now"
            }
          ],
          tips: [
            "💡 Use filters to find exactly what you need",
            "🔒 All transactions are secured with escrow protection",
            "⭐ Check dataset ratings and reviews before purchasing"
          ]
        };

      case '/datasets':
        const suggestions = activityTracker.getSmartSuggestions();
        let datasetsGreeting = getPersonalizedGreeting(path);
        
        if (suggestions.length > 0) {
          datasetsGreeting += ` 💡 ${suggestions[0]}`;
        } else {
          datasetsGreeting += " Let me help you find the perfect datasets!";
        }
        
        return {
          greeting: datasetsGreeting,
          steps: [
            {
              id: 1,
              title: "🔍 Search & Filter",
              content: "Use the search bar and filters to narrow down datasets. You can filter by category, price range, and sort by popularity or date.",
              action: "Try using the search or filters"
            },
            {
              id: 2,
              title: "📋 Dataset Cards",
              content: "Each card shows key information: title, description, price, file size, and ratings. Click on any dataset to view detailed information.",
              action: "Click on a dataset card"
            },
            {
              id: 3,
              title: "💰 Purchase Process",
              content: "When you find a dataset you like, click 'Purchase' to buy it. All purchases are protected by our escrow system.",
              action: "Browse available datasets"
            },
            {
              id: 4,
              title: "⭐ Reviews & Ratings",
              content: "Check reviews and ratings from other users to ensure dataset quality before making a purchase.",
              action: "Look for highly rated datasets"
            }
          ],
          tips: [
            "💡 Start with free datasets to test the platform",
            "🏷️ Use category filters to find relevant data quickly",
            "📈 Sort by 'Most Popular' to see trending datasets"
          ]
        };

      case '/upload':
        let uploadGreeting = getPersonalizedGreeting(path);
        
        if (userActivity.datasetsUploaded > 0) {
          uploadGreeting += ` You've already uploaded ${userActivity.datasetsUploaded} dataset${userActivity.datasetsUploaded > 1 ? 's' : ''}! Ready for another one?`;
        } else {
          uploadGreeting += " Ready to monetize your data? Let's upload your first dataset!";
        }
        
        return {
          greeting: uploadGreeting,
          steps: [
            {
              id: 1,
              title: "📄 Dataset Information",
              content: "Start by filling out your dataset's basic information: title, description, and category. Make it descriptive and engaging!",
              action: "Fill out the dataset details form"
            },
            {
              id: 2,
              title: "💰 Set Your Price",
              content: "Choose a competitive price for your dataset. Consider the data quality, uniqueness, and market demand.",
              action: "Set your dataset price in NCR"
            },
            {
              id: 3,
              title: "🏷️ Add Tags & Category",
              content: "Select relevant tags and category to help users discover your dataset. Good tagging increases visibility!",
              action: "Choose appropriate tags and category"
            },
            {
              id: 4,
              title: "📁 Upload Files",
              content: "Upload your dataset files. Supported formats include CSV, JSON, images, and compressed archives. Max size: 100MB.",
              action: "Select and upload your files"
            },
            {
              id: 5,
              title: "✅ Review & Submit",
              content: "Review all information and submit for approval. Our team will review your dataset within 24 hours.",
              action: "Submit your dataset for review"
            }
          ],
          tips: [
            "📝 Write clear, detailed descriptions to attract buyers",
            "🎯 Research similar datasets to price competitively",
            "🔍 Use relevant keywords in your title and description"
          ]
        };

      case '/ml/training':
        let mlGreeting = getPersonalizedGreeting(path);
        
        if (userActivity.datasetsUploaded > 0 || userActivity.datasetsPurchased > 0) {
          mlGreeting += " Perfect! You have datasets ready. Let's train some AI models!";
        } else {
          mlGreeting += " Let's train your first AI model together!";
        }
        
        return {
          greeting: mlGreeting,
          steps: [
            {
              id: 1,
              title: "🤖 Choose Algorithm",
              content: "Select from our available ML algorithms based on your data type and problem. Each algorithm shows compatibility and use cases.",
              action: "Browse available algorithms"
            },
            {
              id: 2,
              title: "📊 Select Dataset",
              content: "Choose a dataset from your purchased datasets or use one of our sample datasets to train your model.",
              action: "Select a training dataset"
            },
            {
              id: 3,
              title: "⚙️ Configure Parameters",
              content: "Adjust training parameters like learning rate, epochs, and batch size. Use default values if you're unsure.",
              action: "Configure training settings"
            },
            {
              id: 4,
              title: "🚀 Start Training",
              content: "Launch your training job! You can monitor progress in real-time and view training metrics and logs.",
              action: "Start the training process"
            },
            {
              id: 5,
              title: "📈 Monitor Progress",
              content: "Track your model's training progress, view metrics, and download the trained model when complete.",
              action: "Monitor your training job"
            }
          ],
          tips: [
            "🎯 Start with smaller datasets for faster training",
            "📊 Monitor training metrics to avoid overfitting",
            "💾 Download your trained models for local use"
          ]
        };

      default:
        return {
          greeting: "Hi there! I'm your NeuroData assistant. How can I help you today?",
          steps: [
            {
              id: 1,
              title: "🤖 I'm Here to Help",
              content: "I provide step-by-step guidance for using NeuroData. Navigate to different pages to get specific help!",
              action: "Explore the platform"
            }
          ],
          tips: ["💡 I appear on every page with relevant guidance!"]
        };
    }
  };

  const guidance = getCurrentPageGuidance();

  // Check if user wants guidance and show banner on page load
  useEffect(() => {
    // Track page visit
    activityTracker.trackPageVisit(location.pathname);
    
    // Update activity state
    setUserActivity(activityTracker.getActivity());
    
    const guidanceDisabled = localStorage.getItem('guidance_disabled') === 'true';
    const pageKey = `guidance_seen_${location.pathname}`;
    const hasSeenThisPage = localStorage.getItem(pageKey);
    
    setIsGuidanceEnabled(!guidanceDisabled);
    
    // Show banner if guidance is enabled and user hasn't seen this page
    if (!guidanceDisabled && !hasSeenThisPage && isGuidanceEnabled) {
      setShowBanner(true);
      setShowHelpButton(false); // Hide help button when banner is shown
    } else {
      setShowBanner(false);
      setShowHelpButton(true); // Show help button when banner is hidden
    }
    
    // Reset step when page changes
    setCurrentStep(0);
    
    // Generate personalized message based on activity
    const insights = activityTracker.getPersonalizedInsights();
    if (insights.length > 0) {
      setPersonalizedMessage(insights[Math.floor(Math.random() * insights.length)]);
    }
  }, [location.pathname, isGuidanceEnabled]);

  const nextStep = () => {
    if (currentStep < guidance.steps.length - 1) {
      setCurrentStep(currentStep + 1);
      activityTracker.trackGuidanceStep();
      
      // Check if tutorial is completed
      if (currentStep + 1 === guidance.steps.length - 1) {
        activityTracker.trackTutorialCompletion(location.pathname);
      }
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const resetTutorial = () => {
    setCurrentStep(0);
  };

  const skipGuidance = () => {
    const pageKey = `guidance_seen_${location.pathname}`;
    localStorage.setItem(pageKey, 'true');
    setShowBanner(false);
    setShowHelpButton(true);
    activityTracker.trackGuidanceSkip();
  };

  const disableGuidance = () => {
    localStorage.setItem('guidance_disabled', 'true');
    setIsGuidanceEnabled(false);
    setShowBanner(false);
    setShowHelpButton(true);
    activityTracker.trackGuidanceSkip();
  };

  const enableGuidance = () => {
    localStorage.removeItem('guidance_disabled');
    setIsGuidanceEnabled(true);
    setShowBanner(true);
    setShowHelpButton(false);
    activityTracker.trackHelpButtonClick();
    // Reset current page as not seen
    const pageKey = `guidance_seen_${location.pathname}`;
    localStorage.removeItem(pageKey);
  };

  return (
    <>
      {/* Top Banner Guidance */}
      {showBanner && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 text-white shadow-lg animate-slide-down">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              {/* Left: Icon and Current Step Info */}
              <div className="flex items-center space-x-4">
                <div className="bg-white/20 rounded-full p-2">
                  <SparklesIcon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold text-sm">
                      {guidance.steps[currentStep]?.title}
                    </h3>
                    <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                      {currentStep + 1}/{guidance.steps.length}
                    </span>
                  </div>
                  <p className="text-white/90 text-sm leading-relaxed max-w-2xl">
                    {guidance.steps[currentStep]?.content}
                  </p>
                  
                  {/* Personalized Message */}
                  {personalizedMessage && (
                    <div className="mt-2 flex items-center space-x-1 text-yellow-200 bg-white/10 rounded-lg px-2 py-1">
                      <TrophyIcon className="h-3 w-3" />
                      <span className="text-xs font-medium">
                        {personalizedMessage}
                      </span>
                    </div>
                  )}
                  
                  {guidance.steps[currentStep]?.action && (
                    <button
                      onClick={() => handleAction(guidance.steps[currentStep].action!)}
                      className="mt-2 flex items-center space-x-2 text-cyan-200 bg-white/10 hover:bg-white/20 px-3 py-2 rounded-lg transition-all duration-300 hover:scale-105 group"
                    >
                      <ArrowRightIcon className="h-3 w-3 group-hover:translate-x-1 transition-transform duration-300" />
                      <span className="text-xs font-medium">
                        {guidance.steps[currentStep].action}
                      </span>
                      <SparklesIcon className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    </button>
                  )}
                </div>
              </div>

              {/* Right: Controls */}
              <div className="flex items-center space-x-3">
                {/* Progress Bar */}
                <div className="hidden md:flex items-center space-x-2">
                  <div className="w-24 bg-white/20 rounded-full h-2">
                    <div 
                      className="bg-white h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((currentStep + 1) / guidance.steps.length) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-white/80">
                    {Math.round(((currentStep + 1) / guidance.steps.length) * 100)}%
                  </span>
                </div>

                {/* Navigation Buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={prevStep}
                    disabled={currentStep === 0}
                    className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Previous Step"
                  >
                    <ChevronLeftIcon className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={nextStep}
                    disabled={currentStep === guidance.steps.length - 1}
                    className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Next Step"
                  >
                    <ChevronRightIcon className="h-4 w-4" />
                  </button>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2 border-l border-white/20 pl-3">
                  <button
                    onClick={skipGuidance}
                    className="px-3 py-1.5 text-xs bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                  >
                    Skip for this page
                  </button>
                  
                  <button
                    onClick={disableGuidance}
                    className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 transition-colors group"
                    title="Disable guidance"
                  >
                    <EyeSlashIcon className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={skipGuidance}
                    className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
                    title="Close"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Help Button */}
      {showHelpButton && (
        <div className="fixed bottom-6 right-6 z-40 group">
          {/* Animated Rings */}
          <div className="absolute inset-0 rounded-full animate-ping bg-gradient-to-r from-purple-400 to-cyan-400 opacity-20"></div>
          <div className="absolute inset-0 rounded-full animate-pulse bg-gradient-to-r from-purple-500 to-cyan-500 opacity-30 scale-110"></div>
          
          <button
            onClick={enableGuidance}
            className="relative bg-gradient-to-br from-purple-600 via-blue-600 to-cyan-600 text-white p-4 rounded-full shadow-2xl hover:shadow-purple-500/25 hover:scale-110 transition-all duration-500 group backdrop-blur-sm border border-white/20 overflow-hidden"
            title="Get Help & Guidance"
          >
            {/* Button Background Animation */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="absolute inset-0 bg-gradient-to-br from-transparent via-cyan-400/20 to-purple-400/20 animate-pulse"></div>
            
            {/* Icon */}
            <QuestionMarkCircleIcon className="relative h-6 w-6 group-hover:rotate-12 group-hover:scale-110 transition-all duration-300" />
            
            {/* Sparkle Effects */}
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-ping opacity-75"></div>
            <div className="absolute -bottom-1 -left-1 w-2 h-2 bg-cyan-300 rounded-full animate-bounce delay-300 opacity-75"></div>
          </button>
          
          {/* Enhanced Tooltip */}
          <div className="absolute bottom-full right-0 mb-3 px-4 py-2 bg-gradient-to-r from-gray-900 via-slate-800 to-gray-900 text-white text-sm rounded-xl opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap pointer-events-none shadow-2xl border border-white/20 backdrop-blur-sm transform group-hover:scale-105">
            <div className="flex items-center space-x-2">
              <SparklesIcon className="h-4 w-4 text-cyan-400 animate-pulse" />
              <span className="font-medium">Need help? Click for guidance!</span>
            </div>
            
            {/* Tooltip Arrow */}
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900"></div>
            
            {/* Tooltip Glow */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/20 to-cyan-500/20 animate-pulse"></div>
          </div>
        </div>
      )}

      {/* Add top padding to page content when banner is shown */}
      {showBanner && (
        <div className="h-20 md:h-16"></div>
      )}
    </>
  );
};

export default GuidanceBot;
