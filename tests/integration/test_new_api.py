#!/usr/bin/env python3
"""
Simple API Key Activation Checker
"""

import requests
import time
import hmac
import hashlib

def test_new_api_key(api_key, api_secret):
    """Test if new API key works"""
    print(f"🔍 Testing API Key: {api_key}")
    
    timestamp = str(int(time.time() * 1000))
    recv_window = '5000'
    
    # Test simplest endpoint - account info
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
        
        if data.get('retCode') == 0:
            print("✅ SUCCESS! API key is active!")
            return True
        elif data.get('retCode') == 10003:
            print("❌ API key invalid/pending activation")
            return False
        else:
            print(f"❌ Error: {data.get('retMsg')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == '__main__':
    print("🔑 API Key Activation Checker")
    print("=" * 40)
    print()
    print("Paste your NEW API credentials:")
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    if api_key and api_secret:
        result = test_new_api_key(api_key, api_secret)
        
        if result:
            print("\n🎉 Ready to update .env file!")
            print(f"BYBIT_API_KEY={api_key}")
            print(f"BYBIT_API_SECRET={api_secret}")
        else:
            print("\n⏳ API key not yet active. Try again in a few minutes.")
    else:
        print("❌ No credentials provided")