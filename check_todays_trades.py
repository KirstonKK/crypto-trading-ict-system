#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def check_todays_trades():
    """Check today's trades specifically"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        print("🗓️ Checking trades for {today}")
        
        # Get trades from today
        cursor.execute("""
            SELECT id, signal_id, symbol, direction, entry_price, status, 
                   entry_time, exit_time, realized_pnl, created_date
            FROM paper_trades 
            WHERE created_date = ? OR DATE(entry_time) = ?
            ORDER BY entry_time DESC
        """, (today, today))
        
        todays_trades = cursor.fetchall()
        
        print("📊 Found {len(todays_trades)} trades from today:")
        
        if not todays_trades:
            print("   No trades found for today")
        else:
            for trade in todays_trades:
                id_col, signal_id, symbol, direction, entry_price, status, entry_time, exit_time, realized_pnl, created_date = trade
                pnl_str = f"${realized_pnl:.2f}" if realized_pnl else "$0.00"
                exit_str = exit_time if exit_time else "NONE"
                print("   {id_col}: {symbol} {direction} @ ${entry_price} - {status}")
                print("       Entry: {entry_time}")
                print("       Exit: {exit_str}")
                print("       PnL: {pnl_str}")
                print()
        
        # Check specifically for closed trades today
        cursor.execute("""
            SELECT COUNT(*), SUM(realized_pnl)
            FROM paper_trades 
            WHERE DATE(exit_time) = ? AND status = 'CLOSED'
        """, (today,))
        
        closed_result = cursor.fetchone()
        closed_count, closed_pnl = closed_result
        closed_pnl = closed_pnl if closed_pnl else 0.0
        
        print("🎯 Closed trades today: {closed_count}")
        print("💰 Total realized PnL today: ${closed_pnl:.2f}")
        
        # Also check open trades from today
        cursor.execute("""
            SELECT COUNT(*)
            FROM paper_trades 
            WHERE DATE(entry_time) = ? AND status != 'CLOSED'
        """, (today,))
        
        open_count = cursor.fetchone()[0]
        print("📈 Open trades from today: {open_count}")
        
        conn.close()
        
    except Exception as e:
        print("❌ Error: {e}")

if __name__ == "__main__":
    check_todays_trades()