import { useCallback } from 'react';
import { activityTracker } from '../services/activityTracker';

// Custom hook for tracking user activities across the app
export const useActivityTracker = () => {
  const trackSearch = useCallback(() => {
    activityTracker.trackSearch();
  }, []);

  const trackDatasetView = useCallback(() => {
    activityTracker.trackDatasetView();
  }, []);

  const trackDatasetUpload = useCallback(() => {
    activityTracker.trackDatasetUpload();
  }, []);

  const trackDatasetPurchase = useCallback(() => {
    activityTracker.trackDatasetPurchase();
  }, []);

  const trackCategoryInterest = useCallback((category: string) => {
    activityTracker.trackCategoryInterest(category);
  }, []);

  const getUserActivity = useCallback(() => {
    return activityTracker.getActivity();
  }, []);

  const getUserEngagementLevel = useCallback(() => {
    return activityTracker.getUserEngagementLevel();
  }, []);

  const getPersonalizedInsights = useCallback(() => {
    return activityTracker.getPersonalizedInsights();
  }, []);

  const getSmartSuggestions = useCallback(() => {
    return activityTracker.getSmartSuggestions();
  }, []);

  return {
    trackSearch,
    trackDatasetView,
    trackDatasetUpload,
    trackDatasetPurchase,
    trackCategoryInterest,
    getUserActivity,
    getUserEngagementLevel,
    getPersonalizedInsights,
    getSmartSuggestions
  };
};
