"""
Django management command to start blockchain monitoring services.
"""
import logging
import signal
import sys
import time
from django.core.management.base import BaseCommand
from django.conf import settings

from core.blockchain_monitor import blockchain_monitor
from core.event_listener import event_listener
from core.web3_service import web3_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start blockchain monitoring services'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown = False
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--monitor-only',
            action='store_true',
            help='Start only the blockchain monitor (not event listener)',
        )
        parser.add_argument(
            '--listener-only',
            action='store_true',
            help='Start only the event listener (not blockchain monitor)',
        )
        parser.add_argument(
            '--no-auto-restart',
            action='store_true',
            help='Disable automatic restart on failure',
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting NeuroData Blockchain Monitoring Services...')
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Check Web3 connection
        if not web3_service.is_connected():
            self.stdout.write(
                self.style.ERROR('❌ Web3 service is not connected. Please check your configuration.')
            )
            return
        
        network_info = web3_service.get_network_info()
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Connected to blockchain network (Chain ID: {network_info.get("chain_id")})'
            )
        )
        
        # Determine which services to start
        start_monitor = not options['listener_only']
        start_listener = not options['monitor_only']
        auto_restart = not options['no_auto_restart']
        
        try:
            # Start services
            if start_monitor:
                self._start_blockchain_monitor()
            
            if start_listener:
                self._start_event_listener()
            
            # Main monitoring loop
            self._monitoring_loop(start_monitor, start_listener, auto_restart)
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⚠️  Received interrupt signal'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error in monitoring services: {str(e)}'))
            logger.error(f"Error in blockchain monitoring: {str(e)}")
        finally:
            self._shutdown_services(start_monitor, start_listener)
    
    def _start_blockchain_monitor(self):
        """Start the blockchain monitor."""
        try:
            blockchain_monitor.start_monitoring()
            self.stdout.write(
                self.style.SUCCESS('✅ Blockchain monitor started successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to start blockchain monitor: {str(e)}')
            )
            raise
    
    def _start_event_listener(self):
        """Start the event listener."""
        try:
            event_listener.start()
            self.stdout.write(
                self.style.SUCCESS('✅ Event listener started successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to start event listener: {str(e)}')
            )
            raise
    
    def _monitoring_loop(self, monitor_enabled: bool, listener_enabled: bool, auto_restart: bool):
        """Main monitoring loop."""
        self.stdout.write(
            self.style.SUCCESS('🔄 Monitoring services are running. Press Ctrl+C to stop.')
        )
        
        check_interval = 30  # Check every 30 seconds
        
        while not self.shutdown:
            try:
                time.sleep(check_interval)
                
                # Check service health
                if monitor_enabled:
                    monitor_status = blockchain_monitor.get_monitoring_status()
                    if not monitor_status['is_running'] and auto_restart:
                        self.stdout.write(
                            self.style.WARNING('⚠️  Blockchain monitor stopped, restarting...')
                        )
                        self._start_blockchain_monitor()
                
                if listener_enabled:
                    listener_status = event_listener.get_status()
                    if listener_status['status'] != 'running' and auto_restart:
                        self.stdout.write(
                            self.style.WARNING('⚠️  Event listener stopped, restarting...')
                        )
                        self._start_event_listener()
                
                # Check Web3 connection
                if not web3_service.is_connected():
                    self.stdout.write(
                        self.style.ERROR('❌ Lost connection to blockchain network')
                    )
                    if auto_restart:
                        self.stdout.write(
                            self.style.WARNING('🔄 Attempting to reconnect...')
                        )
                        # Web3 service will attempt to reconnect automatically
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error in monitoring loop: {str(e)}')
                )
                logger.error(f"Error in monitoring loop: {str(e)}")
                
                if not auto_restart:
                    break
                
                # Wait before retrying
                time.sleep(10)
    
    def _shutdown_services(self, monitor_enabled: bool, listener_enabled: bool):
        """Shutdown monitoring services gracefully."""
        self.stdout.write(self.style.WARNING('🛑 Shutting down monitoring services...'))
        
        try:
            if monitor_enabled:
                blockchain_monitor.stop_monitoring()
                self.stdout.write(self.style.SUCCESS('✅ Blockchain monitor stopped'))
            
            if listener_enabled:
                event_listener.stop()
                self.stdout.write(self.style.SUCCESS('✅ Event listener stopped'))
            
            self.stdout.write(self.style.SUCCESS('✅ All services stopped successfully'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during shutdown: {str(e)}')
            )
            logger.error(f"Error during shutdown: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.stdout.write(
            self.style.WARNING(f'\n⚠️  Received signal {signum}, initiating graceful shutdown...')
        )
        self.shutdown = True
    
    def _print_status(self):
        """Print current status of monitoring services."""
        try:
            # Blockchain monitor status
            monitor_status = blockchain_monitor.get_monitoring_status()
            self.stdout.write(
                self.style.SUCCESS(
                    f'📊 Blockchain Monitor: {"Running" if monitor_status["is_running"] else "Stopped"}'
                )
            )
            
            if monitor_status['is_running']:
                self.stdout.write(f'   - Active threads: {monitor_status["active_threads"]}')
                self.stdout.write(f'   - Contracts monitored: {len(monitor_status["contracts_monitored"])}')
                self.stdout.write(f'   - Current block: {monitor_status.get("current_block", "Unknown")}')
            
            # Event listener status
            listener_status = event_listener.get_status()
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎧 Event Listener: {listener_status["status"].title()}'
                )
            )
            
            if listener_status['status'] == 'running':
                self.stdout.write(f'   - Subscriptions: {listener_status["subscriptions_count"]}')
                self.stdout.write(f'   - Active filters: {listener_status["active_filters"]}')
            
            # Web3 connection status
            network_info = web3_service.get_network_info()
            self.stdout.write(
                self.style.SUCCESS(
                    f'🌐 Web3 Connection: {"Connected" if network_info.get("is_connected") else "Disconnected"}'
                )
            )
            
            if network_info.get('is_connected'):
                self.stdout.write(f'   - Chain ID: {network_info.get("chain_id")}')
                self.stdout.write(f'   - Block number: {network_info.get("block_number")}')
                self.stdout.write(f'   - Gas price: {network_info.get("gas_price", 0) // 10**9} gwei')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting status: {str(e)}')
            )
