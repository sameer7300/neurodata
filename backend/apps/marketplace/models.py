"""
Marketplace models for NeuroData platform.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Purchase(models.Model):
    """
    Dataset purchase transactions.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('crypto', 'Cryptocurrency'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    dataset = models.ForeignKey('datasets.Dataset', on_delete=models.CASCADE, related_name='purchases')
    
    # Transaction Details
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000000'))]
    )
    currency = models.CharField(max_length=10, default='NRC')  # NeuroCoin
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='crypto')
    transaction_hash = models.CharField(max_length=66, blank=True)  # Blockchain tx hash
    payment_address = models.CharField(max_length=42, blank=True)  # Wallet address
    
    # Status and Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'marketplace_purchases'
        verbose_name = 'Purchase'
        verbose_name_plural = 'Purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['dataset', 'status']),
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.buyer.email} - {self.dataset.title} ({self.amount} {self.currency})"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def can_download(self):
        return self.status in ['completed']
    
    def mark_completed(self):
        """Mark purchase as completed."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])


class Transaction(models.Model):
    """
    Blockchain transaction records.
    """
    TRANSACTION_TYPES = [
        ('purchase', 'Dataset Purchase'),
        ('payout', 'Seller Payout'),
        ('refund', 'Refund'),
        ('fee', 'Platform Fee'),
        ('reward', 'Reward'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Blockchain Information
    transaction_hash = models.CharField(max_length=66, unique=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    block_hash = models.CharField(max_length=66, blank=True)
    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price = models.BigIntegerField(null=True, blank=True)
    
    # Transaction Details
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42)
    amount = models.DecimalField(max_digits=30, decimal_places=18)
    currency = models.CharField(max_length=10, default='NRC')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmations = models.PositiveIntegerField(default=0)
    
    # Related Objects
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'marketplace_transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['from_address']),
            models.Index(fields=['to_address']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_hash[:10]}..."
    
    @property
    def is_confirmed(self):
        return self.status == 'confirmed' and self.confirmations >= 3


class Escrow(models.Model):
    """
    Enhanced escrow system for secure dataset transactions.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),           # Funds locked, waiting for confirmation
        ('completed', 'Completed'),     # Buyer confirmed, funds released to seller
        ('disputed', 'Disputed'),       # Buyer disputed, waiting for resolution
        ('refunded', 'Refunded'),       # Dispute resolved in favor of buyer
        ('cancelled', 'Cancelled'),     # Cancelled before completion
        ('auto_released', 'Auto Released'), # Auto-released after timeout
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name='escrow')
    
    # Blockchain Information
    escrow_contract_id = models.BigIntegerField(null=True, blank=True)  # Smart contract escrow ID
    escrow_address = models.CharField(max_length=42, blank=True)  # Smart contract address
    creation_tx_hash = models.CharField(max_length=66, blank=True)  # Transaction hash for escrow creation
    release_tx_hash = models.CharField(max_length=66, blank=True)  # Transaction hash for release/refund
    
    # Escrow Details
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default='NCR')
    escrow_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00000000'))
    
    # Status and Confirmations
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    buyer_confirmed = models.BooleanField(default=False)
    seller_delivered = models.BooleanField(default=False)
    
    # Dispute Information
    dispute_reason = models.TextField(blank=True)
    dispute_evidence = models.JSONField(default=dict, blank=True)  # Store evidence files, screenshots, etc.
    validator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_escrows')
    resolution_notes = models.TextField(blank=True)
    
    # Auto-release Settings
    auto_release_time = models.DateTimeField(null=True, blank=True)  # When to auto-release
    dispute_deadline = models.DateTimeField(null=True, blank=True)   # Deadline for disputes
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    funded_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)  # When seller marked as delivered
    confirmed_at = models.DateTimeField(null=True, blank=True)  # When buyer confirmed
    disputed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'marketplace_escrows'
        verbose_name = 'Escrow'
        verbose_name_plural = 'Escrows'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['escrow_contract_id']),
            models.Index(fields=['auto_release_time']),
            models.Index(fields=['dispute_deadline']),
        ]
    
    def __str__(self):
        return f"Escrow #{self.escrow_contract_id} for {self.purchase}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def can_auto_release(self):
        from django.utils import timezone
        return (
            self.status == 'active' and
            self.seller_delivered and
            self.auto_release_time and
            timezone.now() >= self.auto_release_time
        )
    
    @property
    def can_dispute(self):
        from django.utils import timezone
        return (
            self.status == 'active' and
            self.dispute_deadline and
            timezone.now() <= self.dispute_deadline
        )
    
    @property
    def time_until_auto_release(self):
        from django.utils import timezone
        if not self.auto_release_time:
            return None
        remaining = self.auto_release_time - timezone.now()
        return remaining if remaining.total_seconds() > 0 else None
    
    def mark_delivered(self):
        """Mark dataset as delivered by seller."""
        from django.utils import timezone
        self.seller_delivered = True
        self.delivered_at = timezone.now()
        self.save(update_fields=['seller_delivered', 'delivered_at'])
    
    def mark_confirmed(self):
        """Mark dataset as confirmed by buyer."""
        from django.utils import timezone
        self.buyer_confirmed = True
        self.confirmed_at = timezone.now()
        self.status = 'completed'
        self.save(update_fields=['buyer_confirmed', 'confirmed_at', 'status'])
    
    def create_dispute(self, reason, evidence=None):
        """Create a dispute for this escrow."""
        from django.utils import timezone
        self.status = 'disputed'
        self.dispute_reason = reason
        self.dispute_evidence = evidence or {}
        self.disputed_at = timezone.now()
        self.save(update_fields=['status', 'dispute_reason', 'dispute_evidence', 'disputed_at'])
    
    def resolve_dispute(self, validator, buyer_wins, resolution_notes=""):
        """Resolve dispute with validator decision."""
        from django.utils import timezone
        self.validator = validator
        self.resolution_notes = resolution_notes
        self.resolved_at = timezone.now()
        
        if buyer_wins:
            self.status = 'refunded'
        else:
            self.status = 'completed'
        
        self.save(update_fields=['validator', 'resolution_notes', 'resolved_at', 'status'])


