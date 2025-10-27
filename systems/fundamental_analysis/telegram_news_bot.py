#!/usr/bin/env python3
"""
WatcherGuru Telegram News Bot Integration
Connects to WatcherGuru Telegram channel for real-time crypto news alerts
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TelegramNewsBot')

class WatcherGuruTelegramBot:
    """
    Real-time news monitoring from WatcherGuru Telegram channel
    """
    
    def __init__(self):
        self.telegram_api_url = "https://api.telegram.org/bot"
        self.bot_token = None  # Will be configured
        self.watcher_guru_channel = "@watcherguru"  # WatcherGuru main channel
        self.chat_id = None
        self.last_update_id = 0
        self.news_cache = []
        self.last_cache_time = 0
        self.running = False
        
        # Database for storing telegram news
        self.db_path = "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/databases/telegram_news.db"
        self.init_database()
        
        # News analysis patterns
        self.crypto_patterns = {
            'BTC': ['bitcoin', 'btc', '$btc'],
            'ETH': ['ethereum', 'eth', '$eth'],
            'SOL': ['solana', 'sol', '$sol'],
            'XRP': ['ripple', 'xrp', '$xrp'],
            'ADA': ['cardano', 'ada', '$ada'],
            'DOGE': ['dogecoin', 'doge', '$doge']
        }
        
        self.price_patterns = [
            'falls below', 'drops under', 'breaks below', 'falls to',
            'rallies above', 'breaks above', 'surges to', 'climbs to',
            'reaches', 'hits', 'touches', 'tests'
        ]
        
        self.sentiment_keywords = {
            'BULLISH': ['rally', 'surge', 'moon', 'bullish', 'pump', 'breakout', 'all-time high', 'ATH'],
            'BEARISH': ['crash', 'dump', 'bearish', 'drop', 'fall', 'plunge', 'decline', 'correction'],
            'NEUTRAL': ['consolidates', 'sideways', 'range', 'stable', 'holds']
        }

    def init_database(self):
        """Initialize SQLite database for telegram news"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER UNIQUE,
                channel TEXT,
                timestamp TEXT,
                content TEXT,
                crypto_mentioned TEXT,
                sentiment TEXT,
                price_alert TEXT,
                importance_score INTEGER,
                processed_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crypto TEXT,
                price REAL,
                direction TEXT,
                timestamp TEXT,
                source_message TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Telegram news database initialized")

    def configure_bot_token(self, token: str):
        """Configure Telegram bot token"""
        self.bot_token = token
        logger.info("📱 Telegram bot token configured")

    async def start_monitoring(self):
        """Start monitoring WatcherGuru Telegram channel"""
        if not self.bot_token:
            logger.error("❌ Bot token not configured. Use configure_bot_token() first")
            return
            
        self.running = True
        logger.info("🚀 Starting WatcherGuru Telegram monitoring...")
        
        while self.running:
            try:
                await self.fetch_channel_updates()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error

    async def fetch_channel_updates(self):
        """Fetch latest updates from WatcherGuru channel"""
        try:
            url = f"{self.telegram_api_url}{self.bot_token}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'limit': 10,
                'timeout': 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok') and data.get('result'):
                            for update in data['result']:
                                await self.process_update(update)
                                self.last_update_id = update['update_id']
                    else:
                        logger.warning(f"Telegram API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching channel updates: {e}")

    async def process_update(self, update: dict):
        """Process a single Telegram update"""
        try:
            # Check for channel posts
            if 'channel_post' in update:
                message = update['channel_post']
                await self.process_channel_message(message)
            
            # Check for messages (if bot is in groups)
            elif 'message' in update:
                message = update['message']
                # Only process if from WatcherGuru related channels
                if self.is_watcher_guru_related(message):
                    await self.process_channel_message(message)
                    
        except Exception as e:
            logger.error(f"Error processing update: {e}")

    def is_watcher_guru_related(self, message: dict) -> bool:
        """Check if message is from WatcherGuru related channel"""
        chat = message.get('chat', {})
        chat_username = chat.get('username', '').lower()
        chat_title = chat.get('title', '').lower()
        
        watcher_guru_keywords = ['watcherguru', 'watcher guru', 'watcher_guru']
        
        return any(keyword in chat_username or keyword in chat_title for keyword in watcher_guru_keywords)

    async def process_channel_message(self, message: dict):
        """Process a channel message for crypto news"""
        try:
            message_id = message.get('message_id')
            timestamp = datetime.fromtimestamp(message.get('date', 0)).isoformat()
            text = message.get('text', '')
            
            if not text or len(text) < 10:
                return
            
            # Analyze the message
            analysis = self.analyze_message(text)
            
            # Check if it's a significant crypto news
            if analysis['crypto_mentioned'] and analysis['importance_score'] >= 7:
                
                # Store in database
                self.store_telegram_news(
                    message_id=message_id,
                    channel=message.get('chat', {}).get('username', 'unknown'),
                    timestamp=timestamp,
                    content=text,
                    analysis=analysis
                )
                
                # Check for price alerts
                await self.check_price_alerts(text, analysis, timestamp)
                
                logger.info(f"📰 Processed important crypto news: {analysis['crypto_mentioned']} - {analysis['sentiment']}")
                
        except Exception as e:
            logger.error(f"Error processing channel message: {e}")

    def analyze_message(self, text: str) -> dict:
        """Analyze message content for crypto relevance and sentiment"""
        text_lower = text.lower()
        
        # Detect mentioned cryptocurrencies
        crypto_mentioned = []
        for crypto, patterns in self.crypto_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                crypto_mentioned.append(crypto)
        
        # Analyze sentiment
        sentiment = 'NEUTRAL'
        sentiment_score = 0
        
        for sent, keywords in self.sentiment_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > sentiment_score:
                sentiment_score = matches
                sentiment = sent
        
        # Check for price alerts
        price_alert = None
        for pattern in self.price_patterns:
            if pattern in text_lower:
                price_alert = self.extract_price_info(text, pattern)
                break
        
        # Calculate importance score
        importance_score = self.calculate_importance_score(
            crypto_mentioned, sentiment, price_alert, text
        )
        
        return {
            'crypto_mentioned': crypto_mentioned,
            'sentiment': sentiment,
            'price_alert': price_alert,
            'importance_score': importance_score
        }

    def extract_price_info(self, text: str, pattern: str) -> Optional[dict]:
        """Extract price information from message"""
        import re
        
        # Look for price patterns
        price_regex = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        
        pattern_index = text.lower().find(pattern)
        if pattern_index == -1:
            return None
        
        # Look for price near the pattern
        search_area = text[max(0, pattern_index-50):pattern_index+50]
        price_matches = re.findall(price_regex, search_area)
        
        if price_matches:
            price_str = price_matches[0].replace(',', '')
            try:
                price = float(price_str)
                direction = 'DOWN' if any(word in pattern for word in ['below', 'under', 'drop', 'fall']) else 'UP'
                
                return {
                    'price': price,
                    'direction': direction,
                    'pattern': pattern
                }
            except ValueError:
                pass
        
        return None

    def calculate_importance_score(self, crypto_mentioned: List[str], sentiment: str, price_alert: dict, text: str) -> int:
        """Calculate importance score (1-10)"""
        score = 0
        
        # Base score for crypto mention
        if crypto_mentioned:
            score += 3
        
        # Major cryptos get higher score
        major_cryptos = ['BTC', 'ETH']
        if any(crypto in major_cryptos for crypto in crypto_mentioned):
            score += 2
        
        # Price alerts are important
        if price_alert:
            score += 3
        
        # Strong sentiment
        if sentiment in ['BULLISH', 'BEARISH']:
            score += 2
        
        # Urgent keywords
        urgent_keywords = ['alert', 'breaking', 'urgent', 'important', 'major']
        if any(keyword in text.lower() for keyword in urgent_keywords):
            score += 2
        
        return min(score, 10)

    def store_telegram_news(self, message_id: int, channel: str, timestamp: str, content: str, analysis: dict):
        """Store processed news in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO telegram_news 
                (message_id, channel, timestamp, content, crypto_mentioned, sentiment, price_alert, importance_score, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                channel,
                timestamp,
                content,
                ','.join(analysis['crypto_mentioned']),
                analysis['sentiment'],
                json.dumps(analysis['price_alert']) if analysis['price_alert'] else None,
                analysis['importance_score'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing telegram news: {e}")

    def check_price_alerts(self, text: str, analysis: dict, timestamp: str):
        """Check for price alerts and store them"""
        if analysis['price_alert'] and analysis['crypto_mentioned']:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for crypto in analysis['crypto_mentioned']:
                    cursor.execute('''
                        INSERT INTO price_alerts 
                        (crypto, price, direction, timestamp, source_message, processed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        crypto,
                        analysis['price_alert']['price'],
                        analysis['price_alert']['direction'],
                        timestamp,
                        text[:200],  # First 200 chars
                        False
                    ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"🚨 Price alert stored: {analysis['crypto_mentioned']} {analysis['price_alert']['direction']} ${analysis['price_alert']['price']}")
                
            except Exception as e:
                logger.error(f"Error storing price alert: {e}")

    def get_recent_news(self, hours: int = 1) -> List[dict]:
        """Get recent news from the last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT * FROM telegram_news 
                WHERE timestamp > ? 
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT 50
            ''', (since_time,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            columns = ['id', 'message_id', 'channel', 'timestamp', 'content', 'crypto_mentioned', 
                      'sentiment', 'price_alert', 'importance_score', 'processed_at']
            
            news = []
            for row in rows:
                news_item = dict(zip(columns, row))
                if news_item['price_alert']:
                    try:
                        news_item['price_alert'] = json.loads(news_item['price_alert'])
                    except Exception as e:
                        news_item['price_alert'] = None
                news.append(news_item)
            
            return news
            
        except Exception as e:
            logger.error(f"Error getting recent news: {e}")
            return []

    def get_price_alerts(self, processed: bool = False) -> List[dict]:
        """Get price alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM price_alerts 
                WHERE processed = ?
                ORDER BY timestamp DESC
                LIMIT 20
            ''', (processed,))
            
            rows = cursor.fetchall()
            conn.close()
            
            columns = ['id', 'crypto', 'price', 'direction', 'timestamp', 'source_message', 'processed']
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting price alerts: {e}")
            return []

    def mark_alert_processed(self, alert_id: int):
        """Mark a price alert as processed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE price_alerts SET processed = TRUE WHERE id = ?', (alert_id,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error marking alert processed: {e}")

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("🛑 Stopping WatcherGuru Telegram monitoring")

# Example usage and testing
def test_telegram_bot():
    """Test the telegram bot functionality"""
    bot = WatcherGuruTelegramBot()
    
    # Example: Test message analysis
    test_messages = [
        "🚨 ALERT: Bitcoin falls below $105,000 as market experiences volatility",
        "📈 Ethereum rallies above $3,700 with strong momentum",
        "⚠️ Breaking: SOL drops to $210 amid broader market correction",
        "🔥 Dogecoin surges 15% following major announcement"
    ]
    
    print("📰 Testing message analysis:")
    for msg in test_messages:
        _ = bot.analyze_message(msg)  # Remove unused variable
        print(f"Message: {msg[:50]}...")
        # print(f"Analysis: {analysis}")  # Commented out since analysis is not used
        print("-" * 50)
    
    # Test database operations
    bot.store_telegram_news(
        message_id=12345,
        channel="watcherguru",
        timestamp=datetime.now().isoformat(),
        content=test_messages[0],
        analysis=bot.analyze_message(test_messages[0])
    )
    
    _ = bot.get_recent_news(24)  # Remove unused variable
    print("📊 Recent news items retrieved")
    
    _ = bot.get_price_alerts()  # Remove unused variable
    print("🚨 Active price alerts: {len(price_alerts)}")

if __name__ == "__main__":
    asyncio.run(test_telegram_bot())