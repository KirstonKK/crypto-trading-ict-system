#!/usr/bin/env python3
from datetime import datetime
import sqlite3
import os

print('🕐 CHECKING CURRENT TIME AND DATABASE STATE')
print('=' * 50)

now = datetime.now()
print(f'Current time: {now}')
print(f'Current date: {now.date()}')

print()
print('📊 CHECKING DATABASE RECORDS...')

if os.path.exists('trading_data.db'):
    with sqlite3.connect('databases/trading_data.db') as conn:
        cursor = conn.execute('SELECT date, scan_count, signals_generated, paper_balance FROM daily_stats ORDER BY date DESC LIMIT 3')
        rows = cursor.fetchall()
        
        print('Recent daily_stats records:')
        for row in rows:
            date_str, scan_count, signals, balance = row
            print(f'  {date_str}: scans={scan_count}, signals={signals}, balance=${balance:.2f}')
        
        # Check signals table for today
        today = now.date()
        cursor = conn.execute('SELECT COUNT(*) FROM signals WHERE date(created_at) = ?', (today,))
        result = cursor.fetchone()
        todays_signals = result[0] if result else 0
        print(f'Signals created today ({today}): {todays_signals}')
        
else:
    print('No trading_data.db found')