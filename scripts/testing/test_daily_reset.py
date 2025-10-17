#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Reset Functionality Test
=============================

Test that the system correctly resets daily counters (scan_count, signals_generated) 
to 0 for new days while preserving the account balance.
"""

from src.database.trading_database import TradingDatabase
from datetime import datetime, date, timedelta
import sqlite3
import json

def test_daily_reset_functionality():
    """Test daily reset preserves balance but resets counters"""
    
    print("🌅 TESTING DAILY RESET FUNCTIONALITY")
    print("=" * 60)
    
    # Clean slate
    import os
    if os.path.exists("test_daily_reset.db"):
        os.remove("test_daily_reset.db")
    
    # Initialize database
    db = TradingDatabase("test_daily_reset.db")
    
    print("1️⃣ DAY 1 - SIMULATING TRADING ACTIVITY...")
    
    # Simulate Day 1 trading activity
    db.increment_scan_count()  # 1
    db.increment_scan_count()  # 2
    db.increment_scan_count()  # 3
    
    # Add signals
    signal_data = {
        'symbol': 'BTC/USDT',
        'signal_type': 'ORDER_BLOCK_LONG',
        'direction': 'LONG',
        'entry_price': 65000.0,
        'stop_loss': 64000.0,
        'take_profit': 67000.0,
        'confluence_score': 0.85,
        'timeframes': ['5m', '15m'],
        'ict_concepts': ['ORDER_BLOCKS'],
        'session': 'LONDON',
        'market_regime': 'TRENDING',
        'directional_bias': 'BULLISH',
        'signal_strength': 'HIGH',
        'status': 'ACTIVE'
    }
    
    signal_id_1 = db.add_signal(signal_data)  # signals_generated = 1
    signal_id_2 = db.add_signal(signal_data)  # signals_generated = 2\n    \n    # Update balance (simulate trading results)\n    db.update_balance(85.50, 'paper')  # Lost some money\n    \n    # Get Day 1 stats\n    day1_stats = db.get_daily_stats()\n    print(f\"   📊 Day 1 End Stats:\")\n    print(f\"     🔢 Scan Count: {day1_stats.get('scan_count', 0)}\")\n    print(f\"     📈 Signals Generated: {day1_stats.get('signals_generated', 0)}\")\n    print(f\"     💰 Paper Balance: ${day1_stats.get('paper_balance', 100):.2f}\")\n    \n    print(\"\\n2️⃣ SIMULATING DAY 2 - DIRECT DATABASE DATE MANIPULATION...\")\n    \n    # Manually create a \"tomorrow\" entry to simulate day change\n    tomorrow = date.today() + timedelta(days=1)\n    \n    # Manually trigger the reset by calling get_daily_stats with manipulated date\n    # First, we'll modify the database date check method temporarily\n    original_date = datetime.now().date()\n    \n    # Insert tomorrow's date manually to test reset\n    with sqlite3.connect(\"test_daily_reset.db\") as conn:\n        conn.execute(\n            'UPDATE daily_stats SET date = ? WHERE date = ?',\n            (tomorrow, original_date)\n        )\n        conn.commit()\n    \n    # Now create a new database instance to test reset for \"today\"\n    db2 = TradingDatabase(\"test_daily_reset.db\")\n    \n    # This should trigger the daily reset logic\n    day2_stats = db2.get_daily_stats()\n    \n    print(f\"   📊 Day 2 Reset Stats:\")\n    print(f\"     🔢 Scan Count: {day2_stats.get('scan_count', 0)} (should be 0)\")\n    print(f\"     📈 Signals Generated: {day2_stats.get('signals_generated', 0)} (should be 0)\")\n    print(f\"     💰 Paper Balance: ${day2_stats.get('paper_balance', 100):.2f} (should be $85.50)\")\n    \n    print(\"\\n3️⃣ TESTING DAY 2 ACTIVITY...\")\n    \n    # Add some Day 2 activity\n    db2.increment_scan_count()  # Should be 1\n    db2.increment_scan_count()  # Should be 2\n    \n    signal_data['symbol'] = 'ETH/USDT'\n    signal_id_3 = db2.add_signal(signal_data)  # Should be signals_generated = 1\n    \n    # Update balance again\n    db2.update_balance(95.75, 'paper')  # Made some money back\n    \n    day2_after_activity = db2.get_daily_stats()\n    print(f\"   📊 Day 2 After Activity:\")\n    print(f\"     🔢 Scan Count: {day2_after_activity.get('scan_count', 0)} (should be 2)\")\n    print(f\"     📈 Signals Generated: {day2_after_activity.get('signals_generated', 0)} (should be 1)\")\n    print(f\"     💰 Paper Balance: ${day2_after_activity.get('paper_balance', 100):.2f} (should be $95.75)\")\n    \n    print(\"\\n4️⃣ VERIFYING HISTORICAL DATA PRESERVATION...\")\n    \n    # Check that historical data is still preserved\n    with sqlite3.connect(\"test_daily_reset.db\") as conn:\n        cursor = conn.execute('SELECT date, scan_count, signals_generated, paper_balance FROM daily_stats ORDER BY date')\n        rows = cursor.fetchall()\n        \n        print(f\"   📋 Historical Records:\")\n        for i, row in enumerate(rows, 1):\n            date_str, scan_count, signals_gen, balance = row\n            print(f\"     Day {i} ({date_str}): Scans={scan_count}, Signals={signals_gen}, Balance=${balance:.2f}\")\n    \n    # Verify reset worked correctly\n    reset_success = (\n        day2_stats.get('scan_count', -1) == 0 and\n        day2_stats.get('signals_generated', -1) == 0 and\n        day2_stats.get('paper_balance', 0) == 85.50\n    )\n    \n    activity_success = (\n        day2_after_activity.get('scan_count', -1) == 2 and\n        day2_after_activity.get('signals_generated', -1) == 1 and\n        day2_after_activity.get('paper_balance', 0) == 95.75\n    )\n    \n    # Cleanup\n    os.remove(\"test_daily_reset.db\")\n    \n    return reset_success, activity_success\n\ndef test_fresh_start_new_day():\n    \"\"\"Test that completely fresh start on new day uses default balance\"\"\"\n    \n    print(\"\\n5️⃣ TESTING COMPLETELY FRESH START...\")\n    \n    # Clean slate - no previous data at all\n    import os\n    if os.path.exists(\"test_fresh_start.db\"):\n        os.remove(\"test_fresh_start.db\")\n    \n    db = TradingDatabase(\"test_fresh_start.db\")\n    \n    # Get stats (should be defaults)\n    fresh_stats = db.get_daily_stats()\n    \n    print(f\"   📊 Fresh Start Stats:\")\n    print(f\"     🔢 Scan Count: {fresh_stats.get('scan_count', 0)} (should be 0)\")\n    print(f\"     📈 Signals Generated: {fresh_stats.get('signals_generated', 0)} (should be 0)\")\n    print(f\"     💰 Paper Balance: ${fresh_stats.get('paper_balance', 100):.2f} (should be $100.00)\")\n    \n    fresh_start_success = (\n        fresh_stats.get('scan_count', -1) == 0 and\n        fresh_stats.get('signals_generated', -1) == 0 and\n        fresh_stats.get('paper_balance', 0) == 100.0\n    )\n    \n    # Cleanup\n    os.remove(\"test_fresh_start.db\")\n    \n    return fresh_start_success\n\nif __name__ == \"__main__\":\n    print(\"\"\"\n╔══════════════════════════════════════════════════════════════════╗\n║                    DAILY RESET TEST SUITE                       ║\n╚══════════════════════════════════════════════════════════════════╝\n\"\"\")\n    \n    # Test daily reset functionality\n    reset_ok, activity_ok = test_daily_reset_functionality()\n    fresh_ok = test_fresh_start_new_day()\n    \n    print(f\"\"\"\n╔══════════════════════════════════════════════════════════════════╗\n║                        TEST RESULTS                             ║\n╠══════════════════════════════════════════════════════════════════╣\n║  🌅 Daily Reset Logic: {'✅ WORKING' if reset_ok else '❌ FAILED'}                             ║\n║  🔄 New Day Activity: {'✅ WORKING' if activity_ok else '❌ FAILED'}                              ║\n║  🆕 Fresh Start: {'✅ WORKING' if fresh_ok else '❌ FAILED'}                                   ║\n║                                                                  ║\n║  🎯 NEW DAY BEHAVIOR:                                            ║\n║     • Balance: PRESERVED from previous day                       ║\n║     • Scan Count: RESET to 0                                    ║\n║     • Signals Generated: RESET to 0                             ║\n║     • Historical Data: PRESERVED in database                    ║\n║                                                                  ║\n║  🚀 DAILY RESET SYSTEM: {'READY!' if all([reset_ok, activity_ok, fresh_ok]) else 'NEEDS FIXES!'}                               ║\n╚══════════════════════════════════════════════════════════════════╝\n\"\"\")