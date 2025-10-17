#!/usr/bin/env python3
"""
ICT Paper Trading Launcher
==========================

Simple launcher script to start ICT paper trading with all components.
This script connects the ICT monitor, signal processor, and dashboard
for comprehensive institutional trading validation.

Features:
✅ ICT Proactive Monitor
✅ ICT Signal Processing
✅ Paper Trading Execution
✅ ICT Dashboard (optional)
✅ Performance Tracking
✅ Comprehensive Results

Usage:
    python launch_ict_paper_trading.py
    python launch_ict_paper_trading.py --no-dashboard
    python launch_ict_paper_trading.py --balance 25000

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"ict_paper_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger(__name__)

# Import main controller
from main import TradingAlgorithmController

class ICTPaperTradingLauncher:
    """Simple launcher for ICT paper trading system."""
    
    def __init__(self):
        self.controller = None
        self.running = False
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info(f"Received signal {signum}, shutting down ICT paper trading...")
        self.running = False
        if self.controller:
            self.controller.system_running = False
    
    async def run_ict_paper_trading(self, enable_dashboard: bool = True, starting_balance: float = 10000.0):
        """Run ICT paper trading with all components."""
        try:
            logger.info("🎯 Starting ICT Paper Trading System")
            
            # Initialize controller
            self.controller = TradingAlgorithmController()
            self.running = True
            
            # Set starting balance if different from default
            if hasattr(self.controller, 'paper_portfolio'):
                self.controller.paper_portfolio['balance'] = starting_balance
            
            # Start ICT paper trading
            await self.controller.run_ict_paper_trading(enable_dashboard=enable_dashboard)
            
        except KeyboardInterrupt:
            logger.info("👋 ICT Paper Trading stopped by user")
        except Exception as e:
            logger.error(f"ICT Paper Trading error: {e}")
            raise
        finally:
            logger.info("🏁 ICT Paper Trading session ended")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ICT Paper Trading Launcher")
    
    parser.add_argument('--no-dashboard', action='store_true',
                       help='Disable ICT dashboard')
    parser.add_argument('--balance', type=float, default=10000.0,
                       help='Starting balance for paper trading')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║               🎯 ICT PAPER TRADING LAUNCHER 🎯                   ║
║                                                                  ║
║  🏦 Inner Circle Trader Methodology                             ║
║  📈 Institutional Smart Money Analysis                          ║
║  💰 Risk-Free Paper Trading Validation                          ║
║  🎯 Order Blocks • FVGs • Market Structure                      ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Initialize launcher
    launcher = ICTPaperTradingLauncher()
    
    try:
        # Run ICT paper trading
        asyncio.run(launcher.run_ict_paper_trading(
            enable_dashboard=not args.no_dashboard,
            starting_balance=args.balance
        ))
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()