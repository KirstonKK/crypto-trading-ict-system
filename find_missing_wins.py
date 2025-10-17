#!/usr/bin/env python3

import sqlite3
from datetime import date

DATABASE_PATH = 'databases/trading_data.db'

def _search_for_trade(cursor, symbol, entry_price):
    """Search for trades matching symbol and entry price"""
    cursor.execute("""
        SELECT id, symbol, status, entry_time, exit_time, realized_pnl, entry_price, exit_price
        FROM paper_trades 
        WHERE symbol = ? AND ABS(entry_price - ?) < 1.0
        ORDER BY entry_time DESC
        LIMIT 3
    """, (symbol + "USDT", entry_price))
    
    return cursor.fetchall()

def _display_trade_match(match, expected_pnl, today):
    """Display information about a trade match"""
    trade_id, _, status, entry_time, exit_time, realized_pnl, entry_price, _ = match
    
    pnl_str = f"${realized_pnl:.2f}" if realized_pnl else "$0.00"
    exit_date = exit_time[:10] if exit_time else "Not closed"
    
    print(f"    Trade {trade_id}: {status} - Entry: ${entry_price:.2f} - PnL: {pnl_str}")
    print(f"      Entry Date: {entry_time[:10]}")
    print(f"      Exit Date: {exit_date}")
    
    # Check if this matches our expected win
    if realized_pnl and abs(realized_pnl - expected_pnl) < 0.1:
        print("      ✅ This matches the expected win!")
        if exit_time and not exit_time.startswith(today):
            print(f"      ⚠️  But it was closed on {exit_date}, not today ({today})")
    elif realized_pnl and realized_pnl > 0:
        print(f"      ⚠️  This is a win but PnL doesn't match (expected ${expected_pnl})")
    print()

def _search_expected_wins(cursor, expected_wins, today):
    """Search for each expected winning trade"""
    for win in expected_wins:
        symbol = win["symbol"]
        entry_price = win["entry_price"]
        expected_pnl = win["pnl"]
        
        print(f"Looking for {symbol} trade @ ${entry_price} (expected PnL: +${expected_pnl})")
        
        matches = _search_for_trade(cursor, symbol, entry_price)
        
        if matches:
            print(f"  Found {len(matches)} {symbol} trades:")
            for match in matches:
                _display_trade_match(match, expected_pnl, today)
        else:
            print(f"  ❌ No {symbol} trades found near ${entry_price}")
        
        print()

def _display_recent_wins(cursor):
    """Display all recent winning trades"""
    print("🔍 ALL RECENT WINNING TRADES:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT id, symbol, status, entry_time, exit_time, realized_pnl, entry_price, exit_price
        FROM paper_trades 
        WHERE realized_pnl > 0
        ORDER BY exit_time DESC
        LIMIT 10
    """)
    
    wins = cursor.fetchall()
    
    if wins:
        print(f"Found {len(wins)} recent winning trades:")
        for win in wins:
            _, symbol, _, _, exit_time, realized_pnl, _, _ = win
            exit_date = exit_time[:10] if exit_time else "Not closed"
            print(f"  Trade: {symbol} - ${realized_pnl:.2f} - Closed: {exit_date}")
    else:
        print("❌ No winning trades found in database!")

def find_missing_wins():
    """Find the missing winning trades that should contribute to daily PnL"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("🔍 SEARCHING FOR MISSING WINNING TRADES:")
    print("=" * 60)
    
    # Expected winning trades from monitor
    expected_wins = [
        {"symbol": "XRP", "entry_price": 2.42, "pnl": 18.86},
        {"symbol": "SOL", "entry_price": 196.22, "pnl": 10.12},
        {"symbol": "ETH", "entry_price": 3948.13, "pnl": 8.70}
    ]
    
    today = date.today().isoformat()
    
    # Search for expected wins
    _search_expected_wins(cursor, expected_wins, today)
    
    # Display recent wins
    _display_recent_wins(cursor)
    
    conn.close()

if __name__ == "__main__":
    find_missing_wins()