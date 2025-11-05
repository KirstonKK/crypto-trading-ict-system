#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')

from core.monitors.ict_enhanced_monitor import ICTEnhancedMonitor

def test_daily_pnl():
    """Test the fixed daily_pnl property"""
    print("🧪 Testing daily_pnl property after fix...")
    
    try:
        # Create monitor instance
        monitor = ICTEnhancedMonitor()
        
        # Test daily_pnl property
        daily_pnl = monitor.daily_pnl
        
        print("✅ Daily PnL from monitor.daily_pnl: ${daily_pnl:.2f}")
        
        if daily_pnl == -2.8:
            print("🎉 SUCCESS: Daily PnL calculation is now correct!")
        else:
            print("⚠️  Expected -$2.80, got ${daily_pnl:.2f}")
            
    except Exception:
        print("❌ Error checking daily PnL")

if __name__ == "__main__":
    test_daily_pnl()