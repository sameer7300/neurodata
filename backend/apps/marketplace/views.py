from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Purchase
from core.utils import create_response_data


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_purchase(request, purchase_id):
    """
    Update a purchase with transaction hash and status.
    """
    try:
        # Get the purchase and verify ownership
        purchase = get_object_or_404(Purchase, id=purchase_id, buyer=request.user)
        
        # Handle GET request (retrieve purchase details)
        if request.method == 'GET':
            return Response(
                create_response_data(
                    success=True,
                    message="Purchase retrieved successfully",
                    data={
                        'id': str(purchase.id),
                        'dataset_id': str(purchase.dataset.id),
                        'dataset_title': purchase.dataset.title,
                        'amount': str(purchase.amount),
                        'currency': purchase.currency,
                        'payment_method': purchase.payment_method,
                        'transaction_hash': purchase.transaction_hash,
                        'status': purchase.status,
                        'created_at': purchase.created_at.isoformat(),
                        'completed_at': purchase.completed_at.isoformat() if purchase.completed_at else None
                    }
                ),
                status=status.HTTP_200_OK
            )
        
        # Handle PATCH request (update purchase)
        # Get data from request
        transaction_hash = request.data.get('transaction_hash')
        new_status = request.data.get('status')
        
        # Validate status
        valid_statuses = [choice[0] for choice in Purchase.STATUS_CHOICES]
        if new_status and new_status not in valid_statuses:
            return Response(
                create_response_data(
                    success=False,
                    message="Invalid status",
                    errors={'status': f'Status must be one of: {valid_statuses}'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update purchase
        if transaction_hash:
            purchase.transaction_hash = transaction_hash
        
        if new_status:
            purchase.status = new_status
            
            # Set completion time if status is completed
            if new_status == 'completed':
                purchase.completed_at = timezone.now()
        
        purchase.save()
        
        return Response(
            create_response_data(
                success=True,
                message="Purchase updated successfully",
                data={
                    'id': str(purchase.id),
                    'status': purchase.status,
                    'transaction_hash': purchase.transaction_hash,
                    'completed_at': purchase.completed_at.isoformat() if purchase.completed_at else None
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message="Failed to update purchase",
                errors={'detail': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_purchase(request, purchase_id):
    """
    Get purchase details.
    """
    try:
        purchase = get_object_or_404(Purchase, id=purchase_id, buyer=request.user)
        
        return Response(
            create_response_data(
                success=True,
                message="Purchase retrieved successfully",
                data={
                    'id': str(purchase.id),
                    'dataset_id': str(purchase.dataset.id),
                    'dataset_title': purchase.dataset.title,
                    'amount': str(purchase.amount),
                    'currency': purchase.currency,
                    'payment_method': purchase.payment_method,
                    'transaction_hash': purchase.transaction_hash,
                    'status': purchase.status,
                    'created_at': purchase.created_at.isoformat(),
                    'completed_at': purchase.completed_at.isoformat() if purchase.completed_at else None
                }
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message="Failed to retrieve purchase",
                errors={'detail': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_purchases(request):
    """
    List all purchases for the authenticated user.
    """
    try:
        purchases = Purchase.objects.filter(buyer=request.user).order_by('-created_at')
        
        purchase_data = []
        for purchase in purchases:
            purchase_data.append({
                'id': str(purchase.id),
                'dataset_id': str(purchase.dataset.id),
                'dataset_title': purchase.dataset.title,
                'amount': str(purchase.amount),
                'currency': purchase.currency,
                'payment_method': purchase.payment_method,
                'transaction_hash': purchase.transaction_hash,
                'status': purchase.status,
                'created_at': purchase.created_at.isoformat(),
                'completed_at': purchase.completed_at.isoformat() if purchase.completed_at else None
            })
        
        return Response(
            create_response_data(
                success=True,
                message="Purchases retrieved successfully",
                data=purchase_data
            ),
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            create_response_data(
                success=False,
                message="Failed to retrieve purchases",
                errors={'detail': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
