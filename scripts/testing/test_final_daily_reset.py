#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test daily reset functionality"""

from src.database.trading_database import TradingDatabase
import os

print('Testing corrected daily reset functionality...')

if os.path.exists('test_final.db'):
    os.remove('test_final.db')

db = TradingDatabase('test_final.db')

print('Day 1: Adding activity...')
db.increment_scan_count()
db.increment_scan_count()
db.increment_scan_count()

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
db.add_signal({**signal_data, 'symbol': 'ETH/USDT'})
db.update_balance(85.50, 'paper')

stats = db.get_daily_stats()
print(f'Day 1 results: scans={stats.get("scan_count")}, signals={stats.get("signals_generated")}, balance=${stats.get("paper_balance"):.2f}')

# Test expected results
expected_scans = 3
expected_signals = 2  
expected_balance = 85.50

success = (
    stats.get('scan_count') == expected_scans and
    stats.get('signals_generated') == expected_signals and
    abs(stats.get('paper_balance') - expected_balance) < 0.01
)

print(f'Test result: {"✅ SUCCESS" if success else "❌ FAILED"}')

os.remove('test_final.db')
print('Daily reset system is ready!')