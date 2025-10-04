"""
IPFS provider implementations for different services.
"""
import json
import logging
import requests
import tempfile
from typing import Dict, Any, Tuple
from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from .ipfs_service import IPFSUploadResult

logger = logging.getLogger(__name__)


class PinataProvider:
    """Pinata IPFS provider implementation."""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.pinata.cloud"
        self.gateway_url = "https://gateway.pinata.cloud/ipfs/"
    
    def upload(self, data: bytes, filename: str, metadata: Dict = None) -> IPFSUploadResult:
        """Upload file to Pinata."""
        try:
            url = f"{self.base_url}/pinning/pinFileToIPFS"
            
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            files = {
                'file': (filename, data, 'application/octet-stream')
            }
            
            pinata_metadata = {
                'name': filename,
                'keyvalues': {
                    'uploaded_at': timezone.now().isoformat(),
                    'service': 'neurodata',
                    **(metadata or {})
                }
            }
            
            data_payload = {
                'pinataMetadata': json.dumps(pinata_metadata),
                'pinataOptions': json.dumps({
                    'cidVersion': 1,
                    'wrapWithDirectory': False
                })
            }
            
            response = requests.post(
                url, 
                files=files, 
                data=data_payload, 
                headers=headers,
                timeout=300  # 5 minutes timeout
            )
            
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
                logger.error(f"Pinata upload failed: {response.status_code} - {response.text}")
                return IPFSUploadResult(
                    success=False,
                    error=f"Upload failed: {response.text}"
                )
                
        except requests.exceptions.Timeout:
            return IPFSUploadResult(
                success=False,
                error="Upload timeout - file may be too large"
            )
        except Exception as e:
            logger.error(f"Pinata upload error: {str(e)}")
            return IPFSUploadResult(
                success=False,
                error=str(e)
            )
    
    def download(self, ipfs_hash: str) -> Tuple[bool, bytes, str]:
        """Download file from Pinata gateway."""
        try:
            url = f"{self.gateway_url}{ipfs_hash}"
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                return True, response.content, ""
            else:
                return False, b"", f"Download failed: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Pinata download error: {str(e)}")
            return False, b"", str(e)
    
    def pin_status(self, ipfs_hash: str) -> Dict[str, Any]:
        """Get pin status from Pinata."""
        try:
            url = f"{self.base_url}/data/pinList"
            
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            params = {
                'hashContains': ipfs_hash,
                'status': 'pinned'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'pinned': len(result.get('rows', [])) > 0,
                    'data': result
                }
            else:
                return {'pinned': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Pinata pin status error: {str(e)}")
            return {'pinned': False, 'error': str(e)}
    
    def unpin(self, ipfs_hash: str) -> bool:
        """Unpin file from Pinata."""
        try:
            url = f"{self.base_url}/pinning/unpin/{ipfs_hash}"
            
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            response = requests.delete(url, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Pinata unpin error: {str(e)}")
            return False


class Web3StorageProvider:
    """Web3.Storage IPFS provider implementation."""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.web3.storage"
        self.gateway_url = "https://w3s.link/ipfs/"
    
    def upload(self, data: bytes, filename: str, metadata: Dict = None) -> IPFSUploadResult:
        """Upload file to Web3.Storage."""
        try:
            url = f"{self.base_url}/upload"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'X-NAME': filename
            }
            
            files = {
                'file': (filename, data, 'application/octet-stream')
            }
            
            response = requests.post(
                url, 
                files=files, 
                headers=headers,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result['cid']
                
                return IPFSUploadResult(
                    success=True,
                    ipfs_hash=ipfs_hash,
                    ipfs_url=f"{self.gateway_url}{ipfs_hash}",
                    size=len(data),
                    metadata=result
                )
            else:
                logger.error(f"Web3.Storage upload failed: {response.status_code} - {response.text}")
                return IPFSUploadResult(
                    success=False,
                    error=f"Upload failed: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Web3.Storage upload error: {str(e)}")
            return IPFSUploadResult(
                success=False,
                error=str(e)
            )
    
    def download(self, ipfs_hash: str) -> Tuple[bool, bytes, str]:
        """Download file from Web3.Storage gateway."""
        try:
            url = f"{self.gateway_url}{ipfs_hash}"
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                return True, response.content, ""
            else:
                return False, b"", f"Download failed: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Web3.Storage download error: {str(e)}")
            return False, b"", str(e)
    
    def get_status(self, ipfs_hash: str) -> Dict[str, Any]:
        """Get upload status from Web3.Storage."""
        try:
            url = f"{self.base_url}/status/{ipfs_hash}"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': response.text}
                
        except Exception as e:
            logger.error(f"Web3.Storage status error: {str(e)}")
            return {'error': str(e)}


class InfuraProvider:
    """Infura IPFS provider implementation."""
    
    def __init__(self, project_id: str, project_secret: str):
        self.project_id = project_id
        self.project_secret = project_secret
        self.base_url = "https://ipfs.infura.io:5001/api/v0"
        self.gateway_url = "https://ipfs.infura.io/ipfs/"
        
        # Setup authentication
        import base64
        credentials = base64.b64encode(f"{project_id}:{project_secret}".encode()).decode()
        self.auth_header = f"Basic {credentials}"
    
    def upload(self, data: bytes, filename: str, metadata: Dict = None) -> IPFSUploadResult:
        """Upload file to Infura IPFS."""
        try:
            url = f"{self.base_url}/add"
            
            headers = {
                'Authorization': self.auth_header
            }
            
            files = {
                'file': (filename, data, 'application/octet-stream')
            }
            
            params = {
                'pin': 'true',
                'cid-version': 1
            }
            
            response = requests.post(
                url, 
                files=files, 
                headers=headers,
                params=params,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result['Hash']
                
                return IPFSUploadResult(
                    success=True,
                    ipfs_hash=ipfs_hash,
                    ipfs_url=f"{self.gateway_url}{ipfs_hash}",
                    size=int(result.get('Size', len(data))),
                    metadata=result
                )
            else:
                logger.error(f"Infura upload failed: {response.status_code} - {response.text}")
                return IPFSUploadResult(
                    success=False,
                    error=f"Upload failed: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Infura upload error: {str(e)}")
            return IPFSUploadResult(
                success=False,
                error=str(e)
            )
    
    def download(self, ipfs_hash: str) -> Tuple[bool, bytes, str]:
        """Download file from Infura gateway."""
        try:
            url = f"{self.gateway_url}{ipfs_hash}"
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                return True, response.content, ""
            else:
                return False, b"", f"Download failed: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Infura download error: {str(e)}")
            return False, b"", str(e)
    
    def pin_status(self, ipfs_hash: str) -> Dict[str, Any]:
        """Get pin status from Infura."""
        try:
            url = f"{self.base_url}/pin/ls"
            
            headers = {
                'Authorization': self.auth_header
            }
            
            params = {
                'arg': ipfs_hash
            }
            
            response = requests.post(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'pinned': ipfs_hash in result.get('Keys', {}),
                    'data': result
                }
            else:
                return {'pinned': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Infura pin status error: {str(e)}")
            return {'pinned': False, 'error': str(e)}


class LocalIPFSProvider:
    """Local IPFS node provider implementation."""
    
    def __init__(self, node_url: str = "http://localhost:5001/api/v0", 
                 gateway_url: str = "http://localhost:8080/ipfs/"):
        self.base_url = node_url
        self.gateway_url = gateway_url
    
    def upload(self, data: bytes, filename: str, metadata: Dict = None) -> IPFSUploadResult:
        """Upload file to local IPFS node."""
        try:
            url = f"{self.base_url}/add"
            
            files = {
                'file': (filename, data, 'application/octet-stream')
            }
            
            params = {
                'pin': 'true',
                'cid-version': 1
            }
            
            response = requests.post(
                url, 
                files=files, 
                params=params,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result['Hash']
                
                return IPFSUploadResult(
                    success=True,
                    ipfs_hash=ipfs_hash,
                    ipfs_url=f"{self.gateway_url}{ipfs_hash}",
                    size=int(result.get('Size', len(data))),
                    metadata=result
                )
            else:
                logger.error(f"Local IPFS upload failed: {response.status_code} - {response.text}")
                return IPFSUploadResult(
                    success=False,
                    error=f"Upload failed: {response.text}"
                )
                
        except requests.exceptions.ConnectionError:
            return IPFSUploadResult(
                success=False,
                error="Cannot connect to local IPFS node. Make sure IPFS daemon is running."
            )
        except Exception as e:
            logger.error(f"Local IPFS upload error: {str(e)}")
            return IPFSUploadResult(
                success=False,
                error=str(e)
            )
    
    def download(self, ipfs_hash: str) -> Tuple[bool, bytes, str]:
        """Download file from local IPFS gateway."""
        try:
            url = f"{self.gateway_url}{ipfs_hash}"
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                return True, response.content, ""
            else:
                return False, b"", f"Download failed: HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, b"", "Cannot connect to local IPFS gateway"
        except Exception as e:
            logger.error(f"Local IPFS download error: {str(e)}")
            return False, b"", str(e)
    
    def node_info(self) -> Dict[str, Any]:
        """Get local IPFS node information."""
        try:
            url = f"{self.base_url}/id"
            response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': response.text}
                
        except Exception as e:
            logger.error(f"Local IPFS node info error: {str(e)}")
            return {'error': str(e)}


def get_provider_instance(provider_type: str, config: Dict[str, Any]):
    """
    Factory function to get provider instance.
    
    Args:
        provider_type: Type of provider ('pinata', 'web3_storage', 'infura', 'local')
        config: Provider configuration
        
    Returns:
        Provider instance
    """
    if provider_type == 'pinata':
        return PinataProvider(
            api_key=config.get('PINATA_API_KEY'),
            api_secret=config.get('PINATA_API_SECRET')
        )
    elif provider_type == 'web3_storage':
        return Web3StorageProvider(
            api_token=config.get('WEB3_STORAGE_TOKEN')
        )
    elif provider_type == 'infura':
        return InfuraProvider(
            project_id=config.get('INFURA_PROJECT_ID'),
            project_secret=config.get('INFURA_PROJECT_SECRET')
        )
    elif provider_type == 'local':
        return LocalIPFSProvider(
            node_url=config.get('LOCAL_NODE_URL', 'http://localhost:5001/api/v0'),
            gateway_url=config.get('LOCAL_GATEWAY_URL', 'http://localhost:8080/ipfs/')
        )
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")


def test_provider_connection(provider_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test connection to IPFS provider.
    
    Args:
        provider_type: Type of provider
        config: Provider configuration
        
    Returns:
        Test result dictionary
    """
    try:
        provider = get_provider_instance(provider_type, config)
        
        # Test with a small file
        test_data = b"NeuroData IPFS connection test"
        test_filename = "test.txt"
        
        # Upload test
        upload_result = provider.upload(test_data, test_filename)
        
        if not upload_result.success:
            return {
                'success': False,
                'error': f"Upload test failed: {upload_result.error}"
            }
        
        # Download test
        download_success, downloaded_data, download_error = provider.download(upload_result.ipfs_hash)
        
        if not download_success:
            return {
                'success': False,
                'error': f"Download test failed: {download_error}"
            }
        
        # Verify data integrity
        if downloaded_data != test_data:
            return {
                'success': False,
                'error': "Data integrity check failed"
            }
        
        return {
            'success': True,
            'message': f"{provider_type.title()} connection test successful",
            'test_hash': upload_result.ipfs_hash,
            'upload_size': upload_result.size
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Connection test failed: {str(e)}"
        }
