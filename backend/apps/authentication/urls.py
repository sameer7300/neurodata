"""
URL patterns for authentication app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Traditional Authentication
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Web3 Wallet Authentication
    path('wallet/connect/', views.WalletConnectView.as_view(), name='wallet_connect'),
    path('wallet/auth/', views.WalletAuthView.as_view(), name='wallet_auth'),
    path('wallet/link/', views.link_wallet, name='wallet_link'),
    path('wallet/unlink/', views.unlink_wallet, name='wallet_unlink'),
    
    # Password Management
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # User Profile
    path('user/', views.UserView.as_view(), name='user'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('stats/', views.user_stats, name='user_stats'),
    
    # API Keys
    path('api-keys/', views.APIKeyListCreateView.as_view(), name='api_keys'),
]
