"""
Admin configuration for authentication models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.html import format_html
from .models import User, UserProfile, APIKey, UserActivity


class APIKeyInline(admin.TabularInline):
    """Inline admin for API keys."""
    model = APIKey
    extra = 0
    readonly_fields = ('key', 'created_at', 'last_used')
    fields = ('name', 'key', 'can_read', 'can_write', 'can_delete', 'is_active', 'expires_at', 'created_at', 'last_used')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ('email', 'username', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    inlines = [APIKeyInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    
    list_display = (
        'user_email', 'wallet_address_short', 'verification_status', 
        'reputation_score', 'total_datasets_uploaded', 'created_at'
    )
    list_filter = ('verification_status', 'email_notifications', 'created_at')
    search_fields = ('user__email', 'wallet_address', 'bio')
    readonly_fields = (
        'total_datasets_uploaded', 'total_datasets_purchased', 
        'total_earnings', 'total_spent', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'verification_status')
        }),
        ('Blockchain Information', {
            'fields': ('wallet_address',)
        }),
        ('Profile Information', {
            'fields': ('bio', 'avatar', 'website', 'location')
        }),
        ('Statistics', {
            'fields': (
                'reputation_score', 'total_datasets_uploaded', 
                'total_datasets_purchased', 'total_earnings', 'total_spent'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'marketing_emails'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # inlines = [APIKeyInline]  # APIKey is related to User, not UserProfile
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def wallet_address_short(self, obj):
        if obj.wallet_address:
            return f"{obj.wallet_address[:6]}...{obj.wallet_address[-4:]}"
        return "Not set"
    wallet_address_short.short_description = 'Wallet'
    
    actions = ['verify_users', 'update_user_stats']
    
    def verify_users(self, request, queryset):
        """Bulk verify users."""
        updated = queryset.update(verification_status='verified')
        self.message_user(request, f'{updated} users verified successfully.')
    verify_users.short_description = 'Verify selected users'
    
    def update_user_stats(self, request, queryset):
        """Bulk update user statistics."""
        for profile in queryset:
            profile.update_stats()
        self.message_user(request, f'Statistics updated for {queryset.count()} users.')
    update_user_stats.short_description = 'Update user statistics'


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API keys."""
    
    list_display = (
        'name', 'user_email', 'key_short', 'is_active', 
        'usage_count', 'last_used', 'created_at'
    )
    list_filter = ('is_active', 'can_read', 'can_write', 'can_delete', 'created_at')
    search_fields = ('name', 'user__email', 'key')
    readonly_fields = ('key', 'usage_count', 'last_used', 'created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'key', 'is_active')
        }),
        ('Permissions', {
            'fields': ('can_read', 'can_write', 'can_delete')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def key_short(self, obj):
        return f"{obj.key[:8]}...{obj.key[-8:]}"
    key_short.short_description = 'API Key'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin interface for user activities."""
    
    list_display = (
        'user_email', 'activity_type', 'description_short', 
        'ip_address', 'timestamp'
    )
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__email', 'description', 'ip_address')
    readonly_fields = ('user', 'activity_type', 'description', 'ip_address', 'user_agent', 'metadata', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def description_short(self, obj):
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
