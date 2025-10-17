#!/usr/bin/env python3
"""
Test V5 API Authentication with different endpoints
"""

import requests
import time
import hmac
import hashlib
import json

def test_v5_auth():
    api_key = 'Iohh3GFMrEIVhEcFHP'
    api_secret = 'G5H4wmVdDnDah4UMjxm7qZO9nlwfXWTPC0hh'
    
    print("🔍 Testing V5 API Authentication...")
    print("API Key: {api_key}")
    print()
    
    # Test different endpoints in order of complexity
    endpoints = [
        {
            'name': 'Account Info',
            'method': 'GET',
            'url': 'https://api-testnet.bybit.com/v5/account/info',
            'params': ''
        },
        {
            'name': 'Wallet Balance (UNIFIED)',
            'method': 'GET', 
            'url': 'https://api-testnet.bybit.com/v5/account/wallet-balance',
            'params': 'accountType=UNIFIED'
        },
        {
            'name': 'Wallet Balance (CONTRACT)',
            'method': 'GET',
            'url': 'https://api-testnet.bybit.com/v5/account/wallet-balance', 
            'params': 'accountType=CONTRACT'
        }
    ]
    
    for endpoint in endpoints:
        print("📡 Testing: {endpoint['name']}")
        
        timestamp = str(int(time.time() * 1000))
        recv_window = '5000'
        
        # Generate signature
        param_str = timestamp + api_key + recv_window + endpoint['params']
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
            if endpoint['method'] == 'GET':
                if endpoint['params']:
                    response = requests.get(f"{endpoint['url']}?{endpoint['params']}", headers=headers)
                else:
                    response = requests.get(endpoint['url'], headers=headers)
            
            data = response.json()
            
            print("   Status: {response.status_code}")
            print("   RetCode: {data.get('retCode')}")
            print("   Message: {data.get('retMsg')}")
            
            if data.get('retCode') == 0:
                print("   ✅ SUCCESS!")
                result = data.get('result', {})
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key == 'list' and isinstance(value, list):
                            print("     {key}: {len(value)} items")
                        else:
                            print("     {key}: {value}")
            else:
                print("   ❌ FAILED")
                
        except Exception as e:
            print("   ❌ ERROR: {e}")
            
        print()

if __name__ == '__main__':
    test_v5_auth()