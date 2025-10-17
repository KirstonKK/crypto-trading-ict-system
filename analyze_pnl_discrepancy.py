#!/usr/bin/env python3

import sqlite3
from datetime import datetime, date

DATABASE_PATH = 'databases/trading_data.db'

def analyze_trades():
    """Analyze today's trades to understand the PnL discrepancy"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        print("📊 ANALYZING TRADES FOR {today}")
        print("=" * 60)
        
        # Get all trades from today
        cursor.execute("""
            SELECT id, symbol, status, entry_time, exit_time, realized_pnl, entry_price, exit_price
            FROM paper_trades 
            WHERE date(entry_time) = ?
            ORDER BY entry_time
        """, (today,))
        
        all_trades = cursor.fetchall()
        print("📈 Total trades today: {len(all_trades)}")
        print()
        
        # Unused tracking variables
        total_pnl = 0.0
        
        for trade in all_trades:
            _, _, _, _, exit_time, realized_pnl, _, _ = trade
            
            # Count wins/losses
            if realized_pnl is not None and realized_pnl != 0:
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
            elif status == 'OPEN':
                open_trades += 1
                print("   ⏳ OPEN")
            else:
                print("   ⚪ NO PnL")
            
            print()
        
        print("=" * 60)
        print("📊 SUMMARY:")
        print("   Total Trades: {len(all_trades)}")
        print("   Open Trades: {open_trades}")
        print("   Closed Trades: {wins + losses}")
        print("   Wins: {wins}")
        print("   Losses: {losses}")
        print("   Total PnL from all trades: ${total_pnl:.2f}")
        print("   Trades closed today: {closed_today}")
        
        # Check the daily PnL calculation (what the system uses)
        cursor.execute("""
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM paper_trades 
            WHERE date(exit_time) = ? 
            AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
            AND status != 'CLEANUP'
        """, (today,))
        
        daily_pnl_calc = cursor.fetchone()[0]
        
        print("   Daily PnL (system calculation): ${daily_pnl_calc:.2f}")
        
        # Check if there's a discrepancy
        if abs(total_pnl - daily_pnl_calc) > 0.01:
            print("\n⚠️  DISCREPANCY FOUND!")
            print("   Expected from trades: ${total_pnl:.2f}")
            print("   System calculated: ${daily_pnl_calc:.2f}")
            print("   Difference: ${abs(total_pnl - daily_pnl_calc):.2f}")
            
            # Check what the daily calculation is missing
            cursor.execute("""
                SELECT id, symbol, status, exit_time, realized_pnl
                FROM paper_trades 
                WHERE date(entry_time) = ?
                AND (realized_pnl IS NULL OR realized_pnl = 0 OR date(exit_time) != ?)
            """, (today, today))
            
            missing_trades = cursor.fetchall()
            if missing_trades:
                print("\n🔍 Trades not counted in daily PnL:")
                for trade in missing_trades:
                    id_col, symbol, status, exit_time, realized_pnl = trade
                    print("   Trade {id_col}: {symbol} - {status} - Exit: {exit_time} - PnL: ${realized_pnl or 0:.2f}")
        else:
            print("\n✅ PnL calculations match!")
        
        conn.close()
        
    except Exception:
        print("❌ Error analyzing trades: {e}")

if __name__ == "__main__":
    analyze_trades()