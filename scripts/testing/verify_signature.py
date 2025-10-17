#!/usr/bin/env python3
"""
Verify our signature generation matches official Bybit examples exactly
"""

import os
import hmac
import hashlib
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def official_bybit_signature(api_key, secret_key, timestamp, recv_window, payload):
    """Official Bybit signature generation from their examples"""
    param_str = str(timestamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature

def our_signature_generation(api_key, api_secret, timestamp, params):
    """Our current signature generation"""
    recv_window = "5000"
    param_str = str(timestamp) + api_key + recv_window + params
    signature = hmac.new(
        api_secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def main():
    print("🔍 Verifying signature generation...")
    
    # Get API credentials
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Missing API credentials in .env file")
        return
    
    # Test parameters
    timestamp = int(time.time() * 1000)
    recv_window = "5000"
    
    # Test cases
    test_cases = [
        "",  # Empty payload (GET request)
        'category=linear&symbol=BTCUSDT',  # Simple GET params
        '{"category":"linear","symbol":"BTCUSDT","side":"Buy","orderType":"Market","qty":"0.001"}',  # POST JSON
    ]
    
    print(f"📊 Using API Key: {api_key[:8]}...")
    print(f"📊 Timestamp: {timestamp}")
    print()
    
    for i, payload in enumerate(test_cases, 1):
        print(f"Test Case {i}: {payload[:50]}{'...' if len(payload) > 50 else ''}")
        
        # Official method
        official_sig = official_bybit_signature(api_key, api_secret, timestamp, recv_window, payload)
        
        # Our method
        our_sig = our_signature_generation(api_key, api_secret, timestamp, payload)
        
        print(f"  Official: {official_sig}")
        print(f"  Our impl: {our_sig}")
        print(f"  Match: {'✅' if official_sig == our_sig else '❌'}")
        print()
    
    # Test with current timestamp for real API call
    print("🔄 Testing with live API call simulation...")
    current_timestamp = int(time.time() * 1000)
    test_payload = ""  # Simple server time endpoint
    
    signature = our_signature_generation(api_key, api_secret, current_timestamp, test_payload)
    
    print(f"Generated signature for server time call:")
    print(f"  Timestamp: {current_timestamp}")
    print(f"  Payload: '{test_payload}'")
    print(f"  Signature: {signature}")
    
    # Show the exact string being signed
    param_str = str(current_timestamp) + api_key + "5000" + test_payload
    print(f"  String being signed: '{param_str}'")

if __name__ == "__main__":
    main()