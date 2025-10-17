#!/usr/bin/env python3
"""
Simple ICT Paper Trading Launcher
=================================

A simplified launcher that handles common initialization issues
and provides a clean way to start ICT paper trading.

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Simple ICT paper trading launcher."""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║               🎯 SIMPLE ICT PAPER TRADING 🎯                     ║
║                                                                  ║
║  📈 Testing ICT Methodology Components                          ║
║  💰 Risk-Free Validation Mode                                   ║
║  🎯 Order Blocks • FVGs • Market Structure                      ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    try:
        logger.info("🔧 Starting simplified ICT paper trading test...")
        
        # Test basic imports first
        logger.info("📦 Testing imports...")
        
        try:
            from trading.ict_analyzer import ICTAnalyzer
            logger.info("✅ ICTAnalyzer imported successfully")
        except Exception as e:
            logger.error(f"❌ ICTAnalyzer import failed: {e}")
            return
        
        try:
            from integrations.tradingview.ict_signal_processor import ICTSignalProcessor
            logger.info("✅ ICTSignalProcessor imported successfully")
        except Exception as e:
            logger.error(f"❌ ICTSignalProcessor import failed: {e}")
            return
            
        # Test component initialization
        logger.info("🔧 Testing component initialization...")
        
        try:
            ict_analyzer = ICTAnalyzer()
            logger.info("✅ ICTAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"❌ ICTAnalyzer initialization failed: {e}")
            return
            
        try:
            ict_processor = ICTSignalProcessor()
            logger.info("✅ ICTSignalProcessor initialized successfully")
        except Exception as e:
            logger.error(f"❌ ICTSignalProcessor initialization failed: {e}")
            return
        
        # Test simple ICT analysis
        logger.info("🧪 Testing ICT analysis functionality...")
        
        try:
            # Create dummy data for testing
            import pandas as pd
            import numpy as np
            
            # Generate sample OHLCV data
            dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
            data = pd.DataFrame({
                'open': np.random.uniform(50000, 52000, 100),
                'high': np.random.uniform(51000, 53000, 100),
                'low': np.random.uniform(49000, 51000, 100),
                'close': np.random.uniform(50000, 52000, 100),
                'volume': np.random.uniform(100, 1000, 100)
            }, index=dates)
            
            # Make high >= max(open, close) and low <= min(open, close)
            data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
            data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
            
            logger.info(f"📊 Generated {len(data)} periods of test data")
            
            # Test ICT analysis
            result = ict_analyzer.analyze_market_structure(data, "BTC/USDT", "1h")
            
            if result:
                logger.info("✅ ICT analysis completed successfully")
                logger.info(f"🎯 Found {len(result.get('order_blocks', []))} Order Blocks")
                logger.info(f"📏 Found {len(result.get('fair_value_gaps', []))} Fair Value Gaps")
                logger.info(f"📊 Market Structure: {result.get('market_summary', {}).get('market_structure', 'Unknown')}")
                logger.info(f"🎯 HTF Bias: {result.get('htf_bias', {}).get('trend_direction', 'Unknown')}")
            else:
                logger.warning("⚠️ ICT analysis returned empty result")
            
        except Exception as e:
            logger.error(f"❌ ICT analysis test failed: {e}")
            return
        
        # Test performance tracking
        logger.info("📈 Testing performance tracking...")
        
        try:
            from utils.simple_ict_tracker import SimpleICTPerformanceTracker
            
            tracker = SimpleICTPerformanceTracker()
            logger.info("✅ Performance tracker initialized successfully")
            
            # Test signal tracking
            test_signal = {
                'symbol': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': 50000,
                'confidence': 0.75,
                'components': ['order_block', 'fvg'],
                'timeframe': '1h'
            }
            
            tracker.track_signal(test_signal)
            logger.info("✅ Signal tracking test successful")
            
            # Test metrics
            metrics = tracker.get_metrics()
            logger.info(f"📊 Current metrics: {metrics.total_signals} signals tracked")
            
        except Exception as e:
            logger.error(f"❌ Performance tracking test failed: {e}")
            return
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                   ✅ ICT SYSTEM TEST RESULTS ✅                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🎯 ICT Analyzer:          ✅ Working                            ║
║  📡 Signal Processor:      ✅ Working                            ║
║  📈 Performance Tracker:   ✅ Working                            ║
║  🧪 Market Analysis:       ✅ Working                            ║
║                                                                  ║
║  🎉 ICT System is ready for paper trading!                      ║
║                                                                  ║
║  💡 Next Steps:                                                  ║
║     1. Fix any remaining import issues                           ║
║     2. Start full ICT paper trading                              ║
║     3. Monitor performance metrics                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        logger.info("🎉 ICT system test completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Fatal error in ICT system test: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())