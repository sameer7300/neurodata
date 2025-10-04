"""
Django admin configuration for marketplace models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Purchase, Escrow


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """
    Admin interface for Purchase model.
    """
    list_display = [
        'id', 'buyer_link', 'dataset_link', 'amount', 'currency', 
        'status', 'payment_method', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'currency', 'created_at'
    ]
    search_fields = [
        'buyer__username', 'buyer__email', 'dataset__title', 
        'transaction_hash', 'payment_address'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'transaction_hash'
    ]
    ordering = ['-created_at']
    
    def buyer_link(self, obj):
        """Link to buyer's admin page."""
        url = reverse('admin:auth_user_change', args=[obj.buyer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.buyer.username)
    buyer_link.short_description = 'Buyer'
    
    def dataset_link(self, obj):
        """Link to dataset's admin page."""
        return format_html('<strong>{}</strong>', obj.dataset.title)
    dataset_link.short_description = 'Dataset'


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    """
    Admin interface for Escrow model with dispute management.
    """
    list_display = [
        'id', 'purchase_info', 'amount', 'status_badge', 'dispute_status',
        'buyer_confirmed', 'seller_delivered', 'validator_assigned',
        'created_at', 'action_status'
    ]
    list_filter = [
        'status', 'buyer_confirmed', 'seller_delivered', 
        'created_at', 'disputed_at', 'resolved_at'
    ]
    search_fields = [
        'purchase__buyer__username', 'purchase__dataset__title',
        'dispute_reason', 'resolution_notes', 'escrow_contract_id'
    ]
    readonly_fields = [
        'id', 'created_at', 'funded_at', 'delivered_at', 
        'confirmed_at', 'disputed_at', 'resolved_at', 'released_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'purchase', 'amount', 'currency', 'status', 
                'escrow_fee', 'escrow_contract_id'
            )
        }),
        ('Status Tracking', {
            'fields': (
                'buyer_confirmed', 'seller_delivered', 
                'auto_release_time', 'dispute_deadline'
            )
        }),
        ('Dispute Management', {
            'fields': (
                'dispute_reason', 'dispute_evidence', 
                'validator', 'resolution_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Blockchain Information', {
            'fields': (
                'escrow_address', 'creation_tx_hash', 'release_tx_hash'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'funded_at', 'delivered_at', 
                'confirmed_at', 'disputed_at', 'resolved_at', 'released_at'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['assign_to_me', 'resolve_dispute_buyer', 'resolve_dispute_seller']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'purchase', 'purchase__buyer', 'purchase__dataset', 'validator'
        )
    
    def purchase_info(self, obj):
        """Display purchase information."""
        return format_html(
            '<strong>{}</strong><br>'
            '<small>Buyer: {}<br>Dataset: {}</small>',
            obj.purchase.id,
            obj.purchase.buyer.username,
            obj.purchase.dataset.title
        )
    purchase_info.short_description = 'Purchase Details'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'active': '#007cba',
            'completed': '#28a745',
            'disputed': '#dc3545',
            'refunded': '#ffc107',
            'cancelled': '#6c757d',
            'auto_released': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def dispute_status(self, obj):
        """Display dispute information."""
        if obj.status == 'disputed':
            if obj.dispute_reason:
                return format_html(
                    '<span style="color: #dc3545;">🚨 DISPUTED</span><br>'
                    '<small>{}</small>',
                    obj.dispute_reason[:50] + ('...' if len(obj.dispute_reason) > 50 else '')
                )
            return format_html('<span style="color: #dc3545;">🚨 DISPUTED</span>')
        elif obj.resolved_at:
            return format_html('<span style="color: #28a745;">✅ RESOLVED</span>')
        return '-'
    dispute_status.short_description = 'Dispute Status'
    
    def validator_assigned(self, obj):
        """Display assigned validator."""
        if obj.validator:
            return format_html(
                '<span style="color: #007cba;">{}</span>',
                obj.validator.username
            )
        elif obj.status == 'disputed':
            return format_html('<span style="color: #ffc107;">⚠️ NEEDS VALIDATOR</span>')
        return '-'
    validator_assigned.short_description = 'Validator'
    
    def action_status(self, obj):
        """Display action status for escrow."""
        if obj.status == 'disputed' and not obj.validator:
            return format_html('<span style="color: #ffc107;">⚠️ NEEDS VALIDATOR</span>')
        elif obj.status == 'disputed' and obj.validator:
            return format_html('<span style="color: #dc3545;">🔄 PENDING RESOLUTION</span>')
        elif obj.status == 'active':
            try:
                if obj.can_auto_release:
                    return format_html('<span style="color: #17a2b8;">🚀 CAN AUTO-RELEASE</span>')
                else:
                    return format_html('<span style="color: #007cba;">⏳ WAITING</span>')
            except:
                return format_html('<span style="color: #007cba;">⏳ WAITING</span>')
        elif obj.status == 'completed':
            return format_html('<span style="color: #28a745;">✅ COMPLETED</span>')
        elif obj.status == 'refunded':
            return format_html('<span style="color: #6c757d;">💰 REFUNDED</span>')
        else:
            return format_html('<span style="color: #6c757d;">{}</span>', obj.status.upper())
    action_status.short_description = 'Action Status'
    
    def assign_to_me(self, request, queryset):
        """Assign disputed escrows to current admin user."""
        disputed_escrows = queryset.filter(status='disputed', validator__isnull=True)
        count = disputed_escrows.update(validator=request.user)
        
        self.message_user(
            request,
            f'Successfully assigned {count} disputed escrow(s) to you for validation.'
        )
    assign_to_me.short_description = 'Assign disputed escrows to me'
    
    def resolve_dispute_buyer(self, request, queryset):
        """Resolve dispute in favor of buyer (refund)."""
        disputed_escrows = queryset.filter(status='disputed')
        count = 0
        
        for escrow in disputed_escrows:
            escrow.status = 'refunded'
            escrow.validator = request.user
            escrow.resolved_at = timezone.now()
            escrow.resolution_notes = f'Dispute resolved in favor of buyer by admin {request.user.username}'
            escrow.save()
            count += 1
        
        self.message_user(
            request,
            f'Successfully resolved {count} dispute(s) in favor of buyer (refunded).'
        )
    resolve_dispute_buyer.short_description = 'Resolve dispute → Refund buyer'
    
    def resolve_dispute_seller(self, request, queryset):
        """Resolve dispute in favor of seller (release funds)."""
        disputed_escrows = queryset.filter(status='disputed')
        count = 0
        
        for escrow in disputed_escrows:
            escrow.status = 'completed'
            escrow.validator = request.user
            escrow.resolved_at = timezone.now()
            escrow.buyer_confirmed = True
            escrow.confirmed_at = timezone.now()
            escrow.resolution_notes = f'Dispute resolved in favor of seller by admin {request.user.username}'
            escrow.save()
            count += 1
        
        self.message_user(
            request,
            f'Successfully resolved {count} dispute(s) in favor of seller (released funds).'
        )
    resolve_dispute_seller.short_description = 'Resolve dispute → Release to seller'
    
    def get_queryset(self, request):
        """Optimize queryset with related objects."""
        return super().get_queryset(request).select_related(
            'purchase__buyer', 'purchase__dataset', 'validator'
        )


# Custom admin site configuration
admin.site.site_header = 'NeuroData Marketplace Admin'
admin.site.site_title = 'NeuroData Admin'
admin.site.index_title = 'Marketplace Management'
