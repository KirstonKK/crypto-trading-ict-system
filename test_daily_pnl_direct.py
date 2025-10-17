#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')

import sqlite3
from datetime import datetime

DATABASE_PATH = 'databases/trading_data.db'

def test_daily_pnl_calculation():
    """Test the daily PnL calculation logic"""
    try:
        # Connect to the same database the monitor uses
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get today's date
        print("Testing daily PnL calculation")
        
        # Query exactly like the monitor does
        cursor.execute("""
            SELECT SUM(realized_pnl) 
            FROM paper_trades 
            WHERE DATE(exit_time) = DATE('now') 
            AND status = 'CLOSED'
        """)
        
        result = cursor.fetchone()
        
        print(f"Daily PnL from calculation: ${result[0] if result[0] is not None else 0.0:.2f}")
        
        # Also check what trades exist today
        cursor.execute("""
            SELECT trade_id, symbol, status, entry_time, exit_time, realized_pnl
            FROM paper_trades 
            WHERE DATE(entry_time) = DATE('now')
            ORDER BY entry_time DESC
        """)
        
        trades = cursor.fetchall()
        print(f"\nFound {len(trades)} trades today:")
        
        for trade in trades:
            _, symbol, status, entry_time, exit_time, realized_pnl = trade
            print(f"  {symbol} - {status} - Entry: {entry_time} - Exit: {exit_time if exit_time else 'None'} - PnL: ${realized_pnl:.2f if realized_pnl else 0.00}")
        
        # Check specifically for closed trades
        cursor.execute("""
            SELECT COUNT(*), SUM(realized_pnl)
            FROM paper_trades 
            WHERE DATE(exit_time) = DATE('now') 
            AND status = 'CLOSED'
        """)
        
        closed_result = cursor.fetchone()
        _, closed_pnl = closed_result
        closed_pnl = closed_pnl if closed_pnl else 0.0
        
        print(f"\nClosed trades today: {closed_result[0]}, Total PnL: ${closed_pnl:.2f}")
        
        conn.close()
        
    except Exception:
        print("Error: {e}")

if __name__ == "__main__":
    test_daily_pnl_calculation()