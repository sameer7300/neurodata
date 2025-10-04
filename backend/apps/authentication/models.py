"""
Authentication models for NeuroData platform.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal
import uuid


class User(AbstractUser):
    """
    Extended User model with additional fields for blockchain integration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username to make it optional
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'authentication_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """
    Extended profile information for users.
    """
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Blockchain/Wallet Information
    wallet_address = models.CharField(
        max_length=42,
        validators=[
            RegexValidator(
                regex=r'^0x[a-fA-F0-9]{40}$',
                message='Enter a valid Ethereum wallet address'
            )
        ],
        unique=True,
        null=True,
        blank=True
    )
    
    # Profile Information
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Verification and Reputation
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    reputation_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Statistics
    total_datasets_uploaded = models.PositiveIntegerField(default=0)
    total_datasets_purchased = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000')
    )
    total_spent = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000')
    )
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # Favorites
    favorite_datasets = models.ManyToManyField(
        'datasets.Dataset',
        blank=True,
        related_name='favorited_by'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email}'s Profile"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'
    
    def update_stats(self):
        """Update user statistics based on their activity."""
        from apps.datasets.models import Dataset
        from apps.marketplace.models import Purchase
        from decimal import Decimal
        
        # Update dataset counts
        self.total_datasets_uploaded = Dataset.objects.filter(owner=self.user).count()
        
        # Update purchase counts and spending
        purchases = Purchase.objects.filter(buyer=self.user, status='completed')
        self.total_datasets_purchased = purchases.count()
        self.total_spent = sum(p.amount for p in purchases) if purchases.exists() else Decimal('0.00')
        
        # Update earnings from dataset sales
        sales = Purchase.objects.filter(
            dataset__owner=self.user,
            status='completed'
        )
        self.total_earnings = sum(s.amount for s in sales) if sales.exists() else Decimal('0.00')
        
        # Update reputation score based on activity
        if self.total_datasets_uploaded > 0:
            # Basic reputation calculation: base score + uploads + sales
            base_score = Decimal('3.0')  # Starting score
            upload_bonus = min(self.total_datasets_uploaded * Decimal('0.1'), Decimal('2.0'))  # Max 2.0 from uploads
            sales_bonus = min(sales.count() * Decimal('0.05'), Decimal('1.0'))  # Max 1.0 from sales
            self.reputation_score = min(base_score + upload_bonus + sales_bonus, Decimal('5.0'))
        
        self.save()


class APIKey(models.Model):
    """
    API keys for programmatic access to the platform.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    
    # Permissions
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class UserActivity(models.Model):
    """
    Track user activities for analytics and security.
    """
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('dataset_upload', 'Dataset Upload'),
        ('dataset_purchase', 'Dataset Purchase'),
        ('profile_update', 'Profile Update'),
        ('wallet_connect', 'Wallet Connect'),
        ('api_access', 'API Access'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional context data
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.timestamp}"
