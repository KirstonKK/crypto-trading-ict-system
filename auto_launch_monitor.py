#!/usr/bin/env python3
"""
Continuous API Activation Monitor
Will test every 60 seconds and auto-launch trading when active
"""

import requests
import time
import hmac
import hashlib
import subprocess
import os
from datetime import datetime

def test_api_key():
    """Test if API key is active"""
    api_key = 'WEI4vIDFhy7XXRxq14'
    api_secret = 'uyJXtykzYRyTTd90gy85h5nJNe5clEiaa7hJ'
    
    timestamp = str(int(time.time() * 1000))
    recv_window = '5000'
    params = ''
    param_str = timestamp + api_key + recv_window + params
    signature = hmac.new(
        api_secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'https://api-testnet.bybit.com/v5/account/info',
            headers=headers,
            timeout=10
        )
        
        data = response.json()
        return data.get('retCode') == 0
        
    except Exception:
        return False

def launch_trading_systems():
    """Launch both ICT monitor and demo trading when API is active"""
    print("🚀 API ACTIVE! Launching trading systems...")
    
    # Change to project directory
    os.chdir('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')
    
    try:
        # Start ICT monitor in background
        print("📊 Starting ICT Enhanced Monitor...")
        subprocess.Popen(['python3', 'ict_enhanced_monitor.py'])
        time.sleep(3)
        
        # Start demo trading system
        print("🏪 Starting Bybit Demo Trading System...")
        subprocess.Popen(['python3', 'demo_trading_system.py', '--auto-trading'])
        
        print("✅ Both systems launched!")
        print("📱 Monitor at: http://localhost:5001")
        print("🏪 Bybit Testnet: https://testnet.bybit.com/trade/usdt/BTCUSDT")
        return True
        
    except Exception as e:
        print("❌ Launch error: {e}")
        return False

def main():
    """Main monitoring loop"""
    print("🔄 CONTINUOUS API ACTIVATION MONITOR")
    print("=" * 50)
    print("Checking every 60 seconds...")
    print("Will auto-launch trading when API becomes active")
    print("Press Ctrl+C to stop")
    print()
    
    start_time = time.time()
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = int(time.time() - start_time)
            
            print("🔍 Check #{check_count} at {current_time} ({elapsed}s elapsed)")
            
            if test_api_key():
                print("🎉 API KEY ACTIVATED!")
                
                if launch_trading_systems():
                    print("✅ Trading systems launched successfully!")
                    print("🎯 Demo trading is now LIVE!")
                    break
                else:
                    print("❌ Failed to launch systems, continuing monitoring...")
            else:
                print("⏳ Still pending activation...")
            
            print("   Waiting 60 seconds...\n")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print("\n❌ Monitor error: {e}")

if __name__ == '__main__':
    main()