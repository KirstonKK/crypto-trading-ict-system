#!/usr/bin/env python3
"""
Telegram News Integration Bridge
Connects WatcherGuru Telegram Bot to Fundamental Analysis System
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_news_bot import WatcherGuruTelegramBot

logger = logging.getLogger('TelegramBridge')

class TelegramNewsBridge:
    """
    Bridge between Telegram news bot and fundamental analysis system
    """
    
    def __init__(self, fundamental_analysis_system=None):
        self.telegram_bot = WatcherGuruTelegramBot()
        self.fundamental_system = fundamental_analysis_system
        self.last_check_time = datetime.now()
        
        # Real-time alert settings
        self.alert_thresholds = {
            'BTC': {'min_price': 50000, 'max_price': 150000},
            'ETH': {'min_price': 2000, 'max_price': 8000},
            'SOL': {'min_price': 100, 'max_price': 500},
            'XRP': {'min_price': 0.3, 'max_price': 5.0}
        }
        
    def configure_telegram_bot(self, bot_token: str):
        """Configure the Telegram bot token"""
        self.telegram_bot.configure_bot_token(bot_token)
        logger.info("✅ Telegram bot configured for WatcherGuru integration")
    
    async def start_telegram_monitoring(self):
        """Start monitoring WatcherGuru Telegram channel"""
        logger.info("🚀 Starting WatcherGuru Telegram monitoring bridge...")
        
        # Start the telegram bot monitoring in background
        telegram_task = asyncio.create_task(self.telegram_bot.start_monitoring())
        
        # Start processing alerts
        bridge_task = asyncio.create_task(self.process_telegram_alerts())
        
        # Run both tasks concurrently
        await asyncio.gather(telegram_task, bridge_task)
    
    async def process_telegram_alerts(self):
        """Process new Telegram alerts and integrate with fundamental analysis"""
        while True:
            try:
                # Get unprocessed price alerts
                price_alerts = self.telegram_bot.get_price_alerts(processed=False)
                
                for alert in price_alerts:
                    await self.handle_price_alert(alert)
                    
                # Get recent high-importance news
                recent_news = self.telegram_bot.get_recent_news(hours=1)
                high_importance_news = [news for news in recent_news if news['importance_score'] >= 8]
                
                for news in high_importance_news:
                    await self.handle_important_news(news)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error processing telegram alerts: {e}")
                await asyncio.sleep(60)
    
    async def handle_price_alert(self, alert: dict):
        """Handle a price alert from Telegram"""
        try:
            crypto = alert['crypto']
            price = alert['price']
            direction = alert['direction']
            timestamp = alert['timestamp']
            
            logger.info(f"🚨 Processing price alert: {crypto} {direction} ${price}")
            
            # Check if this is a significant price movement
            if self.is_significant_price_movement(crypto, price, direction):
                
                # Create news entry for fundamental analysis
                news_entry = {
                    'title': f"{crypto} Price Alert: {direction} ${price:,.0f}",
                    'sentiment': 'BEARISH' if direction == 'DOWN' else 'BULLISH',
                    'impact_level': 'HIGH',
                    'crypto_mentioned': [crypto],
                    'published_at': timestamp,
                    'summary': f"WatcherGuru reported {crypto} {'falling below' if direction == 'DOWN' else 'rising above'} ${price:,.0f}",
                    'source': 'WatcherGuru Telegram',
                    'url': '',
                    'image': ''
                }
                
                # Update fundamental analysis system
                if self.fundamental_system:
                    await self.update_fundamental_analysis(news_entry)
                
                # Log the significant alert
                logger.warning(f"⚠️ SIGNIFICANT PRICE ALERT: {crypto} {direction} ${price:,.0f}")
                
            # Mark alert as processed
            self.telegram_bot.mark_alert_processed(alert['id'])
            
        except Exception as e:
            logger.error(f"Error handling price alert: {e}")
    
    def is_significant_price_movement(self, crypto: str, price: float, direction: str) -> bool:
        """Check if price movement is significant enough to trigger alerts"""
        if crypto not in self.alert_thresholds:
            return True  # Default to significant for unknown cryptos
        
        thresholds = self.alert_thresholds[crypto]
        
        # Check if price is at significant levels
        if direction == 'DOWN':
            # Significant if dropping below psychological levels
            significant_levels = [
                thresholds['min_price'], 
                thresholds['min_price'] * 1.5,
                (thresholds['min_price'] + thresholds['max_price']) / 2
            ]
            return any(abs(price - level) / level < 0.05 for level in significant_levels)
        
        else:  # direction == 'UP'
            # Significant if rising above psychological levels
            significant_levels = [
                thresholds['max_price'],
                thresholds['max_price'] * 0.8,
                (thresholds['min_price'] + thresholds['max_price']) / 2
            ]
            return any(abs(price - level) / level < 0.05 for level in significant_levels)
    
    async def handle_important_news(self, news: dict):
        """Handle important news from Telegram"""
        try:
            # Convert telegram news to fundamental analysis format
            crypto_mentioned = news['crypto_mentioned'].split(',') if news['crypto_mentioned'] else ['GENERAL']
            
            news_entry = {
                'title': f"WatcherGuru Alert: {news['content'][:100]}...",
                'sentiment': news['sentiment'],
                'impact_level': 'HIGH' if news['importance_score'] >= 9 else 'MEDIUM',
                'crypto_mentioned': crypto_mentioned,
                'published_at': news['timestamp'],
                'summary': news['content'][:300] + '...' if len(news['content']) > 300 else news['content'],
                'source': f"WatcherGuru Telegram ({news['channel']})",
                'url': '',
                'image': ''
            }
            
            # Update fundamental analysis system
            if self.fundamental_system:
                await self.update_fundamental_analysis(news_entry)
            
            logger.info(f"📰 Processed important news: Score {news['importance_score']}, Cryptos: {crypto_mentioned}")
            
        except Exception as e:
            logger.error(f"Error handling important news: {e}")
    
    def update_fundamental_analysis(self, news_entry: dict):
        """Update the fundamental analysis system with new news"""
        try:
            # Add to fundamental analysis news cache
            if hasattr(self.fundamental_system, '_news_cache'):
                # Insert at beginning to prioritize real-time news
                self.fundamental_system._news_cache.insert(0, news_entry)
                
                # Keep only latest 20 news items
                self.fundamental_system._news_cache = self.fundamental_system._news_cache[:20]
                
                # Update cache timestamp
                self.fundamental_system._news_cache_time = datetime.now().timestamp()
                
                logger.info("✅ Updated fundamental analysis with real-time Telegram news")
            
        except Exception as e:
            logger.error(f"Error updating fundamental analysis: {e}")
    
    def _analyze_news_by_crypto(self, recent_news):
        """Analyze news items by cryptocurrency"""
        crypto_summary = {}
        
        for news in recent_news:
            if news['crypto_mentioned']:
                for crypto in news['crypto_mentioned'].split(','):
                    if crypto not in crypto_summary:
                        crypto_summary[crypto] = {
                            'news_count': 0,
                            'sentiment_distribution': {'BULLISH': 0, 'BEARISH': 0, 'NEUTRAL': 0},
                            'avg_importance': 0,
                            'recent_alerts': []
                        }
                    
                    crypto_summary[crypto]['news_count'] += 1
                    crypto_summary[crypto]['sentiment_distribution'][news['sentiment']] += 1
                    crypto_summary[crypto]['avg_importance'] += news['importance_score']
        
        return crypto_summary
    
    def _add_price_alerts(self, crypto_summary, price_alerts):
        """Add price alerts to crypto summary"""
        for alert in price_alerts[-10:]:  # Last 10 alerts
            crypto = alert['crypto']
            if crypto in crypto_summary:
                crypto_summary[crypto]['recent_alerts'].append({
                    'price': alert['price'],
                    'direction': alert['direction'],
                    'timestamp': alert['timestamp']
                })

    def get_telegram_news_summary(self, hours: int = 24) -> dict:
        """Get a summary of recent Telegram news"""
        try:
            recent_news = self.telegram_bot.get_recent_news(hours=hours)
            price_alerts = self.telegram_bot.get_price_alerts(processed=True)
            
            # Analyze by crypto
            crypto_summary = self._analyze_news_by_crypto(recent_news)
            
            # Calculate averages
            for crypto in crypto_summary:
                count = crypto_summary[crypto]['news_count']
                if count > 0:
                    crypto_summary[crypto]['avg_importance'] /= count
            
            # Add price alerts
            self._add_price_alerts(crypto_summary, price_alerts)
            
            return {
                'summary_period_hours': hours,
                'total_news_items': len(recent_news),
                'total_price_alerts': len(price_alerts),
                'crypto_analysis': crypto_summary,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating telegram news summary: {e}")
            return {}
    
    def check_bitcoin_105k_alert(self) -> Optional[dict]:
        """Specifically check if we caught the Bitcoin $105K alert mentioned by user"""
        try:
            # Look for recent BTC alerts around $105,000
            price_alerts = self.telegram_bot.get_price_alerts(processed=True)
            
            btc_105k_alerts = []
            for alert in price_alerts:
                if (alert['crypto'] == 'BTC' and 
                    104500 <= alert['price'] <= 105500 and 
                    alert['direction'] == 'DOWN'):
                    btc_105k_alerts.append(alert)
            
            if btc_105k_alerts:
                latest_alert = max(btc_105k_alerts, key=lambda x: x['timestamp'])
                return {
                    'caught': True,
                    'alert_details': latest_alert,
                    'message': f"✅ Caught Bitcoin drop below ${latest_alert['price']} at {latest_alert['timestamp']}"
                }
            else:
                return {
                    'caught': False,
                    'message': "❌ No Bitcoin $105K alerts found in recent data"
                }
                
        except Exception as e:
            logger.error(f"Error checking Bitcoin 105K alert: {e}")
            return {'caught': False, 'error': str(e)}

# Integration with existing fundamental analysis system
def integrate_with_fundamental_analysis():
    """Integration function for the main fundamental analysis system"""
    
    # Import the existing fundamental analysis system
    try:
        import sys
        import os
        sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/systems/fundamental_analysis')
        
        # This would be called from the main fundamental analysis server
        logger.info("🔗 Telegram news bridge ready for integration")
        return True
        
    except Exception as e:
        logger.error(f"Error integrating with fundamental analysis: {e}")
        return False

# Demo/Test function
def demo_telegram_integration():
    """Demo the Telegram integration"""
    
    print("🚀 WatcherGuru Telegram Integration Demo")
    print("=" * 50)
    
    # Create bridge
    bridge = TelegramNewsBridge()
    
    # Note: In real usage, you'd configure with actual bot token
    # bridge.configure_telegram_bot("YOUR_BOT_TOKEN_HERE")
    
    # Test message analysis
    test_messages = [
        "🚨 BITCOIN ALERT: BTC falls below $105,000 amid market volatility",
        "📈 Ethereum breaks above $3,800 with strong volume",
        "⚠️ SOL drops to $200 as altcoins face pressure"
    ]
    
    print("📰 Testing Telegram message analysis:")
    for msg in test_messages:
        _ = bridge.telegram_bot.analyze_message(msg)
        print(f"Message: {msg}")
        print(f"Analysis: {_}")
        print("-" * 40)
    
    # Test Bitcoin 105K check
    _ = bridge.check_bitcoin_105k_alert()
    print(f"Bitcoin $105K Alert Check: {_}")
    
    # Generate summary
    _ = bridge.get_telegram_news_summary(24)
    print(f"📊 News Summary: {_}")

if __name__ == "__main__":
    demo_telegram_integration()