class Payout(models.Model):
    """
    Seller payouts for dataset sales.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name='payout')
    
    # Payout Details
    gross_amount = models.DecimalField(max_digits=20, decimal_places=8)
    platform_fee = models.DecimalField(max_digits=20, decimal_places=8)
    net_amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default='NRC')
    
    # Payment Information
    recipient_address = models.CharField(max_length=42)
    transaction_hash = models.CharField(max_length=66, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'marketplace_payouts'
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payout to {self.seller.email} - {self.net_amount} {self.currency}"


class PlatformFee(models.Model):
    """
    Platform fee configuration and tracking.
    """
    FEE_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    # Fee Configuration
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default='percentage')
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.50'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fixed_amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000')
    )
    currency = models.CharField(max_length=10, default='NRC')
    
    # Applicability
    min_transaction_amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000')
    )
    max_transaction_amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'marketplace_platform_fees'
        verbose_name = 'Platform Fee'
        verbose_name_plural = 'Platform Fees'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.fee_type == 'percentage':
            return f"{self.percentage}% fee"
        return f"{self.fixed_amount} {self.currency} fee"
    
    def calculate_fee(self, amount):
        """Calculate fee for given amount."""
        if self.fee_type == 'percentage':
            return amount * (self.percentage / 100)
        return self.fixed_amount


class Refund(models.Model):
    """
    Refund requests and processing.
    """
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    REASON_CHOICES = [
        ('defective', 'Defective Dataset'),
        ('not_as_described', 'Not as Described'),
        ('duplicate', 'Duplicate Purchase'),
        ('technical_issue', 'Technical Issue'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name='refund')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    
    # Refund Details
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default='NRC')
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    admin_notes = models.TextField(blank=True)
    transaction_hash = models.CharField(max_length=66, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'marketplace_refunds'
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund for {self.purchase} - {self.status}"
