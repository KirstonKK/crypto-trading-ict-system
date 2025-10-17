#!/usr/bin/env python3
"""
ICT-Bybit Signal Bridge
======================

This module bridges ICT Enhanced Trading Monitor signals with Bybit demo trading.
It polls the ICT monitor for new signals and executes them as real orders on Bybit testnet.

Key Features:
- Real-time signal monitoring from ICT Enhanced Monitor
- Automatic trade execution on Bybit demo account
- Risk management and position sizing
- Performance tracking and comparison
- Model training data collection

Usage:
    python ict_bybit_bridge.py [--auto-trading] [--dry-run]
"""

import asyncio
import logging
import json
import sys
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp

# Add the bybit_integration directory to the path
sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')

from bybit_integration import BybitIntegrationManager, create_integration_manager
from bybit_integration.config import load_config_from_env, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ict_bybit_bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ICTBybitBridge:
    """
    Bridge between ICT Enhanced Trading Monitor and Bybit demo trading
    
    This class:
    1. Monitors ICT Enhanced Monitor for new signals
    2. Validates signals for execution
    3. Executes approved signals on Bybit testnet
    4. Tracks performance and collects training data
    5. Compares real execution vs paper trading
    """
    
    def __init__(self, auto_trading: bool = False, dry_run: bool = False):
        """
        Initialize the ICT-Bybit bridge
        
        Args:
            auto_trading: Enable automatic trade execution
            dry_run: Log trades but don't execute (testing mode)
        """
        self.auto_trading = auto_trading
        self.dry_run = dry_run
        self.running = False
        
        # Integration components
        self.bybit_manager = None
        self.ict_session = None
        
        # Signal tracking
        self.last_signal_id = None
        self.processed_signals = set()
        self.signal_stats = {
            "total_received": 0,
            "total_executed": 0,
            "total_skipped": 0,
            "execution_rate": 0.0
        }
        
        # Performance tracking
        self.trade_comparisons = []
        self.paper_trades = {}  # Track paper trading results
        self.demo_trades = {}   # Track demo trading results
        
        logger.info("🌉 ICT-Bybit Bridge initialized")
        logger.info(f"   Auto Trading: {'ON' if auto_trading else 'OFF'}")
        logger.info(f"   Dry Run Mode: {'ON' if dry_run else 'OFF'}")

    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🔧 Initializing ICT-Bybit bridge...")
            
            # Load and validate configuration
            config = load_config_from_env()
            is_valid, errors = validate_config(config)
            
            if not is_valid:
                logger.error("❌ Configuration validation failed:")
                for error in errors:
                    logger.error(f"   - {error}")
                raise Exception("Invalid configuration")
            
            # Initialize Bybit integration manager
            if not self.dry_run:
                self.bybit_manager = BybitIntegrationManager(
                    api_key=config.bybit.api_key,
                    api_secret=config.bybit.api_secret,
                    ict_monitor_url=config.ict.monitor_url,
                    testnet=config.bybit.testnet,
                    auto_trading=self.auto_trading
                )
                
                await self.bybit_manager.initialize()
                logger.info("✅ Bybit integration initialized")
            else:
                logger.info("🧪 Dry run mode - Bybit integration simulated")
            
            # Create HTTP session for ICT monitor
            self.ict_session = aiohttp.ClientSession()
            
            # Test ICT monitor connection
            await self._test_ict_connection()
            
            logger.info("✅ Bridge initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Bridge initialization failed: {e}")
            raise

    async def _test_ict_connection(self):
        """Test connection to ICT Enhanced Monitor"""
        try:
            async with self.ict_session.get("http://localhost:5001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ ICT Monitor connection successful")
                    logger.info(f"   Status: {data.get('status', 'Unknown')}")
                    logger.info(f"   Signals Today: {data.get('signals_today', 0)}")
                    logger.info(f"   Scan Count: {data.get('scan_count', 0)}")
                else:
                    raise Exception(f"ICT Monitor returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ ICT Monitor connection failed: {e}")
            logger.error("   Make sure ICT Enhanced Trading Monitor is running on port 5001")
            raise

    async def monitor_ict_signals(self):
        """Main loop to monitor ICT signals"""
        logger.info("📡 Starting ICT signal monitoring...")
        
        while self.running:
            try:
                # Get latest signals from ICT monitor
                async with self.ict_session.get("http://localhost:5001/api/signals/latest") as response:
                    if response.status == 200:
                        signals_data = await response.json()
                        signals = signals_data.get('signals', [])
                        
                        # Process new signals
                        for signal in signals:
                            await self._process_signal(signal)
                
                # Update statistics
                await self._update_signal_stats()
                
                # Wait before next poll
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Error monitoring ICT signals: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def _process_signal(self, signal: Dict[str, Any]):
        """Process a single ICT signal"""
        try:
            signal_id = signal.get('id') or signal.get('signal_id')
            
            # Skip if already processed
            if signal_id in self.processed_signals:
                return
            
            self.processed_signals.add(signal_id)
            self.signal_stats["total_received"] += 1
            
            logger.info(f"📡 New ICT Signal: {signal.get('symbol')} {signal.get('action')}")
            logger.info(f"   Confidence: {signal.get('confidence', 0)*100:.1f}%")
            logger.info(f"   Price: ${signal.get('entry_price', 0):,.4f}")
            logger.info(f"   Confluences: {len(signal.get('confluence_factors', []))}")
            
            # Validate signal for execution
            if await self._validate_signal_for_execution(signal):
                
                if self.dry_run:
                    # Dry run mode - just log
                    await self._log_simulated_execution(signal)
                else:
                    # Execute on Bybit
                    await self._execute_signal_on_bybit(signal)
                    
                self.signal_stats["total_executed"] += 1
                
            else:
                self.signal_stats["total_skipped"] += 1
                logger.info("🚫 Signal skipped (validation failed)")
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")

    async def _validate_signal_for_execution(self, signal: Dict[str, Any]) -> bool:
        """Validate if signal should be executed"""
        try:
            # Check confidence threshold
            confidence = signal.get('confidence', 0)
            if confidence < 0.6:  # 60% minimum
                logger.debug(f"⚠️  Signal confidence {confidence:.1%} below threshold")
                return False
            
            # Check required fields
            required_fields = ['symbol', 'action', 'entry_price', 'confidence']
            for field in required_fields:
                if field not in signal or signal[field] is None:
                    logger.debug(f"⚠️  Missing required field: {field}")
                    return False
            
            # Check action validity
            action = signal.get('action', '').upper()
            if action not in ['BUY', 'SELL']:
                logger.debug(f"⚠️  Invalid action: {action}")
                return False
            
            # Check confluence factors
            confluences = signal.get('confluence_factors', [])
            if len(confluences) < 2:
                logger.debug(f"⚠️  Insufficient confluence factors: {len(confluences)}")
                return False
            
            # Check symbol format
            symbol = signal.get('symbol', '')
            if not symbol or len(symbol) < 3:
                logger.debug(f"⚠️  Invalid symbol: {symbol}")
                return False
            
            logger.debug("✅ Signal validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating signal: {e}")
            return False

    async def _log_simulated_execution(self, signal: Dict[str, Any]):
        """Log simulated execution for dry run mode"""
        logger.info("🧪 DRY RUN - Simulated Execution:")
        logger.info(f"   Symbol: {signal.get('symbol')}")
        logger.info(f"   Action: {signal.get('action')}")
        logger.info(f"   Price: ${signal.get('entry_price', 0):,.4f}")
        logger.info(f"   Confidence: {signal.get('confidence', 0)*100:.1f}%")
        logger.info(f"   Stop Loss: ${signal.get('stop_loss', 0):,.4f}")
        logger.info(f"   Take Profit: ${signal.get('take_profit', 0):,.4f}")
        logger.info("   Trade would be executed on Bybit testnet")

    async def _execute_signal_on_bybit(self, signal: Dict[str, Any]):
        """Execute signal on Bybit demo account"""
        try:
            logger.info("🚀 Executing signal on Bybit...")
            
            # Convert ICT signal format to Bybit format
            bybit_signal = self._convert_signal_format(signal)
            
            # Execute through Bybit integration manager
            execution = await self.bybit_manager.manual_trade(bybit_signal)
            
            if execution:
                logger.info("✅ Signal executed successfully on Bybit")
                logger.info(f"   Order ID: {execution.order_id}")
                logger.info(f"   Quantity: {execution.quantity:.6f}")
                logger.info(f"   Entry Price: ${execution.entry_price:.4f}")
                
                # Store for performance comparison
                await self._record_demo_trade(signal, execution)
                
            else:
                logger.warning("❌ Signal execution failed on Bybit")
                
        except Exception as e:
            logger.error(f"❌ Error executing signal on Bybit: {e}")

    def _convert_signal_format(self, ict_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ICT signal format to Bybit-compatible format"""
        return {
            "symbol": ict_signal.get('symbol', ''),
            "action": ict_signal.get('action', ''),
            "confidence": ict_signal.get('confidence', 0),
            "price": ict_signal.get('entry_price', 0),
            "timestamp": ict_signal.get('timestamp', datetime.now().isoformat()),
            "confluence_factors": ict_signal.get('confluence_factors', []),
            "stop_loss": ict_signal.get('stop_loss'),
            "take_profit": ict_signal.get('take_profit'),
            "signal_id": ict_signal.get('id') or ict_signal.get('signal_id'),
            "session_multiplier": ict_signal.get('session_multiplier', 1.0),
            "market_session": ict_signal.get('market_session', 'Unknown')
        }

    async def _record_demo_trade(self, signal: Dict[str, Any], execution):
        """Record demo trade for performance tracking"""
        try:
            signal_id = signal.get('id') or signal.get('signal_id')
            
            self.demo_trades[signal_id] = {
                "signal": signal,
                "execution": execution,
                "timestamp": datetime.now(),
                "status": "active"
            }
            
            logger.debug(f"📊 Demo trade recorded: {signal_id}")
            
        except Exception as e:
            logger.error(f"❌ Error recording demo trade: {e}")

    async def _update_signal_stats(self):
        """Update signal processing statistics"""
        try:
            total = self.signal_stats["total_received"]
            executed = self.signal_stats["total_executed"]
            
            if total > 0:
                self.signal_stats["execution_rate"] = (executed / total) * 100
            
            # Log stats every 10 signals
            if total > 0 and total % 10 == 0:
                logger.info("📊 Signal Processing Stats:")
                logger.info(f"   Total Received: {total}")
                logger.info(f"   Total Executed: {executed}")
                logger.info(f"   Total Skipped: {self.signal_stats['total_skipped']}")
                logger.info(f"   Execution Rate: {self.signal_stats['execution_rate']:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ Error updating signal stats: {e}")

    async def compare_performance(self):
        """Compare paper trading vs demo trading performance"""
        try:
            logger.info("📊 Performance Comparison:")
            logger.info("=" * 50)
            
            # Get paper trading data from ICT monitor
            async with self.ict_session.get("http://localhost:5001/api/data") as response:
                if response.status == 200:
                    data = await response.json()
                    paper_balance = data.get('paper_balance', 100.0)
                    paper_signals = data.get('total_signals', 0)
                    
                    logger.info(f"📈 Paper Trading:")
                    logger.info(f"   Balance: ${paper_balance:.2f}")
                    logger.info(f"   Total Signals: {paper_signals}")
            
            # Get demo trading data from Bybit
            if self.bybit_manager and not self.dry_run:
                status = self.bybit_manager.get_status()
                performance = status.get("performance", {})
                
                logger.info(f"🏪 Demo Trading:")
                logger.info(f"   Total PnL: {performance.get('total_pnl', '$0.00')}")
                logger.info(f"   Win Rate: {performance.get('win_rate', '0.0%')}")
                logger.info(f"   Active Positions: {performance.get('active_positions', 0)}")
            
            # Signal processing stats
            logger.info(f"🌉 Bridge Performance:")
            logger.info(f"   Signals Processed: {self.signal_stats['total_received']}")
            logger.info(f"   Execution Rate: {self.signal_stats['execution_rate']:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Error comparing performance: {e}")

    async def run(self):
        """Main execution loop"""
        try:
            logger.info("🚀 Starting ICT-Bybit Bridge")
            logger.info("=" * 50)
            
            self.running = True
            
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self.monitor_ict_signals()),
            ]
            
            # Start Bybit manager if not in dry run mode
            if not self.dry_run and self.bybit_manager:
                tasks.append(asyncio.create_task(self.bybit_manager.start()))
            
            # Performance comparison every 5 minutes
            async def periodic_comparison():
                while self.running:
                    await asyncio.sleep(300)  # 5 minutes
                    await self.compare_performance()
            
            tasks.append(asyncio.create_task(periodic_comparison()))
            
            # Run all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Bridge runtime error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown"""
        try:
            logger.info("🛑 Shutting down ICT-Bybit Bridge...")
            
            self.running = False
            
            # Close HTTP session
            if self.ict_session:
                await self.ict_session.close()
            
            # Stop Bybit manager
            if self.bybit_manager:
                await self.bybit_manager.stop()
            
            # Final performance report
            await self.compare_performance()
            
            logger.info("✅ Bridge shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ICT-Bybit Signal Bridge")
    parser.add_argument(
        "--auto-trading", 
        action="store_true", 
        help="Enable automatic trade execution"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Simulate trades without actual execution"
    )
    
    args = parser.parse_args()
    
    # Create bridge instance
    bridge = ICTBybitBridge(
        auto_trading=args.auto_trading,
        dry_run=args.dry_run
    )
    
    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        asyncio.create_task(bridge.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and run
        await bridge.initialize()
        await bridge.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    """
    ICT-Bybit Signal Bridge
    
    This script connects your ICT Enhanced Trading Monitor with Bybit demo trading.
    
    Usage modes:
    1. Dry run (testing): python ict_bybit_bridge.py --dry-run
    2. Demo trading: python ict_bybit_bridge.py --auto-trading
    3. Signal monitoring only: python ict_bybit_bridge.py
    
    Prerequisites:
    1. ICT Enhanced Trading Monitor running on port 5001
    2. Bybit testnet credentials in .env file
    3. Dependencies installed (aiohttp, websockets, cryptography)
    """
    
    print("🌉 ICT-Bybit Signal Bridge")
    print("==========================")
    print()
    print("This bridge connects ICT Enhanced Trading Monitor")
    print("with Bybit demo trading for signal validation.")
    print()
    print("Modes:")
    print("  --dry-run      : Test mode (no actual trades)")
    print("  --auto-trading : Execute trades automatically")
    print("  (no flags)     : Monitor signals only")
    print()
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(130)