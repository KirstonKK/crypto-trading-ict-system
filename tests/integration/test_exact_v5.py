#!/usr/bin/env python3
"""
Test with exact Bybit V5 Python example format
"""

import requests
import time
import hashlib
import hmac
import uuid

# Exact format from Bybit V5 examples
api_key = 'Iohh3GFMrEIVhEcFHP'
secret_key = 'G5H4wmVdDnDah4UMjxm7qZO9nlwfXWTPC0hh'
httpClient = requests.Session()
recv_window = str(5000)
url = "https://api-testnet.bybit.com"

def HTTP_Request(endPoint, method, payload, Info):
    global time_stamp
    time_stamp = str(int(time.time() * 10 ** 3))
    signature = genSignature(payload)
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if method == "POST":
        response = httpClient.request(method, url + endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url + endPoint + "?" + payload, headers=headers)
    
    print(f"{Info} Response Status: {response.status_code}")
    print(f"{Info} Response: {response.text}")
    return response

def genSignature(payload):
    param_str = str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature

# Test exact V5 endpoints from examples
print("🔍 Testing with exact Bybit V5 format...")

# Test 1: Account Info (simple endpoint)
endpoint = "/v5/account/info"
method = "GET"
params = ""
HTTP_Request(endpoint, method, params, "AccountInfo")

print("\n" + "="*50 + "\n")

# Test 2: Wallet Balance  
endpoint = "/v5/account/wallet-balance"
method = "GET"
params = "accountType=UNIFIED"
HTTP_Request(endpoint, method, params, "WalletBalance")

print("\n" + "="*50 + "\n")

# Test 3: Position Info
endpoint = "/v5/position/list"
method = "GET" 
params = "category=linear&symbol=BTCUSDT"
HTTP_Request(endpoint, method, params, "PositionInfo")