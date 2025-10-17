#!/usr/bin/env python3

import requests
import json
from datetime import date

def check_trading_journal():
    """Check what's in the trading journal from the web interface"""
    try:
        # Get data from the API
        response = requests.get('http://127.0.0.1:5001/api/data', timeout=5)
        
        if response.status_code != 200:
            print("❌ API request failed: {response.status_code}")
            return
            
        data = response.json()
        
        # Extract trading journal
        journal = data.get('trading_journal', [])
        
        print("🗂️  TRADING JOURNAL FROM WEB INTERFACE:")
        print("=" * 60)
        print("📋 Total journal entries: {len(journal)}")
        print()
        
        today = date.today().isoformat()
        today_entries = 0
        
        for i, entry in enumerate(journal, 1):
            timestamp = entry.get('timestamp', 'No timestamp')
            trade_type = entry.get('type', 'No type')
            action = entry.get('action', 'No action') 
            symbol = entry.get('symbol', 'No symbol')
            details = entry.get('details', 'No details')
            entry_price = entry.get('entry_price', 0)
            trade_id = entry.get('id', 'No ID')
            
            # Check if this entry is from today
            is_today = timestamp.startswith(today) if timestamp != 'No timestamp' else False
            if is_today:
                today_entries += 1
            
            print("{i}. {timestamp} {'🔴 TODAY' if is_today else '📅 PAST'}")
            print("   {trade_type}: {action} {symbol}")
            print("   Details: {details}")
            print("   Entry Price: ${entry_price:.2f}")
            if trade_id != 'No ID':
                print("   Trade ID: {trade_id}")
            print()
        
        print("=" * 60)
        print("📊 SUMMARY:")
        print("   Total journal entries: {len(journal)}")
        print("   Entries from today ({today}): {today_entries}")
        print("   Entries from other days: {len(journal) - today_entries}")
        
        # Also check daily PnL
        daily_pnl = data.get('daily_pnl', 'Not found')
        print("   Current daily PnL: ${daily_pnl}")
        
    except requests.exceptions.RequestException as e:
        print("❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print("❌ JSON decode error: {e}")
    except Exception as e:
        print("❌ Error: {e}")

if __name__ == "__main__":
    check_trading_journal()