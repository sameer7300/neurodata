"""
Web3 utility functions and helpers.
"""
import json
import logging
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from web3 import Web3
from eth_utils import to_checksum_address, is_address

from .web3_service import web3_service
from .gas_manager import gas_manager, GasSpeed
from .wallet_verification import wallet_verification_service

logger = logging.getLogger(__name__)


class Web3Utils:
    """
    Collection of Web3 utility functions.
    """
    
    @staticmethod
    def format_address(address: str, length: int = 10) -> str:
        """
        Format an Ethereum address for display.
        
        Args:
            address: The address to format
            length: Number of characters to show from start and end
            
        Returns:
            Formatted address string
        """
        if not address or not is_address(address):
            return "Invalid Address"
        
        if len(address) <= length * 2:
            return address
        
        return f"{address[:length]}...{address[-length:]}"
    
    @staticmethod
    def wei_to_ether(wei_amount: Union[int, str]) -> Decimal:
        """
        Convert Wei to Ether.
        
        Args:
            wei_amount: Amount in Wei
            
        Returns:
            Amount in Ether as Decimal
        """
        try:
            return Decimal(str(wei_amount)) / Decimal('1000000000000000000')
        except (ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def ether_to_wei(ether_amount: Union[float, str, Decimal]) -> int:
        """
        Convert Ether to Wei.
        
        Args:
            ether_amount: Amount in Ether
            
        Returns:
            Amount in Wei as integer
        """
        try:
            return int(Decimal(str(ether_amount)) * Decimal('1000000000000000000'))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def gwei_to_wei(gwei_amount: Union[float, str, Decimal]) -> int:
        """
        Convert Gwei to Wei.
        
        Args:
            gwei_amount: Amount in Gwei
            
        Returns:
            Amount in Wei as integer
        """
        try:
            return int(Decimal(str(gwei_amount)) * Decimal('1000000000'))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def wei_to_gwei(wei_amount: Union[int, str]) -> Decimal:
        """
        Convert Wei to Gwei.
        
        Args:
            wei_amount: Amount in Wei
            
        Returns:
            Amount in Gwei as Decimal
        """
        try:
            return Decimal(str(wei_amount)) / Decimal('1000000000')
        except (ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def is_valid_transaction_hash(tx_hash: str) -> bool:
        """
        Validate transaction hash format.
        
        Args:
            tx_hash: Transaction hash to validate
            
        Returns:
            True if valid transaction hash format
        """
        if not tx_hash or not isinstance(tx_hash, str):
            return False
        
        # Remove 0x prefix if present
        if tx_hash.startswith('0x'):
            tx_hash = tx_hash[2:]
        
        # Check length and hex format
        return len(tx_hash) == 64 and all(c in '0123456789abcdefABCDEF' for c in tx_hash)
    
    @staticmethod
    def get_transaction_status(tx_hash: str) -> Dict[str, Any]:
        """
        Get comprehensive transaction status.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Dictionary with transaction status information
        """
        if not Web3Utils.is_valid_transaction_hash(tx_hash):
            return {'error': 'Invalid transaction hash'}
        
        try:
            # Get transaction details
            transaction = web3_service.get_transaction(tx_hash)
            if not transaction:
                return {'status': 'not_found', 'message': 'Transaction not found'}
            
            # Get transaction receipt
            receipt = web3_service.get_transaction_receipt(tx_hash)
            if not receipt:
                return {
                    'status': 'pending',
                    'message': 'Transaction is pending',
                    'transaction': transaction
                }
            
            # Determine status
            status = 'success' if receipt.get('status') == 1 else 'failed'
            
            # Get current block for confirmations
            current_block = web3_service.w3.eth.block_number
            confirmations = current_block - receipt['blockNumber']
            
            return {
                'status': status,
                'confirmations': confirmations,
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'gas_price': transaction.get('gasPrice', 0),
                'transaction_fee': receipt['gasUsed'] * transaction.get('gasPrice', 0),
                'transaction': transaction,
                'receipt': receipt
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction status: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def estimate_confirmation_time(gas_price_gwei: float) -> Dict[str, Any]:
        """
        Estimate transaction confirmation time based on gas price.
        
        Args:
            gas_price_gwei: Gas price in Gwei
            
        Returns:
            Dictionary with time estimates
        """
        try:
            # Get current gas prices
            current_prices = gas_manager.get_current_gas_prices()
            
            # Find closest speed category
            gas_price_wei = Web3Utils.gwei_to_wei(gas_price_gwei)
            
            closest_speed = GasSpeed.STANDARD
            min_diff = float('inf')
            
            for speed, price_info in current_prices.items():
                diff = abs(price_info.gas_price - gas_price_wei)
                if diff < min_diff:
                    min_diff = diff
                    closest_speed = speed
            
            speed_info = current_prices[closest_speed]
            
            return {
                'estimated_minutes': speed_info.estimated_time_minutes,
                'confidence_level': speed_info.confidence_level,
                'speed_category': closest_speed.value,
                'gas_price_gwei': gas_price_gwei,
                'gas_price_wei': gas_price_wei
            }
            
        except Exception as e:
            logger.error(f"Error estimating confirmation time: {str(e)}")
            return {
                'estimated_minutes': 2,
                'confidence_level': 0.5,
                'speed_category': 'standard',
                'error': str(e)
            }
    
    @staticmethod
    def get_network_status() -> Dict[str, Any]:
        """
        Get comprehensive network status information.
        
        Returns:
            Dictionary with network status
        """
        try:
            if not web3_service.is_connected():
                return {'connected': False, 'error': 'Not connected to network'}
            
            # Get basic network info
            network_info = web3_service.get_network_info()
            
            # Get gas prices
            gas_prices = gas_manager.get_current_gas_prices()
            
            # Get latest block
            latest_block = web3_service.get_block('latest')
            
            # Calculate network congestion
            congestion_level = Web3Utils._calculate_congestion_level(gas_prices)
            
            return {
                'connected': True,
                'chain_id': network_info.get('chain_id'),
                'block_number': network_info.get('block_number'),
                'gas_price': network_info.get('gas_price'),
                'latest_block': {
                    'number': latest_block.get('number'),
                    'timestamp': latest_block.get('timestamp'),
                    'gas_used': latest_block.get('gasUsed'),
                    'gas_limit': latest_block.get('gasLimit'),
                    'transaction_count': len(latest_block.get('transactions', []))
                } if latest_block else None,
                'gas_prices': {
                    speed.value: {
                        'gwei': Web3Utils.wei_to_gwei(price.gas_price),
                        'estimated_time_minutes': price.estimated_time_minutes,
                        'confidence_level': price.confidence_level
                    }
                    for speed, price in gas_prices.items()
                },
                'congestion_level': congestion_level,
                'network_name': Web3Utils._get_network_name(network_info.get('chain_id'))
            }
            
        except Exception as e:
            logger.error(f"Error getting network status: {str(e)}")
            return {'connected': False, 'error': str(e)}
    
    @staticmethod
    def _calculate_congestion_level(gas_prices: Dict) -> str:
        """
        Calculate network congestion level based on gas prices.
        
        Args:
            gas_prices: Dictionary of gas prices
            
        Returns:
            Congestion level string
        """
        try:
            standard_price_gwei = Web3Utils.wei_to_gwei(
                gas_prices[GasSpeed.STANDARD].gas_price
            )
            
            if standard_price_gwei < 10:
                return 'low'
            elif standard_price_gwei < 30:
                return 'medium'
            elif standard_price_gwei < 100:
                return 'high'
            else:
                return 'extreme'
                
        except Exception:
            return 'unknown'
    
    @staticmethod
    def _get_network_name(chain_id: int) -> str:
        """
        Get network name from chain ID.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            Network name
        """
        network_names = {
            1: 'Ethereum Mainnet',
            5: 'Goerli Testnet',
            11155111: 'Sepolia Testnet',
            137: 'Polygon Mainnet',
            80001: 'Mumbai Testnet',
            56: 'BSC Mainnet',
            97: 'BSC Testnet',
            42161: 'Arbitrum One',
            421613: 'Arbitrum Goerli',
            10: 'Optimism',
            420: 'Optimism Goerli'
        }
        
        return network_names.get(chain_id, f'Unknown Network (Chain ID: {chain_id})')
    
    @staticmethod
    def batch_get_balances(addresses: List[str], token_contract: str = None) -> Dict[str, str]:
        """
        Get balances for multiple addresses efficiently.
        
        Args:
            addresses: List of addresses
            token_contract: Optional token contract name
            
        Returns:
            Dictionary mapping addresses to balances
        """
        balances = {}
        
        for address in addresses:
            try:
                if Web3Utils.validate_address(address):
                    balance = web3_service.get_balance(address, token_contract)
                    balances[address] = str(balance)
                else:
                    balances[address] = '0'
            except Exception as e:
                logger.error(f"Error getting balance for {address}: {str(e)}")
                balances[address] = '0'
        
        return balances
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """
        Validate Ethereum address.
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid address
        """
        return web3_service.validate_address(address)
    
    @staticmethod
    def get_contract_info(contract_name: str) -> Dict[str, Any]:
        """
        Get contract information.
        
        Args:
            contract_name: Name of the contract
            
        Returns:
            Dictionary with contract information
        """
        try:
            contract_info = web3_service.contracts.get(contract_name)
            if not contract_info:
                return {'error': f'Contract {contract_name} not found'}
            
            contract = web3_service.get_contract(contract_name)
            if not contract:
                return {'error': f'Failed to load contract {contract_name}'}
            
            # Get contract code to verify deployment
            code = web3_service.w3.eth.get_code(contract_info.address)
            is_deployed = len(code) > 2  # More than just '0x'
            
            return {
                'name': contract_info.name,
                'address': contract_info.address,
                'is_deployed': is_deployed,
                'abi_functions': len([item for item in contract_info.abi if item.get('type') == 'function']),
                'abi_events': len([item for item in contract_info.abi if item.get('type') == 'event']),
                'network': Web3Utils._get_network_name(web3_service.w3.eth.chain_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting contract info: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def decode_transaction_input(tx_hash: str, contract_name: str = None) -> Dict[str, Any]:
        """
        Decode transaction input data.
        
        Args:
            tx_hash: Transaction hash
            contract_name: Optional contract name for ABI decoding
            
        Returns:
            Dictionary with decoded transaction data
        """
        try:
            transaction = web3_service.get_transaction(tx_hash)
            if not transaction:
                return {'error': 'Transaction not found'}
            
            input_data = transaction.get('input', '0x')
            if input_data == '0x':
                return {'type': 'simple_transfer', 'data': None}
            
            if not contract_name:
                return {
                    'type': 'contract_interaction',
                    'raw_input': input_data,
                    'method_id': input_data[:10] if len(input_data) >= 10 else None
                }
            
            # Try to decode with contract ABI
            contract = web3_service.get_contract(contract_name)
            if contract:
                try:
                    decoded = contract.decode_function_input(input_data)
                    function = decoded[0]
                    inputs = decoded[1]
                    
                    return {
                        'type': 'decoded_function_call',
                        'function_name': function.function_identifier,
                        'inputs': dict(inputs),
                        'raw_input': input_data
                    }
                except Exception as decode_error:
                    return {
                        'type': 'contract_interaction',
                        'raw_input': input_data,
                        'decode_error': str(decode_error)
                    }
            
            return {
                'type': 'contract_interaction',
                'raw_input': input_data,
                'error': f'Contract {contract_name} not found'
            }
            
        except Exception as e:
            logger.error(f"Error decoding transaction input: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def get_token_info(token_contract_name: str) -> Dict[str, Any]:
        """
        Get ERC-20 token information.
        
        Args:
            token_contract_name: Name of the token contract
            
        Returns:
            Dictionary with token information
        """
        try:
            # Get basic contract info
            contract_info = Web3Utils.get_contract_info(token_contract_name)
            if 'error' in contract_info:
                return contract_info
            
            # Get token-specific information
            name = web3_service.call_contract_function(token_contract_name, 'name')
            symbol = web3_service.call_contract_function(token_contract_name, 'symbol')
            decimals = web3_service.call_contract_function(token_contract_name, 'decimals')
            total_supply = web3_service.call_contract_function(token_contract_name, 'totalSupply')
            
            return {
                **contract_info,
                'token_name': name,
                'token_symbol': symbol,
                'decimals': decimals,
                'total_supply': str(total_supply) if total_supply else '0',
                'total_supply_formatted': str(Web3Utils.wei_to_ether(total_supply)) if total_supply else '0'
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def create_wallet_signature_message(wallet_address: str, action: str, 
                                      timestamp: int = None) -> str:
        """
        Create a standardized message for wallet signatures.
        
        Args:
            wallet_address: Wallet address
            action: Action being performed
            timestamp: Optional timestamp
            
        Returns:
            Message string for signing
        """
        if timestamp is None:
            timestamp = int(timezone.now().timestamp())
        
        domain = getattr(settings, 'FRONTEND_DOMAIN', 'neurodata.io')
        
        return (
            f"NeuroData Action Verification\n\n"
            f"Action: {action}\n"
            f"Wallet: {wallet_address}\n"
            f"Timestamp: {timestamp}\n"
            f"Domain: {domain}\n\n"
            f"This signature proves you own this wallet address."
        )


# Convenience functions for common operations
def format_nrc_amount(amount_wei: Union[int, str]) -> str:
    """Format NRC amount for display."""
    amount_nrc = Web3Utils.wei_to_ether(amount_wei)
    return f"{amount_nrc:.4f} NRC"


def format_eth_amount(amount_wei: Union[int, str]) -> str:
    """Format ETH amount for display."""
    amount_eth = Web3Utils.wei_to_ether(amount_wei)
    return f"{amount_eth:.6f} ETH"


def format_gas_price(gas_price_wei: Union[int, str]) -> str:
    """Format gas price for display."""
    gas_price_gwei = Web3Utils.wei_to_gwei(gas_price_wei)
    return f"{gas_price_gwei:.2f} gwei"


def get_transaction_url(tx_hash: str, chain_id: int = None) -> str:
    """Get block explorer URL for transaction."""
    if chain_id is None and web3_service.is_connected():
        chain_id = web3_service.w3.eth.chain_id
    
    explorers = {
        1: 'https://etherscan.io/tx/',
        5: 'https://goerli.etherscan.io/tx/',
        11155111: 'https://sepolia.etherscan.io/tx/',
        137: 'https://polygonscan.com/tx/',
        80001: 'https://mumbai.polygonscan.com/tx/',
        56: 'https://bscscan.com/tx/',
        97: 'https://testnet.bscscan.com/tx/',
        42161: 'https://arbiscan.io/tx/',
        10: 'https://optimistic.etherscan.io/tx/'
    }
    
    base_url = explorers.get(chain_id, 'https://etherscan.io/tx/')
    return f"{base_url}{tx_hash}"


def get_address_url(address: str, chain_id: int = None) -> str:
    """Get block explorer URL for address."""
    if chain_id is None and web3_service.is_connected():
        chain_id = web3_service.w3.eth.chain_id
    
    explorers = {
        1: 'https://etherscan.io/address/',
        5: 'https://goerli.etherscan.io/address/',
        11155111: 'https://sepolia.etherscan.io/address/',
        137: 'https://polygonscan.com/address/',
        80001: 'https://mumbai.polygonscan.com/address/',
        56: 'https://bscscan.com/address/',
        97: 'https://testnet.bscscan.com/address/',
        42161: 'https://arbiscan.io/address/',
        10: 'https://optimistic.etherscan.io/address/'
    }
    
    base_url = explorers.get(chain_id, 'https://etherscan.io/address/')
    return f"{base_url}{address}"
