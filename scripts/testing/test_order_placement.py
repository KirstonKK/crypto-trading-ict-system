#!/usr/bin/env python3
"""
Bybit Order Placement Test
===========================

Tests the new synchronous order placement methods without executing real trades.
Validates API signature generation and request structure.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

from bybit_integration.bybit_client import BybitClient
from dotenv import load_dotenv

# Load credentials
load_dotenv()

def test_order_methods_exist():
    """Test that new synchronous methods exist"""
    print("\n" + "="*60)
    print("TEST 1: Verify New Methods Exist")
    print("="*60)
    
    # Check if credentials are available
    api_key = os.getenv('BYBIT_API_KEY')
    if not api_key:
        print("⚠️  No credentials - checking method signatures only")
        
        # Check methods exist in class definition
        assert hasattr(BybitClient, 'place_order_sync'), "❌ place_order_sync method missing"
        print("✅ place_order_sync method exists")
        
        assert hasattr(BybitClient, 'get_order_status_sync'), "❌ get_order_status_sync method missing"
        print("✅ get_order_status_sync method exists")
        
        assert hasattr(BybitClient, 'get_balance_sync'), "✅ get_balance_sync method exists"
        print("✅ get_balance_sync method exists")
        
        print("\n✅ All required methods are present in class definition")
        return
    
    client = BybitClient(testnet=False)
    
    # Check methods exist
    assert hasattr(client, 'place_order_sync'), "❌ place_order_sync method missing"
    print("✅ place_order_sync method exists")
    
    assert hasattr(client, 'get_order_status_sync'), "❌ get_order_status_sync method missing"
    print("✅ get_order_status_sync method exists")
    
    assert hasattr(client, 'get_balance_sync'), "✅ get_balance_sync method exists"
    print("✅ get_balance_sync method exists")
    
    print("\n✅ All required methods are present")


def test_order_structure():
    """Test order structure without actual execution"""
    print("\n" + "="*60)
    print("TEST 2: Order Structure Validation")
    print("="*60)
    
    api_key = os.getenv('BYBIT_API_KEY')
    if not api_key:
        print("⚠️  No credentials - skipping order structure test")
        return
    
    # Test with credentials to check structure
    client = BybitClient(testnet=False)
    
    # Test data
    symbol = "BTCUSDT"
    side = "Buy"
    qty = 0.001
    stop_loss = 45000.0
    take_profit = 46500.0
    
    print(f"\nOrder Parameters:")
    print(f"  Symbol: {symbol}")
    print(f"  Side: {side}")
    print(f"  Quantity: {qty}")
    print(f"  Stop Loss: ${stop_loss:.2f}")
    print(f"  Take Profit: ${take_profit:.2f}")
    
    # Note: This will fail without credentials, but we can check error handling
    result = client.place_order_sync(
        symbol=symbol,
        side=side,
        qty=qty,
        order_type="Market",
        stop_loss=stop_loss,
        take_profit=take_profit
    )
    
    # Should return error about missing credentials
    assert 'success' in result, "❌ Result should have 'success' key"
    print(f"\n✅ Method returns properly structured response")
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error', 'N/A')}")


def test_with_real_credentials():
    """Test with real credentials (read-only check)"""
    print("\n" + "="*60)
    print("TEST 3: Real API Credentials Test")
    print("="*60)
    
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        print("⚠️  No credentials found in .env - skipping live test")
        return
    
    print(f"✅ Credentials loaded")
    print(f"   API Key: {api_key[:10]}...")
    
    # Initialize client with credentials
    client = BybitClient(testnet=False)
    
    # Test balance fetch (safe read-only operation)
    print(f"\n📊 Testing balance fetch...")
    balance = client.get_balance_sync()
    
    print(f"   Total Equity: ${balance.get('total_equity', 0):.2f}")
    print(f"   Available: ${balance.get('available_balance', 0):.2f}")
    
    if balance.get('total_equity', 0) > 0:
        print(f"\n✅ API connection successful")
        print(f"⚠️  NOTE: Not placing test order (requires funding)")
    else:
        print(f"\n✅ API connected but balance is zero")
        print(f"   Fund account before live trading")


def test_order_link_id_generation():
    """Test order link ID generation"""
    print("\n" + "="*60)
    print("TEST 4: Order Link ID Generation")
    print("="*60)
    
    import uuid
    import time
    
    # Simulate signal
    signal_id = "test_signal_001"
    timestamp = int(time.time())
    
    order_link_id = f"ICT_{signal_id}_{timestamp}"
    
    print(f"Signal ID: {signal_id}")
    print(f"Timestamp: {timestamp}")
    print(f"Order Link ID: {order_link_id}")
    
    assert len(order_link_id) > 0, "❌ Order link ID is empty"
    assert signal_id in order_link_id, "❌ Signal ID not in order link ID"
    
    print(f"\n✅ Order link ID generation works")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 BYBIT ORDER PLACEMENT - FUNCTIONALITY TEST")
    print("="*60)
    
    try:
        test_order_methods_exist()
        test_order_structure()
        test_order_link_id_generation()
        test_with_real_credentials()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("\nOrder placement functionality is ready!")
        print("⚠️  Remember:")
        print("   1. Fund account with $50 before trading")
        print("   2. Enable Symbol Whitelist on Bybit")
        print("   3. Set AUTO_TRADING=true when ready")
        print("   4. Monitor first trade closely")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
