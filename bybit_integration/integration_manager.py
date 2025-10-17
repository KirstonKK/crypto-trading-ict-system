"""
Bybit Integration Manager
========================

Main orchestration layer that integrates ICT Enhanced Trading Monitor 
with Bybit demo trading environment.

Features:
- Signal processing from ICT monitor
- Trade execution management
- Real-time market data integration
- Performance monitoring and reporting
- Risk management coordination
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from .bybit_client import BybitDemoClient
from .trading_executor import BybitTradingExecutor, TradingSignal, TradeExecution
from .websocket_client import BybitWebSocketClient, MarketData, OrderUpdate, PositionUpdate

logger = logging.getLogger(__name__)

@dataclass
class IntegrationStatus:
    """Integration system status"""
    bybit_connected: bool = False
    websocket_connected: bool = False
    ict_monitor_connected: bool = False
    total_signals_received: int = 0
    total_trades_executed: int = 0
    active_positions: int = 0
    last_signal_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None
    system_uptime: timedelta = timedelta()
    start_time: datetime = datetime.now()

class BybitIntegrationManager:
    """
    Main integration manager for Bybit demo trading
    
    Coordinates:
    - ICT signal reception and validation
    - Bybit trade execution
    - Real-time market data
    - Performance tracking
    - Risk management
    - System monitoring
    """
    
    def __init__(self, 
                 api_key: str = None,
                 api_secret: str = None,
                 ict_monitor_url: str = "http://localhost:5001",
                 testnet: bool = True,
                 auto_trading: bool = False):
        """
        Initialize integration manager
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            ict_monitor_url: ICT Enhanced Monitor URL
            testnet: Use Bybit testnet
            auto_trading: Enable automatic trade execution
        """
        self.ict_monitor_url = ict_monitor_url
        self.auto_trading = auto_trading
        self.testnet = testnet
        
        # Initialize clients
        self.bybit_client = BybitDemoClient(api_key, api_secret, testnet)
        self.websocket_client = BybitWebSocketClient(api_key, api_secret, testnet)
        
        # Initialize trading executor with strict 1% risk and dynamic RR
        self.trading_executor = BybitTradingExecutor(
            bybit_client=self.bybit_client,
            max_positions=3,
            max_risk_per_trade=0.01,    # 1% strict risk limit
            max_portfolio_risk=0.03,    # 3% total portfolio risk
            min_confidence=0.7,         # 70% minimum confidence
            dynamic_take_profit=True    # Enable dynamic RR ratios
        )
        
        # System state
        self.status = IntegrationStatus()
        self.running = False
        
        # Signal processing
        self.signal_queue = asyncio.Queue()
        self.signal_callbacks: List[Callable] = []
        self.trade_callbacks: List[Callable] = []
        
        # Performance tracking
        self.performance_data = {
            "daily_pnl": 0.0,
            "total_signals": 0,
            "executed_signals": 0,
            "signal_accuracy": 0.0,
            "average_hold_time": timedelta(),
            "best_trade": 0.0,
            "worst_trade": 0.0
        }
        
        # HTTP session for ICT monitor communication
        self.http_session = None
        
        logger.info("🔧 Bybit Integration Manager initialized")
        logger.info(f"   ICT Monitor: {ict_monitor_url}")
        logger.info(f"   Auto Trading: {'Enabled' if auto_trading else 'Disabled'}")
        logger.info(f"   Environment: {'Testnet' if testnet else 'Mainnet'}")

    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🔄 Initializing Bybit integration components...")
            
            # Create HTTP session
            self.http_session = aiohttp.ClientSession()
            
            # Test Bybit connection
            connection_test = await self.bybit_client.test_connection()
            if connection_test:
                self.status.bybit_connected = True
                logger.info("✅ Bybit API connection successful")
            else:
                raise Exception("Bybit API connection failed")
            
            # Initialize trading executor
            await self.trading_executor.initialize()
            
            # Setup WebSocket callbacks
            self._setup_websocket_callbacks()
            
            # Test ICT monitor connection
            await self._test_ict_connection()
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise

    def _setup_websocket_callbacks(self):
        """Setup WebSocket event callbacks"""
        
        async def on_price_update(market_data: MarketData):
            """Handle real-time price updates"""
            logger.debug(f"💰 Price update: {market_data.symbol} = ${market_data.price:.4f}")
            
            # Trigger any registered callbacks
            for callback in self.signal_callbacks:
                try:
                    await callback("price_update", asdict(market_data))
                except Exception as e:
                    logger.error(f"❌ Price callback error: {e}")
        
        async def on_order_update(order_update: OrderUpdate):
            """Handle order status updates"""
            logger.info(f"📋 Order update: {order_update.symbol} {order_update.status}")
            
            # Update trading executor
            # (The executor will handle this through its own monitoring)
            
        async def on_position_update(position_update: PositionUpdate):
            """Handle position updates"""
            logger.info(f"📊 Position update: {position_update.symbol} Size: {position_update.size}")
            
            # Update status
            positions = await self.bybit_client.get_positions()
            self.status.active_positions = len([p for p in positions if float(p.get('size', 0)) > 0])
        
        # Register callbacks
        self.websocket_client.callbacks[self.websocket_client.SubscriptionType.TICKER].append(on_price_update)
        self.websocket_client.callbacks[self.websocket_client.SubscriptionType.ORDER].append(on_order_update)
        self.websocket_client.callbacks[self.websocket_client.SubscriptionType.POSITION].append(on_position_update)

    async def _test_ict_connection(self):
        """Test connection to ICT Enhanced Monitor"""
        try:
            async with self.http_session.get(f"{self.ict_monitor_url}/api/status") as response:
                if response.status == 200:
                    data = await response.json()
                    self.status.ict_monitor_connected = True
                    logger.info("✅ ICT Monitor connection successful")
                    logger.info(f"   Status: {data.get('status', 'Unknown')}")
                else:
                    raise Exception(f"ICT Monitor returned status {response.status}")
                    
        except Exception as e:
            logger.warning(f"⚠️  ICT Monitor connection failed: {e}")
            self.status.ict_monitor_connected = False

    async def _monitor_ict_signals(self):
        """Monitor ICT Enhanced Monitor for new signals"""
        last_signal_id = None
        
        while self.running:
            try:
                # Check for new signals
                async with self.http_session.get(f"{self.ict_monitor_url}/api/signals/latest") as response:
                    if response.status == 200:
                        signals = await response.json()
                        
                        for signal in signals:
                            signal_id = signal.get('signal_id')
                            
                            # Process only new signals
                            if signal_id != last_signal_id:
                                await self.signal_queue.put(signal)
                                last_signal_id = signal_id
                                self.status.total_signals_received += 1
                                self.status.last_signal_time = datetime.now()
                                
                                logger.info(f"📡 New signal received: {signal.get('symbol')} {signal.get('action')}")
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Error monitoring ICT signals: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def _process_signals(self):
        """Process signals from the queue"""
        while self.running:
            try:
                # Wait for signal with timeout
                try:
                    signal_data = await asyncio.wait_for(self.signal_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                logger.info(f"🔄 Processing signal: {signal_data.get('symbol')} {signal_data.get('action')}")
                
                # Validate signal format
                if not self._validate_signal_format(signal_data):
                    logger.warning("⚠️  Invalid signal format, skipping")
                    continue
                
                # Call signal callbacks
                for callback in self.signal_callbacks:
                    try:
                        await callback("new_signal", signal_data)
                    except Exception as e:
                        logger.error(f"❌ Signal callback error: {e}")
                
                # Execute trade if auto-trading is enabled
                if self.auto_trading:
                    execution = await self.trading_executor.process_ict_signal(signal_data)
                    
                    if execution:
                        self.status.total_trades_executed += 1
                        self.status.last_trade_time = datetime.now()
                        
                        # Call trade callbacks
                        for callback in self.trade_callbacks:
                            try:
                                await callback("trade_executed", asdict(execution))
                            except Exception as e:
                                logger.error(f"❌ Trade callback error: {e}")
                        
                        logger.info(f"✅ Trade executed: {execution.symbol} {execution.side}")
                    else:
                        logger.info("🚫 Signal not executed (validation failed)")
                else:
                    logger.info("📊 Signal logged (auto-trading disabled)")
                
                # Update performance data
                await self._update_performance_data()
                
            except Exception as e:
                logger.error(f"❌ Error processing signal: {e}")

    def _validate_signal_format(self, signal_data: Dict) -> bool:
        """Validate signal data format"""
        required_fields = ['symbol', 'action', 'confidence', 'price', 'timestamp']
        
        for field in required_fields:
            if field not in signal_data:
                logger.warning(f"⚠️  Missing required field: {field}")
                return False
        
        # Validate action
        if signal_data['action'].upper() not in ['BUY', 'SELL']:
            logger.warning(f"⚠️  Invalid action: {signal_data['action']}")
            return False
        
        # Validate confidence
        confidence = signal_data.get('confidence', 0)
        if not 0 <= confidence <= 1:
            logger.warning(f"⚠️  Invalid confidence: {confidence}")
            return False
        
        return True

    async def _update_performance_data(self):
        """Update performance tracking data"""
        try:
            # Get trading executor performance
            executor_performance = self.trading_executor.get_performance_summary()
            
            # Update our performance data
            self.performance_data.update({
                "total_signals": self.status.total_signals_received,
                "executed_signals": self.status.total_trades_executed,
                "signal_accuracy": (self.status.total_trades_executed / max(self.status.total_signals_received, 1)) * 100,
                "total_pnl": float(executor_performance.get("total_pnl", "$0.00").replace("$", "")),
                "win_rate": executor_performance.get("win_rate", "0.0%"),
                "active_positions": executor_performance.get("active_positions", 0)
            })
            
        except Exception as e:
            logger.error(f"❌ Error updating performance data: {e}")

    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while self.running:
            try:
                # Update system uptime
                self.status.system_uptime = datetime.now() - self.status.start_time
                
                # Check component health
                if self.status.bybit_connected:
                    try:
                        await self.bybit_client.test_connection()
                    except:
                        self.status.bybit_connected = False
                        logger.warning("⚠️  Bybit connection lost")
                
                # Check WebSocket health
                self.status.websocket_connected = self.websocket_client.connected
                
                # Check ICT monitor health
                if self.status.ict_monitor_connected:
                    try:
                        await self._test_ict_connection()
                    except:
                        pass  # Already logged in _test_ict_connection
                
                # Monitor trading executor
                await self.trading_executor.monitor_trades()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ System health monitoring error: {e}")
                await asyncio.sleep(60)

    # Public API Methods
    
    async def start(self):
        """Start the integration system"""
        try:
            logger.info("🚀 Starting Bybit integration system...")
            
            if not self.running:
                await self.initialize()
                
                self.running = True
                self.status.start_time = datetime.now()
                
                # Start background tasks
                tasks = [
                    asyncio.create_task(self._monitor_ict_signals()),
                    asyncio.create_task(self._process_signals()),
                    asyncio.create_task(self._monitor_system_health()),
                    asyncio.create_task(self.websocket_client.start())
                ]
                
                logger.info("✅ Integration system started successfully")
                logger.info(f"   Auto Trading: {'ON' if self.auto_trading else 'OFF'}")
                
                # Run all tasks concurrently
                await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to start integration system: {e}")
            raise

    async def stop(self):
        """Stop the integration system"""
        try:
            logger.info("🛑 Stopping Bybit integration system...")
            
            self.running = False
            
            # Close WebSocket connections
            await self.websocket_client.stop()
            
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
            
            # Close Bybit client
            await self.bybit_client.close()
            
            logger.info("✅ Integration system stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping integration system: {e}")

    def enable_auto_trading(self):
        """Enable automatic trade execution"""
        self.auto_trading = True
        logger.info("✅ Auto-trading enabled")

    def disable_auto_trading(self):
        """Disable automatic trade execution"""
        self.auto_trading = False
        logger.info("⏸️  Auto-trading disabled")

    def add_signal_callback(self, callback: Callable):
        """Add callback for signal events"""
        self.signal_callbacks.append(callback)
        logger.info("📡 Signal callback registered")

    def add_trade_callback(self, callback: Callable):
        """Add callback for trade events"""
        self.trade_callbacks.append(callback)
        logger.info("💱 Trade callback registered")

    def subscribe_to_symbol(self, symbol: str):
        """Subscribe to real-time data for a symbol"""
        self.websocket_client.subscribe_ticker(symbol)
        self.websocket_client.subscribe_trades(symbol)
        logger.info(f"📡 Subscribed to real-time data: {symbol}")

    async def manual_trade(self, signal_data: Dict) -> Optional[TradeExecution]:
        """Manually execute a trade"""
        try:
            logger.info(f"🔧 Manual trade execution: {signal_data.get('symbol')}")
            
            if not self._validate_signal_format(signal_data):
                logger.warning("⚠️  Invalid signal format for manual trade")
                return None
            
            execution = await self.trading_executor.process_ict_signal(signal_data)
            
            if execution:
                self.status.total_trades_executed += 1
                self.status.last_trade_time = datetime.now()
                logger.info(f"✅ Manual trade executed: {execution.symbol}")
            
            return execution
            
        except Exception as e:
            logger.error(f"❌ Manual trade execution failed: {e}")
            return None

    async def close_all_positions(self):
        """Emergency close all positions"""
        try:
            logger.warning("🚨 Emergency close all positions")
            await self.trading_executor.close_all_positions()
            logger.info("✅ All positions closed")
        except Exception as e:
            logger.error(f"❌ Error closing positions: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "system": asdict(self.status),
            "performance": self.performance_data,
            "trading_executor": self.trading_executor.get_performance_summary(),
            "auto_trading": self.auto_trading,
            "running": self.running
        }

    def get_active_trades(self) -> List[Dict]:
        """Get currently active trades"""
        return [asdict(trade) for trade in self.trading_executor.active_trades.values()]

    def get_trade_history(self) -> List[Dict]:
        """Get trade execution history"""
        return [asdict(trade) for trade in self.trading_executor.execution_history]

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


# Utility Functions

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    return {
        "api_key": os.getenv("BYBIT_API_KEY"),
        "api_secret": os.getenv("BYBIT_API_SECRET"),
        "ict_monitor_url": os.getenv("ICT_MONITOR_URL", "http://localhost:5001"),
        "testnet": os.getenv("BYBIT_TESTNET", "true").lower() == "true",
        "auto_trading": os.getenv("AUTO_TRADING", "false").lower() == "true"
    }

async def create_integration_manager(**kwargs) -> BybitIntegrationManager:
    """Factory function to create and initialize integration manager"""
    config = load_config_from_env()
    config.update(kwargs)
    
    manager = BybitIntegrationManager(**config)
    await manager.initialize()
    
    return manager