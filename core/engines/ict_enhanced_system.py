#!/usr/bin/env python3
"""
ICT Enhanced System Launcher - Port 5001
========================================

Complete ICT system with Enhanced Order Blocks, real-time monitoring,
institutional analysis dashboard, and comprehensive signal processing.

Features:
✅ Enhanced Order Blocks (EOB) with institutional validation
✅ ICT Proactive Monitor with real-time analysis
✅ ICT Signal Processing with confluence scoring
✅ ICT Dashboard on port 5001
✅ Webhook Server for TradingView integration
✅ Performance Tracking and Analytics
✅ Comprehensive ICT methodology validation

Author: GitHub Copilot Trading Algorithm
Date: September 2025
Version: 1.0 - CodeRabbit Review Target
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"ict_enhanced_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger(__name__)

class ICTEnhancedSystemLauncher:
    """Enhanced ICT System Launcher with comprehensive monitoring."""
    
    def __init__(self):
        """Initialize the enhanced ICT system."""
        self.system_running = False
        self.components = {}
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🎯 ICT Enhanced System Launcher initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info(f"Received signal {signum}, shutting down ICT Enhanced System...")
        self.system_running = False
    
    async def launch_ict_enhanced_system(self, port: int = 5001):
        """Launch complete ICT Enhanced System on specified port."""
        try:
            logger.info("🚀 Starting ICT Enhanced System with EOBs...")
            
            print("""
╔══════════════════════════════════════════════════════════════════╗
║               🎯 ICT ENHANCED SYSTEM LAUNCHER 🎯                 ║
║                                                                  ║
║  🏦 Enhanced Order Blocks (EOB) Detection                       ║
║  📈 Institutional Smart Money Analysis                          ║
║  🎯 Real-time ICT Monitor & Dashboard                           ║
║  📡 TradingView Webhook Integration                              ║
║  💰 Comprehensive Performance Tracking                          ║
║                                                                  ║
║  🌐 System URL: http://localhost:{port}                         ║
╚══════════════════════════════════════════════════════════════════╝
""")
            
            # Initialize and run the main controller in webhook mode
            from src.core.main import TradingAlgorithmController
            
            controller = TradingAlgorithmController()
            self.components['controller'] = controller
            
            logger.info(f"✅ Starting ICT Enhanced System on port {port}")
            
            # Run webhook mode which includes all ICT components
            await controller.run_webhook_mode(port=port)
            
        except KeyboardInterrupt:
            logger.info("👋 ICT Enhanced System stopped by user")
        except Exception as e:
            logger.error(f"💥 ICT Enhanced System error: {e}")
            raise
        finally:
            logger.info("🏁 ICT Enhanced System session ended")

def main():
    """Main entry point for ICT Enhanced System."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ICT Enhanced System Launcher")
    
    parser.add_argument('--port', type=int, default=5001,
                       help='Port for webhook server and dashboard')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Initialize launcher
    launcher = ICTEnhancedSystemLauncher()
    
    try:
        # Run ICT Enhanced System
        asyncio.run(launcher.launch_ict_enhanced_system(port=args.port))
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()