#!/usr/bin/env python3

import sqlite3
from datetime import date

def analyze_todays_trades():
    """Analyze all trades from today to understand the PnL discrepancy"""
    try:
        conn = sqlite3.connect('databases/trading_data.db')
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        print(f"📊 ANALYZING TRADES FOR {today}")
        print("=" * 50)
        
        # Get all trades from today
        cursor.execute("""
            SELECT id, symbol, status, entry_time, exit_time, realized_pnl, entry_price, exit_price
            FROM paper_trades 
            WHERE date(entry_time) = ?
            ORDER BY entry_time
        """, (today,))
        
        all_trades = cursor.fetchall()
        
        print(f"📈 Total trades today: {len(all_trades)}")
        print()
        
        wins = 0
        losses = 0
        total_pnl = 0
        closed_today = 0
        
        for trade in all_trades:
            id_col, symbol, status, entry_time, exit_time, realized_pnl, entry_price, exit_price = trade
            
            pnl_str = f"${realized_pnl:.2f}" if realized_pnl else "$0.00"
            exit_str = exit_time if exit_time else "OPEN"
            exit_price_str = f"${exit_price:.2f}" if exit_price else "N/A"
            
            print(f"Trade {id_col}: {symbol} - {status}")
            print(f"   Entry: {entry_time} @ ${entry_price:.2f}")
            print(f"   Exit:  {exit_str} @ {exit_price_str}")
            print(f"   PnL:   {pnl_str}")
            
            # Count wins/losses
            if realized_pnl:
                total_pnl += realized_pnl
                if realized_pnl > 0:
                    wins += 1
                    print("   ✅ WIN")
                else:
                    losses += 1
                    print("   ❌ LOSS")
                    
                # Check if closed today
                if exit_time and exit_time.startswith(today):
                    closed_today += 1
            else:
                print("   ⏳ OPEN")
            
            print()
        
        print("=" * 50)
        print(f"📊 SUMMARY:")
        print(f"   Total Trades: {len(all_trades)}")
        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")
        print(f"   Total PnL: ${total_pnl:.2f}")
        print(f"   Closed Today: {closed_today}")
        
        # Now check the daily PnL calculation
        cursor.execute("""
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM paper_trades 
            WHERE date(exit_time) = ? 
            AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
            AND status != 'CLEANUP'
        """, (today,))
        
        daily_pnl_calc = cursor.fetchone()[0]
        
        print(f"   Daily PnL Calculation: ${daily_pnl_calc:.2f}")
        
        if abs(total_pnl - daily_pnl_calc) > 0.01:
            print("⚠️  DISCREPANCY FOUND!")
            print(f"   Total PnL from all trades: ${total_pnl:.2f}")
            print(f"   Daily PnL calculation: ${daily_pnl_calc:.2f}")
        else:
            print("✅ PnL calculations match")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_todays_trades()