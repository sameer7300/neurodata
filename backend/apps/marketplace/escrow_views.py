"""
Escrow system views for NeuroData marketplace.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Purchase, Escrow
from core.utils import create_response_data
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_escrow(request, purchase_id):
    """
    Create escrow for a purchase.
    """
    try:
        purchase = get_object_or_404(Purchase, id=purchase_id, buyer=request.user)
        
        # Check if escrow already exists
        if hasattr(purchase, 'escrow'):
            return Response(
                create_response_data(
                    success=False,
                    message="Escrow already exists for this purchase"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create escrow with default settings
        auto_release_time = timezone.now() + timedelta(hours=24)  # 24 hours auto-release
        dispute_deadline = timezone.now() + timedelta(days=7)     # 7 days dispute window
        
        escrow = Escrow.objects.create(
            purchase=purchase,
            amount=purchase.amount,
            currency=purchase.currency,
            auto_release_time=auto_release_time,
            dispute_deadline=dispute_deadline,
            escrow_fee=purchase.amount * 0.01,  # 1% escrow fee
        )
        
        return Response(
            create_response_data(
                success=True,
                message="Escrow created successfully",
                data={
                    'escrow_id': str(escrow.id),
                    'amount': str(escrow.amount),
                    'currency': escrow.currency,
                    'status': escrow.status,
                    'auto_release_time': escrow.auto_release_time.isoformat(),
                    'dispute_deadline': escrow.dispute_deadline.isoformat(),
                }
            ),
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to create escrow: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_escrow(request, escrow_id):
    """
    Get escrow details.
    """
    try:
        escrow = get_object_or_404(Escrow, id=escrow_id)
        
        # Check if user is buyer or seller
        if request.user not in [escrow.purchase.buyer, escrow.purchase.dataset.owner]:
            return Response(
                create_response_data(
                    success=False,
                    message="Not authorized to view this escrow"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(
            create_response_data(
                success=True,
                message="Escrow retrieved successfully",
                data={
                    'id': str(escrow.id),
                    'purchase_id': str(escrow.purchase.id),
                    'amount': str(escrow.amount),
                    'currency': escrow.currency,
                    'status': escrow.status,
                    'buyer_confirmed': escrow.buyer_confirmed,
                    'seller_delivered': escrow.seller_delivered,
                    'auto_release_time': escrow.auto_release_time.isoformat() if escrow.auto_release_time else None,
                    'dispute_deadline': escrow.dispute_deadline.isoformat() if escrow.dispute_deadline else None,
                    'can_auto_release': escrow.can_auto_release,
                    'can_dispute': escrow.can_dispute,
                    'time_until_auto_release': str(escrow.time_until_auto_release) if escrow.time_until_auto_release else None,
                    'dispute_reason': escrow.dispute_reason,
                    'created_at': escrow.created_at.isoformat(),
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to retrieve escrow: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_delivery(request, escrow_id):
    """
    Seller confirms dataset delivery.
    """
    try:
        escrow = get_object_or_404(Escrow, id=escrow_id)
        
        # Check if user is the seller
        if request.user != escrow.purchase.dataset.owner:
            return Response(
                create_response_data(
                    success=False,
                    message="Only the seller can confirm delivery"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if escrow is active
        if escrow.status != 'active':
            return Response(
                create_response_data(
                    success=False,
                    message="Escrow is not active"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        escrow.mark_delivered()
        
        return Response(
            create_response_data(
                success=True,
                message="Delivery confirmed successfully",
                data={
                    'escrow_id': str(escrow.id),
                    'seller_delivered': escrow.seller_delivered,
                    'delivered_at': escrow.delivered_at.isoformat(),
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to confirm delivery: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_receipt(request, escrow_id):
    """
    Buyer confirms receipt and releases escrow.
    """
    try:
        escrow = get_object_or_404(Escrow, id=escrow_id)
        
        # Check if user is the buyer
        if request.user != escrow.purchase.buyer:
            return Response(
                create_response_data(
                    success=False,
                    message="Only the buyer can confirm receipt"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if escrow is active
        if escrow.status != 'active':
            return Response(
                create_response_data(
                    success=False,
                    message="Escrow is not active"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if seller has delivered
        if not escrow.seller_delivered:
            return Response(
                create_response_data(
                    success=False,
                    message="Seller has not confirmed delivery yet"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        escrow.mark_confirmed()
        
        # TODO: Trigger smart contract release
        # This would call the smart contract to release funds to seller
        
        return Response(
            create_response_data(
                success=True,
                message="Receipt confirmed and escrow released",
                data={
                    'escrow_id': str(escrow.id),
                    'status': escrow.status,
                    'buyer_confirmed': escrow.buyer_confirmed,
                    'confirmed_at': escrow.confirmed_at.isoformat(),
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to confirm receipt: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_dispute(request, escrow_id):
    """
    Validator resolves a dispute.
    """
    try:
        escrow = get_object_or_404(Escrow, id=escrow_id)
        
        # Check if user is a validator (for now, only superusers)
        if not request.user.is_superuser:
            return Response(
                create_response_data(
                    success=False,
                    message="Only validators can resolve disputes"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if escrow is disputed
        if escrow.status != 'disputed':
            return Response(
                create_response_data(
                    success=False,
                    message="Escrow is not disputed"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        buyer_wins = request.data.get('buyer_wins', False)
        resolution_notes = request.data.get('resolution_notes', '')
        
        escrow.resolve_dispute(request.user, buyer_wins, resolution_notes)
        
        # TODO: Trigger smart contract resolution
        # This would call the smart contract to either release or refund
        
        return Response(
            create_response_data(
                success=True,
                message="Dispute resolved successfully",
                data={
                    'escrow_id': str(escrow.id),
                    'status': escrow.status,
                    'buyer_wins': buyer_wins,
                    'resolution_notes': resolution_notes,
                    'resolved_at': escrow.resolved_at.isoformat(),
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to resolve dispute: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_release_escrow(request, escrow_id):
    """
    Auto-release escrow after timeout.
    """
    try:
        escrow = get_object_or_404(Escrow, id=escrow_id)
        
        # Check if escrow can be auto-released
        if not escrow.can_auto_release:
            return Response(
                create_response_data(
                    success=False,
                    message="Escrow cannot be auto-released yet"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        escrow.status = 'auto_released'
        escrow.released_at = timezone.now()
        escrow.save(update_fields=['status', 'released_at'])
        
        # TODO: Trigger smart contract auto-release
        
        return Response(
            create_response_data(
                success=True,
                message="Escrow auto-released successfully",
                data={
                    'escrow_id': str(escrow.id),
                    'status': escrow.status,
                    'released_at': escrow.released_at.isoformat(),
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to auto-release escrow: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_escrows(request):
    """
    List all escrows for the authenticated user.
    """
    try:
        # Get escrows where user is buyer or seller
        buyer_escrows = Escrow.objects.filter(purchase__buyer=request.user)
        seller_escrows = Escrow.objects.filter(purchase__dataset__owner=request.user)
        
        # Combine and remove duplicates
        all_escrows = (buyer_escrows | seller_escrows).distinct().order_by('-created_at')
        
        escrows_data = []
        for escrow in all_escrows:
            escrows_data.append({
                'id': str(escrow.id),
                'purchase_id': str(escrow.purchase.id),
                'dataset_id': str(escrow.purchase.dataset.id),
                'dataset_title': escrow.purchase.dataset.title,
                'amount': str(escrow.amount),
                'currency': escrow.currency,
                'status': escrow.status,
                'buyer_confirmed': escrow.buyer_confirmed,
                'seller_delivered': escrow.seller_delivered,
                'is_buyer': request.user == escrow.purchase.buyer,
                'is_seller': request.user == escrow.purchase.dataset.owner,
                'can_auto_release': escrow.can_auto_release,
                'can_dispute': escrow.can_dispute and request.user == escrow.purchase.buyer,
                'can_confirm': escrow.status == 'active' and request.user == escrow.purchase.buyer and escrow.seller_delivered,
                'created_at': escrow.created_at.isoformat(),
                'auto_release_time': escrow.auto_release_time.isoformat() if escrow.auto_release_time else None,
                'dispute_reason': escrow.dispute_reason if escrow.dispute_reason else None,
                'disputed_at': escrow.disputed_at.isoformat() if escrow.disputed_at else None,
                'validator': escrow.validator.username if escrow.validator else None,
                'resolution_notes': escrow.resolution_notes if escrow.resolution_notes else None,
                'resolved_at': escrow.resolved_at.isoformat() if escrow.resolved_at else None,
                'buyer_username': escrow.purchase.buyer.username,
                'seller_username': escrow.purchase.dataset.owner.username,
                'escrow_fee': str(escrow.escrow_fee),
            })
        
        return Response(
            create_response_data(
                success=True,
                message="Escrows retrieved successfully",
                data={
                    'escrows': escrows_data,
                    'total': len(escrows_data)
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message=f"Failed to retrieve escrows: {str(e)}"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_dispute(request, escrow_id):
    """
    Create a dispute for an escrow.
    """
    try:
        escrow = get_object_or_404(Escrow, id=escrow_id)
        
        # Check permissions
        if escrow.purchase.buyer != request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="You can only dispute your own purchases",
                    errors={'permission': 'Access denied'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if dispute is allowed
        if not escrow.can_dispute:
            return Response(
                create_response_data(
                    success=False,
                    message="Dispute period has expired or escrow is not in active state",
                    errors={'escrow': 'Cannot dispute'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get dispute reason from request
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response(
                create_response_data(
                    success=False,
                    message="Dispute reason is required",
                    errors={'reason': 'This field is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update escrow status
        escrow.status = 'disputed'
        escrow.dispute_reason = reason
        escrow.disputed_at = timezone.now()
        
        # Auto-assign first available admin as validator
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.filter(is_staff=True, is_active=True).first()
        if admin_user:
            escrow.validator = admin_user
            logger.info(f"Auto-assigned admin {admin_user.username} as validator for escrow {escrow_id}")
        
        escrow.save()
        
        logger.info(f"Dispute created for escrow {escrow_id} by user {request.user}")
        
        return Response(
            create_response_data(
                success=True,
                message="Dispute created successfully and assigned to admin for review",
                data={
                    'escrow_id': str(escrow.id),
                    'status': escrow.status,
                    'dispute_reason': escrow.dispute_reason,
                    'disputed_at': escrow.disputed_at.isoformat(),
                    'validator': escrow.validator.username if escrow.validator else None
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error creating dispute for escrow {escrow_id}: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to create dispute",
                errors={'error': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
