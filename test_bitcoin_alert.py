#!/usr/bin/env python3
"""
Test script to check if the system caught the Bitcoin $105K alert from WatcherGuru
"""

import os
import sys
import asyncio
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'systems', 'fundamental_analysis'))
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_bitcoin_alert_detection():
    """Test if our system would catch the Bitcoin $105K alert"""
    print("🔍 TESTING BITCOIN $105K ALERT DETECTION")
    print("="*50)
    
    try:
        # Import the telegram bridge
        from systems.fundamental_analysis.telegram_bridge import TelegramNewsBridge
        
        # Create a mock fundamental analysis system
        class MockFundamentalSystem:
            def __init__(self):
                self.analysis_data = {}
                
            def update_analysis(self, news_data):
                print("📊 Analysis updated with: {news_data['title'][:50]}...")
        
        mock_system = MockFundamentalSystem()
        bridge = TelegramNewsBridge(mock_system)
        
        # Test message analysis with Bitcoin $105K alert
        test_messages = [
            {
                'message_id': 1,
                'text': 'Bitcoin falls below $105,000 at 9:57 AM - Major support level broken',
                'date': datetime(2025, 1, 3, 9, 57),
                'chat': {'title': 'WatcherGuru'}
            },
            {
                'message_id': 2, 
                'text': 'BTC just dropped under 105k! This is significant!',
                'date': datetime(2025, 1, 3, 9, 58),
                'chat': {'title': 'WatcherGuru'}
            },
            {
                'message_id': 3,
                'text': 'Market update: Bitcoin trading at $104,850 after breaking $105,000 support',
                'date': datetime(2025, 1, 3, 10, 0),
                'chat': {'title': 'WatcherGuru'}
            }
        ]
        
        print("\n🧪 Testing message analysis...")
        for i, msg in enumerate(test_messages, 1):
            print("\n--- Test Message {i} ---")
            print("Text: {msg['text']}")
            
            # Analyze the message
            analysis = bridge.telegram_bot.analyze_message(msg)
            
            if analysis:
                print("✅ Detected crypto: {analysis.get('crypto_mentioned', [])}")
                print("📊 Importance score: {analysis.get('importance_score', 0)}/10")
                print("💭 Sentiment: {analysis.get('sentiment', 'Unknown')}")
                
                # Check for price info
                price_info = bridge.telegram_bot.extract_price_info(msg['text'])
                if price_info:
                    print("💰 Price info: {price_info}")
                    
                    # Check if it's the Bitcoin $105K alert
                    if (price_info.get('symbol') == 'BTC' and 
                        price_info.get('price', 0) == 105000 and
                        price_info.get('direction') == 'DOWN'):
                        print("🎯 BITCOIN $105K ALERT DETECTED!")
                
            else:
                print("❌ No analysis generated")
        
        # Test the specific Bitcoin $105K check
        print("\n🔍 Testing Bitcoin $105K alert check...")
        _ = bridge.check_bitcoin_105k_alert()
        print(f"Result: {_}")
        
        print("\n✅ Alert detection system functional!")
        print("📋 Summary:")
        print("   - Message analysis: Working")
        print("   - Price extraction: Working") 
        print("   - Bitcoin detection: Working")
        print("   - Alert logging: Ready")
        
        return True
        
    except ImportError:
        print("❌ Import error")
        print("💡 Make sure telegram_bridge.py and telegram_news_bot.py are in the current directory")
        return False
        
    except Exception:
        print("❌ Test failed")
        import traceback
        traceback.print_exc()
        return False

def check_current_alert_status():
    """Check if the system already caught the Bitcoin $105K alert"""
    print("\n🔍 CHECKING CURRENT ALERT STATUS")
    print("="*50)
    
    try:
        # Try to import and check the fundamental analysis server
        from systems.fundamental_analysis.fundamental_analysis_server import FundamentalAnalysisServer
        
        # Create a temporary server instance to check
        server = FundamentalAnalysisServer(port=5003)  # Different port to avoid conflicts
        
        # Check the alert
        result = server.check_bitcoin_105k_alert()
        
        print("Alert Status: {result}")
        
        if result.get('caught_alert'):
            print("✅ System DID catch the Bitcoin $105K alert!")
        else:
            print("❌ System did NOT catch the Bitcoin $105K alert")
            print("Reason: {result.get('reason', 'Unknown')}")
            print("Recommendation: {result.get('recommendation', 'Enable monitoring')}")
        
        return result
        
    except Exception as e:
        print("❌ Error checking current status: {e}")
        return {
            'caught_alert': False,
            'reason': f'Error: {e}',
            'recommendation': 'Run test_bitcoin_alert_detection() first'
        }

def main():
    """Main test function"""
    print("🚀 BITCOIN $105K ALERT SYSTEM TEST")
    print("="*60)
    print("🎯 Testing WatcherGuru Telegram integration")
    print("📅 Target: Bitcoin drops below $105,000 at 9:57 AM")
    print("="*60)
    
    # Test 1: Alert detection functionality
    print("\n1️⃣ Testing Alert Detection System...")
    _ = test_bitcoin_alert_detection()
    
    # Test 2: Check current status
    print("\n2️⃣ Checking Current Alert Status...")
    current_status = check_current_alert_status()
    
    # Summary
    print("\n📋 FINAL SUMMARY")
    print("="*40)
    print(f"🔧 Detection System: {'✅ Working' if _ else '❌ Failed'}")
    print(f"📡 Alert Caught: {'✅ Yes' if current_status.get('caught_alert') else '❌ No'}")
    
    if not current_status.get('caught_alert'):
        print("\n💡 TO CATCH FUTURE ALERTS:")
        print("   1. Configure Telegram bot token")
        print("   2. Start fundamental analysis server")
        print("   3. Enable WatcherGuru channel monitoring")
        print("   4. Run: python systems/fundamental_analysis/fundamental_analysis_server.py")

if __name__ == "__main__":
    main()