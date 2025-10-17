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

def test_eod_closure():
    print("🔍 EOD CLOSURE TEST")
    print("=" * 60)
    
    # Check current open positions
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'")
    open_count = cursor.fetchone()[0]
    
    print("📊 Current Open Positions: {open_count}")
    
    if open_count == 0:
        print("✅ No open positions to close")
        conn.close()
        return
    
    # Get current prices from the API
    try:
        response = requests.get('http://localhost:5001/api/data', timeout=5)
        data = response.json()
        
        print(f"💰 Current Balance: ${data.get('paper_balance', 0):.2f}")
        print(f"📈 Today's PnL: ${data.get('daily_pnl', 0):.2f}")
        
    except Exception:
        print("❌ Could not get current balance")
    
    # Get current prices from Bybit (REAL PRICES - NO MORE FICTIONAL DATA!)
    try:
        # Try to get real prices from Bybit API
        import sys
        sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')
        from bybit_integration.real_time_prices import BybitRealTimePrices
        
        bybit_prices = BybitRealTimePrices()
        
        real_prices = {}
        for symbol, crypto in [('BTCUSDT', 'BTC'), ('ETHUSDT', 'ETH'), ('SOLUSDT', 'SOL'), ('XRPUSDT', 'XRP')]:
            price_data = bybit_prices.get_price(symbol)
            if price_data and price_data.get('price', 0) > 0:
                real_prices[crypto] = {'price': float(price_data['price'])}
                print("📡 Real {crypto} price: ${price_data['price']}")
            else:
                print("⚠️ Could not get real price for {crypto}")
        
        if len(real_prices) > 0:
            mock_prices = real_prices
            print("✅ Using REAL Bybit prices for EOD closure test")
        else:
            raise RuntimeError("No real prices available")
            
    except Exception:
        print("⚠️ Could not get real prices, using safer mock prices")
        # Use more realistic mock prices that won't create massive losses
        mock_prices = {
            'BTC': {'price': 110000.0},  # Realistic BTC price 
            'ETH': {'price': 4000.0},    # Realistic ETH price
            'SOL': {'price': 230.0},     # Realistic SOL price
            'XRP': {'price': 0.70}       # Realistic XRP price
        }
    
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
    
    total_pnl = 0
    closed_count = 0
    
    for position in positions:
        trade_id, symbol, direction, entry_price, position_size, entry_time = position
        crypto = symbol.replace('USDT', '')
        
        if crypto not in mock_prices:
            print(f"⚠️ No price for {crypto}, skipping")
            continue
            
        current_price = mock_prices[crypto]['price']
        
        # Calculate PnL
        if direction == 'BUY':
            pnl = (current_price - entry_price) * position_size
        else:
            pnl = (entry_price - current_price) * position_size
        
        total_pnl += pnl
        closed_count += 1
        
        # Show the closure
        entry_date = entry_time[:10]
        pnl_color = "🟢" if pnl > 0 else "🔴"
        print(f"💰 Closing {symbol} position - PnL: ${pnl:.2f}")
        print(f"{pnl_color} {crypto:4} {direction:4} | Entry: ${entry_price:8.2f} | Exit: ${current_price:8.2f} | PnL: ${pnl:+8.2f} | From: {entry_date}")
    
    print("-" * 60)
    print(f"💰 Total EOD PnL: ${total_pnl:.2f}")
    print(f"📊 Positions to Close: {closed_count}")
    
    # Get current balance
    try:
        response = requests.get('http://localhost:5001/api/data', timeout=5)
        data = response.json()
        current_balance = data.get('paper_balance', 0)
        print(f"🎯 New Balance: ${current_balance + total_pnl:.2f}")
    except Exception:
        print("🎯 Unable to calculate new balance")
    
    # Ask user if they want to actually close them
    print(f"\n❓ Do you want to ACTUALLY close these {closed_count} positions?")
    print("   This will update the database and close all open trades.")
    
    choice = input("Type 'YES' to proceed: ").strip().upper()
    
    if choice == 'YES':
        print(f"\n🔄 CLOSING {closed_count} POSITIONS...")
        
        # Update all open positions to EOD_CLOSE
        now = datetime.now().isoformat()
        
        for position in positions:
            _, symbol, direction, entry_price, position_size, _ = position
            crypto = symbol.replace('USDT', '')
            
            if crypto not in mock_prices:
                continue
                
            current_price = mock_prices[crypto]['price']
            
            if direction == 'BUY':
                pnl = (current_price - entry_price) * position_size
            else:
                pnl = (entry_price - current_price) * position_size
            
            # Update in database
            cursor.execute("""
                UPDATE paper_trades 
                SET exit_price = ?, exit_time = ?, status = 'EOD_CLOSE', 
                    realized_pnl = ?
                WHERE id = ?
            """, (current_price, now, pnl, trade_id))
        
        conn.commit()
        
        # Verify closure
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'")
        remaining_open = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'EOD_CLOSE'")
        eod_closed = cursor.fetchone()[0]
        
        print("✅ EOD CLOSURE COMPLETE!")
        print(f"   - Closed: {closed_count} positions")
        print(f"   - Remaining Open: {remaining_open}")
        print(f"   - Total EOD Closures: {eod_closed}")
        print(f"   - Total PnL Impact: ${total_pnl:.2f}")
        
    else:
        print("❌ EOD closure cancelled")
    
    conn.close()
    print("\n🎯 EOD Test Complete!")

if __name__ == "__main__":
    test_eod_closure()