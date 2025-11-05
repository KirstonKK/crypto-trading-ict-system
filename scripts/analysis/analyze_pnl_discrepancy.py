#!/usr/bin/env python3

import sqlite3
from datetime import datetime

# SINGLE MAIN DATABASE
DATABASE_PATH = 'data/trading.db'

def _process_trade_pnl(trade, today):
    """Process PnL for a single trade"""
    _, _, status, _, exit_time, realized_pnl, _, _ = trade
    
    total_pnl = 0.0
    wins = 0
    losses = 0
    closed_today = 0
    open_trades = 0
    
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
    
    return {
        'total_pnl': total_pnl,
        'wins': wins,
        'losses': losses,
        'closed_today': closed_today,
        'open_trades': open_trades
    }

def _aggregate_trade_stats(all_trades, today):
    """Aggregate statistics from all trades"""
    total_pnl = 0.0
    wins = 0
    losses = 0
    closed_today = 0
    open_trades = 0
    
    for trade in all_trades:
        stats = _process_trade_pnl(trade, today)
        total_pnl += stats['total_pnl']
        wins += stats['wins']
        losses += stats['losses']
        closed_today += stats['closed_today']
        open_trades += stats['open_trades']
    
    return {
        'total_pnl': total_pnl,
        'wins': wins,
        'losses': losses,
        'closed_today': closed_today,
        'open_trades': open_trades
    }

def _check_for_discrepancy(cursor, total_pnl, daily_pnl_calc, today):
    """Check if there's a discrepancy between expected and calculated PnL"""
    if abs(total_pnl - daily_pnl_calc) > 0.01:
        print("\n⚠️  DISCREPANCY FOUND!")
        print(f"   Expected from trades: ${total_pnl:.2f}")
        print(f"   System calculated: ${daily_pnl_calc:.2f}")
        print(f"   Difference: ${abs(total_pnl - daily_pnl_calc):.2f}")
        
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
                _, symbol, status, exit_time, realized_pnl = trade
                print(f"   Trade: {symbol} - {status} - Exit: {exit_time} - PnL: ${realized_pnl or 0:.2f}")
    else:
        print("\n✅ PnL calculations match!")

def analyze_trades():
    """Analyze today's trades to understand the PnL discrepancy"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        print(f"📊 ANALYZING TRADES FOR {today}")
        print("=" * 60)
        
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
        
        # Aggregate trade statistics
        stats = _aggregate_trade_stats(all_trades, today)
        
        print("=" * 60)
        print("📊 SUMMARY:")
        print(f"   Total Trades: {len(all_trades)}")
        print(f"   Open Trades: {stats['open_trades']}")
        print(f"   Closed Trades: {stats['wins'] + stats['losses']}")
        print(f"   Wins: {stats['wins']}")
        print(f"   Losses: {stats['losses']}")
        print(f"   Total PnL from all trades: ${stats['total_pnl']:.2f}")
        print(f"   Trades closed today: {stats['closed_today']}")
        
        # Check the daily PnL calculation (what the system uses)
        cursor.execute("""
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM paper_trades 
            WHERE date(exit_time) = ? 
            AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
            AND status != 'CLEANUP'
        """, (today,))
        
        daily_pnl_calc = cursor.fetchone()[0]
        
        print(f"   Daily PnL (system calculation): ${daily_pnl_calc:.2f}")
        
        # Check for discrepancy
        _check_for_discrepancy(cursor, stats['total_pnl'], daily_pnl_calc, today)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing trades: {e}")

if __name__ == "__main__":
    analyze_trades()