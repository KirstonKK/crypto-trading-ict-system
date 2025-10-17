#!/usr/bin/env python3
"""
Bybit Integration Example
========================

Example script demonstrating how to integrate ICT Enhanced Trading Monitor
with Bybit demo trading environment.

This example shows:
1. Setting up the integration manager
2. Connecting to Bybit testnet
3. Subscribing to real-time data
4. Processing ICT signals
5. Managing trades and positions
6. Monitoring performance

Usage:
    python example_usage.py [--auto-trading] [--config-file .env]

Requirements:
    - Bybit testnet account with API credentials
    - ICT Enhanced Trading Monitor running on localhost:5001
    - Environment variables configured (see .env.template)
"""

import asyncio
import logging
import argparse
import signal
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Import our Bybit integration components
from bybit_integration import (
    BybitIntegrationManager,
    create_integration_manager,
    load_config_from_env
)
from bybit_integration.config import load_config_from_env as load_full_config, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bybit_integration_example.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class IntegrationExample:
    """
    Example integration setup and management
    """
    
    def __init__(self, auto_trading: bool = False):
        self.auto_trading = auto_trading
        self.manager = None
        self.running = False
        self.stats = {
            "signals_received": 0,
            "trades_executed": 0,
            "profitable_trades": 0,
            "total_pnl": 0.0,
            "start_time": datetime.now()
        }
        
        # Tracked symbols for demo
        self.tracked_symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"]
        
    async def setup(self):
        """Initialize the integration manager"""
        try:
            logger.info("🔧 Setting up Bybit integration...")
            
            # Load configuration
            config = load_full_config()
            is_valid, errors = validate_config(config)
            
            if not is_valid:
                logger.error("❌ Configuration validation failed:")
                for error in errors:
                    logger.error(f"   - {error}")
                raise Exception("Invalid configuration")
            
            # Create integration manager
            self.manager = BybitIntegrationManager(
                api_key=config.bybit.api_key,
                api_secret=config.bybit.api_secret,
                ict_monitor_url=config.ict.monitor_url,
                testnet=config.bybit.testnet,
                auto_trading=self.auto_trading
            )
            
            # Initialize the manager
            await self.manager.initialize()
            
            # Setup callbacks
            self.manager.add_signal_callback(self.on_signal_received)
            self.manager.add_trade_callback(self.on_trade_executed)
            
            # Subscribe to real-time data for tracked symbols
            for symbol in self.tracked_symbols:
                self.manager.subscribe_to_symbol(symbol)
            
            logger.info("✅ Integration setup completed")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

    async def on_signal_received(self, event_type: str, signal_data: Dict[str, Any]):
        """Handle ICT signal events"""
        try:
            if event_type == "new_signal":
                self.stats["signals_received"] += 1
                
                symbol = signal_data.get("symbol", "Unknown")
                action = signal_data.get("action", "Unknown")
                confidence = signal_data.get("confidence", 0.0)
                confluences = signal_data.get("confluence_factors", [])
                
                logger.info(f"📡 ICT Signal Received:")
                logger.info(f"   Symbol: {symbol}")
                logger.info(f"   Action: {action}")
                logger.info(f"   Confidence: {confidence:.1%}")
                logger.info(f"   Confluences: {', '.join(confluences)}")
                
                # Log signal statistics
                await self.log_signal_stats()
                
            elif event_type == "price_update":
                # Handle real-time price updates
                symbol = signal_data.get("symbol", "")
                price = signal_data.get("price", 0.0)
                logger.debug(f"💰 {symbol}: ${price:.4f}")
                
        except Exception as e:
            logger.error(f"❌ Error handling signal: {e}")

    async def on_trade_executed(self, event_type: str, trade_data: Dict[str, Any]):
        """Handle trade execution events"""
        try:
            if event_type == "trade_executed":
                self.stats["trades_executed"] += 1
                
                symbol = trade_data.get("symbol", "Unknown")
                side = trade_data.get("side", "Unknown")
                quantity = trade_data.get("quantity", 0.0)
                price = trade_data.get("entry_price", 0.0)
                
                logger.info(f"🚀 Trade Executed:")
                logger.info(f"   Symbol: {symbol}")
                logger.info(f"   Side: {side}")
                logger.info(f"   Quantity: {quantity:.6f}")
                logger.info(f"   Price: ${price:.4f}")
                
                # Update statistics
                if trade_data.get("pnl", 0) > 0:
                    self.stats["profitable_trades"] += 1
                
                self.stats["total_pnl"] += trade_data.get("pnl", 0.0)
                
                await self.log_trading_stats()
                
        except Exception as e:
            logger.error(f"❌ Error handling trade: {e}")

    async def log_signal_stats(self):
        """Log current signal statistics"""
        uptime = datetime.now() - self.stats["start_time"]
        signals_per_hour = self.stats["signals_received"] / max(uptime.total_seconds() / 3600, 0.01)
        
        logger.info(f"📊 Signal Stats: {self.stats['signals_received']} total, {signals_per_hour:.1f}/hour")

    async def log_trading_stats(self):
        """Log current trading statistics"""
        if self.stats["trades_executed"] > 0:
            win_rate = (self.stats["profitable_trades"] / self.stats["trades_executed"]) * 100
            avg_pnl = self.stats["total_pnl"] / self.stats["trades_executed"]
            
            logger.info(f"💹 Trading Stats:")
            logger.info(f"   Trades: {self.stats['trades_executed']}")
            logger.info(f"   Win Rate: {win_rate:.1f}%")
            logger.info(f"   Total PnL: ${self.stats['total_pnl']:.2f}")
            logger.info(f"   Avg PnL: ${avg_pnl:.2f}")

    async def run_status_monitor(self):
        """Run periodic status monitoring"""
        while self.running:
            try:
                # Get system status
                status = self.manager.get_status()
                
                # Log system health
                system_status = status.get("system", {})
                performance = status.get("performance", {})
                
                logger.info("🔍 System Status:")
                logger.info(f"   Bybit: {'✅' if system_status.get('bybit_connected') else '❌'}")
                logger.info(f"   WebSocket: {'✅' if system_status.get('websocket_connected') else '❌'}")
                logger.info(f"   ICT Monitor: {'✅' if system_status.get('ict_monitor_connected') else '❌'}")
                logger.info(f"   Active Positions: {system_status.get('active_positions', 0)}")
                logger.info(f"   Total Signals: {system_status.get('total_signals_received', 0)}")
                logger.info(f"   Auto Trading: {'ON' if status.get('auto_trading') else 'OFF'}")
                
                # Wait 5 minutes before next status check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Status monitoring error: {e}")
                await asyncio.sleep(60)

    async def demonstrate_manual_trading(self):
        """Demonstrate manual trade execution"""
        if not self.auto_trading:
            logger.info("📝 Demonstrating manual trade execution...")
            
            # Example signal data
            demo_signal = {
                "symbol": "BTCUSDT",
                "action": "BUY",
                "confidence": 0.75,
                "price": 45000.0,
                "timestamp": datetime.now().isoformat(),
                "confluence_factors": ["FVG", "Order Block", "Premium Discount"],
                "stop_loss": 44100.0,
                "take_profit": 46800.0,
                "signal_id": f"demo_{int(datetime.now().timestamp())}",
                "session_multiplier": 1.2,
                "market_session": "London"
            }
            
            logger.info("🔧 Executing demo signal manually...")
            execution = await self.manager.manual_trade(demo_signal)
            
            if execution:
                logger.info("✅ Demo trade executed successfully")
            else:
                logger.info("❌ Demo trade execution failed")

    async def run(self):
        """Main execution loop"""
        try:
            logger.info("🚀 Starting Bybit Integration Example")
            logger.info(f"   Auto Trading: {'ENABLED' if self.auto_trading else 'DISABLED'}")
            logger.info(f"   Tracked Symbols: {', '.join(self.tracked_symbols)}")
            
            self.running = True
            
            # Start the integration manager
            manager_task = asyncio.create_task(self.manager.start())
            
            # Start status monitoring
            monitor_task = asyncio.create_task(self.run_status_monitor())
            
            # Demonstrate manual trading if auto-trading is disabled
            if not self.auto_trading:
                demo_task = asyncio.create_task(self.demonstrate_manual_trading())
                await demo_task
            
            # Wait for both tasks
            await asyncio.gather(manager_task, monitor_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Runtime error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown"""
        try:
            logger.info("🛑 Shutting down integration...")
            
            self.running = False
            
            if self.manager:
                await self.manager.stop()
            
            # Final statistics
            logger.info("📊 Final Statistics:")
            logger.info(f"   Signals Received: {self.stats['signals_received']}")
            logger.info(f"   Trades Executed: {self.stats['trades_executed']}")
            logger.info(f"   Total PnL: ${self.stats['total_pnl']:.2f}")
            
            uptime = datetime.now() - self.stats['start_time']
            logger.info(f"   Runtime: {uptime}")
            
            logger.info("✅ Shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Bybit Integration Example")
    parser.add_argument(
        "--auto-trading", 
        action="store_true", 
        help="Enable automatic trade execution"
    )
    parser.add_argument(
        "--config-file", 
        default=".env", 
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    # Create example instance
    example = IntegrationExample(auto_trading=args.auto_trading)
    
    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        asyncio.create_task(example.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Setup and run
        await example.setup()
        await example.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    """
    Run the example:
    
    1. First, ensure your environment is set up:
       cp .env.template .env
       # Edit .env with your Bybit testnet credentials
    
    2. Start ICT Enhanced Trading Monitor:
       python ict_enhanced_monitor.py
    
    3. Run this example:
       # Paper trading mode (signals logged only)
       python example_usage.py
       
       # Auto-trading mode (signals executed automatically)
       python example_usage.py --auto-trading
    """
    
    # Print usage information
    print("🔗 Bybit Integration Example")
    print("============================")
    print()
    print("Prerequisites:")
    print("1. Bybit testnet account with API credentials")
    print("2. ICT Enhanced Trading Monitor running")
    print("3. Environment variables configured")
    print()
    print("Usage:")
    print("  python example_usage.py                 # Paper trading mode")
    print("  python example_usage.py --auto-trading  # Live trading mode")
    print()
    
    # Run the example
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(130)