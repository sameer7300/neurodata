"""
Gas estimation and management utilities for blockchain transactions.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from .web3_service import web3_service, GasEstimate

logger = logging.getLogger(__name__)


class GasSpeed(Enum):
    """Gas speed options."""
    SLOW = "slow"
    STANDARD = "standard"
    FAST = "fast"
    INSTANT = "instant"


@dataclass
class GasPrice:
    """Gas price information."""
    speed: GasSpeed
    gas_price: int  # in wei
    max_fee_per_gas: Optional[int] = None  # EIP-1559
    max_priority_fee_per_gas: Optional[int] = None  # EIP-1559
    estimated_time_minutes: int = 0
    confidence_level: float = 0.0  # 0-1


@dataclass
class TransactionCost:
    """Transaction cost breakdown."""
    gas_limit: int
    gas_price_info: GasPrice
    total_cost_wei: int
    total_cost_eth: float
    total_cost_usd: Optional[float] = None
    network_fee_wei: int = 0
    priority_fee_wei: int = 0


class GasManager:
    """
    Comprehensive gas estimation and management system.
    """
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'GAS_CACHE_TIMEOUT', 30)  # 30 seconds
        self.gas_limit_buffer = getattr(settings, 'GAS_LIMIT_BUFFER', 1.2)  # 20% buffer
        self.max_gas_price = getattr(settings, 'MAX_GAS_PRICE_GWEI', 100)  # 100 gwei max
        self.eth_price_cache_timeout = 300  # 5 minutes for ETH price
    
    def get_current_gas_prices(self) -> Dict[GasSpeed, GasPrice]:
        """
        Get current gas prices for different speed options.
        
        Returns:
            Dictionary mapping speed to gas price information
        """
        cache_key = "current_gas_prices"
        cached_prices = cache.get(cache_key)
        
        if cached_prices:
            return cached_prices
        
        try:
            if not web3_service.is_connected():
                return self._get_fallback_gas_prices()
            
            # Get current gas price
            current_gas_price = web3_service.w3.eth.gas_price
            
            # Try to get EIP-1559 fee data
            fee_data = self._get_eip1559_fees()
            
            if fee_data:
                # EIP-1559 network
                base_fee = fee_data['base_fee']
                priority_fees = fee_data['priority_fees']
                
                gas_prices = {
                    GasSpeed.SLOW: GasPrice(
                        speed=GasSpeed.SLOW,
                        gas_price=base_fee + priority_fees['slow'],
                        max_fee_per_gas=base_fee + priority_fees['slow'],
                        max_priority_fee_per_gas=priority_fees['slow'],
                        estimated_time_minutes=5,
                        confidence_level=0.7
                    ),
                    GasSpeed.STANDARD: GasPrice(
                        speed=GasSpeed.STANDARD,
                        gas_price=base_fee + priority_fees['standard'],
                        max_fee_per_gas=base_fee + priority_fees['standard'],
                        max_priority_fee_per_gas=priority_fees['standard'],
                        estimated_time_minutes=2,
                        confidence_level=0.85
                    ),
                    GasSpeed.FAST: GasPrice(
                        speed=GasSpeed.FAST,
                        gas_price=base_fee + priority_fees['fast'],
                        max_fee_per_gas=base_fee + priority_fees['fast'],
                        max_priority_fee_per_gas=priority_fees['fast'],
                        estimated_time_minutes=1,
                        confidence_level=0.95
                    ),
                    GasSpeed.INSTANT: GasPrice(
                        speed=GasSpeed.INSTANT,
                        gas_price=base_fee + priority_fees['instant'],
                        max_fee_per_gas=base_fee + priority_fees['instant'],
                        max_priority_fee_per_gas=priority_fees['instant'],
                        estimated_time_minutes=0.5,
                        confidence_level=0.99
                    )
                }
            else:
                # Legacy gas pricing
                gas_prices = {
                    GasSpeed.SLOW: GasPrice(
                        speed=GasSpeed.SLOW,
                        gas_price=int(current_gas_price * 0.8),
                        estimated_time_minutes=5,
                        confidence_level=0.7
                    ),
                    GasSpeed.STANDARD: GasPrice(
                        speed=GasSpeed.STANDARD,
                        gas_price=current_gas_price,
                        estimated_time_minutes=2,
                        confidence_level=0.85
                    ),
                    GasSpeed.FAST: GasPrice(
                        speed=GasSpeed.FAST,
                        gas_price=int(current_gas_price * 1.2),
                        estimated_time_minutes=1,
                        confidence_level=0.95
                    ),
                    GasSpeed.INSTANT: GasPrice(
                        speed=GasSpeed.INSTANT,
                        gas_price=int(current_gas_price * 1.5),
                        estimated_time_minutes=0.5,
                        confidence_level=0.99
                    )
                }
            
            # Apply maximum gas price limit
            max_gas_price_wei = self.max_gas_price * 10**9  # Convert gwei to wei
            for speed, price_info in gas_prices.items():
                if price_info.gas_price > max_gas_price_wei:
                    price_info.gas_price = max_gas_price_wei
                    price_info.confidence_level *= 0.8  # Reduce confidence
            
            # Cache the results
            cache.set(cache_key, gas_prices, timeout=self.cache_timeout)
            
            return gas_prices
            
        except Exception as e:
            logger.error(f"Error getting gas prices: {str(e)}")
            return self._get_fallback_gas_prices()
    
    def _get_eip1559_fees(self) -> Optional[Dict[str, Any]]:
        """
        Get EIP-1559 fee data if available.
        
        Returns:
            Dictionary with base fee and priority fees, or None if not available
        """
        try:
            # Get fee history for the last few blocks
            fee_history = web3_service.w3.eth.fee_history(
                block_count=10,
                newest_block='latest',
                reward_percentiles=[10, 25, 50, 75, 90]
            )
            
            if not fee_history or not fee_history.get('baseFeePerGas'):
                return None
            
            # Get the latest base fee
            base_fee = fee_history['baseFeePerGas'][-1]
            
            # Calculate priority fees from recent blocks
            rewards = fee_history.get('reward', [])
            if not rewards:
                return None
            
            # Average the priority fees across recent blocks
            avg_rewards = []
            for i in range(5):  # 5 percentiles
                percentile_rewards = [block_rewards[i] for block_rewards in rewards if len(block_rewards) > i]
                if percentile_rewards:
                    avg_rewards.append(sum(percentile_rewards) // len(percentile_rewards))
                else:
                    avg_rewards.append(0)
            
            return {
                'base_fee': base_fee,
                'priority_fees': {
                    'slow': avg_rewards[1],      # 25th percentile
                    'standard': avg_rewards[2],  # 50th percentile
                    'fast': avg_rewards[3],      # 75th percentile
                    'instant': avg_rewards[4]    # 90th percentile
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting EIP-1559 fees: {str(e)}")
            return None
    
    def _get_fallback_gas_prices(self) -> Dict[GasSpeed, GasPrice]:
        """
        Get fallback gas prices when Web3 is unavailable.
        
        Returns:
            Dictionary with fallback gas prices
        """
        # Fallback to reasonable default values (in wei)
        base_price = 20 * 10**9  # 20 gwei
        
        return {
            GasSpeed.SLOW: GasPrice(
                speed=GasSpeed.SLOW,
                gas_price=int(base_price * 0.8),
                estimated_time_minutes=5,
                confidence_level=0.5
            ),
            GasSpeed.STANDARD: GasPrice(
                speed=GasSpeed.STANDARD,
                gas_price=base_price,
                estimated_time_minutes=2,
                confidence_level=0.6
            ),
            GasSpeed.FAST: GasPrice(
                speed=GasSpeed.FAST,
                gas_price=int(base_price * 1.2),
                estimated_time_minutes=1,
                confidence_level=0.7
            ),
            GasSpeed.INSTANT: GasPrice(
                speed=GasSpeed.INSTANT,
                gas_price=int(base_price * 1.5),
                estimated_time_minutes=0.5,
                confidence_level=0.8
            )
        }
    
    def estimate_transaction_cost(self, transaction: Dict[str, Any], 
                                 speed: GasSpeed = GasSpeed.STANDARD) -> TransactionCost:
        """
        Estimate the cost of a transaction.
        
        Args:
            transaction: Transaction dictionary
            speed: Desired transaction speed
            
        Returns:
            TransactionCost object with detailed cost breakdown
        """
        try:
            # Get current gas prices
            gas_prices = self.get_current_gas_prices()
            gas_price_info = gas_prices.get(speed, gas_prices[GasSpeed.STANDARD])
            
            # Estimate gas limit
            gas_estimate = web3_service.estimate_gas(transaction)
            
            # Apply buffer to gas limit
            gas_limit = int(gas_estimate.gas_limit * self.gas_limit_buffer)
            
            # Calculate costs
            if gas_price_info.max_fee_per_gas:
                # EIP-1559 transaction
                max_fee = gas_price_info.max_fee_per_gas
                priority_fee = gas_price_info.max_priority_fee_per_gas or 0
                
                total_cost_wei = gas_limit * max_fee
                priority_fee_wei = gas_limit * priority_fee
                network_fee_wei = total_cost_wei - priority_fee_wei
            else:
                # Legacy transaction
                total_cost_wei = gas_limit * gas_price_info.gas_price
                priority_fee_wei = 0
                network_fee_wei = total_cost_wei
            
            total_cost_eth = total_cost_wei / 10**18
            
            # Get USD price if available
            total_cost_usd = self._convert_eth_to_usd(total_cost_eth)
            
            return TransactionCost(
                gas_limit=gas_limit,
                gas_price_info=gas_price_info,
                total_cost_wei=total_cost_wei,
                total_cost_eth=total_cost_eth,
                total_cost_usd=total_cost_usd,
                network_fee_wei=network_fee_wei,
                priority_fee_wei=priority_fee_wei
            )
            
        except Exception as e:
            logger.error(f"Error estimating transaction cost: {str(e)}")
            # Return fallback estimate
            fallback_gas_limit = 21000  # Standard transfer
            fallback_gas_price = 20 * 10**9  # 20 gwei
            fallback_cost_wei = fallback_gas_limit * fallback_gas_price
            
            return TransactionCost(
                gas_limit=fallback_gas_limit,
                gas_price_info=GasPrice(
                    speed=speed,
                    gas_price=fallback_gas_price,
                    estimated_time_minutes=2,
                    confidence_level=0.5
                ),
                total_cost_wei=fallback_cost_wei,
                total_cost_eth=fallback_cost_wei / 10**18
            )
    
    def estimate_contract_function_cost(self, contract_name: str, function_name: str,
                                      args: List = None, kwargs: Dict = None,
                                      from_address: str = None, value: int = 0,
                                      speed: GasSpeed = GasSpeed.STANDARD) -> TransactionCost:
        """
        Estimate cost for a specific contract function call.
        
        Args:
            contract_name: Name of the contract
            function_name: Name of the function to call
            args: Function arguments
            kwargs: Function keyword arguments
            from_address: Sender address
            value: ETH value to send
            speed: Desired transaction speed
            
        Returns:
            TransactionCost object
        """
        try:
            # Build transaction
            transaction = web3_service.build_transaction(
                contract_name=contract_name,
                function_name=function_name,
                args=args,
                kwargs=kwargs,
                from_address=from_address,
                value=value
            )
            
            if not transaction:
                raise ValueError("Failed to build transaction")
            
            return self.estimate_transaction_cost(transaction, speed)
            
        except Exception as e:
            logger.error(f"Error estimating contract function cost: {str(e)}")
            raise
    
    def get_optimal_gas_price(self, target_time_minutes: int = 2) -> GasPrice:
        """
        Get optimal gas price for a target confirmation time.
        
        Args:
            target_time_minutes: Target confirmation time in minutes
            
        Returns:
            GasPrice object with optimal settings
        """
        gas_prices = self.get_current_gas_prices()
        
        # Find the best match for target time
        best_match = None
        min_time_diff = float('inf')
        
        for speed, price_info in gas_prices.items():
            time_diff = abs(price_info.estimated_time_minutes - target_time_minutes)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_match = price_info
        
        return best_match or gas_prices[GasSpeed.STANDARD]
    
    def _convert_eth_to_usd(self, eth_amount: float) -> Optional[float]:
        """
        Convert ETH amount to USD.
        
        Args:
            eth_amount: Amount in ETH
            
        Returns:
            USD amount or None if conversion fails
        """
        try:
            cache_key = "eth_price_usd"
            eth_price = cache.get(cache_key)
            
            if eth_price is None:
                # In a real implementation, you would fetch from a price API
                # For now, we'll use a placeholder
                eth_price = 2000.0  # Placeholder price
                cache.set(cache_key, eth_price, timeout=self.eth_price_cache_timeout)
            
            return eth_amount * eth_price
            
        except Exception as e:
            logger.error(f"Error converting ETH to USD: {str(e)}")
            return None
    
    def get_gas_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get gas price history for analysis.
        
        Args:
            hours: Number of hours of history to retrieve
            
        Returns:
            List of gas price data points
        """
        try:
            if not web3_service.is_connected():
                return []
            
            current_block = web3_service.w3.eth.block_number
            blocks_per_hour = 240  # Approximate for 15-second blocks
            blocks_to_check = hours * blocks_per_hour
            
            history = []
            
            # Sample blocks at regular intervals
            sample_interval = max(1, blocks_to_check // 100)  # Max 100 samples
            
            for i in range(0, blocks_to_check, sample_interval):
                block_number = current_block - i
                if block_number < 0:
                    break
                
                try:
                    block = web3_service.get_block(block_number)
                    if block:
                        # Get average gas price from transactions in block
                        transactions = block.get('transactions', [])
                        if transactions:
                            gas_prices = []
                            for tx_hash in transactions[:10]:  # Sample first 10 transactions
                                try:
                                    tx = web3_service.get_transaction(tx_hash)
                                    if tx and tx.get('gasPrice'):
                                        gas_prices.append(tx['gasPrice'])
                                except:
                                    continue
                            
                            if gas_prices:
                                avg_gas_price = sum(gas_prices) // len(gas_prices)
                                history.append({
                                    'block_number': block_number,
                                    'timestamp': block['timestamp'],
                                    'gas_price_wei': avg_gas_price,
                                    'gas_price_gwei': avg_gas_price / 10**9
                                })
                except:
                    continue
            
            return sorted(history, key=lambda x: x['timestamp'])
            
        except Exception as e:
            logger.error(f"Error getting gas history: {str(e)}")
            return []
    
    def predict_gas_price(self, target_time_minutes: int = 2) -> Dict[str, Any]:
        """
        Predict optimal gas price based on network conditions.
        
        Args:
            target_time_minutes: Target confirmation time
            
        Returns:
            Dictionary with prediction data
        """
        try:
            # Get current gas prices
            current_prices = self.get_current_gas_prices()
            
            # Get gas history for trend analysis
            history = self.get_gas_history(hours=6)
            
            # Simple trend analysis
            if len(history) >= 2:
                recent_prices = [h['gas_price_gwei'] for h in history[-10:]]
                avg_recent = sum(recent_prices) / len(recent_prices)
                
                older_prices = [h['gas_price_gwei'] for h in history[-20:-10]]
                avg_older = sum(older_prices) / len(older_prices) if older_prices else avg_recent
                
                trend = "increasing" if avg_recent > avg_older * 1.1 else \
                       "decreasing" if avg_recent < avg_older * 0.9 else "stable"
            else:
                trend = "unknown"
            
            # Get optimal price for target time
            optimal_price = self.get_optimal_gas_price(target_time_minutes)
            
            return {
                'optimal_gas_price': {
                    'wei': optimal_price.gas_price,
                    'gwei': optimal_price.gas_price / 10**9,
                    'speed': optimal_price.speed.value,
                    'estimated_time_minutes': optimal_price.estimated_time_minutes,
                    'confidence_level': optimal_price.confidence_level
                },
                'network_trend': trend,
                'current_prices': {
                    speed.value: {
                        'wei': price.gas_price,
                        'gwei': price.gas_price / 10**9,
                        'estimated_time_minutes': price.estimated_time_minutes
                    }
                    for speed, price in current_prices.items()
                },
                'recommendation': self._get_gas_recommendation(current_prices, trend)
            }
            
        except Exception as e:
            logger.error(f"Error predicting gas price: {str(e)}")
            return {'error': str(e)}
    
    def _get_gas_recommendation(self, current_prices: Dict[GasSpeed, GasPrice], 
                               trend: str) -> str:
        """
        Get gas price recommendation based on current conditions.
        
        Args:
            current_prices: Current gas prices
            trend: Network trend
            
        Returns:
            Recommendation string
        """
        standard_price = current_prices[GasSpeed.STANDARD]
        
        if trend == "increasing":
            if standard_price.gas_price > 50 * 10**9:  # > 50 gwei
                return "Gas prices are high and increasing. Consider waiting or using slow speed."
            else:
                return "Gas prices are increasing. Consider using fast speed for important transactions."
        elif trend == "decreasing":
            return "Gas prices are decreasing. Good time for transactions."
        else:
            if standard_price.gas_price > 100 * 10**9:  # > 100 gwei
                return "Gas prices are very high. Consider waiting for better conditions."
            elif standard_price.gas_price < 10 * 10**9:  # < 10 gwei
                return "Gas prices are very low. Excellent time for transactions."
            else:
                return "Gas prices are moderate. Standard speed recommended."


# Global gas manager instance
gas_manager = GasManager()
