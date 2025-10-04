"""
Wallet connection verification and authentication utilities.
"""
import hashlib
import secrets
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from eth_account.messages import encode_defunct
from web3 import Web3

from .web3_service import web3_service
from apps.authentication.models import UserProfile

import logging

logger = logging.getLogger(__name__)


class WalletVerificationService:
    """
    Service for wallet connection verification and authentication.
    """
    
    def __init__(self):
        self.nonce_expiry = getattr(settings, 'WALLET_NONCE_EXPIRY', 600)  # 10 minutes
        self.signature_expiry = getattr(settings, 'WALLET_SIGNATURE_EXPIRY', 300)  # 5 minutes
        self.max_attempts = getattr(settings, 'WALLET_MAX_ATTEMPTS', 5)
    
    def generate_nonce(self, wallet_address: str) -> str:
        """
        Generate a unique nonce for wallet verification.
        
        Args:
            wallet_address: The wallet address to generate nonce for
            
        Returns:
            Generated nonce string
        """
        try:
            # Validate wallet address
            if not web3_service.validate_address(wallet_address):
                raise ValueError("Invalid wallet address")
            
            wallet_address = wallet_address.lower()
            
            # Check rate limiting
            attempts_key = f"wallet_attempts_{wallet_address}"
            attempts = cache.get(attempts_key, 0)
            
            if attempts >= self.max_attempts:
                raise ValueError("Too many verification attempts. Please try again later.")
            
            # Generate cryptographically secure nonce
            timestamp = int(time.time())
            random_bytes = secrets.token_bytes(16)
            nonce_data = f"{wallet_address}:{timestamp}:{random_bytes.hex()}"
            nonce = hashlib.sha256(nonce_data.encode()).hexdigest()[:16]
            
            # Store nonce in cache
            nonce_key = f"wallet_nonce_{wallet_address}"
            cache.set(nonce_key, nonce, timeout=self.nonce_expiry)
            
            # Increment attempts counter
            cache.set(attempts_key, attempts + 1, timeout=3600)  # 1 hour
            
            logger.info(f"Generated nonce for wallet {wallet_address[:10]}...")
            return nonce
            
        except Exception as e:
            logger.error(f"Error generating nonce: {str(e)}")
            raise
    
    def create_sign_message(self, wallet_address: str, nonce: str) -> str:
        """
        Create a message for the user to sign.
        
        Args:
            wallet_address: The wallet address
            nonce: The generated nonce
            
        Returns:
            Message string to be signed
        """
        timestamp = int(time.time())
        domain = getattr(settings, 'FRONTEND_DOMAIN', 'neurodata.io')
        
        message = (
            f"Welcome to NeuroData!\n\n"
            f"Please sign this message to verify your wallet ownership.\n\n"
            f"Wallet: {wallet_address}\n"
            f"Nonce: {nonce}\n"
            f"Timestamp: {timestamp}\n"
            f"Domain: {domain}\n\n"
            f"This request will not trigger any blockchain transaction or cost any gas fees."
        )
        
        return message
    
    def verify_signature(self, wallet_address: str, signature: str, 
                        message: str = None) -> Tuple[bool, Optional[str]]:
        """
        Verify wallet signature.
        
        Args:
            wallet_address: The wallet address
            signature: The signature to verify
            message: Optional custom message (if not provided, will reconstruct)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate inputs
            if not web3_service.validate_address(wallet_address):
                return False, "Invalid wallet address"
            
            if not signature:
                return False, "Signature is required"
            
            wallet_address = wallet_address.lower()
            
            # Get stored nonce
            nonce_key = f"wallet_nonce_{wallet_address}"
            stored_nonce = cache.get(nonce_key)
            
            if not stored_nonce:
                return False, "Nonce expired or not found. Please request a new nonce."
            
            # Reconstruct message if not provided
            if not message:
                message = self.create_sign_message(wallet_address, stored_nonce)
            
            # Verify signature using Web3
            try:
                # Create message hash
                message_hash = encode_defunct(text=message)
                
                # Recover address from signature
                recovered_address = web3_service.w3.eth.account.recover_message(
                    message_hash, 
                    signature=signature
                )
                
                # Compare addresses (case-insensitive)
                is_valid = recovered_address.lower() == wallet_address.lower()
                
                if is_valid:
                    # Clear the nonce to prevent replay attacks
                    cache.delete(nonce_key)
                    
                    # Reset attempts counter
                    attempts_key = f"wallet_attempts_{wallet_address}"
                    cache.delete(attempts_key)
                    
                    # Store successful verification
                    verification_key = f"wallet_verified_{wallet_address}"
                    cache.set(verification_key, True, timeout=self.signature_expiry)
                    
                    logger.info(f"Wallet verification successful for {wallet_address[:10]}...")
                    return True, None
                else:
                    return False, "Signature verification failed"
                    
            except Exception as e:
                logger.error(f"Error verifying signature: {str(e)}")
                return False, f"Signature verification error: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in verify_signature: {str(e)}")
            return False, f"Verification error: {str(e)}"
    
    def is_wallet_verified(self, wallet_address: str) -> bool:
        """
        Check if wallet is currently verified.
        
        Args:
            wallet_address: The wallet address to check
            
        Returns:
            True if wallet is verified and verification hasn't expired
        """
        if not web3_service.validate_address(wallet_address):
            return False
        
        wallet_address = wallet_address.lower()
        verification_key = f"wallet_verified_{wallet_address}"
        return cache.get(verification_key, False)
    
    def get_wallet_info(self, wallet_address: str) -> Dict[str, any]:
        """
        Get comprehensive wallet information.
        
        Args:
            wallet_address: The wallet address
            
        Returns:
            Dictionary with wallet information
        """
        if not web3_service.validate_address(wallet_address):
            return {'error': 'Invalid wallet address'}
        
        try:
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # Get balances
            eth_balance = web3_service.get_balance(wallet_address)
            nrc_balance = web3_service.get_balance(wallet_address, 'NeuroCoin')
            
            # Get transaction count (nonce)
            transaction_count = web3_service.w3.eth.get_transaction_count(wallet_address)
            
            # Check if wallet is associated with a user
            user_profile = None
            try:
                profile = UserProfile.objects.get(wallet_address__iexact=wallet_address)
                user_profile = {
                    'user_id': profile.user.id,
                    'username': profile.user.username,
                    'email': profile.user.email,
                    'is_verified': profile.is_verified,
                    'reputation_score': str(profile.reputation_score)
                }
            except UserProfile.DoesNotExist:
                pass
            
            # Get verification status
            is_verified = self.is_wallet_verified(wallet_address)
            
            return {
                'address': wallet_address,
                'eth_balance': str(eth_balance),
                'nrc_balance': str(nrc_balance),
                'transaction_count': transaction_count,
                'is_verified': is_verified,
                'user_profile': user_profile,
                'network_info': web3_service.get_network_info()
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet info: {str(e)}")
            return {'error': str(e)}
    
    def link_wallet_to_user(self, user, wallet_address: str) -> Tuple[bool, Optional[str]]:
        """
        Link a verified wallet to a user account.
        
        Args:
            user: Django user instance
            wallet_address: The wallet address to link
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate wallet address
            if not web3_service.validate_address(wallet_address):
                return False, "Invalid wallet address"
            
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # Check if wallet is verified
            if not self.is_wallet_verified(wallet_address):
                return False, "Wallet must be verified before linking"
            
            # Check if wallet is already linked to another user
            existing_profile = UserProfile.objects.filter(
                wallet_address__iexact=wallet_address
            ).exclude(user=user).first()
            
            if existing_profile:
                return False, "Wallet is already linked to another account"
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'wallet_address': wallet_address}
            )
            
            if not created and profile.wallet_address:
                if profile.wallet_address.lower() != wallet_address.lower():
                    return False, "User already has a different wallet linked"
            else:
                profile.wallet_address = wallet_address
                profile.save()
            
            logger.info(f"Linked wallet {wallet_address[:10]}... to user {user.username}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error linking wallet to user: {str(e)}")
            return False, str(e)
    
    def unlink_wallet_from_user(self, user) -> Tuple[bool, Optional[str]]:
        """
        Unlink wallet from user account.
        
        Args:
            user: Django user instance
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            profile = UserProfile.objects.get(user=user)
            
            if not profile.wallet_address:
                return False, "No wallet linked to this account"
            
            old_address = profile.wallet_address
            profile.wallet_address = None
            profile.save()
            
            # Clear verification cache
            verification_key = f"wallet_verified_{old_address.lower()}"
            cache.delete(verification_key)
            
            logger.info(f"Unlinked wallet {old_address[:10]}... from user {user.username}")
            return True, None
            
        except UserProfile.DoesNotExist:
            return False, "User profile not found"
        except Exception as e:
            logger.error(f"Error unlinking wallet: {str(e)}")
            return False, str(e)
    
    def get_verification_status(self, wallet_address: str) -> Dict[str, any]:
        """
        Get detailed verification status for a wallet.
        
        Args:
            wallet_address: The wallet address
            
        Returns:
            Dictionary with verification status details
        """
        if not web3_service.validate_address(wallet_address):
            return {'error': 'Invalid wallet address'}
        
        wallet_address = wallet_address.lower()
        
        # Check if nonce exists
        nonce_key = f"wallet_nonce_{wallet_address}"
        has_nonce = cache.get(nonce_key) is not None
        
        # Check verification status
        is_verified = self.is_wallet_verified(wallet_address)
        
        # Check attempts
        attempts_key = f"wallet_attempts_{wallet_address}"
        attempts = cache.get(attempts_key, 0)
        
        return {
            'wallet_address': wallet_address,
            'has_active_nonce': has_nonce,
            'is_verified': is_verified,
            'attempts_used': attempts,
            'max_attempts': self.max_attempts,
            'can_request_nonce': attempts < self.max_attempts,
            'nonce_expiry_seconds': self.nonce_expiry,
            'verification_expiry_seconds': self.signature_expiry
        }
    
    def cleanup_expired_data(self):
        """
        Clean up expired verification data.
        This method can be called periodically to clean up cache.
        """
        # This is handled automatically by cache TTL
        # But we could implement additional cleanup logic here if needed
        logger.info("Wallet verification cleanup completed")


# Global wallet verification service instance
wallet_verification_service = WalletVerificationService()
