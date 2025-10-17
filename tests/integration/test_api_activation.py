#!/usr/bin/env python3
"""
Quick API Key Activation Test
============================

Run this script every few minutes to check when your new Bybit testnet API key becomes active.
"""

import asyncio
import aiohttp
import json
import time
import hmac
import hashlib
from datetime import datetime

async def test_api_activation():
    """Test if the new API key is activated"""
    
    # New API credentials
    api_key = 'WEI4vIDFhy7XXRxq14'
    api_secret = 'uyJXtykzYRyTTd90gy85h5nJNe5clEiaa7hJ'
    
    print(f'🕐 {datetime.now().strftime("%H:%M:%S")} - Testing API key activation...')
    
    async with aiohttp.ClientSession() as session:
        # Generate authentication headers
        timestamp = str(int(time.time() * 1000))
        recv_window = '5000'
        query_params = 'accountType=UNIFIED'
        
        param_str = timestamp + api_key + recv_window + query_params
        signature = hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'Content-Type': 'application/json'
        }
        
        try:
            url = 'https://api-testnet.bybit.com/v5/account/wallet-balance'
            params = {'accountType': 'UNIFIED'}
            
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                if data.get('retCode') == 0:
                    print('🎉 SUCCESS! API key is now ACTIVE!')
                    print('✅ Ready to start demo trading!')
                    
                    # Show account info
                    result = data.get('result', {})
                    account_list = result.get('list', [])
                    
                    if account_list:
                        for account in account_list:
                            coins = account.get('coin', [])
                            for coin in coins:
                                balance = float(coin.get('walletBalance', 0))
                                if balance > 0:
                                    coin_name = coin.get('coin')
                                    print(f'💰 {coin_name}: {balance:,.2f}')
                    
                    print('\n🚀 Next steps:')
                    print('1. Start ICT monitor: python3 ict_enhanced_monitor.py')
                    print('2. Start demo trading: python3 demo_trading_system.py')
                    
                    return True
                    
                elif data.get('retCode') == 10003:
                    print('⏳ API key still pending activation...')
                    return False
                    
                else:
                    print(f'❌ API Error: {data.get("retMsg", "Unknown")}')
                    return False
                    
        except Exception as e:
            print(f'❌ Connection Error: {e}')
            return False

if __name__ == '__main__':
    result = asyncio.run(test_api_activation())
    
    if not result:
        print('\n💡 Suggestions:')
        print('• Wait 5-10 minutes and run this script again')
        print('• Check API key status at: https://testnet.bybit.com/app/user/api-management')
        print('• Ensure all trading permissions are selected')
        print('• If pending > 15 minutes, consider recreating the key')