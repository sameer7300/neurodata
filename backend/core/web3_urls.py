"""
URL patterns for Web3 integration API endpoints.
"""
from django.urls import path
from . import web3_views

app_name = 'web3'

urlpatterns = [
    # Network and status endpoints
    path('network/status/', web3_views.network_status, name='network_status'),
    path('gas/prices/', web3_views.gas_prices, name='gas_prices'),
    path('gas/estimate/', web3_views.estimate_gas, name='estimate_gas'),
    
    # Wallet verification endpoints
    path('wallet/nonce/', web3_views.wallet_nonce, name='wallet_nonce'),
    path('wallet/verify/', web3_views.verify_wallet_signature, name='verify_wallet_signature'),
    path('wallet/info/', web3_views.wallet_info, name='wallet_info'),
    path('wallet/link/', web3_views.link_wallet, name='link_wallet'),
    path('wallet/unlink/', web3_views.unlink_wallet, name='unlink_wallet'),
    
    # Transaction endpoints
    path('transaction/status/', web3_views.transaction_status, name='transaction_status'),
    
    # Contract endpoints
    path('contract/info/', web3_views.contract_info, name='contract_info'),
    
    # Monitoring endpoints
    path('monitoring/status/', web3_views.monitoring_status, name='monitoring_status'),
    path('events/recent/', web3_views.recent_events, name='recent_events'),
]
