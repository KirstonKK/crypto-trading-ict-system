"""
Bybit Integration Module
=======================

Integration layer for connecting ICT Enhanced Trading Monitor
with Bybit demo trading environment.

This module provides:
- BybitDemoClient: Core API client for Bybit testnet/mainnet
- BybitTradingExecutor: Signal processing and trade execution
- BybitWebSocketClient: Real-time market data and order updates
- BybitIntegrationManager: Main orchestration layer

Usage:
    from bybit_integration import BybitIntegrationManager
    
    # Initialize with environment variables
    manager = await create_integration_manager()
    
    # Or with explicit configuration
    manager = BybitIntegrationManager(
        api_key="your_api_key",
        api_secret="your_api_secret",
        testnet=True,
        auto_trading=True
    )
    
    # Start the integration
    await manager.start()
"""

__version__ = "1.0.0"
__author__ = "Trading Algorithm Development Team"

# Core imports
from .bybit_client import BybitDemoClient, format_bybit_symbol, calculate_quantity_precision
from .trading_executor import (
    BybitTradingExecutor, 
    TradingSignal, 
    TradeExecution, 
    OrderStatus, 
    PositionSide
)
from .websocket_client import (
    BybitWebSocketClient, 
    MarketData, 
    OrderUpdate, 
    PositionUpdate, 
    SubscriptionType
)
from .integration_manager import (
    BybitIntegrationManager, 
    IntegrationStatus, 
    load_config_from_env,
    create_integration_manager
)

__all__ = [
    # Main classes
    "BybitDemoClient",
    "BybitTradingExecutor", 
    "BybitWebSocketClient",
    "BybitIntegrationManager",
    
    # Data classes
    "TradingSignal",
    "TradeExecution",
    "MarketData",
    "OrderUpdate", 
    "PositionUpdate",
    "IntegrationStatus",
    
    # Enums
    "OrderStatus",
    "PositionSide", 
    "SubscriptionType",
    
    # Utility functions
    "format_bybit_symbol",
    "calculate_quantity_precision",
    "load_config_from_env",
    "create_integration_manager"
]