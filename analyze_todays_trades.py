#!/usr/bin/env python3

import sqlite3
from datetime import date

DATABASE_PATH = 'databases/trading_data.db'

def _display_trade_info(trade):
    """Display information for a single trade"""
    _, _, _, _, exit_time, realized_pnl, _, exit_price = trade
    
    pnl_str = f"${realized_pnl:.2f}" if realized_pnl else "$0.00"
    exit_str = exit_time if exit_time else "OPEN"
    exit_price_str = f"${exit_price:.2f}" if exit_price else "N/A"
    
    print(f"   Exit:  {exit_str} @ {exit_price_str}")
    print(f"   PnL:   {pnl_str}")
    
    # Count wins/losses
    win_loss_status = None
    if realized_pnl:
        if realized_pnl > 0:
            print("   ✅ WIN")
            win_loss_status = 'win'
        else:
            print("   ❌ LOSS")
            win_loss_status = 'loss'
    else:
        print("   ⏳ OPEN")
    
    print()
    
    return {
        'pnl': realized_pnl or 0,
        'status': win_loss_status
    }

def _check_pnl_discrepancy(cursor, total_pnl, today, wins, losses, all_trades, closed_today):
    """Check for discrepancy between total PnL and daily calculation"""
    cursor.execute("""
        SELECT COALESCE(SUM(realized_pnl), 0)
        FROM paper_trades 
        WHERE date(exit_time) = ? 
        AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
        AND status != 'CLEANUP'
    """, (today,))
    
    daily_pnl_calc = cursor.fetchone()[0]
    
    print("=" * 50)
    print("📊 SUMMARY:")
    print(f"   Total Trades: {len(all_trades)}")
    print(f"   Wins: {wins}")
    print(f"   Losses: {losses}")
    print(f"   Total PnL: ${total_pnl:.2f}")
    print(f"   Closed Today: {closed_today}")
    print(f"   Daily PnL Calculation: ${daily_pnl_calc:.2f}")
    
    if abs(total_pnl - daily_pnl_calc) > 0.01:
        print("⚠️  DISCREPANCY FOUND!")
        print(f"   Total PnL from all trades: ${total_pnl:.2f}")
        print(f"   Daily PnL calculation: ${daily_pnl_calc:.2f}")
    else:
        print("✅ PnL calculations match")

def analyze_todays_trades():
    """Analyze all trades from today to understand the PnL discrepancy"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
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
        
        total_pnl = 0
        wins = 0
        losses = 0
        closed_today = 0
        
        for trade in all_trades:
            result = _display_trade_info(trade)
            total_pnl += result['pnl']
            
            if result['status'] == 'win':
                wins += 1
            elif result['status'] == 'loss':
                losses += 1
            
            # Check if closed today
            exit_time = trade[4]
            if exit_time and exit_time.startswith(today):
                closed_today += 1
        
        # Check for discrepancy
        _check_pnl_discrepancy(cursor, total_pnl, today, wins, losses, all_trades, closed_today)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing trades: {e}")

if __name__ == "__main__":
    analyze_todays_trades()