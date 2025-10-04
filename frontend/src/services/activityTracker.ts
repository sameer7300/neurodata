// User Activity Tracking Service for Personalized Guidance

export interface UserActivity {
  // Page visits
  totalVisits: number;
  pagesVisited: string[];
  lastVisitDate: string;
  sessionCount: number;
  
  // Actions performed
  searchesPerformed: number;
  datasetsViewed: number;
  datasetsUploaded: number;
  datasetsPurchased: number;
  
  // Engagement metrics
  guidanceStepsCompleted: number;
  guidanceSkipped: number;
  helpButtonClicks: number;
  
  // Learning progress
  completedTutorials: string[];
  currentStreak: number;
  lastActiveDate: string;
  
  // Preferences
  preferredCategories: string[];
  averageSessionDuration: number;
}

class ActivityTracker {
  private storageKey = 'neurodata_user_activity';
  
  // Initialize or get existing activity data
  getActivity(): UserActivity {
    const stored = localStorage.getItem(this.storageKey);
    if (stored) {
      return JSON.parse(stored);
    }
    
    // Default activity structure
    return {
      totalVisits: 0,
      pagesVisited: [],
      lastVisitDate: new Date().toISOString(),
      sessionCount: 0,
      searchesPerformed: 0,
      datasetsViewed: 0,
      datasetsUploaded: 0,
      datasetsPurchased: 0,
      guidanceStepsCompleted: 0,
      guidanceSkipped: 0,
      helpButtonClicks: 0,
      completedTutorials: [],
      currentStreak: 0,
      lastActiveDate: new Date().toISOString(),
      preferredCategories: [],
      averageSessionDuration: 0
    };
  }
  
  // Save activity data
  private saveActivity(activity: UserActivity): void {
    localStorage.setItem(this.storageKey, JSON.stringify(activity));
  }
  
  // Track page visit
  trackPageVisit(pagePath: string): void {
    const activity = this.getActivity();
    
    activity.totalVisits += 1;
    if (!activity.pagesVisited.includes(pagePath)) {
      activity.pagesVisited.push(pagePath);
    }
    
    // Update session info
    const today = new Date().toDateString();
    const lastVisit = new Date(activity.lastVisitDate).toDateString();
    
    if (today !== lastVisit) {
      activity.sessionCount += 1;
      // Update streak
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      
      if (lastVisit === yesterday.toDateString()) {
        activity.currentStreak += 1;
      } else if (lastVisit !== today) {
        activity.currentStreak = 1; // Reset streak
      }
    }
    
    activity.lastVisitDate = new Date().toISOString();
    activity.lastActiveDate = new Date().toISOString();
    
    this.saveActivity(activity);
  }
  
  // Track specific actions
  trackSearch(): void {
    const activity = this.getActivity();
    activity.searchesPerformed += 1;
    this.saveActivity(activity);
  }
  
  trackDatasetView(): void {
    const activity = this.getActivity();
    activity.datasetsViewed += 1;
    this.saveActivity(activity);
  }
  
  trackDatasetUpload(): void {
    const activity = this.getActivity();
    activity.datasetsUploaded += 1;
    this.saveActivity(activity);
  }
  
  trackDatasetPurchase(): void {
    const activity = this.getActivity();
    activity.datasetsPurchased += 1;
    this.saveActivity(activity);
  }
  
  trackGuidanceStep(): void {
    const activity = this.getActivity();
    activity.guidanceStepsCompleted += 1;
    this.saveActivity(activity);
  }
  
  trackGuidanceSkip(): void {
    const activity = this.getActivity();
    activity.guidanceSkipped += 1;
    this.saveActivity(activity);
  }
  
  trackHelpButtonClick(): void {
    const activity = this.getActivity();
    activity.helpButtonClicks += 1;
    this.saveActivity(activity);
  }
  
  trackTutorialCompletion(tutorialId: string): void {
    const activity = this.getActivity();
    if (!activity.completedTutorials.includes(tutorialId)) {
      activity.completedTutorials.push(tutorialId);
    }
    this.saveActivity(activity);
  }
  
  trackCategoryInterest(category: string): void {
    const activity = this.getActivity();
    const existing = activity.preferredCategories.find(c => c === category);
    if (!existing) {
      activity.preferredCategories.push(category);
    }
    this.saveActivity(activity);
  }
  
  // Get user engagement level
  getUserEngagementLevel(): 'new' | 'beginner' | 'active' | 'expert' | 'power_user' {
    const activity = this.getActivity();
    
    if (activity.totalVisits <= 2) return 'new';
    if (activity.totalVisits <= 10 && activity.datasetsViewed <= 5) return 'beginner';
    if (activity.datasetsUploaded > 0 || activity.datasetsPurchased > 0) return 'active';
    if (activity.datasetsUploaded >= 3 || activity.datasetsPurchased >= 5) return 'expert';
    if (activity.totalVisits >= 50 && activity.currentStreak >= 7) return 'power_user';
    
    return 'active';
  }
  
  // Get personalized insights
  getPersonalizedInsights(): string[] {
    const activity = this.getActivity();
    const insights: string[] = [];
    
    if (activity.currentStreak >= 3) {
      insights.push(`🔥 ${activity.currentStreak} day streak! You're on fire!`);
    }
    
    if (activity.datasetsUploaded > 0) {
      insights.push(`📊 You've uploaded ${activity.datasetsUploaded} dataset${activity.datasetsUploaded > 1 ? 's' : ''}!`);
    }
    
    if (activity.datasetsPurchased > 0) {
      insights.push(`🛒 You've purchased ${activity.datasetsPurchased} dataset${activity.datasetsPurchased > 1 ? 's' : ''}!`);
    }
    
    if (activity.searchesPerformed >= 10) {
      insights.push(`🔍 You're quite the explorer with ${activity.searchesPerformed} searches!`);
    }
    
    if (activity.pagesVisited.length >= 5) {
      insights.push(`🗺️ You've explored ${activity.pagesVisited.length} different sections!`);
    }
    
    return insights;
  }
  
  // Get smart suggestions based on activity
  getSmartSuggestions(): string[] {
    const activity = this.getActivity();
    const suggestions: string[] = [];
    
    if (activity.datasetsViewed > 5 && activity.datasetsPurchased === 0) {
      suggestions.push("You've viewed many datasets! Ready to make your first purchase?");
    }
    
    if (activity.datasetsPurchased > 0 && activity.datasetsUploaded === 0) {
      suggestions.push("Since you're buying datasets, why not upload your own and start earning?");
    }
    
    if (activity.datasetsUploaded > 0 && activity.pagesVisited.includes('/ml/training') === false) {
      suggestions.push("Try our ML Training lab to train models with your datasets!");
    }
    
    if (activity.searchesPerformed === 0 && activity.totalVisits > 3) {
      suggestions.push("Use the search feature to find exactly what you need!");
    }
    
    if (activity.preferredCategories.length > 0) {
      suggestions.push(`Check out more ${activity.preferredCategories[0]} datasets!`);
    }
    
    return suggestions;
  }
  
  // Check if user is returning
  isReturningUser(): boolean {
    const activity = this.getActivity();
    return activity.totalVisits > 1;
  }
  
  // Get time-based greeting
  getTimeBasedGreeting(): string {
    const hour = new Date().getHours();
    
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    if (hour < 21) return "Good evening";
    return "Good night";
  }
}

export const activityTracker = new ActivityTracker();
