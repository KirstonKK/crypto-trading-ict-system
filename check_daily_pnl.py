#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def check_daily_pnl():
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check today's closed trades
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as closed_today, SUM(realized_pnl) as total_pnl 
            FROM paper_trades 
            WHERE exit_time LIKE ? AND status = 'CLOSED'
        """, (f'{today}%',))
        
        result = cursor.fetchone()
        closed_count, total_pnl = result
        
        print("📊 Daily PnL Check for {today}:")
        print("   Closed trades: {closed_count}")
        print("   Total PnL: ${total_pnl if total_pnl else 0:.2f}")
        
        # Also check all trades today
        cursor.execute("""
            SELECT trade_id, symbol, status, entry_time, exit_time, realized_pnl 
            FROM paper_trades 
            WHERE entry_time LIKE ?
            ORDER BY entry_time DESC
        """, (f'{today}%',))
        
        all_trades = cursor.fetchall()
        print("\n📋 All trades today ({len(all_trades)}):")
        for trade in all_trades:
            trade_id, symbol, status, entry_time, exit_time, realized_pnl = trade
            print("   {trade_id}: {symbol} - {status} - PnL: ${realized_pnl if realized_pnl else 0:.2f}")
        
        conn.close()
        
    except Exception as e:
        print("❌ Error checking database: {e}")

if __name__ == "__main__":
    check_daily_pnl()