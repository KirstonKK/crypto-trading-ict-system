#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')

import sqlite3
from datetime import datetime

def test_daily_pnl_calculation():
    """Test the daily PnL calculation logic"""
    try:
        # Connect to the same database the monitor uses
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        print("Testing daily PnL calculation for {today}")
        
        # Query exactly like the monitor does
        cursor.execute("""
            SELECT SUM(realized_pnl) 
            FROM paper_trades 
            WHERE DATE(exit_time) = DATE('now') 
            AND status = 'CLOSED'
        """)
        
        result = cursor.fetchone()
        daily_pnl = result[0] if result[0] is not None else 0.0
        
        print("Daily PnL from calculation: ${daily_pnl:.2f}")
        
        # Also check what trades exist today
        cursor.execute("""
            SELECT trade_id, symbol, status, entry_time, exit_time, realized_pnl
            FROM paper_trades 
            WHERE DATE(entry_time) = DATE('now')
            ORDER BY entry_time DESC
        """)
        
        trades = cursor.fetchall()
        print("\nFound {len(trades)} trades today:")
        
        for trade in trades:
            trade_id, symbol, status, entry_time, exit_time, realized_pnl = trade
            pnl_str = f"${realized_pnl:.2f}" if realized_pnl else "$0.00"
            exit_str = exit_time if exit_time else "None"
            print("  {trade_id}: {symbol} - {status} - Entry: {entry_time} - Exit: {exit_str} - PnL: {pnl_str}")
        
        # Check specifically for closed trades
        cursor.execute("""
            SELECT COUNT(*), SUM(realized_pnl)
            FROM paper_trades 
            WHERE DATE(exit_time) = DATE('now') 
            AND status = 'CLOSED'
        """)
        
        closed_result = cursor.fetchone()
        closed_count, closed_pnl = closed_result
        closed_pnl = closed_pnl if closed_pnl else 0.0
        
        print("\nClosed trades today: {closed_count}, Total PnL: ${closed_pnl:.2f}")
        
        conn.close()
        
    except Exception as e:
        print("Error: {e}")

if __name__ == "__main__":
    test_daily_pnl_calculation()