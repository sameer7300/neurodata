"""
API views for Web3 integration.
"""
import logging
from typing import Dict, Any

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .web3_service import web3_service
from .web3_utils import Web3Utils, format_nrc_amount, format_eth_amount, get_transaction_url
from .wallet_verification import wallet_verification_service
from .gas_manager import gas_manager, GasSpeed
from .event_listener import event_listener
from .blockchain_monitor import blockchain_monitor
from core.utils import create_response_data

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(30)  # Cache for 30 seconds
def network_status(request):
    """
    Get current blockchain network status.
    """
    try:
        status_info = Web3Utils.get_network_status()
        
        return Response(
            create_response_data(
                success=True,
                data=status_info
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting network status: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get network status",
                errors={'network': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(30)  # Cache for 30 seconds
def gas_prices(request):
    """
    Get current gas prices for different speeds.
    """
    try:
        current_prices = gas_manager.get_current_gas_prices()
        
        # Format prices for response
        formatted_prices = {}
        for speed, price_info in current_prices.items():
            formatted_prices[speed.value] = {
                'gas_price_wei': price_info.gas_price,
                'gas_price_gwei': float(Web3Utils.wei_to_gwei(price_info.gas_price)),
                'max_fee_per_gas_wei': price_info.max_fee_per_gas,
                'max_fee_per_gas_gwei': float(Web3Utils.wei_to_gwei(price_info.max_fee_per_gas)) if price_info.max_fee_per_gas else None,
                'max_priority_fee_per_gas_wei': price_info.max_priority_fee_per_gas,
                'max_priority_fee_per_gas_gwei': float(Web3Utils.wei_to_gwei(price_info.max_priority_fee_per_gas)) if price_info.max_priority_fee_per_gas else None,
                'estimated_time_minutes': price_info.estimated_time_minutes,
                'confidence_level': price_info.confidence_level
            }
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'prices': formatted_prices,
                    'timestamp': cache.get('gas_prices_timestamp'),
                    'network_info': web3_service.get_network_info()
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting gas prices: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get gas prices",
                errors={'gas': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def estimate_gas(request):
    """
    Estimate gas for a transaction.
    """
    try:
        transaction_data = request.data.get('transaction', {})
        speed = request.data.get('speed', 'standard')
        
        if not transaction_data:
            return Response(
                create_response_data(
                    success=False,
                    message="Transaction data is required",
                    errors={'transaction': 'This field is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate speed
        try:
            gas_speed = GasSpeed(speed)
        except ValueError:
            gas_speed = GasSpeed.STANDARD
        
        # Estimate transaction cost
        cost_estimate = gas_manager.estimate_transaction_cost(transaction_data, gas_speed)
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'gas_limit': cost_estimate.gas_limit,
                    'gas_price': {
                        'wei': cost_estimate.gas_price_info.gas_price,
                        'gwei': float(Web3Utils.wei_to_gwei(cost_estimate.gas_price_info.gas_price)),
                        'speed': cost_estimate.gas_price_info.speed.value,
                        'estimated_time_minutes': cost_estimate.gas_price_info.estimated_time_minutes,
                        'confidence_level': cost_estimate.gas_price_info.confidence_level
                    },
                    'total_cost': {
                        'wei': cost_estimate.total_cost_wei,
                        'eth': cost_estimate.total_cost_eth,
                        'usd': cost_estimate.total_cost_usd,
                        'formatted_eth': format_eth_amount(cost_estimate.total_cost_wei)
                    },
                    'network_fee_wei': cost_estimate.network_fee_wei,
                    'priority_fee_wei': cost_estimate.priority_fee_wei
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error estimating gas: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to estimate gas",
                errors={'estimation': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def wallet_nonce(request):
    """
    Generate a nonce for wallet verification.
    """
    try:
        wallet_address = request.data.get('wallet_address')
        
        if not wallet_address:
            return Response(
                create_response_data(
                    success=False,
                    message="Wallet address is required",
                    errors={'wallet_address': 'This field is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not Web3Utils.validate_address(wallet_address):
            return Response(
                create_response_data(
                    success=False,
                    message="Invalid wallet address",
                    errors={'wallet_address': 'Invalid Ethereum address format'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate nonce
        nonce = wallet_verification_service.generate_nonce(wallet_address)
        
        # Create sign message
        sign_message = wallet_verification_service.create_sign_message(wallet_address, nonce)
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'nonce': nonce,
                    'message': sign_message,
                    'wallet_address': wallet_address,
                    'expires_in_seconds': wallet_verification_service.nonce_expiry
                }
            )
        )
        
    except ValueError as e:
        return Response(
            create_response_data(
                success=False,
                message=str(e),
                errors={'wallet': str(e)}
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error generating wallet nonce: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to generate nonce",
                errors={'nonce': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_wallet_signature(request):
    """
    Verify wallet signature.
    """
    try:
        wallet_address = request.data.get('wallet_address')
        signature = request.data.get('signature')
        message = request.data.get('message')
        
        if not wallet_address or not signature:
            return Response(
                create_response_data(
                    success=False,
                    message="Wallet address and signature are required",
                    errors={
                        'wallet_address': 'This field is required' if not wallet_address else None,
                        'signature': 'This field is required' if not signature else None
                    }
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify signature
        is_valid, error_message = wallet_verification_service.verify_signature(
            wallet_address, signature, message
        )
        
        if is_valid:
            # Get wallet info
            wallet_info = wallet_verification_service.get_wallet_info(wallet_address)
            
            return Response(
                create_response_data(
                    success=True,
                    message="Wallet signature verified successfully",
                    data={
                        'verified': True,
                        'wallet_info': wallet_info
                    }
                )
            )
        else:
            return Response(
                create_response_data(
                    success=False,
                    message=error_message or "Signature verification failed",
                    errors={'signature': error_message}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error verifying wallet signature: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to verify signature",
                errors={'verification': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def wallet_info(request):
    """
    Get wallet information.
    """
    try:
        wallet_address = request.query_params.get('address')
        
        if not wallet_address:
            return Response(
                create_response_data(
                    success=False,
                    message="Wallet address is required",
                    errors={'address': 'This parameter is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not Web3Utils.validate_address(wallet_address):
            return Response(
                create_response_data(
                    success=False,
                    message="Invalid wallet address",
                    errors={'address': 'Invalid Ethereum address format'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get wallet information
        wallet_data = wallet_verification_service.get_wallet_info(wallet_address)
        
        if 'error' in wallet_data:
            return Response(
                create_response_data(
                    success=False,
                    message="Failed to get wallet information",
                    errors={'wallet': wallet_data['error']}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Add formatted amounts
        wallet_data['formatted_eth_balance'] = format_eth_amount(
            Web3Utils.ether_to_wei(wallet_data['eth_balance'])
        )
        wallet_data['formatted_nrc_balance'] = format_nrc_amount(
            Web3Utils.ether_to_wei(wallet_data['nrc_balance'])
        )
        
        return Response(
            create_response_data(
                success=True,
                data=wallet_data
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting wallet info: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get wallet information",
                errors={'wallet': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def transaction_status(request):
    """
    Get transaction status and details.
    """
    try:
        tx_hash = request.query_params.get('hash')
        
        if not tx_hash:
            return Response(
                create_response_data(
                    success=False,
                    message="Transaction hash is required",
                    errors={'hash': 'This parameter is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not Web3Utils.is_valid_transaction_hash(tx_hash):
            return Response(
                create_response_data(
                    success=False,
                    message="Invalid transaction hash",
                    errors={'hash': 'Invalid transaction hash format'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transaction status
        tx_status = Web3Utils.get_transaction_status(tx_hash)
        
        if 'error' in tx_status:
            return Response(
                create_response_data(
                    success=False,
                    message="Failed to get transaction status",
                    errors={'transaction': tx_status['error']}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Add explorer URL
        if web3_service.is_connected():
            tx_status['explorer_url'] = get_transaction_url(
                tx_hash, web3_service.w3.eth.chain_id
            )
        
        # Format transaction fee
        if 'transaction_fee' in tx_status:
            tx_status['formatted_transaction_fee'] = format_eth_amount(tx_status['transaction_fee'])
        
        return Response(
            create_response_data(
                success=True,
                data=tx_status
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting transaction status: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get transaction status",
                errors={'transaction': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def contract_info(request):
    """
    Get smart contract information.
    """
    try:
        contract_name = request.query_params.get('name')
        
        if not contract_name:
            return Response(
                create_response_data(
                    success=False,
                    message="Contract name is required",
                    errors={'name': 'This parameter is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get contract information
        contract_data = Web3Utils.get_contract_info(contract_name)
        
        if 'error' in contract_data:
            return Response(
                create_response_data(
                    success=False,
                    message="Failed to get contract information",
                    errors={'contract': contract_data['error']}
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add token info if it's a token contract
        if contract_name in ['NeuroCoin']:
            token_info = Web3Utils.get_token_info(contract_name)
            if 'error' not in token_info:
                contract_data.update(token_info)
        
        return Response(
            create_response_data(
                success=True,
                data=contract_data
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting contract info: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get contract information",
                errors={'contract': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monitoring_status(request):
    """
    Get blockchain monitoring status (admin only).
    """
    try:
        if not request.user.is_staff:
            return Response(
                create_response_data(
                    success=False,
                    message="Admin access required",
                    errors={'permission': 'Admin access required'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get monitoring status
        monitor_status = blockchain_monitor.get_monitoring_status()
        listener_status = event_listener.get_status()
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'blockchain_monitor': monitor_status,
                    'event_listener': listener_status,
                    'web3_service': {
                        'connected': web3_service.is_connected(),
                        'network_info': web3_service.get_network_info()
                    }
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get monitoring status",
                errors={'monitoring': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_events(request):
    """
    Get recent blockchain events.
    """
    try:
        event_type = request.query_params.get('type')
        limit = int(request.query_params.get('limit', 20))
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        # Get recent events
        events = event_listener.get_recent_events(event_type, limit)
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'events': events,
                    'count': len(events),
                    'event_type_filter': event_type
                }
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting recent events: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to get recent events",
                errors={'events': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_wallet(request):
    """
    Link a verified wallet to user account.
    """
    try:
        wallet_address = request.data.get('wallet_address')
        
        if not wallet_address:
            return Response(
                create_response_data(
                    success=False,
                    message="Wallet address is required",
                    errors={'wallet_address': 'This field is required'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Link wallet to user
        success, error_message = wallet_verification_service.link_wallet_to_user(
            request.user, wallet_address
        )
        
        if success:
            return Response(
                create_response_data(
                    success=True,
                    message="Wallet linked successfully",
                    data={'wallet_address': wallet_address}
                )
            )
        else:
            return Response(
                create_response_data(
                    success=False,
                    message=error_message,
                    errors={'wallet': error_message}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error linking wallet: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to link wallet",
                errors={'wallet': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_wallet(request):
    """
    Unlink wallet from user account.
    """
    try:
        # Unlink wallet from user
        success, error_message = wallet_verification_service.unlink_wallet_from_user(request.user)
        
        if success:
            return Response(
                create_response_data(
                    success=True,
                    message="Wallet unlinked successfully"
                )
            )
        else:
            return Response(
                create_response_data(
                    success=False,
                    message=error_message,
                    errors={'wallet': error_message}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error unlinking wallet: {str(e)}")
        return Response(
            create_response_data(
                success=False,
                message="Failed to unlink wallet",
                errors={'wallet': str(e)}
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
