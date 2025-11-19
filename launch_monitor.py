#!/usr/bin/env python3
"""
Safe launcher for ICT Enhanced Monitor
Handles errors gracefully and allows system to run even with $0 balance
"""

import sys
import os
import traceback
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Launch the ICT monitor with error handling"""
    try:
        # Import and run the monitor
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        logger.info("=" * 70)
        logger.info("🚀 LAUNCHING ICT TRADING MONITOR (SAFE MODE)")
        logger.info("=" * 70)
        logger.info("")
        logger.info("⚠️  This launcher handles errors gracefully")
        logger.info("✅ System will run even with $0 balance")
        logger.info("✅ Web interface will be accessible on http://localhost:5001")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        logger.info("")
        
        # Import the monitor module
        from core.monitors.ict_enhanced_monitor import ICTWebMonitor
        
        # Initialize and start monitor
        logger.info("📊 Initializing ICT Web Monitor...")
        logger.info("")
        logger.info("🌐 Starting web server on http://localhost:5001")
        logger.info("")
        
        monitor = ICTWebMonitor(port=5001)
        monitor.start()  # This will start the Flask app
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 70)
        logger.info("⏹️  System stopped by user (Ctrl+C)")
        logger.info("=" * 70)
        sys.exit(0)
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error("❌ FATAL ERROR - System crashed")
        logger.error("=" * 70)
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("")
        logger.error("=" * 70)
        logger.error("💡 Troubleshooting:")
        logger.error("1. Check if all dependencies are installed")
        logger.error("2. Verify .env file has correct configuration")
        logger.error("3. Check logs in /logs directory")
        logger.error("4. Try: python3 scripts/testing/test_bybit_connection.py")
        logger.error("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
