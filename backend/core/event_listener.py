"""
Real-time smart contract event listener service.
"""
import asyncio
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .web3_service import web3_service
from .blockchain_monitor import blockchain_monitor, BlockchainEvent, EventType

logger = logging.getLogger(__name__)


class ListenerStatus(Enum):
    """Event listener status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class EventSubscription:
    """Event subscription configuration."""
    contract_name: str
    event_name: str
    callback: Callable
    filter_args: Optional[Dict] = None
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = timezone.now()


class EventListener:
    """
    Real-time smart contract event listener with WebSocket support.
    """
    
    def __init__(self):
        self.status = ListenerStatus.STOPPED
        self.subscriptions = {}
        self.event_filters = {}
        self.listener_thread = None
        self.channel_layer = get_channel_layer()
        self.polling_interval = getattr(settings, 'EVENT_POLLING_INTERVAL', 2)
        self.max_retries = getattr(settings, 'EVENT_LISTENER_MAX_RETRIES', 5)
        self.retry_delay = getattr(settings, 'EVENT_LISTENER_RETRY_DELAY', 10)
        
        # Setup default event handlers (only if not in management command)
        import sys
        if 'manage.py' not in sys.argv[0] or 'runserver' in sys.argv:
            self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default event handlers for common events."""
        # Dataset events
        self.subscribe('DatasetMarketplace', 'DatasetListed', self._handle_dataset_listed)
        self.subscribe('DatasetMarketplace', 'DatasetPurchased', self._handle_dataset_purchased)
        self.subscribe('DatasetMarketplace', 'PurchaseCompleted', self._handle_purchase_completed)
        self.subscribe('DatasetMarketplace', 'ReviewSubmitted', self._handle_review_submitted)
        
        # Token events
        self.subscribe('NeuroCoin', 'Transfer', self._handle_token_transfer)
        self.subscribe('NeuroCoin', 'TokensStaked', self._handle_tokens_staked)
        self.subscribe('NeuroCoin', 'RewardsClaimed', self._handle_rewards_claimed)
        
        # Escrow events
        self.subscribe('EscrowManager', 'EscrowReleased', self._handle_escrow_released)
        self.subscribe('EscrowManager', 'DisputeCreated', self._handle_dispute_created)
    
    def subscribe(self, contract_name: str, event_name: str, callback: Callable,
                 filter_args: Optional[Dict] = None) -> str:
        """
        Subscribe to a smart contract event.
        
        Args:
            contract_name: Name of the contract
            event_name: Name of the event
            callback: Callback function to handle the event
            filter_args: Optional filter arguments
            
        Returns:
            Subscription ID
        """
        subscription_id = f"{contract_name}_{event_name}_{id(callback)}"
        
        subscription = EventSubscription(
            contract_name=contract_name,
            event_name=event_name,
            callback=callback,
            filter_args=filter_args
        )
        
        self.subscriptions[subscription_id] = subscription
        
        # Create event filter if listener is running
        if self.status == ListenerStatus.RUNNING:
            self._create_event_filter(subscription_id, subscription)
        
        logger.info(f"Subscribed to {contract_name}.{event_name}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from an event.
        
        Args:
            subscription_id: ID of the subscription to remove
            
        Returns:
            True if successfully unsubscribed
        """
        if subscription_id in self.subscriptions:
            # Remove event filter
            if subscription_id in self.event_filters:
                del self.event_filters[subscription_id]
            
            # Remove subscription
            subscription = self.subscriptions.pop(subscription_id)
            logger.info(f"Unsubscribed from {subscription.contract_name}.{subscription.event_name}")
            return True
        
        return False
    
    def start(self) -> bool:
        """
        Start the event listener.
        
        Returns:
            True if started successfully
        """
        if self.status == ListenerStatus.RUNNING:
            logger.warning("Event listener is already running")
            return True
        
        if not web3_service.is_connected():
            logger.error("Web3 service is not connected")
            return False
        
        try:
            self.status = ListenerStatus.STARTING
            
            # Create event filters for all subscriptions
            for sub_id, subscription in self.subscriptions.items():
                if subscription.is_active:
                    self._create_event_filter(sub_id, subscription)
            
            # Start listener thread
            self.listener_thread = threading.Thread(
                target=self._event_loop,
                daemon=True
            )
            self.listener_thread.start()
            
            self.status = ListenerStatus.RUNNING
            logger.info("Event listener started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting event listener: {str(e)}")
            self.status = ListenerStatus.ERROR
            return False
    
    def stop(self) -> bool:
        """
        Stop the event listener.
        
        Returns:
            True if stopped successfully
        """
        if self.status == ListenerStatus.STOPPED:
            return True
        
        try:
            self.status = ListenerStatus.STOPPING
            
            # Clear event filters
            self.event_filters.clear()
            
            # Wait for thread to finish
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=10)
            
            self.status = ListenerStatus.STOPPED
            logger.info("Event listener stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping event listener: {str(e)}")
            return False
    
    def _create_event_filter(self, subscription_id: str, subscription: EventSubscription):
        """
        Create an event filter for a subscription.
        
        Args:
            subscription_id: ID of the subscription
            subscription: Subscription object
        """
        try:
            contract = web3_service.get_contract(subscription.contract_name)
            if not contract:
                logger.error(f"Contract {subscription.contract_name} not found")
                return
            
            event = getattr(contract.events, subscription.event_name, None)
            if not event:
                logger.error(f"Event {subscription.event_name} not found in {subscription.contract_name}")
                return
            
            # Create filter
            filter_kwargs = {
                'fromBlock': 'latest',
                'argument_filters': subscription.filter_args or {}
            }
            
            event_filter = event.create_filter(**filter_kwargs)
            self.event_filters[subscription_id] = event_filter
            
            logger.info(f"Created event filter for {subscription.contract_name}.{subscription.event_name}")
            
        except Exception as e:
            logger.error(f"Error creating event filter: {str(e)}")
    
    def _event_loop(self):
        """
        Main event listening loop.
        """
        retry_count = 0
        
        while self.status == ListenerStatus.RUNNING:
            try:
                # Check all event filters for new events
                for sub_id, event_filter in list(self.event_filters.items()):
                    try:
                        # Get new events
                        new_events = event_filter.get_new_entries()
                        
                        for event_data in new_events:
                            self._process_event(sub_id, event_data)
                            
                    except Exception as e:
                        logger.error(f"Error processing events for {sub_id}: {str(e)}")
                
                # Reset retry count on successful iteration
                retry_count = 0
                
                # Wait before next poll
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in event loop: {str(e)}")
                retry_count += 1
                
                if retry_count >= self.max_retries:
                    logger.error("Max retries reached, stopping event listener")
                    self.status = ListenerStatus.ERROR
                    break
                
                # Exponential backoff
                delay = self.retry_delay * (2 ** min(retry_count, 5))
                time.sleep(delay)
    
    def _process_event(self, subscription_id: str, event_data: Dict):
        """
        Process a single event.
        
        Args:
            subscription_id: ID of the subscription
            event_data: Event data from Web3
        """
        try:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription or not subscription.is_active:
                return
            
            # Convert event data to our format
            blockchain_event = self._convert_to_blockchain_event(
                subscription.contract_name,
                subscription.event_name,
                event_data
            )
            
            # Call the subscription callback
            try:
                subscription.callback(blockchain_event)
            except Exception as e:
                logger.error(f"Error in event callback: {str(e)}")
            
            # Send to WebSocket clients
            self._broadcast_event(blockchain_event)
            
            # Cache recent event
            self._cache_recent_event(blockchain_event)
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
    
    def _convert_to_blockchain_event(self, contract_name: str, event_name: str, 
                                   event_data: Dict) -> BlockchainEvent:
        """
        Convert Web3 event data to BlockchainEvent.
        
        Args:
            contract_name: Name of the contract
            event_name: Name of the event
            event_data: Raw event data from Web3
            
        Returns:
            BlockchainEvent object
        """
        # Get block timestamp
        block = web3_service.get_block(event_data['blockNumber'])
        block_timestamp = datetime.fromtimestamp(block['timestamp']) if block else timezone.now()
        
        return BlockchainEvent(
            event_type=EventType(event_name),
            contract_name=contract_name,
            transaction_hash=event_data['transactionHash'].hex(),
            block_number=event_data['blockNumber'],
            block_timestamp=block_timestamp,
            event_data=dict(event_data['args'])
        )
    
    def _broadcast_event(self, event: BlockchainEvent):
        """
        Broadcast event to WebSocket clients.
        
        Args:
            event: BlockchainEvent to broadcast
        """
        if not self.channel_layer:
            return
        
        try:
            # Prepare event data for WebSocket
            event_message = {
                'type': 'blockchain_event',
                'event_type': event.event_type.value,
                'contract_name': event.contract_name,
                'transaction_hash': event.transaction_hash,
                'block_number': event.block_number,
                'timestamp': event.block_timestamp.isoformat(),
                'data': event.event_data
            }
            
            # Send to general blockchain events group
            async_to_sync(self.channel_layer.group_send)(
                'blockchain_events',
                {
                    'type': 'send_event',
                    'message': event_message
                }
            )
            
            # Send to specific event type group
            event_group = f"blockchain_events_{event.event_type.value.lower()}"
            async_to_sync(self.channel_layer.group_send)(
                event_group,
                {
                    'type': 'send_event',
                    'message': event_message
                }
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting event: {str(e)}")
    
    def _cache_recent_event(self, event: BlockchainEvent):
        """
        Cache recent event for quick retrieval.
        
        Args:
            event: BlockchainEvent to cache
        """
        try:
            cache_key = f"recent_events_{event.event_type.value}"
            recent_events = cache.get(cache_key, [])
            
            # Add new event
            event_data = {
                'transaction_hash': event.transaction_hash,
                'block_number': event.block_number,
                'timestamp': event.block_timestamp.isoformat(),
                'data': event.event_data
            }
            
            recent_events.insert(0, event_data)
            
            # Keep only last 50 events
            recent_events = recent_events[:50]
            
            # Cache for 1 hour
            cache.set(cache_key, recent_events, timeout=3600)
            
        except Exception as e:
            logger.error(f"Error caching event: {str(e)}")
    
    # Default Event Handlers
    
    def _handle_dataset_listed(self, event: BlockchainEvent):
        """Handle dataset listing events."""
        dataset_id = event.event_data.get('datasetId')
        seller = event.event_data.get('seller')
        title = event.event_data.get('title', '')
        
        logger.info(f"Dataset listed: ID={dataset_id}, Seller={seller[:10]}..., Title={title}")
        
        # Update database if needed
        self._update_dataset_status(dataset_id, 'listed')
    
    def _handle_dataset_purchased(self, event: BlockchainEvent):
        """Handle dataset purchase events."""
        purchase_id = event.event_data.get('purchaseId')
        dataset_id = event.event_data.get('datasetId')
        buyer = event.event_data.get('buyer')
        amount = event.event_data.get('amount', 0)
        
        amount_nrc = amount / (10 ** 18)
        
        logger.info(f"Dataset purchased: Purchase={purchase_id}, Dataset={dataset_id}, "
                   f"Buyer={buyer[:10]}..., Amount={amount_nrc:.2f} NRC")
        
        # Update database
        self._update_purchase_status(purchase_id, 'in_escrow')
    
    def _handle_purchase_completed(self, event: BlockchainEvent):
        """Handle purchase completion events."""
        purchase_id = event.event_data.get('purchaseId')
        
        logger.info(f"Purchase completed: ID={purchase_id}")
        
        # Update database
        self._update_purchase_status(purchase_id, 'completed')
    
    def _handle_review_submitted(self, event: BlockchainEvent):
        """Handle review submission events."""
        purchase_id = event.event_data.get('purchaseId')
        rating = event.event_data.get('rating', 0)
        
        logger.info(f"Review submitted: Purchase={purchase_id}, Rating={rating}")
    
    def _handle_token_transfer(self, event: BlockchainEvent):
        """Handle token transfer events."""
        from_address = event.event_data.get('from')
        to_address = event.event_data.get('to')
        amount = event.event_data.get('value', 0)
        
        amount_nrc = amount / (10 ** 18)
        
        # Only log significant transfers
        if amount_nrc >= 100:
            logger.info(f"Large token transfer: {amount_nrc:.2f} NRC from "
                       f"{from_address[:10]}... to {to_address[:10]}...")
    
    def _handle_tokens_staked(self, event: BlockchainEvent):
        """Handle token staking events."""
        user = event.event_data.get('user')
        amount = event.event_data.get('amount', 0)
        
        amount_nrc = amount / (10 ** 18)
        logger.info(f"Tokens staked: {amount_nrc:.2f} NRC by {user[:10]}...")
    
    def _handle_rewards_claimed(self, event: BlockchainEvent):
        """Handle rewards claimed events."""
        user = event.event_data.get('user')
        amount = event.event_data.get('amount', 0)
        
        amount_nrc = amount / (10 ** 18)
        logger.info(f"Rewards claimed: {amount_nrc:.2f} NRC by {user[:10]}...")
    
    def _handle_escrow_released(self, event: BlockchainEvent):
        """Handle escrow release events."""
        purchase_id = event.event_data.get('purchaseId')
        seller = event.event_data.get('seller')
        amount = event.event_data.get('amount', 0)
        
        amount_nrc = amount / (10 ** 18)
        logger.info(f"Escrow released: {amount_nrc:.2f} NRC to {seller[:10]}... "
                   f"for purchase {purchase_id}")
    
    def _handle_dispute_created(self, event: BlockchainEvent):
        """Handle dispute creation events."""
        purchase_id = event.event_data.get('purchaseId')
        initiator = event.event_data.get('initiator')
        
        logger.info(f"Dispute created: Purchase={purchase_id}, Initiator={initiator[:10]}...")
    
    # Helper Methods
    
    def _update_dataset_status(self, dataset_id: int, status: str):
        """Update dataset status in database."""
        try:
            from apps.datasets.models import Dataset
            Dataset.objects.filter(id=dataset_id).update(
                blockchain_status=status,
                updated_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error updating dataset status: {str(e)}")
    
    def _update_purchase_status(self, purchase_id: int, status: str):
        """Update purchase status in database."""
        try:
            from apps.marketplace.models import Purchase
            Purchase.objects.filter(id=purchase_id).update(
                blockchain_status=status,
                updated_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error updating purchase status: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current listener status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'status': self.status.value,
            'subscriptions_count': len(self.subscriptions),
            'active_filters': len(self.event_filters),
            'web3_connected': web3_service.is_connected(),
            'thread_alive': self.listener_thread.is_alive() if self.listener_thread else False,
            'subscriptions': [
                {
                    'id': sub_id,
                    'contract': sub.contract_name,
                    'event': sub.event_name,
                    'active': sub.is_active,
                    'created_at': sub.created_at.isoformat()
                }
                for sub_id, sub in self.subscriptions.items()
            ]
        }
    
    def get_recent_events(self, event_type: str = None, limit: int = 20) -> List[Dict]:
        """
        Get recent events from cache.
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        if event_type:
            cache_key = f"recent_events_{event_type}"
            events = cache.get(cache_key, [])
        else:
            # Get events from all types
            events = []
            for event_enum in EventType:
                cache_key = f"recent_events_{event_enum.value}"
                type_events = cache.get(cache_key, [])
                events.extend(type_events)
            
            # Sort by timestamp
            events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return events[:limit]


# Global event listener instance
event_listener = EventListener()
