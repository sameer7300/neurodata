"""
IPFS service for decentralized dataset storage with encryption and access control.
"""
import hashlib
import json
import logging
import os
import tempfile
from typing import Dict, List, Optional, Tuple, Any, BinaryIO
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

logger = logging.getLogger(__name__)


class IPFSProvider(Enum):
    """IPFS service providers."""
    PINATA = "pinata"
    WEB3_STORAGE = "web3_storage"
    INFURA = "infura"
    LOCAL = "local"


@dataclass
class IPFSUploadResult:
    """IPFS upload result."""
    success: bool
    ipfs_hash: str = ""
    ipfs_url: str = ""
    size: int = 0
    error: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class EncryptionResult:
    """Encryption result."""
    encrypted_data: bytes
    encryption_key: bytes
    salt: bytes
    nonce: bytes
    tag: bytes


class IPFSService:
    """
    Comprehensive IPFS service with encryption and access control.
    """
    
    def __init__(self):
        self.config = getattr(settings, 'IPFS_CONFIG', {})
        self.provider = IPFSProvider(self.config.get('PROVIDER', 'pinata'))
        self.encryption_enabled = self.config.get('ENCRYPTION_ENABLED', True)
        self.cache_timeout = self.config.get('CACHE_TIMEOUT', 3600)  # 1 hour
        
        # Provider-specific configuration
        self._setup_provider()
    
    def _setup_provider(self):
        """Setup provider-specific configuration."""
        if self.provider == IPFSProvider.PINATA:
            self.api_key = self.config.get('PINATA_API_KEY')
            self.api_secret = self.config.get('PINATA_API_SECRET')
            self.base_url = "https://api.pinata.cloud"
            self.gateway_url = "https://gateway.pinata.cloud/ipfs/"
            
        elif self.provider == IPFSProvider.WEB3_STORAGE:
            self.api_token = self.config.get('WEB3_STORAGE_TOKEN')
            self.base_url = "https://api.web3.storage"
            self.gateway_url = "https://w3s.link/ipfs/"
            
        elif self.provider == IPFSProvider.INFURA:
            self.project_id = self.config.get('INFURA_PROJECT_ID')
            self.project_secret = self.config.get('INFURA_PROJECT_SECRET')
            self.base_url = "https://ipfs.infura.io:5001/api/v0"
            self.gateway_url = "https://ipfs.infura.io/ipfs/"
            
        elif self.provider == IPFSProvider.LOCAL:
            self.base_url = self.config.get('LOCAL_NODE_URL', 'http://localhost:5001/api/v0')
            self.gateway_url = self.config.get('LOCAL_GATEWAY_URL', 'http://localhost:8080/ipfs/')
    
    def upload_dataset(self, file_path: str, dataset_id: int, 
                      owner_id: int, encrypt: bool = True) -> IPFSUploadResult:
        """
        Upload dataset to IPFS with optional encryption.
        
        Args:
            file_path: Path to the dataset file
            dataset_id: Dataset ID
            owner_id: Owner user ID
            encrypt: Whether to encrypt the dataset
            
        Returns:
            IPFSUploadResult object
        """
        try:
            if not os.path.exists(file_path):
                return IPFSUploadResult(
                    success=False,
                    error="File not found"
                )
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Encrypt if enabled
            if encrypt and self.encryption_enabled:
                encryption_result = self._encrypt_data(file_data, dataset_id, owner_id)
                upload_data = encryption_result.encrypted_data
                
                # Store encryption metadata
                self._store_encryption_metadata(
                    dataset_id, 
                    encryption_result.encryption_key,
                    encryption_result.salt,
                    encryption_result.nonce,
                    encryption_result.tag
                )
            else:
                upload_data = file_data
            
            # Upload to IPFS
            result = self._upload_to_ipfs(upload_data, f"dataset_{dataset_id}")
            
            if result.success:
                # Store IPFS metadata
                self._store_ipfs_metadata(dataset_id, result.ipfs_hash, result.size, encrypt)
                
                logger.info(f"Dataset {dataset_id} uploaded to IPFS: {result.ipfs_hash}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading dataset to IPFS: {str(e)}")
            return IPFSUploadResult(
                success=False,
                error=str(e)
            )
    
    def download_dataset(self, dataset_id: int, user_id: int, 
                        ipfs_hash: str = None) -> Tuple[bool, bytes, str]:
        """
        Download and decrypt dataset from IPFS.
        
        Args:
            dataset_id: Dataset ID
            user_id: Requesting user ID
            ipfs_hash: Optional IPFS hash (will be retrieved if not provided)
            
        Returns:
            Tuple of (success, decrypted_data, error_message)
        """
        try:
            # Check access permissions
            if not self._check_access_permission(dataset_id, user_id):
                return False, b"", "Access denied"
            
            # Get IPFS hash if not provided
            if not ipfs_hash:
                metadata = self._get_ipfs_metadata(dataset_id)
                if not metadata:
                    return False, b"", "Dataset metadata not found"
                ipfs_hash = metadata['ipfs_hash']
            
            # Download from IPFS
            success, encrypted_data, error = self._download_from_ipfs(ipfs_hash)
            if not success:
                return False, b"", error
            
            # Decrypt if needed
            metadata = self._get_ipfs_metadata(dataset_id)
            if metadata and metadata.get('encrypted', False):
                decrypted_data = self._decrypt_data(encrypted_data, dataset_id, user_id)
                if decrypted_data is None:
                    return False, b"", "Decryption failed"
                return True, decrypted_data, ""
            else:
                return True, encrypted_data, ""
                
        except Exception as e:
            logger.error(f"Error downloading dataset from IPFS: {str(e)}")
            return False, b"", str(e)
    
    def _encrypt_data(self, data: bytes, dataset_id: int, owner_id: int) -> EncryptionResult:
        """
        Encrypt data using AES-GCM.
        
        Args:
            data: Data to encrypt
            dataset_id: Dataset ID
            owner_id: Owner ID
            
        Returns:
            EncryptionResult object
        """
        try:
            # Generate salt and derive key
            salt = secrets.token_bytes(32)
            key_material = f"{dataset_id}:{owner_id}:{settings.SECRET_KEY}".encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(key_material)
            
            # Generate nonce
            nonce = secrets.token_bytes(12)
            
            # Encrypt data
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(data) + encryptor.finalize()
            
            return EncryptionResult(
                encrypted_data=encrypted_data,
                encryption_key=key,
                salt=salt,
                nonce=nonce,
                tag=encryptor.tag
            )
            
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise
    
    def _decrypt_data(self, encrypted_data: bytes, dataset_id: int, user_id: int) -> Optional[bytes]:
        """
        Decrypt data using stored encryption metadata.
        
        Args:
            encrypted_data: Encrypted data
            dataset_id: Dataset ID
            user_id: User ID
            
        Returns:
            Decrypted data or None if failed
        """
        try:
            # Get encryption metadata
            metadata = self._get_encryption_metadata(dataset_id)
            if not metadata:
                logger.error(f"Encryption metadata not found for dataset {dataset_id}")
                return None
            
            # Reconstruct key
            key_material = f"{dataset_id}:{metadata['owner_id']}:{settings.SECRET_KEY}".encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=metadata['salt'],
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(key_material)
            
            # Decrypt data
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(metadata['nonce'], metadata['tag']),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return None
    
    def _upload_to_ipfs(self, data: bytes, filename: str) -> IPFSUploadResult:
        """
        Upload data to IPFS based on configured provider.
        
        Args:
            data: Data to upload
            filename: Filename for the upload
            
        Returns:
            IPFSUploadResult object
        """
        if self.provider == IPFSProvider.PINATA:
            return self._upload_to_pinata(data, filename)
        elif self.provider == IPFSProvider.WEB3_STORAGE:
            return self._upload_to_web3_storage(data, filename)
        elif self.provider == IPFSProvider.INFURA:
            return self._upload_to_infura(data, filename)
        elif self.provider == IPFSProvider.LOCAL:
            return self._upload_to_local(data, filename)
        else:
            return IPFSUploadResult(
                success=False,
                error=f"Unsupported IPFS provider: {self.provider}"
            )
    
    def _upload_to_pinata(self, data: bytes, filename: str) -> IPFSUploadResult:
        """Upload to Pinata."""
        try:
            url = f"{self.base_url}/pinning/pinFileToIPFS"
            
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            files = {
                'file': (filename, data, 'application/octet-stream')
            }
            
            metadata = {
                'name': filename,
                'keyvalues': {
                    'uploaded_at': timezone.now().isoformat(),
                    'service': 'neurodata'
                }
            }
            
            data_payload = {
                'pinataMetadata': json.dumps(metadata),
                'pinataOptions': json.dumps({'cidVersion': 1})
            }
            
            response = requests.post(url, files=files, data=data_payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result['IpfsHash']
                
                return IPFSUploadResult(
                    success=True,
                    ipfs_hash=ipfs_hash,
                    ipfs_url=f"{self.gateway_url}{ipfs_hash}",
                    size=result.get('PinSize', len(data)),
                    metadata=result
                )
            else:
                return IPFSUploadResult(
                    success=False,
                    error=f"Pinata upload failed: {response.text}"
                )
                
        except Exception as e:
            return IPFSUploadResult(
                success=False,
                error=f"Pinata upload error: {str(e)}"
            )
    
    def _download_from_ipfs(self, ipfs_hash: str) -> Tuple[bool, bytes, str]:
        """
        Download data from IPFS.
        
        Args:
            ipfs_hash: IPFS hash to download
            
        Returns:
            Tuple of (success, data, error_message)
        """
        try:
            # Try cache first
            cache_key = f"ipfs_data_{ipfs_hash}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return True, cached_data, ""
            
            # Download from gateway
            url = f"{self.gateway_url}{ipfs_hash}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.content
                
                # Cache the data
                cache.set(cache_key, data, timeout=self.cache_timeout)
                
                return True, data, ""
            else:
                return False, b"", f"Download failed: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error downloading from IPFS: {str(e)}")
            return False, b"", str(e)
    
    def _check_access_permission(self, dataset_id: int, user_id: int) -> bool:
        """
        Check if user has permission to access dataset.
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID
            
        Returns:
            True if user has access
        """
        try:
            from apps.datasets.models import Dataset
            from apps.marketplace.models import Purchase
            
            # Get dataset
            try:
                dataset = Dataset.objects.get(id=dataset_id)
            except Dataset.DoesNotExist:
                return False
            
            # Owner always has access
            if dataset.owner_id == user_id:
                return True
            
            # Free datasets are accessible to all
            if dataset.price == 0:
                return True
            
            # Check if user has purchased the dataset
            has_purchased = Purchase.objects.filter(
                dataset_id=dataset_id,
                buyer_id=user_id,
                status__in=['completed', 'in_escrow']
            ).exists()
            
            return has_purchased
            
        except Exception as e:
            logger.error(f"Error checking access permission: {str(e)}")
            return False
    
    def _store_encryption_metadata(self, dataset_id: int, key: bytes, 
                                 salt: bytes, nonce: bytes, tag: bytes):
        """Store encryption metadata securely."""
        try:
            from apps.datasets.models import Dataset
            
            # Encode metadata
            metadata = {
                'salt': base64.b64encode(salt).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'tag': base64.b64encode(tag).decode(),
                'owner_id': Dataset.objects.get(id=dataset_id).owner_id
            }
            
            # Store in cache with dataset-specific key
            cache_key = f"encryption_metadata_{dataset_id}"
            cache.set(cache_key, metadata, timeout=None)  # No expiration
            
        except Exception as e:
            logger.error(f"Error storing encryption metadata: {str(e)}")
    
    def _get_encryption_metadata(self, dataset_id: int) -> Optional[Dict]:
        """Get encryption metadata."""
        try:
            cache_key = f"encryption_metadata_{dataset_id}"
            metadata = cache.get(cache_key)
            
            if metadata:
                # Decode metadata
                metadata['salt'] = base64.b64decode(metadata['salt'])
                metadata['nonce'] = base64.b64decode(metadata['nonce'])
                metadata['tag'] = base64.b64decode(metadata['tag'])
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting encryption metadata: {str(e)}")
            return None
    
    def _store_ipfs_metadata(self, dataset_id: int, ipfs_hash: str, 
                           size: int, encrypted: bool):
        """Store IPFS metadata."""
        try:
            metadata = {
                'ipfs_hash': ipfs_hash,
                'size': size,
                'encrypted': encrypted,
                'uploaded_at': timezone.now().isoformat()
            }
            
            cache_key = f"ipfs_metadata_{dataset_id}"
            cache.set(cache_key, metadata, timeout=None)  # No expiration
            
        except Exception as e:
            logger.error(f"Error storing IPFS metadata: {str(e)}")
    
    def _get_ipfs_metadata(self, dataset_id: int) -> Optional[Dict]:
        """Get IPFS metadata."""
        try:
            cache_key = f"ipfs_metadata_{dataset_id}"
            return cache.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting IPFS metadata: {str(e)}")
            return None
    
    def verify_integrity(self, dataset_id: int, expected_hash: str = None) -> bool:
        """
        Verify dataset integrity by comparing hashes.
        
        Args:
            dataset_id: Dataset ID
            expected_hash: Expected hash (will be retrieved if not provided)
            
        Returns:
            True if integrity check passes
        """
        try:
            # Get IPFS metadata
            metadata = self._get_ipfs_metadata(dataset_id)
            if not metadata:
                return False
            
            ipfs_hash = metadata['ipfs_hash']
            
            # Download and verify
            success, data, error = self._download_from_ipfs(ipfs_hash)
            if not success:
                return False
            
            # Calculate hash of downloaded data
            calculated_hash = hashlib.sha256(data).hexdigest()
            
            # Compare with expected hash
            if expected_hash:
                return calculated_hash == expected_hash
            else:
                # Store calculated hash for future verification
                cache_key = f"dataset_hash_{dataset_id}"
                stored_hash = cache.get(cache_key)
                
                if stored_hash:
                    return calculated_hash == stored_hash
                else:
                    # First time - store the hash
                    cache.set(cache_key, calculated_hash, timeout=None)
                    return True
                    
        except Exception as e:
            logger.error(f"Error verifying integrity: {str(e)}")
            return False
    
    def get_dataset_info(self, dataset_id: int) -> Dict[str, Any]:
        """
        Get comprehensive dataset information.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dictionary with dataset information
        """
        try:
            ipfs_metadata = self._get_ipfs_metadata(dataset_id)
            encryption_metadata = self._get_encryption_metadata(dataset_id)
            
            return {
                'dataset_id': dataset_id,
                'ipfs_hash': ipfs_metadata.get('ipfs_hash') if ipfs_metadata else None,
                'size': ipfs_metadata.get('size') if ipfs_metadata else None,
                'encrypted': ipfs_metadata.get('encrypted', False) if ipfs_metadata else False,
                'uploaded_at': ipfs_metadata.get('uploaded_at') if ipfs_metadata else None,
                'has_encryption_metadata': encryption_metadata is not None,
                'gateway_url': f"{self.gateway_url}{ipfs_metadata.get('ipfs_hash')}" if ipfs_metadata else None,
                'provider': self.provider.value
            }
            
        except Exception as e:
            logger.error(f"Error getting dataset info: {str(e)}")
            return {'error': str(e)}


# Global IPFS service instance
ipfs_service = IPFSService()
