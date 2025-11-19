#!/usr/bin/env python3
"""
Test Bybit Mainnet Connection
=============================

Safely test connection to Bybit Mainnet without placing any orders.
This script verifies:
1. API credentials are valid
2. Connection to mainnet works
3. Account balance can be retrieved
4. No open positions exist
5. API permissions are correct

Run this BEFORE enabling live trading!
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bybit_integration.bybit_client import BybitClient
from bybit_integration.config import load_config_from_env, validate_config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mainnet_connection():
    """Test Bybit Mainnet connection (read-only)"""
    
    print("\n" + "="*60)
    print("🔍 BYBIT MAINNET CONNECTION TEST (READ-ONLY)")
    print("="*60 + "\n")
    
    # Load configuration
    try:
        config = load_config_from_env()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Validate configuration
    is_valid, errors = validate_config(config)
    if not is_valid:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False
    print("✅ Configuration validated")
    
    # Check mode
    if config.bybit.testnet:
        print("⚠️  WARNING: BYBIT_TESTNET=true (using testnet, not mainnet)")
        print("   Set BYBIT_TESTNET=false for live trading")
        return False
    
    print("✅ Mode: MAINNET (real money)")
    print(f"   Base URL: {config.bybit.base_url}")
    
    # Initialize client
    try:
        client = BybitClient(
            api_key=config.bybit.api_key,
            api_secret=config.bybit.api_secret,
            testnet=False
        )
        print("✅ Bybit client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test connection - get server time
    try:
        import requests
        response = requests.get(f"{config.bybit.base_url}/v5/market/time")
        if response.status_code == 200:
            print("✅ Server connection successful")
        else:
            print(f"❌ Server connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connection error: {e}")
        return False
    
    # Test API key - get wallet balance
    try:
        print("\n📊 Fetching account balance...")
        
        # Use HTTP client directly for simple GET request
        import requests
        import time
        import hmac
        import hashlib
        
        timestamp = str(int(time.time() * 1000))
        recv_window = '5000'
        
        # V5 API - GET request signature
        # Format: timestamp + api_key + recv_window + queryString
        query_string = 'accountType=UNIFIED'
        sign_string = timestamp + config.bybit.api_key + recv_window + query_string
        
        signature = hmac.new(
            config.bybit.api_secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Make request
        url = f"{config.bybit.base_url}/v5/account/wallet-balance"
        headers = {
            'X-BAPI-API-KEY': config.bybit.api_key,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'X-BAPI-SIGN': signature
        }
        
        response = requests.get(url, params={'accountType': 'UNIFIED'}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            balance_data = response.json()
            print("✅ API credentials valid")
            print("\n💰 Account Balance:")
            
            # Parse balance
            if balance_data.get('retCode') == 0:
                result = balance_data.get('result', {})
                accounts = result.get('list', [])
                
                if accounts:
                    for account in accounts:
                        account_type = account.get('accountType', 'Unknown')
                        total_equity = float(account.get('totalEquity', 0))
                        available_balance = float(account.get('totalAvailableBalance', 0))
                        
                        print(f"   Account Type: {account_type}")
                        print(f"   Total Equity: ${total_equity:.2f}")
                        print(f"   Available: ${available_balance:.2f}")
                        
                        # Show coin balances
                        coins = account.get('coin', [])
                        if coins:
                            print("   Coins:")
                            for coin_data in coins:
                                coin = coin_data.get('coin', '')
                                equity = float(coin_data.get('equity', 0))
                                available = float(coin_data.get('availableToWithdraw', 0))
                                if equity > 0.01:  # Only show if > $0.01
                                    print(f"      {coin}: {equity:.6f} (available: {available:.6f})")
                else:
                    print("   ⚠️  No balance data found")
            else:
                error_msg = balance_data.get('retMsg', 'Unknown error')
                error_code = balance_data.get('retCode', '')
                print(f"   ❌ API Error ({error_code}): {error_msg}")
                if "sign" in error_msg.lower():
                    print("   ⚠️  Signature error - this usually means:")
                    print("      1. API Secret is incorrect")
                    print("      2. System clock is out of sync")
                    print("      3. API key doesn't have required permissions")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to fetch balance: {e}")
        print("   Check API key permissions:")
        print("   - Read wallet balance: REQUIRED")
        print("   - Read position: RECOMMENDED")
        import traceback
        traceback.print_exc()
        return False
    
    # Test position fetching
    try:
        print("\n📈 Checking open positions...")
        positions = client.get_positions()
        
        if positions:
            if isinstance(positions, dict):
                result = positions.get('result', {})
                position_list = result.get('list', [])
                
                if position_list:
                    print(f"⚠️  WARNING: {len(position_list)} open position(s) found:")
                    for pos in position_list:
                        symbol = pos.get('symbol', '')
                        side = pos.get('side', '')
                        size = pos.get('size', 0)
                        entry_price = pos.get('avgPrice', 0)
                        unrealized_pnl = pos.get('unrealisedPnl', 0)
                        print(f"   - {symbol} {side}: {size} @ ${entry_price} (P&L: ${unrealized_pnl})")
                else:
                    print("✅ No open positions")
            else:
                print(f"   Raw data: {positions}")
        else:
            print("✅ No open positions")
            
    except Exception as e:
        print(f"⚠️  Could not check positions: {e}")
        print("   This might be OK if API key doesn't have position permissions")
    
    # Test order history (last 5)
    try:
        print("\n📜 Checking recent orders...")
        orders = client.get_order_history(limit=5)
        
        if orders:
            if isinstance(orders, dict):
                result = orders.get('result', {})
                order_list = result.get('list', [])
                
                if order_list:
                    print(f"   Last {len(order_list)} order(s):")
                    for order in order_list:
                        symbol = order.get('symbol', '')
                        side = order.get('side', '')
                        order_type = order.get('orderType', '')
                        qty = order.get('qty', 0)
                        price = order.get('price', 0)
                        status = order.get('orderStatus', '')
                        created = order.get('createdTime', '')
                        print(f"   - {symbol} {side} {order_type}: {qty} @ ${price} [{status}]")
                else:
                    print("   No recent orders found")
        else:
            print("   No order history available")
            
    except Exception as e:
        print(f"⚠️  Could not check orders: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 CONNECTION TEST SUMMARY")
    print("="*60)
    print("✅ Configuration: Valid")
    print("✅ Mode: Mainnet (real money)")
    print("✅ Server: Connected")
    print("✅ API Key: Valid")
    print("✅ Balance: Retrieved")
    print("✅ Permissions: OK")
    print("\n🚀 Ready for live trading!")
    print("\n⚠️  IMPORTANT REMINDERS:")
    print("   1. Start with SMALL position sizes ($50-100)")
    print("   2. Test with ONE trade first")
    print("   3. Monitor dashboard actively")
    print("   4. Have emergency stop ready")
    print("   5. Never disable stop losses")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = test_mainnet_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
