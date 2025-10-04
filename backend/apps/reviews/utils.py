"""
Review filtering and moderation utilities.
"""
import re
from typing import Dict, List, Any
from django.conf import settings


class ReviewFilterEngine:
    """
    Automatic review content filtering engine.
    """
    
    # Profanity patterns (basic examples - in production use comprehensive lists)
    PROFANITY_PATTERNS = [
        r'\b(damn|hell|crap|stupid|idiot|moron|jerk|sucks|terrible|awful|horrible|worst|hate|disgusting)\b',
        r'\b(scam|fraud|fake|ripoff|steal|cheat|lie|liar|dishonest)\b',
    ]
    
    # Spam indicators
    SPAM_PATTERNS = [
        r'(buy now|click here|visit my|check out my|free money|guaranteed)',
        r'(www\.|http|\.com|\.net|\.org)',
        r'(\$\$\$|!!!|amazing deal|limited time)',
        r'(contact me|email me|call me|whatsapp)',
    ]
    
    # Positive keywords that boost credibility
    POSITIVE_KEYWORDS = [
        'quality', 'accurate', 'comprehensive', 'detailed', 'useful', 'helpful',
        'clean', 'organized', 'structured', 'complete', 'reliable', 'excellent',
        'good', 'great', 'amazing', 'perfect', 'recommend', 'satisfied'
    ]
    
    # Negative sentiment indicators
    NEGATIVE_KEYWORDS = [
        'disappointed', 'useless', 'waste', 'poor', 'bad', 'terrible', 'awful',
        'incomplete', 'missing', 'corrupted', 'outdated', 'inaccurate', 'wrong'
    ]
    
    def __init__(self):
        self.filters = self._load_active_filters()
    
    def _load_active_filters(self):
        """Load active filters from database."""
        try:
            from .models import ReviewFilter
            return list(ReviewFilter.objects.filter(is_active=True))
        except:
            return []
    
    def analyze_review(self, review) -> Dict[str, Any]:
        """
        Analyze review content and return filtering results.
        
        Returns:
            Dict with score (0-1), reasons, and notes
        """
        text = f"{review.title} {review.comment}".lower()
        
        results = {
            'score': 0.0,
            'reasons': [],
            'notes': '',
            'details': {}
        }
        
        # Run all filter checks
        profanity_score = self._check_profanity(text)
        spam_score = self._check_spam(text)
        sentiment_score = self._check_sentiment(text)
        length_score = self._check_length(text)
        
        # Calculate weighted score
        results['score'] = (
            profanity_score * 0.4 +
            spam_score * 0.3 +
            sentiment_score * 0.2 +
            length_score * 0.1
        )
        
        # Collect reasons
        if profanity_score > 0.5:
            results['reasons'].append('Potentially inappropriate language detected')
        if spam_score > 0.5:
            results['reasons'].append('Spam-like content detected')
        if sentiment_score > 0.7:
            results['reasons'].append('Highly negative sentiment')
        if length_score > 0.5:
            results['reasons'].append('Content length issues')
        
        # Generate notes
        notes = []
        if profanity_score > 0.3:
            notes.append(f"Language check: {profanity_score:.2f}")
        if spam_score > 0.3:
            notes.append(f"Spam check: {spam_score:.2f}")
        if sentiment_score > 0.5:
            notes.append(f"Sentiment: {sentiment_score:.2f}")
        
        results['notes'] = '; '.join(notes)
        results['details'] = {
            'profanity_score': profanity_score,
            'spam_score': spam_score,
            'sentiment_score': sentiment_score,
            'length_score': length_score
        }
        
        return results
    
    def _check_profanity(self, text: str) -> float:
        """Check for profanity and inappropriate language."""
        score = 0.0
        matches = 0
        
        for pattern in self.PROFANITY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Score based on number of matches relative to text length
        words = len(text.split())
        if words > 0:
            score = min(matches / words * 5, 1.0)  # Cap at 1.0
        
        return score
    
    def _check_spam(self, text: str) -> float:
        """Check for spam indicators."""
        score = 0.0
        matches = 0
        
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Additional spam checks
        if len(text) < 10:  # Very short reviews
            score += 0.3
        if text.count('!') > 3:  # Excessive exclamation marks
            score += 0.2
        if text.isupper():  # All caps
            score += 0.4
        
        words = len(text.split())
        if words > 0:
            score += min(matches / words * 3, 0.6)
        
        return min(score, 1.0)
    
    def _check_sentiment(self, text: str) -> float:
        """Basic sentiment analysis."""
        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in text)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.5
        
        # Calculate sentiment ratio
        sentiment_ratio = (negative_count - positive_count) / total_words
        
        # Convert to 0-1 score (higher = more negative)
        return max(0, min(sentiment_ratio * 10 + 0.5, 1.0))
    
    def _check_length(self, text: str) -> float:
        """Check content length appropriateness."""
        length = len(text.strip())
        
        if length < 5:  # Too short
            return 0.8
        elif length < 15:  # Very short
            return 0.4
        elif length > 2000:  # Too long
            return 0.3
        else:
            return 0.0


class ReviewAnalytics:
    """
    Review analytics and insights.
    """
    
    @staticmethod
    def get_review_stats(dataset_id=None, user_id=None):
        """Get review statistics."""
        from .models import Review
        
        queryset = Review.objects.filter(status__in=['approved', 'auto_approved'])
        
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        if user_id:
            queryset = queryset.filter(reviewer_id=user_id)
        
        stats = {
            'total_reviews': queryset.count(),
            'average_rating': 0,
            'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'verified_percentage': 0
        }
        
        if stats['total_reviews'] > 0:
            # Calculate average rating
            ratings = queryset.values_list('rating', flat=True)
            stats['average_rating'] = sum(ratings) / len(ratings)
            
            # Rating distribution
            for rating in ratings:
                stats['rating_distribution'][rating] += 1
            
            # Verified percentage
            verified_count = queryset.filter(is_verified_purchase=True).count()
            stats['verified_percentage'] = (verified_count / stats['total_reviews']) * 100
        
        return stats
    
    @staticmethod
    def get_moderation_stats():
        """Get moderation statistics."""
        from .models import Review
        
        total = Review.objects.count()
        if total == 0:
            return {}
        
        stats = {
            'total_reviews': total,
            'pending': Review.objects.filter(status='pending').count(),
            'approved': Review.objects.filter(status='approved').count(),
            'auto_approved': Review.objects.filter(status='auto_approved').count(),
            'rejected': Review.objects.filter(status='rejected').count(),
            'flagged': Review.objects.filter(status='flagged').count(),
        }
        
        # Calculate percentages
        for key in ['pending', 'approved', 'auto_approved', 'rejected', 'flagged']:
            stats[f'{key}_percentage'] = (stats[key] / total) * 100
        
        return stats


def get_review_recommendations(user, limit=5):
    """Get datasets that user might want to review."""
    from apps.marketplace.models import Purchase
    from .models import Review
    
    # Get user's completed purchases without reviews
    purchases = Purchase.objects.filter(
        buyer=user,
        status='completed'
    ).exclude(
        dataset__reviews__reviewer=user
    ).select_related('dataset')[:limit]
    
    return [purchase.dataset for purchase in purchases]
