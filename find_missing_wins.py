#!/usr/bin/env python3

import sqlite3
from datetime import date

DATABASE_PATH = 'databases/trading_data.db'

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
    
    for win in expected_wins:
        symbol = win["symbol"]
        entry_price = win["entry_price"]
        expected_pnl = win["pnl"]
        
        print("Looking for {symbol} trade @ ${entry_price} (expected PnL: +${expected_pnl})")
        
        # Search for trades close to this entry price
        cursor.execute("""
            SELECT id, symbol, status, entry_time, exit_time, realized_pnl, entry_price, exit_price
            FROM paper_trades 
            WHERE symbol = ? AND ABS(entry_price - ?) < 1.0
            ORDER BY entry_time DESC
            LIMIT 3
        """, (symbol + "USDT", entry_price))
        
        matches = cursor.fetchall()
        
        if matches:
            print("  Found {len(matches)} {symbol} trades:")
            for match in matches:
                _, _, _, _, exit_time, realized_pnl, _, _ = match
                
                # Remove unused string formatting variables
                # pnl_str = f"${realized_pnl:.2f}" if realized_pnl else "$0.00"
                # exit_date = exit_time[:10] if exit_time else "Not closed"
                
                print("    Trade {id_col}: {status} - Entry: ${ep:.2f} - PnL: {pnl_str}")
                print("      Entry Date: {entry_time[:10]}")
                print("      Exit Date: {exit_date}")
                
                # Check if this matches our expected win
                if realized_pnl and abs(realized_pnl - expected_pnl) < 0.1:
                    print("      ✅ This matches the expected win!")
                    if exit_time and not exit_time.startswith(today):
                        print("      ⚠️  But it was closed on {exit_date}, not today ({today})")
                elif realized_pnl and realized_pnl > 0:
                    print("      ⚠️  This is a win but PnL doesn't match (expected ${expected_pnl})")
                print()
        else:
            print("  ❌ No {symbol} trades found near ${entry_price}")
        
        print()
    
    # Check all positive PnL trades from recent days
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
    
    conn.close()

if __name__ == "__main__":
    find_missing_wins()