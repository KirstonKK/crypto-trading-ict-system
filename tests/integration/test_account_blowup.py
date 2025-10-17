#!/usr/bin/env python3
"""
Test script to demonstrate account blow-up and reset functionality
"""

import requests
import json
import time

def check_account_status():
    """Check current account status"""
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            balance = data.get('paper_balance', 0)
            blown = data.get('account_blown', False)
            return balance, blown
        return None, None
    except Exception as e:
        print("❌ Error checking status: {e}")
        return None, None

def reset_account():
    """Reset blown account"""
    try:
        response = requests.post('http://localhost:5001/api/reset_account', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ {data.get('message', 'Account reset')}")
            print("   Old Balance: ${data.get('old_balance', 0):.2f}")
            print("   New Balance: ${data.get('new_balance', 0):.2f}")
            print("   Was Blown: {data.get('was_blown', False)}")
            return True
        else:
            print("❌ Reset failed: {response.text}")
            return False
    except Exception as e:
        print("❌ Error resetting account: {e}")
        return False

def main():
    print("🎯 ICT ACCOUNT BLOW-UP SIMULATION TEST")
    print("="*50)
    
    # Check current status
    balance, blown = check_account_status()
    if balance is not None:
        print("Current Balance: ${balance:.2f}")
        print("Account Blown: {blown}")
        
        if blown:
            print("\n💥 Account is currently blown!")
            print("🔄 Testing reset functionality...")
            
            if reset_account():
                print("\n✅ Reset successful! Checking new status...")
                time.sleep(1)
                new_balance, new_blown = check_account_status()
                if new_balance is not None:
                    print("New Balance: ${new_balance:.2f}")
                    print("Account Blown: {new_blown}")
        else:
            print("\n✅ Account is operational with ${balance:.2f}")
            print("💡 When balance goes negative, trading will stop automatically")
            print("💡 Use this script or POST to /api/reset_account to reset")
    else:
        print("❌ Could not connect to monitor. Is it running on port 5001?")
    
    print("\n📋 Test Commands:")
    print("   Check Status:  curl http://localhost:5001/health")
    print("   Reset Account: curl -X POST http://localhost:5001/api/reset_account")
    print("   Run This Test: python3 test_account_blowup.py")

if __name__ == "__main__":
    main()