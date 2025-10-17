#!/usr/bin/env python3
"""
Bybit API Key Activation Monitor
===============================

Continuously monitors the API key activation status and alerts when ready.
Run this script and it will check every 2 minutes until the key is active.
"""

import asyncio
import aiohttp
import json
import time
import hmac
import hashlib
from datetime import datetime

class APIKeyMonitor:
    def __init__(self):
        self.api_key = 'Iohh3GFMrEIVhEcFHP'
        self.api_secret = 'G5H4wmVdDnDah4UMjxm7qZO9nlwfXWTPC0hh'
        self.creation_time = '2025-10-02 14:48:01'
        
    async def test_api_key(self):
        """Test if API key is active"""
        async with aiohttp.ClientSession() as session:
            timestamp = str(int(time.time() * 1000))
            recv_window = '5000'
            query_params = 'accountType=UNIFIED'
            
            param_str = timestamp + self.api_key + recv_window + query_params
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                param_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'X-BAPI-API-KEY': self.api_key,
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
                    return data.get('retCode'), data.get('retMsg', 'Unknown')
                    
            except Exception as e:
                return -1, str(e)
    
    async def monitor_activation(self):
        """Monitor API key activation with automatic checks"""
        print('🔄 BYBIT API KEY ACTIVATION MONITOR')
        print('=' * 50)
        print(f'📋 API Key: {self.api_key}')
        print(f'📅 Created: {self.creation_time}')
        print('⏰ Checking every 2 minutes until active...')
        print()
        
        check_count = 0
        max_checks = 15  # Stop after 30 minutes
        
        while check_count < max_checks:
            check_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f'🔍 Check #{check_count} at {current_time}...', end=' ')
            
            ret_code, ret_msg = await self.test_api_key()
            
            if ret_code == 0:
                print('✅ SUCCESS!')
                print()
                print('🎉 API KEY IS NOW ACTIVE!')
                print('✅ Ready to start demo trading!')
                print()
                print('🚀 Next steps:')
                print('1. Start ICT monitor: python3 ict_enhanced_monitor.py')
                print('2. Start demo trading: python3 demo_trading_system.py')
                print('3. Monitor at: http://localhost:5001')
                return True
                
            elif ret_code == 10003:
                print('⏳ Still pending...')
                
            else:
                print(f'❌ Error {ret_code}: {ret_msg}')
            
            if check_count < max_checks:
                print('   Waiting 2 minutes before next check...')
                await asyncio.sleep(120)  # Wait 2 minutes
        
        print()
        print('⚠️ API key still not active after 30 minutes')
        print('📞 Recommended actions:')
        print('1. Check Bybit testnet dashboard for key status')
        print('2. Consider recreating the API key')
        print('3. Contact Bybit support if issues persist')
        
        return False

async def main():
    monitor = APIKeyMonitor()
    await monitor.monitor_activation()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n⏹️ Monitoring stopped by user')
        print('💡 You can restart this script anytime with: python3 api_monitor.py')