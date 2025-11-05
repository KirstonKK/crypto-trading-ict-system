#!/usr/bin/env python3
"""
EOD Closure Test Script
=======================
Test the fixed EOD closure system to close all open positions
"""

import sqlite3
import requests
import json
from datetime import datetime

DATABASE_PATH = 'databases/trading_data.db'

def _get_current_balance_info():
    """Get current balance and PnL from API"""
    try:
        response = requests.get('http://localhost:5001/api/data', timeout=5)
        data = response.json()
        
        balance = data.get('paper_balance', 0)
        pnl = data.get('daily_pnl', 0)
        
        print(f"💰 Current Balance: ${balance:.2f}")
        print(f"📈 Today's PnL: ${pnl:.2f}")
        return balance
        
    except Exception:
        print("❌ Could not get current balance")
        return None

def _get_real_bybit_prices():
    """Attempt to get real prices from Bybit"""
    try:
        import sys
        sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')
        from bybit_integration.real_time_prices import BybitRealTimePrices
        
        bybit_prices = BybitRealTimePrices()
        
        real_prices = {}
        for symbol, crypto in [('BTCUSDT', 'BTC'), ('ETHUSDT', 'ETH'), ('SOLUSDT', 'SOL'), ('XRPUSDT', 'XRP')]:
            price_data = bybit_prices.get_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                real_prices[crypto] = {'price': float(price_data['price'])}
                print(f"📡 Real {crypto} price: ${price_data['price']}")
            else:
                print(f"⚠️ Could not get real price for {crypto}")
        
        if len(real_prices) > 0:
            print("✅ Using REAL Bybit prices for EOD closure test")
            return real_prices
        else:
            raise RuntimeError("No real prices available")
            
    except Exception:
        print("⚠️ Could not get real prices, using safer mock prices")
        return None

def _get_mock_prices():
    """Get realistic mock prices as fallback"""
    return {
        'BTC': {'price': 110000.0},  # Realistic BTC price 
        'ETH': {'price': 4000.0},    # Realistic ETH price
        'SOL': {'price': 230.0},     # Realistic SOL price
        'XRP': {'price': 0.70}       # Realistic XRP price
    }

def _calculate_position_pnl(position, mock_prices):
    """Calculate PnL for a single position"""
    _, symbol, direction, entry_price, position_size, entry_time = position
    crypto = symbol.replace('USDT', '')
    
    if crypto not in mock_prices:
        return None, None, None, None, None
    
    current_price = mock_prices[crypto]['price']
    
    # Calculate PnL
    if direction == 'BUY':
        pnl = (current_price - entry_price) * position_size
    else:
        pnl = (entry_price - current_price) * position_size
    
    return crypto, current_price, pnl, entry_price, entry_time

def _display_positions_summary(positions, mock_prices):
    """Display summary of positions to be closed"""
    total_pnl = 0
    closed_count = 0
    
    for position in positions:
        crypto, current_price, pnl, entry_price, entry_time = _calculate_position_pnl(position, mock_prices)
        
        if crypto is None:
            print("⚠️ No price for position, skipping")
            continue
        
        total_pnl += pnl
        closed_count += 1
        
        # Show the closure
        symbol = position[1]
        direction = position[2]
        entry_date = entry_time[:10]
        pnl_color = "🟢" if pnl > 0 else "🔴"
        print(f"💰 Closing {symbol} position - PnL: ${pnl:.2f}")
        print(f"{pnl_color} {crypto:4} {direction:4} | Entry: ${entry_price:8.2f} | Exit: ${current_price:8.2f} | PnL: ${pnl:+8.2f} | From: {entry_date}")
    
    return total_pnl, closed_count

def _execute_eod_closure(cursor, positions, mock_prices):
    """Execute the actual EOD closure in database"""
    now = datetime.now().isoformat()
    closed_count = 0
    
    for position in positions:
        trade_id = position[0]
        crypto, current_price, pnl, _, _ = _calculate_position_pnl(position, mock_prices)
        
        if crypto is None:
            continue
        
        # Update in database
        cursor.execute("""
            UPDATE paper_trades 
            SET exit_price = ?, exit_time = ?, status = 'EOD_CLOSE', 
                realized_pnl = ?
            WHERE id = ?
        """, (current_price, now, pnl, trade_id))
        closed_count += 1
    
    return closed_count

def test_eod_closure():
    print("🔍 EOD CLOSURE TEST")
    print("=" * 60)
    
    # Check current open positions
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'")
    open_count = cursor.fetchone()[0]
    
    print(f"📊 Current Open Positions: {open_count}")
    
    if open_count == 0:
        print("✅ No open positions to close")
        conn.close()
        return
    
    # Get current balance
    current_balance = _get_current_balance_info()
    
    # Get prices (real or mock)
    mock_prices = _get_real_bybit_prices()
    if mock_prices is None:
        mock_prices = _get_mock_prices()
    
    print("\n🌙 SIMULATING EOD CLOSURE...")
    print("-" * 60)
    
    # Get all open positions
    cursor.execute("""
        SELECT id, symbol, direction, entry_price, position_size, entry_time
        FROM paper_trades 
        WHERE status = 'OPEN'
        ORDER BY entry_time
    """)
    
    positions = cursor.fetchall()
    
    # Display summary
    total_pnl, closed_count = _display_positions_summary(positions, mock_prices)
    
    print("-" * 60)
    print(f"💰 Total EOD PnL: ${total_pnl:.2f}")
    print(f"📊 Positions to Close: {closed_count}")
    
    if current_balance is not None:
        print(f"🎯 New Balance: ${current_balance + total_pnl:.2f}")
    else:
        print("🎯 Unable to calculate new balance")
    
    # Ask user confirmation
    print(f"\n❓ Do you want to ACTUALLY close these {closed_count} positions?")
    print("   This will update the database and close all open trades.")
    
    choice = input("Type 'YES' to proceed: ").strip().upper()
    
    if choice == 'YES':
        print(f"\n🔄 CLOSING {closed_count} POSITIONS...")
        
        # Execute closure
        closed = _execute_eod_closure(cursor, positions, mock_prices)
        conn.commit()
        
        # Verify closure
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'")
        remaining_open = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'EOD_CLOSE'")
        eod_closed = cursor.fetchone()[0]
        
        print("✅ EOD CLOSURE COMPLETE!")
        print(f"   - Closed: {closed} positions")
        print(f"   - Remaining Open: {remaining_open}")
        print(f"   - Total EOD Closures: {eod_closed}")
        print(f"   - Total PnL Impact: ${total_pnl:.2f}")
        
    else:
        print("❌ EOD closure cancelled")
    
    conn.close()
    print("\n🎯 EOD Test Complete!")

if __name__ == "__main__":
    test_eod_closure()