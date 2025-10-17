#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Real Trading Balance Persistence
====================================

Test that balance behaves like a real trading account - gains/losses persist across days
"""

from src.database.trading_database import TradingDatabase
from datetime import datetime, date, timedelta
import sqlite3
import os

def test_real_balance_behavior():
    """Test that balance acts like real trading account"""
    
    print("💰 TESTING REAL TRADING BALANCE BEHAVIOR")
    print("=" * 60)
    
    # Clean slate
    if os.path.exists("test_balance.db"):
        os.remove("test_balance.db")
    
    db = TradingDatabase("test_balance.db")
    
    print("📅 DAY 1: Start with $100, lose $25 in trading")
    
    # Day 1: Start with default balance, lose money
    db.increment_scan_count()  # Generate some activity
    db.increment_scan_count()
    
    # Add signal and execute losing trade
    signal_data = {
        'symbol': 'BTC/USDT',
        'signal_type': 'ORDER_BLOCK_LONG',
        'direction': 'LONG',
        'entry_price': 65000.0,
        'stop_loss': 64000.0,
        'take_profit': 67000.0,
        'confluence_score': 0.85,
        'status': 'ACTIVE'
    }
    
    db.add_signal(signal_data)
    
    # Simulate losing trade - balance goes down to $75
    db.update_balance(75.00, 'paper')
    
    day1_stats = db.get_daily_stats()
    print(f"   Day 1 End: Scans={day1_stats.get('scan_count')}, Balance=${day1_stats.get('paper_balance'):.2f}")
    
    print("\\n📅 DAY 2: Simulate new day, balance should start at $75")
    
    # Manually simulate new day by changing date in database
    tomorrow = date.today() + timedelta(days=1)
    
    with sqlite3.connect("test_balance.db") as conn:
        conn.execute(
            'UPDATE daily_stats SET date = ? WHERE date = ?',
            (tomorrow, date.today())
        )
        conn.commit()
    
    # Create new database instance to trigger new day reset
    db2 = TradingDatabase("test_balance.db")
    
    # This should trigger daily reset but PRESERVE balance
    day2_stats = db2.get_daily_stats()
    
    print(f"   Day 2 Start: Scans={day2_stats.get('scan_count')} (should be 0), Balance=${day2_stats.get('paper_balance'):.2f} (should be $75)")
    
    print("\\n📅 DAY 2: Win $40 in trading")
    
    # Day 2 activity: make some money
    db2.increment_scan_count()
    db2.add_signal(signal_data)
    
    # Winning trades - balance goes up to $115
    db2.update_balance(115.00, 'paper')
    
    day2_end_stats = db2.get_daily_stats()
    print(f"   Day 2 End: Scans={day2_end_stats.get('scan_count')}, Balance=${day2_end_stats.get('paper_balance'):.2f}")
    
    print("\\n📅 DAY 3: Simulate another new day, balance should start at $115")
    
    # Simulate day 3
    day_after_tomorrow = tomorrow + timedelta(days=1)
    
    with sqlite3.connect("test_balance.db") as conn:
        conn.execute(
            'UPDATE daily_stats SET date = ? WHERE date = ?',
            (day_after_tomorrow, tomorrow)
        )
        conn.commit()
    
    db3 = TradingDatabase("test_balance.db")
    day3_stats = db3.get_daily_stats()
    
    print(f"   Day 3 Start: Scans={day3_stats.get('scan_count')} (should be 0), Balance=${day3_stats.get('paper_balance'):.2f} (should be $115)")
    
    # Verify the results
    balance_progression_correct = (
        day1_stats.get('paper_balance') == 75.00 and  # Day 1: Lost $25
        day2_stats.get('paper_balance') == 75.00 and  # Day 2: Started with $75
        day2_end_stats.get('paper_balance') == 115.00 and  # Day 2: Gained $40  
        day3_stats.get('paper_balance') == 115.00  # Day 3: Started with $115
    )
    
    counter_reset_correct = (
        day2_stats.get('scan_count') == 0 and  # Day 2: Reset to 0
        day3_stats.get('scan_count') == 0  # Day 3: Reset to 0
    )
    
    print("\\n📊 HISTORICAL BALANCE TRACKING:")
    with sqlite3.connect("test_balance.db") as conn:
        cursor = conn.execute('SELECT date, scan_count, signals_generated, paper_balance FROM daily_stats ORDER BY date')
        rows = cursor.fetchall()
        
        for i, row in enumerate(rows, 1):
            date_str, scan_count, signals_gen, balance = row
            print(f"   Day {i} ({date_str}): Scans={scan_count}, Signals={signals_gen}, Balance=${balance:.2f}")
    
    # Cleanup
    os.remove("test_balance.db")
    
    return balance_progression_correct, counter_reset_correct

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                REAL TRADING BALANCE TEST SUITE                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    balance_ok, counter_ok = test_real_balance_behavior()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                        TEST RESULTS                             ║
╠══════════════════════════════════════════════════════════════════╣
║  💰 Balance Persistence: {'✅ WORKING' if balance_ok else '❌ FAILED'}                           ║
║  🔄 Counter Reset: {'✅ WORKING' if counter_ok else '❌ FAILED'}                                 ║
║                                                                  ║
║  🎯 REAL TRADING BEHAVIOR:                                       ║
║     • Balance: NEVER resets, accumulates all trading results    ║
║     • Losses: Persist across days (realistic trading)           ║
║     • Gains: Added to previous balance (realistic trading)      ║
║     • Counters: Reset to 0 each day (daily activity tracking)   ║
║                                                                  ║
║  🚀 BALANCE SYSTEM: {'REALISTIC!' if balance_ok and counter_ok else 'NEEDS FIXES!'}                                ║
╚══════════════════════════════════════════════════════════════════╝
""")