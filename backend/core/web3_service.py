"""
Web3 service for blockchain integration.
"""
import json
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address, is_address
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Handle different web3.py versions for PoA middleware
geth_poa_middleware = None
try:
    # Try the old import path first
    from web3.middleware import geth_poa_middleware
except ImportError:
    try:
        # Try the new import path
        from web3.middleware.geth_poa import geth_poa_middleware
    except ImportError:
        try:
            # Try alternative import
            from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
        except ImportError:
            # If all imports fail, we'll work without PoA middleware
            logger.warning("Could not import PoA middleware - PoA networks may not work correctly")
            geth_poa_middleware = None


@dataclass
class ContractInfo:
    """Contract information structure."""
    address: str
    abi: List[Dict]
    name: str


@dataclass
class TransactionResult:
    """Transaction result structure."""
    success: bool
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    error: Optional[str] = None
    receipt: Optional[Dict] = None


@dataclass
class GasEstimate:
    """Gas estimation structure."""
    gas_limit: int
    gas_price: int
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    estimated_cost_wei: int = 0
    estimated_cost_eth: float = 0.0


class Web3Service:
    """
    Comprehensive Web3 service for blockchain interactions.
    """
    
    def __init__(self):
        self.w3 = None
        self.contracts = {}
        self.network_config = {}
        
        # Only initialize if not in management command (except runserver)
        import sys
        if 'manage.py' not in sys.argv[0] or 'runserver' in sys.argv:
            self._initialize_web3()
            self._load_contracts()
    
    def _initialize_web3(self):
        """Initialize Web3 connection."""
        try:
            # Get network configuration
            self.network_config = getattr(settings, 'WEB3_CONFIG', {})
            provider_url = self.network_config.get('PROVIDER_URL')
            
            if not provider_url:
                logger.error("Web3 provider URL not configured")
                return
            
            # Initialize Web3
            if provider_url.startswith('ws'):
                from web3 import WebsocketProvider
                provider = WebsocketProvider(provider_url)
            else:
                from web3 import HTTPProvider
                provider = HTTPProvider(provider_url)
            
            self.w3 = Web3(provider)
            
            # Add PoA middleware if needed (for networks like BSC, Polygon)
            if self.network_config.get('IS_POA', False) and geth_poa_middleware is not None:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Verify connection
            if self.w3.is_connected():
                chain_id = self.w3.eth.chain_id
                logger.info(f"Connected to blockchain network (Chain ID: {chain_id})")
            else:
                logger.error("Failed to connect to blockchain network")
                
        except Exception as e:
            logger.error(f"Error initializing Web3: {str(e)}")
    
    def _load_contracts(self):
        """Load smart contract ABIs and addresses."""
        try:
            contracts_config = getattr(settings, 'SMART_CONTRACTS', {})
            
            for contract_name, config in contracts_config.items():
                address = config.get('address')
                abi_path = config.get('abi_path')
                
                if not address or not abi_path:
                    logger.warning(f"Incomplete config for contract {contract_name}")
                    continue
                
                # Load ABI
                try:
                    with open(abi_path, 'r') as f:
                        abi = json.load(f)
                    
                    self.contracts[contract_name] = ContractInfo(
                        address=to_checksum_address(address),
                        abi=abi,
                        name=contract_name
                    )
                    
                    logger.info(f"Loaded contract {contract_name} at {address}")
                    
                except FileNotFoundError:
                    logger.error(f"ABI file not found for {contract_name}: {abi_path}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid ABI JSON for {contract_name}")
                    
        except Exception as e:
            logger.error(f"Error loading contracts: {str(e)}")
    
    def get_contract(self, contract_name: str):
        """Get contract instance."""
        if not self.w3 or contract_name not in self.contracts:
            return None
        
        contract_info = self.contracts[contract_name]
        return self.w3.eth.contract(
            address=contract_info.address,
            abi=contract_info.abi
        )
    
    def is_connected(self) -> bool:
        """Check if Web3 is connected."""
        return self.w3 is not None and self.w3.is_connected()
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get current network information."""
        if not self.is_connected():
            return {}
        
        try:
            return {
                'chain_id': self.w3.eth.chain_id,
                'block_number': self.w3.eth.block_number,
                'gas_price': self.w3.eth.gas_price,
                'is_connected': True
            }
        except Exception as e:
            logger.error(f"Error getting network info: {str(e)}")
            return {'is_connected': False, 'error': str(e)}
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address."""
        return is_address(address)
    
    def get_balance(self, address: str, token_contract: str = None) -> Decimal:
        """Get ETH or token balance for an address."""
        if not self.is_connected() or not self.validate_address(address):
            return Decimal('0')
        
        try:
            address = to_checksum_address(address)
            
            if token_contract:
                # Get token balance
                contract = self.get_contract(token_contract)
                if contract:
                    balance_wei = contract.functions.balanceOf(address).call()
                    decimals = contract.functions.decimals().call()
                    return Decimal(balance_wei) / Decimal(10 ** decimals)
            else:
                # Get ETH balance
                balance_wei = self.w3.eth.get_balance(address)
                return Decimal(balance_wei) / Decimal(10 ** 18)
                
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {str(e)}")
            
        return Decimal('0')
    
    def estimate_gas(self, transaction: Dict[str, Any]) -> GasEstimate:
        """Estimate gas for a transaction."""
        if not self.is_connected():
            return GasEstimate(gas_limit=0, gas_price=0)
        
        try:
            # Estimate gas limit
            gas_limit = self.w3.eth.estimate_gas(transaction)
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # For EIP-1559 networks, get fee data
            max_fee_per_gas = None
            max_priority_fee_per_gas = None
            
            try:
                fee_history = self.w3.eth.fee_history(1, 'latest', [25, 50, 75])
                if fee_history:
                    base_fee = fee_history['baseFeePerGas'][-1]
                    priority_fees = fee_history['reward'][0]
                    
                    max_priority_fee_per_gas = priority_fees[1]  # 50th percentile
                    max_fee_per_gas = base_fee + max_priority_fee_per_gas
            except:
                pass  # Fallback to legacy gas pricing
            
            # Calculate estimated cost
            effective_gas_price = max_fee_per_gas or gas_price
            estimated_cost_wei = gas_limit * effective_gas_price
            estimated_cost_eth = estimated_cost_wei / 10**18
            
            return GasEstimate(
                gas_limit=gas_limit,
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                estimated_cost_wei=estimated_cost_wei,
                estimated_cost_eth=estimated_cost_eth
            )
            
        except Exception as e:
            logger.error(f"Error estimating gas: {str(e)}")
            return GasEstimate(gas_limit=0, gas_price=0, error=str(e))
    
    def send_transaction(self, transaction: Dict[str, Any], private_key: str = None) -> TransactionResult:
        """Send a transaction to the blockchain."""
        if not self.is_connected():
            return TransactionResult(success=False, error="Not connected to blockchain")
        
        try:
            # Use configured private key if not provided
            if not private_key:
                private_key = self.network_config.get('PRIVATE_KEY')
            
            if not private_key:
                return TransactionResult(success=False, error="No private key provided")
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            return TransactionResult(
                success=receipt.status == 1,
                tx_hash=tx_hash.hex(),
                block_number=receipt.blockNumber,
                gas_used=receipt.gasUsed,
                receipt=dict(receipt)
            )
            
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return TransactionResult(success=False, error=str(e))
    
    def call_contract_function(self, contract_name: str, function_name: str, 
                             args: List = None, kwargs: Dict = None) -> Any:
        """Call a read-only contract function."""
        if not self.is_connected():
            return None
        
        try:
            contract = self.get_contract(contract_name)
            if not contract:
                logger.error(f"Contract {contract_name} not found")
                return None
            
            function = getattr(contract.functions, function_name)
            if not function:
                logger.error(f"Function {function_name} not found in {contract_name}")
                return None
            
            # Call function
            if args and kwargs:
                result = function(*args, **kwargs).call()
            elif args:
                result = function(*args).call()
            elif kwargs:
                result = function(**kwargs).call()
            else:
                result = function().call()
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling contract function {function_name}: {str(e)}")
            return None
    
    def build_transaction(self, contract_name: str, function_name: str, 
                         args: List = None, kwargs: Dict = None,
                         from_address: str = None, value: int = 0) -> Dict[str, Any]:
        """Build a transaction for a contract function."""
        if not self.is_connected():
            return {}
        
        try:
            contract = self.get_contract(contract_name)
            if not contract:
                return {}
            
            function = getattr(contract.functions, function_name)
            if not function:
                return {}
            
            # Build transaction
            if args and kwargs:
                transaction = function(*args, **kwargs).build_transaction({
                    'from': from_address or self.network_config.get('DEFAULT_ACCOUNT'),
                    'value': value,
                    'gas': 0,  # Will be estimated
                    'gasPrice': 0,  # Will be set based on network
                    'nonce': 0  # Will be set
                })
            elif args:
                transaction = function(*args).build_transaction({
                    'from': from_address or self.network_config.get('DEFAULT_ACCOUNT'),
                    'value': value,
                    'gas': 0,
                    'gasPrice': 0,
                    'nonce': 0
                })
            elif kwargs:
                transaction = function(**kwargs).build_transaction({
                    'from': from_address or self.network_config.get('DEFAULT_ACCOUNT'),
                    'value': value,
                    'gas': 0,
                    'gasPrice': 0,
                    'nonce': 0
                })
            else:
                transaction = function().build_transaction({
                    'from': from_address or self.network_config.get('DEFAULT_ACCOUNT'),
                    'value': value,
                    'gas': 0,
                    'gasPrice': 0,
                    'nonce': 0
                })
            
            # Set nonce
            if transaction.get('from'):
                transaction['nonce'] = self.w3.eth.get_transaction_count(
                    to_checksum_address(transaction['from'])
                )
            
            # Estimate gas
            gas_estimate = self.estimate_gas(transaction)
            transaction['gas'] = gas_estimate.gas_limit
            
            # Set gas price
            if gas_estimate.max_fee_per_gas:
                transaction['maxFeePerGas'] = gas_estimate.max_fee_per_gas
                transaction['maxPriorityFeePerGas'] = gas_estimate.max_priority_fee_per_gas
                transaction.pop('gasPrice', None)  # Remove gasPrice for EIP-1559
            else:
                transaction['gasPrice'] = gas_estimate.gas_price
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error building transaction: {str(e)}")
            return {}
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction receipt."""
        if not self.is_connected():
            return None
        
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
        except Exception as e:
            logger.error(f"Error getting transaction receipt: {str(e)}")
            return None
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction details."""
        if not self.is_connected():
            return None
        
        try:
            transaction = self.w3.eth.get_transaction(tx_hash)
            return dict(transaction)
        except Exception as e:
            logger.error(f"Error getting transaction: {str(e)}")
            return None
    
    def verify_signature(self, message: str, signature: str, address: str) -> bool:
        """Verify a message signature."""
        try:
            # Recover address from signature
            message_hash = self.w3.keccak(text=message)
            recovered_address = self.w3.eth.account.recover_message(
                message_hash, signature=signature
            )
            
            return recovered_address.lower() == address.lower()
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False
    
    def create_message_hash(self, message: str) -> str:
        """Create a hash for message signing."""
        try:
            # Create EIP-191 compliant message hash
            prefixed_message = f"\x19Ethereum Signed Message:\n{len(message)}{message}"
            return self.w3.keccak(text=prefixed_message).hex()
        except Exception as e:
            logger.error(f"Error creating message hash: {str(e)}")
            return ""
    
    def get_block(self, block_identifier: str = 'latest') -> Optional[Dict]:
        """Get block information."""
        if not self.is_connected():
            return None
        
        try:
            block = self.w3.eth.get_block(block_identifier)
            return dict(block)
        except Exception as e:
            logger.error(f"Error getting block: {str(e)}")
            return None
    
    def get_logs(self, contract_name: str, event_name: str, 
                from_block: int = None, to_block: int = None,
                argument_filters: Dict = None) -> List[Dict]:
        """Get contract event logs."""
        if not self.is_connected():
            return []
        
        try:
            contract = self.get_contract(contract_name)
            if not contract:
                return []
            
            event = getattr(contract.events, event_name)
            if not event:
                return []
            
            # Set default block range
            if from_block is None:
                from_block = max(0, self.w3.eth.block_number - 1000)  # Last 1000 blocks
            if to_block is None:
                to_block = 'latest'
            
            # Get logs
            logs = event.create_filter(
                fromBlock=from_block,
                toBlock=to_block,
                argument_filters=argument_filters or {}
            ).get_all_entries()
            
            return [dict(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            return []
    
    def monitor_events(self, contract_name: str, event_name: str, 
                      callback: callable, poll_interval: int = 2):
        """Monitor contract events in real-time."""
        if not self.is_connected():
            return
        
        try:
            contract = self.get_contract(contract_name)
            if not contract:
                return
            
            event = getattr(contract.events, event_name)
            if not event:
                return
            
            # Create event filter
            event_filter = event.create_filter(fromBlock='latest')
            
            logger.info(f"Started monitoring {event_name} events for {contract_name}")
            
            while True:
                try:
                    # Get new events
                    new_events = event_filter.get_new_entries()
                    
                    for event_data in new_events:
                        try:
                            callback(dict(event_data))
                        except Exception as e:
                            logger.error(f"Error in event callback: {str(e)}")
                    
                    # Wait before next poll
                    import time
                    time.sleep(poll_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Event monitoring stopped")
                    break
                except Exception as e:
                    logger.error(f"Error monitoring events: {str(e)}")
                    import time
                    time.sleep(poll_interval)
                    
        except Exception as e:
            logger.error(f"Error setting up event monitoring: {str(e)}")


# Global Web3 service instance
web3_service = Web3Service()
