#!/usr/bin/env python3
"""
Simple ICT Enhanced System Test
==============================

Test the ICT Enhanced System components individually to identify issues.
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all ICT component imports."""
    
    print("🔬 Testing ICT Enhanced System Imports...")
    
    try:
        print("1. Testing Enhanced Order Block Detector...")
        from trading.order_block_detector import EnhancedOrderBlockDetector
        detector = EnhancedOrderBlockDetector()
        print("✅ Enhanced Order Block Detector - OK")
    except Exception as e:
        print(f"❌ Enhanced Order Block Detector - FAILED: {e}")
        return False
    
    try:
        print("2. Testing ICT Analyzer...")
        from trading.ict_analyzer import ICTAnalyzer
        analyzer = ICTAnalyzer()
        print("✅ ICT Analyzer - OK")
    except Exception as e:
        print(f"❌ ICT Analyzer - FAILED: {e}")
        return False
    
    try:
        print("3. Testing ICT Signal Processor...")
        from integrations.tradingview.ict_signal_processor import ICTSignalProcessor
        processor = ICTSignalProcessor()
        print("✅ ICT Signal Processor - OK")
    except Exception as e:
        print(f"❌ ICT Signal Processor - FAILED: {e}")
        return False
    
    try:
        print("4. Testing Main Controller...")
        from main import TradingAlgorithmController
        controller = TradingAlgorithmController()
        print("✅ Main Controller - OK")
    except Exception as e:
        print(f"❌ Main Controller - FAILED: {e}")
        return False
    
    print("🎉 All ICT Enhanced System imports successful!")
    return True

def main():
    """Test the ICT Enhanced System."""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                🔬 ICT ENHANCED SYSTEM TEST 🔬                   ║
║                                                                  ║
║  Testing all components before full system launch               ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    if test_imports():
        print("\n🚀 ICT Enhanced System is ready to launch on port 5001!")
        print("Run: python3 ict_enhanced_system.py --port 5001")
    else:
        print("\n❌ ICT Enhanced System has import issues that need to be resolved.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())