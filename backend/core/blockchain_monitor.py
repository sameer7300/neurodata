"""
Blockchain transaction monitoring and event handling system.
"""
import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .web3_service import web3_service
from apps.authentication.models import UserActivity

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Blockchain event types."""
    DATASET_LISTED = "DatasetListed"
    DATASET_PURCHASED = "DatasetPurchased"
    DATASET_UPDATED = "DatasetUpdated"
    PURCHASE_COMPLETED = "PurchaseCompleted"
    ESCROW_RELEASED = "EscrowReleased"
    DISPUTE_CREATED = "DisputeCreated"
    DISPUTE_RESOLVED = "DisputeResolved"
    REVIEW_SUBMITTED = "ReviewSubmitted"
    TOKENS_STAKED = "TokensStaked"
    TOKENS_UNSTAKED = "TokensUnstaked"
    REWARDS_CLAIMED = "RewardsClaimed"
    TRANSFER = "Transfer"


@dataclass
class BlockchainEvent:
    """Blockchain event data structure."""
    event_type: EventType
    contract_name: str
    transaction_hash: str
    block_number: int
    block_timestamp: datetime
    event_data: Dict[str, Any]
    processed: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = timezone.now()


class BlockchainMonitor:
    """
    Comprehensive blockchain monitoring system.
    """
    
    def __init__(self):
        self.is_running = False
        self.monitor_threads = {}
        self.event_handlers = {}
        self.last_processed_blocks = {}
        self.polling_interval = getattr(settings, 'BLOCKCHAIN_POLLING_INTERVAL', 5)
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for different contract events."""
        # NeuroCoin events
        self.register_handler(EventType.TRANSFER, self._handle_token_transfer)
        self.register_handler(EventType.TOKENS_STAKED, self._handle_tokens_staked)
        self.register_handler(EventType.TOKENS_UNSTAKED, self._handle_tokens_unstaked)
        self.register_handler(EventType.REWARDS_CLAIMED, self._handle_rewards_claimed)
        
        # Marketplace events
        self.register_handler(EventType.DATASET_LISTED, self._handle_dataset_listed)
        self.register_handler(EventType.DATASET_PURCHASED, self._handle_dataset_purchased)
        self.register_handler(EventType.DATASET_UPDATED, self._handle_dataset_updated)
        self.register_handler(EventType.PURCHASE_COMPLETED, self._handle_purchase_completed)
        self.register_handler(EventType.REVIEW_SUBMITTED, self._handle_review_submitted)
        
        # Escrow events
        self.register_handler(EventType.ESCROW_RELEASED, self._handle_escrow_released)
        self.register_handler(EventType.DISPUTE_CREATED, self._handle_dispute_created)
        self.register_handler(EventType.DISPUTE_RESOLVED, self._handle_dispute_resolved)
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def start_monitoring(self):
        """Start monitoring blockchain events."""
        if self.is_running:
            logger.warning("Blockchain monitoring is already running")
            return
        
        if not web3_service.is_connected():
            logger.error("Web3 service is not connected")
            return
        
        self.is_running = True
        logger.info("Starting blockchain monitoring...")
        
        # Start monitoring threads for each contract
        contracts_to_monitor = [
            ('NeuroCoin', ['Transfer', 'TokensStaked', 'TokensUnstaked', 'RewardsClaimed']),
            ('DatasetMarketplace', [
                'DatasetListed', 'DatasetPurchased', 'DatasetUpdated', 
                'PurchaseCompleted', 'ReviewSubmitted'
            ]),
            ('EscrowManager', ['EscrowReleased', 'DisputeCreated', 'DisputeResolved'])
        ]
        
        for contract_name, events in contracts_to_monitor:
            thread = threading.Thread(
                target=self._monitor_contract_events,
                args=(contract_name, events),
                daemon=True
            )
            thread.start()
            self.monitor_threads[contract_name] = thread
            logger.info(f"Started monitoring {contract_name} events")
    
    def stop_monitoring(self):
        """Stop monitoring blockchain events."""
        self.is_running = False
        logger.info("Stopping blockchain monitoring...")
        
        # Wait for threads to finish
        for contract_name, thread in self.monitor_threads.items():
            if thread.is_alive():
                thread.join(timeout=10)
                logger.info(f"Stopped monitoring {contract_name}")
        
        self.monitor_threads.clear()
    
    def _monitor_contract_events(self, contract_name: str, event_names: List[str]):
        """Monitor events for a specific contract."""
        last_block = self._get_last_processed_block(contract_name)
        
        while self.is_running:
            try:
                current_block = web3_service.w3.eth.block_number
                
                if current_block > last_block:
                    # Process new blocks
                    for event_name in event_names:
                        self._process_contract_events(
                            contract_name, 
                            event_name, 
                            last_block + 1, 
                            current_block
                        )
                    
                    # Update last processed block
                    self._set_last_processed_block(contract_name, current_block)
                    last_block = current_block
                
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring {contract_name} events: {str(e)}")
                time.sleep(self.polling_interval * 2)  # Back off on error
    
    def _process_contract_events(self, contract_name: str, event_name: str, 
                                from_block: int, to_block: int):
        """Process events for a specific contract and event type."""
        try:
            logs = web3_service.get_logs(
                contract_name=contract_name,
                event_name=event_name,
                from_block=from_block,
                to_block=to_block
            )
            
            for log in logs:
                try:
                    # Convert log to BlockchainEvent
                    event = self._log_to_event(contract_name, event_name, log)
                    
                    # Process the event
                    self._handle_event(event)
                    
                except Exception as e:
                    logger.error(f"Error processing event log: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error getting logs for {contract_name}.{event_name}: {str(e)}")
    
    def _log_to_event(self, contract_name: str, event_name: str, log: Dict) -> BlockchainEvent:
        """Convert a Web3 log to a BlockchainEvent."""
        # Get block timestamp
        block = web3_service.get_block(log['blockNumber'])
        block_timestamp = datetime.fromtimestamp(block['timestamp']) if block else timezone.now()
        
        return BlockchainEvent(
            event_type=EventType(event_name),
            contract_name=contract_name,
            transaction_hash=log['transactionHash'].hex(),
            block_number=log['blockNumber'],
            block_timestamp=block_timestamp,
            event_data=dict(log['args'])
        )
    
    def _handle_event(self, event: BlockchainEvent):
        """Handle a blockchain event."""
        try:
            # Check if event was already processed
            cache_key = f"processed_event_{event.transaction_hash}_{event.event_type.value}"
            if cache.get(cache_key):
                return
            
            # Get handlers for this event type
            handlers = self.event_handlers.get(event.event_type, [])
            
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {str(e)}")
            
            # Mark event as processed
            cache.set(cache_key, True, timeout=86400)  # 24 hours
            
            logger.info(f"Processed {event.event_type.value} event: {event.transaction_hash}")
            
        except Exception as e:
            logger.error(f"Error handling event: {str(e)}")
    
    def _get_last_processed_block(self, contract_name: str) -> int:
        """Get the last processed block for a contract."""
        cache_key = f"last_block_{contract_name}"
        last_block = cache.get(cache_key)
        
        if last_block is None:
            # Start from recent blocks to avoid processing too much history
            current_block = web3_service.w3.eth.block_number
            last_block = max(0, current_block - 1000)  # Last 1000 blocks
            cache.set(cache_key, last_block, timeout=None)
        
        return last_block
    
    def _set_last_processed_block(self, contract_name: str, block_number: int):
        """Set the last processed block for a contract."""
        cache_key = f"last_block_{contract_name}"
        cache.set(cache_key, block_number, timeout=None)
    
    # Event Handlers
    
    def _handle_token_transfer(self, event: BlockchainEvent):
        """Handle NeuroCoin transfer events."""
        from_address = event.event_data.get('from')
        to_address = event.event_data.get('to')
        amount = event.event_data.get('value', 0)
        
        # Convert amount from wei to NRC
        amount_nrc = amount / (10 ** 18)
        
        # Log user activity for significant transfers
        if amount_nrc >= 100:  # Only log transfers >= 100 NRC
            self._log_user_activity(
                from_address,
                'token_transfer_sent',
                f'Sent {amount_nrc:.2f} NRC to {to_address[:10]}...',
                {
                    'to_address': to_address,
                    'amount': str(amount_nrc),
                    'tx_hash': event.transaction_hash
                }
            )
            
            self._log_user_activity(
                to_address,
                'token_transfer_received',
                f'Received {amount_nrc:.2f} NRC from {from_address[:10]}...',
                {
                    'from_address': from_address,
                    'amount': str(amount_nrc),
                    'tx_hash': event.transaction_hash
                }
            )
    
    def _handle_tokens_staked(self, event: BlockchainEvent):
        """Handle token staking events."""
        user_address = event.event_data.get('user')
        amount = event.event_data.get('amount', 0)
        amount_nrc = amount / (10 ** 18)
        
        self._log_user_activity(
            user_address,
            'tokens_staked',
            f'Staked {amount_nrc:.2f} NRC tokens',
            {
                'amount': str(amount_nrc),
                'tx_hash': event.transaction_hash
            }
        )
    
    def _handle_tokens_unstaked(self, event: BlockchainEvent):
        """Handle token unstaking events."""
        user_address = event.event_data.get('user')
        amount = event.event_data.get('amount', 0)
        amount_nrc = amount / (10 ** 18)
        
        self._log_user_activity(
            user_address,
            'tokens_unstaked',
            f'Unstaked {amount_nrc:.2f} NRC tokens',
            {
                'amount': str(amount_nrc),
                'tx_hash': event.transaction_hash
            }
        )
    
    def _handle_rewards_claimed(self, event: BlockchainEvent):
        """Handle rewards claimed events."""
        user_address = event.event_data.get('user')
        amount = event.event_data.get('amount', 0)
        amount_nrc = amount / (10 ** 18)
        
        self._log_user_activity(
            user_address,
            'rewards_claimed',
            f'Claimed {amount_nrc:.2f} NRC staking rewards',
            {
                'amount': str(amount_nrc),
                'tx_hash': event.transaction_hash
            }
        )
    
    def _handle_dataset_listed(self, event: BlockchainEvent):
        """Handle dataset listing events."""
        dataset_id = event.event_data.get('datasetId')
        seller = event.event_data.get('seller')
        price = event.event_data.get('price', 0)
        title = event.event_data.get('title', '')
        
        price_nrc = price / (10 ** 18)
        
        self._log_user_activity(
            seller,
            'dataset_listed',
            f'Listed dataset "{title}" for {price_nrc:.2f} NRC',
            {
                'dataset_id': str(dataset_id),
                'price': str(price_nrc),
                'title': title,
                'tx_hash': event.transaction_hash
            }
        )
        
        # Update dataset status in database
        self._update_dataset_blockchain_status(dataset_id, 'listed', event.transaction_hash)
    
    def _handle_dataset_purchased(self, event: BlockchainEvent):
        """Handle dataset purchase events."""
        purchase_id = event.event_data.get('purchaseId')
        dataset_id = event.event_data.get('datasetId')
        buyer = event.event_data.get('buyer')
        seller = event.event_data.get('seller')
        amount = event.event_data.get('amount', 0)
        
        amount_nrc = amount / (10 ** 18)
        
        # Log for buyer
        self._log_user_activity(
            buyer,
            'dataset_purchased',
            f'Purchased dataset for {amount_nrc:.2f} NRC',
            {
                'dataset_id': str(dataset_id),
                'purchase_id': str(purchase_id),
                'amount': str(amount_nrc),
                'seller': seller,
                'tx_hash': event.transaction_hash
            }
        )
        
        # Log for seller
        self._log_user_activity(
            seller,
            'dataset_sold',
            f'Dataset sold for {amount_nrc:.2f} NRC',
            {
                'dataset_id': str(dataset_id),
                'purchase_id': str(purchase_id),
                'amount': str(amount_nrc),
                'buyer': buyer,
                'tx_hash': event.transaction_hash
            }
        )
        
        # Update purchase status in database
        self._update_purchase_blockchain_status(purchase_id, 'in_escrow', event.transaction_hash)
    
    def _handle_dataset_updated(self, event: BlockchainEvent):
        """Handle dataset update events."""
        dataset_id = event.event_data.get('datasetId')
        new_price = event.event_data.get('newPrice', 0)
        is_active = event.event_data.get('isActive', True)
        
        price_nrc = new_price / (10 ** 18)
        
        # Get dataset owner from blockchain or database
        # This would require additional logic to map dataset_id to owner
        
        logger.info(f"Dataset {dataset_id} updated: price={price_nrc} NRC, active={is_active}")
    
    def _handle_purchase_completed(self, event: BlockchainEvent):
        """Handle purchase completion events."""
        purchase_id = event.event_data.get('purchaseId')
        dataset_id = event.event_data.get('datasetId')
        buyer = event.event_data.get('buyer')
        
        self._log_user_activity(
            buyer,
            'purchase_completed',
            f'Dataset purchase completed',
            {
                'dataset_id': str(dataset_id),
                'purchase_id': str(purchase_id),
                'tx_hash': event.transaction_hash
            }
        )
        
        # Update purchase status in database
        self._update_purchase_blockchain_status(purchase_id, 'completed', event.transaction_hash)
    
    def _handle_review_submitted(self, event: BlockchainEvent):
        """Handle review submission events."""
        purchase_id = event.event_data.get('purchaseId')
        buyer = event.event_data.get('buyer')
        rating = event.event_data.get('rating', 0)
        
        self._log_user_activity(
            buyer,
            'review_submitted',
            f'Submitted {rating}-star review',
            {
                'purchase_id': str(purchase_id),
                'rating': str(rating),
                'tx_hash': event.transaction_hash
            }
        )
    
    def _handle_escrow_released(self, event: BlockchainEvent):
        """Handle escrow release events."""
        purchase_id = event.event_data.get('purchaseId')
        seller = event.event_data.get('seller')
        amount = event.event_data.get('amount', 0)
        
        amount_nrc = amount / (10 ** 18)
        
        self._log_user_activity(
            seller,
            'escrow_released',
            f'Received {amount_nrc:.2f} NRC from escrow',
            {
                'purchase_id': str(purchase_id),
                'amount': str(amount_nrc),
                'tx_hash': event.transaction_hash
            }
        )
    
    def _handle_dispute_created(self, event: BlockchainEvent):
        """Handle dispute creation events."""
        purchase_id = event.event_data.get('purchaseId')
        initiator = event.event_data.get('initiator')
        reason = event.event_data.get('reason', '')
        
        self._log_user_activity(
            initiator,
            'dispute_created',
            f'Created dispute: {reason[:50]}...',
            {
                'purchase_id': str(purchase_id),
                'reason': reason,
                'tx_hash': event.transaction_hash
            }
        )
    
    def _handle_dispute_resolved(self, event: BlockchainEvent):
        """Handle dispute resolution events."""
        purchase_id = event.event_data.get('purchaseId')
        resolver = event.event_data.get('resolver')
        resolution = event.event_data.get('resolution', '')
        
        logger.info(f"Dispute resolved for purchase {purchase_id}: {resolution}")
    
    # Helper Methods
    
    def _log_user_activity(self, wallet_address: str, activity_type: str, 
                          description: str, metadata: Dict[str, Any]):
        """Log user activity from blockchain events."""
        try:
            # Find user by wallet address
            from apps.authentication.models import UserProfile
            
            try:
                profile = UserProfile.objects.get(wallet_address__iexact=wallet_address)
                user = profile.user
                
                UserActivity.objects.create(
                    user=user,
                    activity_type=activity_type,
                    description=description,
                    metadata=metadata
                )
                
            except UserProfile.DoesNotExist:
                logger.warning(f"No user found for wallet address: {wallet_address}")
                
        except Exception as e:
            logger.error(f"Error logging user activity: {str(e)}")
    
    def _update_dataset_blockchain_status(self, dataset_id: int, status: str, tx_hash: str):
        """Update dataset blockchain status in database."""
        try:
            from apps.datasets.models import Dataset
            
            Dataset.objects.filter(id=dataset_id).update(
                blockchain_status=status,
                blockchain_tx_hash=tx_hash,
                updated_at=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error updating dataset blockchain status: {str(e)}")
    
    def _update_purchase_blockchain_status(self, purchase_id: int, status: str, tx_hash: str):
        """Update purchase blockchain status in database."""
        try:
            from apps.marketplace.models import Purchase
            
            Purchase.objects.filter(id=purchase_id).update(
                blockchain_status=status,
                blockchain_tx_hash=tx_hash,
                updated_at=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error updating purchase blockchain status: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'is_running': self.is_running,
            'active_threads': len([t for t in self.monitor_threads.values() if t.is_alive()]),
            'contracts_monitored': list(self.monitor_threads.keys()),
            'last_processed_blocks': {
                contract: self._get_last_processed_block(contract)
                for contract in self.monitor_threads.keys()
            },
            'web3_connected': web3_service.is_connected(),
            'current_block': web3_service.w3.eth.block_number if web3_service.is_connected() else None
        }


# Global blockchain monitor instance
blockchain_monitor = BlockchainMonitor()
