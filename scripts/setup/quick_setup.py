#!/usr/bin/env python3
"""
Quick API Setup and Trading Launcher
===================================

This script helps you:
1. Update API credentials
2. Test connection
3. Request demo funds
4. Start both trading systems
"""

import os
import asyncio
import sys

sys.path.append('.')
from bybit_integration.bybit_client import BybitDemoClient

def update_env_file(api_key, api_secret):
    """Update .env file with new API credentials"""
    try:
        # Read existing .env content
        env_content = {}
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_content[key] = value
        
        # Update with new credentials
        env_content['BYBIT_API_KEY'] = api_key
        env_content['BYBIT_API_SECRET'] = api_secret
        
        # Write back to .env
        with open('.env', 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        print("✅ .env file updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

async def test_connection_and_setup(api_key, api_secret):
    """Test connection and setup demo account"""
    try:
        print("🔗 Testing Bybit connection...")
        
        client = BybitDemoClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True
        )
        
        # Test connection
        connection_ok = await client.test_connection()
        if not connection_ok:
            print("❌ Connection test failed")
            return False
        
        print("✅ Connection successful!")
        
        # Check account info
        account_info = await client.get_account_info()
        print(f"📋 Account Type: {account_info.get('accountType', 'Unknown')}")
        
        # Check balance
        balance_info = await client.get_balance()
        usdt_balance = balance_info.get('USDT', 0)
        
        if usdt_balance > 0:
            print(f"💰 Demo Balance: ${usdt_balance:,.2f} USDT")
            print("🎉 Demo account ready for trading!")
        else:
            print("⏳ No demo funds yet - they may take a few minutes to appear")
            print("💡 You can request more at: https://testnet.bybit.com/asset")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def start_trading_systems():
    """Start both ICT monitor and demo trading system"""
    try:
        import subprocess
        
        print("🚀 Starting ICT Enhanced Monitor...")
        ict_process = subprocess.Popen([
            'python3', 'ict_enhanced_monitor.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("🏪 Starting Bybit Demo Trading System...")
        demo_process = subprocess.Popen([
            'python3', 'demo_trading_system.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Both systems started!")
        print(f"📊 ICT Monitor PID: {ict_process.pid}")
        print(f"🏪 Demo Trading PID: {demo_process.pid}")
        print()
        print("🔗 MONITORING LINKS:")
        print("• ICT Monitor: http://localhost:5001")
        print("• Bybit Testnet: https://testnet.bybit.com/trade/usdt/BTCUSDT")
        
        return True
        
    except Exception as e:
        print(f"❌ Error starting systems: {e}")
        return False

async def main():
    print("🚀 BYBIT DEMO TRADING QUICK SETUP")
    print("=" * 50)
    print()
    
    # Get API credentials
    print("📝 Enter your new Bybit testnet API credentials:")
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("❌ API credentials required")
        return
    
    # Update .env file
    print("\n🔄 Updating configuration...")
    if not update_env_file(api_key, api_secret):
        return
    
    # Test connection
    print("\n🧪 Testing connection...")
    if not await test_connection_and_setup(api_key, api_secret):
        return
    
    # Ask if user wants to start trading
    print("\n🚀 Ready to start demo trading!")
    start = input("Start trading systems now? (y/n): ").strip().lower()
    
    if start in ['y', 'yes']:
        print("\n🎯 Starting trading systems...")
        if start_trading_systems():
            print("\n🎉 SUCCESS! Demo trading is now live!")
            print("📊 Monitor your trades and signals in real-time")
            print("⚡ Features: 10x leverage, cross margin, 0.1% slippage")
        else:
            print("\n❌ Failed to start systems - check for errors")
    else:
        print("\n💡 You can manually start systems later:")
        print("   python3 ict_enhanced_monitor.py")
        print("   python3 demo_trading_system.py")

if __name__ == "__main__":
    asyncio.run(main())