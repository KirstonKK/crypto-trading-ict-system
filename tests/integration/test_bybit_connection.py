#!/usr/bin/env python3
"""
Bybit Demo Connection Test
=========================

This script tests the connection to Bybit testnet API to verify
that your credentials and setup are working correctly.

Usage:
    python test_bybit_connection.py

Prerequisites:
    1. Set up your .env file with Bybit testnet credentials
    2. Install required dependencies (aiohttp, websockets, cryptography)
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the bybit_integration directory to the path
sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')

from bybit_integration.bybit_client import BybitDemoClient
from bybit_integration.config import load_config_from_env

async def test_bybit_connection():
    """Test Bybit API connection and basic functionality"""
    
    print("🔗 Testing Bybit Demo Trading Connection")
    print("=" * 50)
    print()
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = load_config_from_env()
        
        # Check if credentials are set
        if not config.bybit.api_key or not config.bybit.api_secret:
            print("❌ ERROR: Bybit API credentials not found!")
            print("   Please set BYBIT_API_KEY and BYBIT_API_SECRET in your .env file")
            print("   Get credentials from: https://testnet.bybit.com/")
            return False
        
        print(f"✅ API Key: {config.bybit.api_key[:8]}...{config.bybit.api_key[-4:]}")
        print(f"✅ Environment: {'Testnet' if config.bybit.testnet else 'Mainnet'}")
        print()
        
        # Initialize Bybit client
        print("🔧 Initializing Bybit client...")
        async with BybitDemoClient(
            api_key=config.bybit.api_key,
            api_secret=config.bybit.api_secret,
            testnet=config.bybit.testnet
        ) as client:
            
            # Test 1: Basic connection
            print("🔍 Test 1: Basic API connection...")
            connection_test = await client.test_connection()
            if connection_test:
                print("✅ Connection successful!")
            else:
                print("❌ Connection failed!")
                return False
            
            print()
            
            # Test 2: Account information
            print("🔍 Test 2: Account information...")
            try:
                account_info = await client.get_account_info()
                print(f"✅ Account info retrieved: {len(account_info)} items")
            except Exception as e:
                print(f"❌ Account info failed: {e}")
                return False
            
            print()
            
            # Test 3: Balance retrieval
            print("🔍 Test 3: Balance retrieval...")
            try:
                balances = await client.get_balance()
                print("✅ Balances retrieved:")
                for asset, balance in balances.items():
                    if balance > 0:
                        print(f"   {asset}: {balance:,.2f}")
                
                if not balances or all(balance == 0 for balance in balances.values()):
                    print("⚠️  No demo balance found. This is normal for new testnet accounts.")
                    print("   Demo funds are usually credited automatically.")
                
            except Exception as e:
                print(f"❌ Balance retrieval failed: {e}")
                return False
            
            print()
            
            # Test 4: Market data
            print("🔍 Test 4: Market data retrieval...")
            try:
                ticker = await client.get_ticker("BTCUSDT")
                if ticker:
                    price = float(ticker.get('lastPrice', 0))
                    print(f"✅ BTCUSDT ticker: ${price:,.2f}")
                else:
                    print("❌ No ticker data received")
                    return False
            except Exception as e:
                print(f"❌ Market data failed: {e}")
                return False
            
            print()
            
            # Test 5: Position checking
            print("🔍 Test 5: Position checking...")
            try:
                positions = await client.get_positions()
                print(f"✅ Positions retrieved: {len(positions)} positions")
                
                active_positions = [pos for pos in positions if float(pos.get('size', 0)) > 0]
                if active_positions:
                    print(f"   Active positions: {len(active_positions)}")
                    for pos in active_positions[:3]:  # Show first 3
                        symbol = pos.get('symbol')
                        size = float(pos.get('size', 0))
                        side = pos.get('side')
                        print(f"   - {symbol}: {side} {size}")
                else:
                    print("   No active positions (normal for new account)")
                    
            except Exception as e:
                print(f"❌ Position checking failed: {e}")
                return False
            
            print()
            
            # Test 6: Order history (if any)
            print("🔍 Test 6: Order history...")
            try:
                orders = await client.get_orders()
                print(f"✅ Order history retrieved: {len(orders)} orders")
                
                if orders:
                    recent_orders = orders[:3]  # Show first 3
                    for order in recent_orders:
                        symbol = order.get('symbol')
                        side = order.get('side')
                        status = order.get('orderStatus')
                        print(f"   - {symbol} {side}: {status}")
                else:
                    print("   No order history (normal for new account)")
                    
            except Exception as e:
                print(f"❌ Order history failed: {e}")
                return False
            
            print()
            print("🎉 ALL TESTS PASSED!")
            print("✅ Bybit demo trading integration is ready!")
            print()
            print("📊 Summary:")
            print(f"   API Environment: {'Testnet' if config.bybit.testnet else 'Mainnet'}")
            print(f"   Demo Balance Available: {'Yes' if any(balances.values()) else 'Pending'}")
            print(f"   Market Data: Working")
            print(f"   Order Management: Ready")
            print()
            print("🚀 Next steps:")
            print("   1. Your Bybit connection is working")
            print("   2. Demo funds should be available (check testnet account)")
            print("   3. Ready to integrate with ICT signals")
            print("   4. Run the full integration test next")
            
            return True
            
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        print("\nFull error details:")
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    success = await test_bybit_connection()
    
    if success:
        print("\n✅ CONNECTION TEST SUCCESSFUL!")
        print("Your Bybit demo integration is ready to use.")
        return 0
    else:
        print("\n❌ CONNECTION TEST FAILED!")
        print("Please check your configuration and try again.")
        return 1

if __name__ == "__main__":
    print("🧪 Bybit Demo Connection Test")
    print("=============================")
    print()
    print("This test will verify:")
    print("• API credentials are valid")
    print("• Connection to Bybit testnet works")
    print("• Basic account operations function")
    print("• Market data retrieval works")
    print()
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)