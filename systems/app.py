#!/usr/bin/env python3
"""
Production entry point for Kirston's Trading Algorithm
Organized for staging and production deployment
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.settings import get_config
from src.core.app_launcher import TradingSystemLauncher

def setup_logging(config):
    """Setup production logging"""
    log_dir = config.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'trading_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point"""
    config = get_config()
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting Trading System - Environment: {config.ENVIRONMENT}")
    
    try:
        launcher = TradingSystemLauncher(config)
        launcher.start()
    except KeyboardInterrupt:
        logger.info("👋 Trading System stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()