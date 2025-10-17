#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

print('🔍 CHECKING CURRENT DATABASE STATE')
print('=' * 50)

if os.path.exists('trading_data.db'):
    with sqlite3.connect('databases/trading_data.db') as conn:
        # Check all daily_stats records
        cursor = conn.execute('SELECT date, scan_count, signals_generated, paper_balance FROM daily_stats ORDER BY date')
        rows = cursor.fetchall()
        
        print('ALL DAILY_STATS RECORDS:')
        for row in rows:
            date_str, scan_count, signals, balance = row
            print(f'  {date_str}: scans={scan_count}, signals={signals}, balance=${balance:.2f}')
        
        print()
        # Check what's the actual current state
        today = datetime.now().date()
        cursor = conn.execute('SELECT scan_count, signals_generated, paper_balance FROM daily_stats WHERE date = ?', (today,))
        today_data = cursor.fetchone()
        
        if today_data:
            scan_count, signals, balance = today_data
            print(f'TODAY ({today}) ACTUAL DATA:')
            print(f'  Scans: {scan_count}')
            print(f'  Signals: {signals}') 
            print(f'  Balance: ${balance:.2f}')
        else:
            print(f'No data found for today ({today})')
            
else:
    print('No trading_data.db found')