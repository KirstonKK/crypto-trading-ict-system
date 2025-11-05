#!/usr/bin/env python3
"""
Bybit Demo Funds Monitor
=======================

Continuously monitors Bybit demo account for fund allocation
and automatically starts demo trading when funds are detected.
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.append('.')

from bybit_integration.bybit_client import BybitDemoClient

class FundsMonitor:
    def __init__(self):
        self.client = None
        self.monitoring = True
        self.check_interval = 30  # Check every 30 seconds
        
    async def initialize_client(self):
        """Initialize Bybit client"""
        try:
            # Read env manually
            env_vars = {}
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env_vars[key] = value
            
            self.client = BybitDemoClient(
                api_key=env_vars.get('BYBIT_API_KEY'),
                api_secret=env_vars.get('BYBIT_API_SECRET'),
                testnet=True
            )
            return True
            
        except Exception as e:
            print("❌ Failed to initialize client: {e}")
            return False
    
    async def check_balance(self):
        """Check current USDT balance"""
        try:
            if not self.client:
                await self.initialize_client()
                
            balance_info = await self.client.get_balance()
            usdt_balance = balance_info.get('USDT', 0)
            
            return usdt_balance
            
        except Exception as e:
            print("❌ Error checking balance: {e}")
            return 0
    
    async def monitor_funds(self):
        """Main monitoring loop"""
        print("🔍 BYBIT DEMO FUNDS MONITOR STARTED")
        print("=" * 50)
        print("⏰ Checking every {self.check_interval} seconds...")
        print("🎯 Waiting for demo funds to appear...")
        print("📋 You can request funds at: https://testnet.bybit.com/asset")
        print()
        
        check_count = 0
        
        while self.monitoring:
            try:
                check_count += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                
                print("[{current_time}] Check #{check_count}: ", end="", flush=True)
                
                balance = await self.check_balance()
                
                if balance > 0:
                    print("✅ FUNDS DETECTED: ${balance:,.2f} USDT!")
                    print()
                    print("🎉 DEMO FUNDS ALLOCATION SUCCESSFUL!")
                    print("=" * 50)
                    print("💰 Available Balance: ${balance:,.2f} USDT")
                    print("📊 1% Risk per Trade: ${balance * 0.01:.2f}")
                    print("📈 Target Profit (3x): ${balance * 0.03:.2f}")
                    print()
                    print("🚀 Ready to start demo trading system!")
                    print("💡 Run: python3 demo_trading_system.py")
                    print()
                    
                    # Auto-start demo trading if possible
                    await self.start_demo_trading()
                    break
                    
                else:
                    print("⏳ No funds yet...")
                
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print("❌ Error in monitoring: {e}")
                await asyncio.sleep(self.check_interval)
        
        if self.client:
            await self.client.close()
    
    async def start_demo_trading(self):
        """Attempt to start demo trading system"""
        try:
            print("🚀 Attempting to start demo trading system...")
            
            # Import and start demo trading system
            import subprocess
            
            # Start demo trading in background
            process = subprocess.Popen([
                'python3', 'demo_trading_system.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print("✅ Demo trading system started!")
            print("📊 Process ID: {process.pid}")
            print("🔗 Monitor at: http://localhost:5001")
            
        except Exception as e:
            print("❌ Failed to auto-start demo trading: {e}")
            print("💡 Please manually run: python3 demo_trading_system.py")

async def main():
    monitor = FundsMonitor()
    await monitor.monitor_funds()

if __name__ == "__main__":
    asyncio.run(main())