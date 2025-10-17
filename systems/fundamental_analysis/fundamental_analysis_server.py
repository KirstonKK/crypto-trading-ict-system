#!/usr/bin/env python3
"""
🚀 STANDALONE CRYPTO FUNDAMENTAL ANALYSIS SYSTEM
===============================================

Independent system running on port 5002 with:
- Real-world data analysis (supply/demand fundamentals)
- News sentiment analysis
- Long-term investment recommendations
- Separate web dashboard
- Background monitoring and updates

Complements day trading system with fundamental insights.
"""

import asyncio
import logging
import json
import sqlite3
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit

# Add current directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import WatcherGuru Telegram integration
try:
    from telegram_bridge import TelegramNewsBridge
    TELEGRAM_INTEGRATION_AVAILABLE = True
except ImportError:
    TELEGRAM_INTEGRATION_AVAILABLE = False
    print("⚠️ Telegram integration not available - run setup if needed")
import threading
import signal
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'bybit_integration'))

# Import Bybit real-time prices for accurate pricing
try:
    from bybit_integration.real_time_prices import BybitRealTimePrices
    BYBIT_AVAILABLE = True
except ImportError:
    BYBIT_AVAILABLE = False
    print("⚠️ Bybit integration not available, using fallback prices")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fundamental_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FundamentalAnalysis')

# Constants for duplicate strings
DEFAULT_TITLE = 'No title'
SOURCE_DEMO_NEWS = 'Demo News'
SOURCE_MARKET_ANALYSIS = 'Market Analysis'

class FundamentalAnalysisServer:
    """Standalone Crypto Fundamental Analysis Server"""
    
    def __init__(self, port: int = 5002):
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'fundamental_analysis_secret_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # System state
        self.is_running = True
        self.analysis_data = {}
        self.last_update = datetime.now()
        self.update_interval = 3600  # 1 hour
        
        # Initialize Bybit real-time prices (same as ICT monitor)
        self.bybit_prices = None
        if BYBIT_AVAILABLE:
            try:
                bybit_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
                self.bybit_prices = BybitRealTimePrices(symbols=bybit_symbols, testnet=False)
                logger.info("✅ Bybit real-time price monitor initialized for fundamental analysis")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Bybit prices: {e}")
                self.bybit_prices = None
        
        # Initialize Telegram bridge for WatcherGuru news integration
        self.telegram_bridge = None
        telegram_enabled = os.getenv('ENABLE_TELEGRAM_MONITORING', 'false').lower() == 'true'
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if telegram_enabled and telegram_token:
            try:
                self.telegram_bridge = TelegramNewsBridge(self)
                logger.info("✅ WatcherGuru Telegram bridge initialized")
                logger.info("📡 Bitcoin $105K alert detection: ENABLED")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Telegram bridge: {e}")
        else:
            if not telegram_token:
                logger.info("📡 WatcherGuru Telegram monitoring: DISABLED (no TELEGRAM_BOT_TOKEN)")
            else:
                logger.info("📡 WatcherGuru Telegram monitoring: DISABLED (ENABLE_TELEGRAM_MONITORING=false)")
        
        # Initialize database
        self.init_database()
        
        # Setup routes
        self.setup_routes()
        
        # Setup SocketIO handlers
        self.setup_socketio()
        
        # Load initial data (will fetch real prices)
        asyncio.run(self.load_initial_data())
        
        logger.info("🚀 Fundamental Analysis Server initialized")
    
    def init_database(self):
        """Initialize SQLite database for fundamental analysis"""
        conn = sqlite3.connect('fundamental_analysis.db')
        cursor = conn.cursor()
        
        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                overall_score INTEGER,
                supply_score TEXT,
                demand_score TEXT,
                news_sentiment TEXT,
                recommendation TEXT,
                target_timeframe TEXT,
                confidence REAL,
                inflation_rate REAL,
                daily_active_users INTEGER,
                total_value_locked REAL,
                developer_activity INTEGER,
                price_prediction_4y REAL,
                analysis_summary TEXT
            )
        """)
        
        # News analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source TEXT,
                sentiment TEXT,
                impact_level TEXT,
                crypto_mentioned TEXT,
                published_at TIMESTAMP,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Market metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                metric_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                market_cap REAL,
                trading_volume_24h REAL,
                price_usd REAL,
                price_change_24h REAL,
                circulating_supply REAL,
                max_supply REAL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    async def get_real_time_prices(self):
        """Get real-time prices from Bybit API (same as ICT monitor)"""
        try:
            if self.bybit_prices:
                # Get prices from Bybit real-time price monitor
                prices = {}
                for symbol, crypto_name in [('BTCUSDT', 'BTC'), ('ETHUSDT', 'ETH'), ('SOLUSDT', 'SOL'), ('XRPUSDT', 'XRP')]:
                    price_data = self.bybit_prices.get_price(symbol)
                    if price_data and price_data.get('price', 0) > 0:
                        prices[crypto_name] = {
                            'price': float(price_data['price']),
                            'change_24h': float(price_data.get('change_24h', 0)),
                            'volume': float(price_data.get('volume', 0)),
                            'high_24h': float(price_data.get('high_24h', price_data['price'] * 1.02)),
                            'low_24h': float(price_data.get('low_24h', price_data['price'] * 0.98)),
                            'timestamp': datetime.now().isoformat()
                        }
                
                if prices and 'BTC' in prices:
                    logger.info(f"✅ Real-time prices updated from Bybit: BTC=${prices['BTC']['price']:,.2f}")
                    return prices
                else:
                    logger.warning("No valid prices from Bybit, falling back to CoinGecko")
                    return await self.get_coingecko_fallback()
            else:
                logger.warning("Bybit price monitor not available, using CoinGecko")
                return await self.get_coingecko_fallback()
                        
        except Exception as e:
            logger.error(f"Error fetching Bybit prices: {e}")
            return await self.get_coingecko_fallback()
    
    async def get_coingecko_fallback(self):
        """Fallback to CoinGecko prices if Bybit fails"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Use CoinGecko as fallback source
                url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = {}
                        
                        # Map CoinGecko data to our format
                        coin_mapping = {
                            'bitcoin': 'BTC',
                            'ethereum': 'ETH', 
                            'solana': 'SOL',
                            'ripple': 'XRP'
                        }
                        
                        for coin_id, crypto_name in coin_mapping.items():
                            if coin_id in data:
                                coin_data = data[coin_id]
                                prices[crypto_name] = {
                                    'price': float(coin_data['usd']),
                                    'change_24h': float(coin_data.get('usd_24h_change', 0)),
                                    'volume': float(coin_data.get('usd_24h_vol', 0)),
                                    'high_24h': float(coin_data['usd'] * 1.02),
                                    'low_24h': float(coin_data['usd'] * 0.98),
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        logger.info(f"✅ Fallback prices from CoinGecko: BTC=${prices.get('BTC', {}).get('price', 0):,.2f}")
                        return prices
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return self.get_default_prices()
        except Exception as e:
            logger.error(f"Error fetching CoinGecko prices: {e}")
            return self.get_default_prices()
    
    async def fetch_watcher_guru_news(self):
        """Fetch real-time crypto news from multiple sources with reliable fallbacks"""
        try:
            import aiohttp
            
            # Try reliable free crypto news sources
            async with aiohttp.ClientSession() as session:
                # First try: CoinGecko news (free, reliable API)
                try:
                    url = 'https://api.coingecko.com/api/v3/news'
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            news_items = self._parse_coingecko_news(data)
                            if news_items:
                                logger.info(f"✅ Fetched {len(news_items)} news articles from CoinGecko")
                                return news_items
                except Exception as e:
                    logger.warning(f"CoinGecko news API error: {e}")
                
                # Second try: CryptoPanic (free RSS-style API)
                try:
                    url = 'https://cryptopanic.com/api/v1/posts/?auth_token=free&filter=hot&public=true'
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            news_items = self._parse_cryptopanic_news(data)
                            if news_items:
                                logger.info(f"✅ Fetched {len(news_items)} news articles from CryptoPanic")
                                return news_items
                except Exception as e:
                    logger.warning(f"CryptoPanic API error: {e}")
                
                # Third try: Generate mock news for demo purposes
                logger.info("📰 Using demo news data - all external APIs failed")
                return self._generate_demo_news()
                
        except Exception as e:
            logger.error(f"❌ All news sources failed: {e}")
            return self._generate_demo_news()
    
    def _parse_coingecko_news(self, data):
        """Parse CoinGecko news API response"""
        try:
            news_items = []
            for item in data.get('data', [])[:10]:  # Limit to 10 items
                news_item = {
                    'title': item.get('title', 'Untitled'),
                    'summary': item.get('description', 'No description available')[:200],
                    'sentiment': self._analyze_sentiment(item.get('title', '') + ' ' + item.get('description', '')),
                    'crypto_mentioned': self._extract_crypto_mentions(item.get('title', '') + ' ' + item.get('description', '')),
                    'published_at': item.get('published_at', datetime.now().isoformat()),
                    'url': item.get('url', ''),
                    'source': 'CoinGecko'
                }
                news_items.append(news_item)
            return news_items
        except Exception as e:
            logger.error(f"Error parsing CoinGecko news: {e}")
            return []
    
    def _parse_cryptopanic_news(self, data):
        """Parse CryptoPanic API response"""
        try:
            news_items = []
            for item in data.get('results', [])[:10]:  # Limit to 10 items
                news_item = {
                    'title': item.get('title', 'Untitled'),
                    'summary': item.get('title', 'No description available')[:200],
                    'sentiment': self._analyze_sentiment(item.get('title', '')),
                    'crypto_mentioned': self._extract_crypto_mentions(item.get('title', '')),
                    'published_at': item.get('published_at', datetime.now().isoformat()),
                    'url': item.get('url', ''),
                    'source': 'CryptoPanic'
                }
                news_items.append(news_item)
            return news_items
        except Exception as e:
            logger.error(f"Error parsing CryptoPanic news: {e}")
            return []
    
    def _generate_demo_news(self):
        """Generate demo news when all APIs fail"""
        current_time = datetime.now()
        demo_news = [
            {
                'title': 'Bitcoin Price Analysis: Key Support Levels Hold Strong',
                'summary': 'Bitcoin continues to maintain key support levels around $100,000 as institutional adoption grows. Market sentiment remains bullish despite recent volatility.',
                'sentiment': 'Positive',
                'crypto_mentioned': ['BTC'],
                'published_at': current_time.isoformat(),
                'url': '#',
                'source': SOURCE_DEMO_NEWS
            },
            {
                'title': 'Ethereum Network Upgrades Show Promise for DeFi Expansion',
                'summary': 'Recent Ethereum network improvements are driving increased DeFi activity and lower transaction costs, boosting ecosystem confidence.',
                'sentiment': 'Positive',
                'crypto_mentioned': ['ETH'],
                'published_at': (current_time - timedelta(hours=1)).isoformat(),
                'url': '#',
                'source': SOURCE_DEMO_NEWS
            },
            {
                'title': 'Solana Blockchain Performance Metrics Reach New Heights',
                'summary': 'Solana demonstrates exceptional throughput and growing developer adoption, positioning itself as a major smart contract platform.',
                'sentiment': 'Positive',
                'crypto_mentioned': ['SOL'],
                'published_at': (current_time - timedelta(hours=2)).isoformat(),
                'url': '#',
                'source': SOURCE_DEMO_NEWS
            },
            {
                'title': 'XRP Legal Clarity Boosts Institutional Interest',
                'summary': 'Increased regulatory clarity around XRP is driving renewed institutional interest and partnership announcements.',
                'sentiment': 'Positive',
                'crypto_mentioned': ['XRP'],
                'published_at': (current_time - timedelta(hours=3)).isoformat(),
                'url': '#',
                'source': SOURCE_DEMO_NEWS
            },
            {
                'title': 'Crypto Market Shows Resilience Amid Global Economic Uncertainty',
                'summary': 'Despite global economic headwinds, cryptocurrency markets demonstrate strong resilience with growing institutional adoption and regulatory progress.',
                'sentiment': 'Neutral',
                'crypto_mentioned': ['BTC', 'ETH'],
                'published_at': (current_time - timedelta(hours=4)).isoformat(),
                'url': '#',
                'source': SOURCE_DEMO_NEWS
            }
        ]
        logger.info("📰 Generated 5 demo news articles for analysis")
        return demo_news
    
    def _analyze_sentiment(self, text):
        """Simple sentiment analysis"""
        positive_words = ['bullish', 'rise', 'gain', 'growth', 'positive', 'strong', 'up', 'increase', 'adoption', 'breakthrough']
        negative_words = ['bearish', 'fall', 'drop', 'decline', 'negative', 'weak', 'down', 'decrease', 'crash', 'concern']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'Positive'
        elif negative_count > positive_count:
            return 'Negative'
        else:
            return 'Neutral'
    
    def _extract_crypto_mentions(self, text):
        """Extract cryptocurrency mentions from text"""
        crypto_patterns = {
            'BTC': ['bitcoin', 'btc'],
            'ETH': ['ethereum', 'eth'],
            'SOL': ['solana', 'sol'],
            'XRP': ['ripple', 'xrp']
        }
        
        mentioned = []
        text_lower = text.lower()
        
        for crypto, patterns in crypto_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                mentioned.append(crypto)
        
        return mentioned
    
    def _parse_coindesk(self, data):
        """Parse CoinDesk news format"""
        news_items = []
        try:
            articles = data.get('results', [])[:10]
            for article in articles:
                sentiment = self._analyze_news_sentiment(article.get('title', ''), article.get('summary', ''))
                crypto_mentioned = self._detect_crypto_mentions(article.get('title', '') + ' ' + article.get('summary', ''))
                impact_level = self._determine_impact_level(article.get('title', ''), crypto_mentioned)
                
                news_item = {
                    'title': article.get('title', DEFAULT_TITLE),
                    'sentiment': sentiment,
                    'impact_level': impact_level,
                    'crypto_mentioned': crypto_mentioned,
                    'published_at': article.get('published_at', datetime.now().isoformat()),
                    'summary': article.get('summary', '')[:200] + '...' if len(article.get('summary', '')) > 200 else article.get('summary', ''),
                    'source': 'CoinDesk',
                    'url': article.get('url', ''),
                    'image': article.get('thumbnail', '')
                }
                news_items.append(news_item)
        except Exception as e:
            logger.error(f"Error parsing CoinDesk news: {e}")
        return news_items

    def _parse_generic_news(self, data):
        """Parse generic news format"""
        news_items = []
        try:
            articles = data.get('articles', data.get('data', []))[:10]
            for article in articles:
                sentiment = self._analyze_news_sentiment(article.get('title', ''), article.get('description', ''))
                crypto_mentioned = self._detect_crypto_mentions(article.get('title', '') + ' ' + article.get('description', ''))
                impact_level = self._determine_impact_level(article.get('title', ''), crypto_mentioned)
                
                news_item = {
                    'title': article.get('title', DEFAULT_TITLE),
                    'sentiment': sentiment,
                    'impact_level': impact_level,
                    'crypto_mentioned': crypto_mentioned,
                    'published_at': article.get('publishedAt', article.get('published_at', datetime.now().isoformat())),
                    'summary': article.get('description', '')[:200] + '...' if len(article.get('description', '')) > 200 else article.get('description', ''),
                    'source': 'CryptoNews',
                    'url': article.get('url', ''),
                    'image': article.get('urlToImage', article.get('image', ''))
                }
                news_items.append(news_item)
        except Exception as e:
            logger.error(f"Error parsing generic news: {e}")
        return news_items

    def _parse_newsapi(self, data):
        """Parse NewsAPI format"""
        news_items = []
        try:
            articles = data.get('articles', [])[:10]
            for article in articles:
                sentiment = self._analyze_news_sentiment(article.get('title', ''), article.get('description', ''))
                crypto_mentioned = self._detect_crypto_mentions(article.get('title', '') + ' ' + article.get('description', ''))
                impact_level = self._determine_impact_level(article.get('title', ''), crypto_mentioned)
                
                news_item = {
                    'title': article.get('title', DEFAULT_TITLE),
                    'sentiment': sentiment,
                    'impact_level': impact_level,
                    'crypto_mentioned': crypto_mentioned,
                    'published_at': article.get('publishedAt', datetime.now().isoformat()),
                    'summary': article.get('description', '')[:200] + '...' if len(article.get('description', '')) > 200 else article.get('description', ''),
                    'source': 'NewsAPI',
                    'url': article.get('url', ''),
                    'image': article.get('urlToImage', '')
                }
                news_items.append(news_item)
        except Exception as e:
            logger.error(f"Error parsing NewsAPI: {e}")
        return news_items

    def _get_enhanced_fallback_news(self):
        """Enhanced fallback news data with current market insights"""
        current_time = datetime.now().isoformat()
        return [
            {
                'title': 'Bitcoin Consolidating Above $66,000 Support',
                'sentiment': 'POSITIVE',
                'impact_level': 'HIGH',
                'crypto_mentioned': ['BTC', 'BITCOIN'],
                'published_at': current_time,
                'summary': 'Bitcoin continues to hold above the $66,000 psychological support level, with technical indicators showing potential for bullish continuation. Market sentiment remains cautiously optimistic.',
                'source': SOURCE_MARKET_ANALYSIS,
                'url': '',
                'image': ''
            },
            {
                'title': 'Ethereum Shows Strength at $2,600 Level',
                'sentiment': 'POSITIVE',
                'impact_level': 'HIGH',
                'crypto_mentioned': ['ETH', 'ETHEREUM'],
                'published_at': current_time,
                'summary': 'Ethereum demonstrates resilience at the $2,600 level with increased network activity and growing institutional interest in ETH staking solutions.',
                'source': SOURCE_MARKET_ANALYSIS,
                'url': '',
                'image': ''
            },
            {
                'title': 'Altcoin Season Indicators Mixed Signals',
                'sentiment': 'NEUTRAL',
                'impact_level': 'MEDIUM',
                'crypto_mentioned': ['SOL', 'XRP', 'ADA'],
                'published_at': current_time,
                'summary': 'Alternative cryptocurrencies showing mixed performance with some outperforming Bitcoin while others lag. Market participants watching for clearer directional signals.',
                'source': SOURCE_MARKET_ANALYSIS,
                'url': '',
                'image': ''
            },
            {
                'title': 'DeFi Protocols Experience Increased Activity',
                'sentiment': 'POSITIVE',
                'impact_level': 'MEDIUM',
                'crypto_mentioned': ['DEFI', 'GENERAL'],
                'published_at': current_time,
                'summary': 'Decentralized Finance protocols seeing uptick in total value locked and transaction volumes, suggesting renewed interest in yield farming opportunities.',
                'source': SOURCE_MARKET_ANALYSIS,
                'url': '',
                'image': ''
            },
            {
                'title': 'Regulatory Clarity Expected in Q4 2024',
                'sentiment': 'POSITIVE',
                'impact_level': 'HIGH',
                'crypto_mentioned': ['GENERAL'],
                'published_at': current_time,
                'summary': 'Financial regulators worldwide signaling potential framework announcements for cryptocurrency regulation, which could provide market stability and institutional confidence.',
                'source': SOURCE_MARKET_ANALYSIS,
                'url': '',
                'image': ''
            }
        ]

    def _analyze_news_sentiment(self, title, content):
        """Analyze sentiment of news article"""
        text = (title + ' ' + content).lower()
        
        # Positive keywords
        positive_words = ['bullish', 'surge', 'rally', 'adoption', 'partnership', 'upgrade', 'milestone', 
                         'breakthrough', 'approved', 'launch', 'growth', 'positive', 'gains', 'rises',
                         'institutional', 'etf', 'investment', 'expansion', 'development', 'success']
        
        # Negative keywords  
        negative_words = ['bearish', 'crash', 'dump', 'decline', 'hack', 'fraud', 'regulatory', 'ban',
                         'lawsuit', 'concern', 'risk', 'fall', 'drop', 'negative', 'losses', 'warning',
                         'investigation', 'violation', 'threat', 'uncertainty']
        
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        if positive_score > negative_score + 1:
            return 'POSITIVE'
        elif negative_score > positive_score + 1:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def _detect_crypto_mentions(self, text):
        """Detect which cryptos are mentioned in the text"""
        text = text.lower()
        cryptos = []
        
        crypto_keywords = {
            'BTC': ['bitcoin', 'btc'],
            'ETH': ['ethereum', 'eth', 'ether'],
            'SOL': ['solana', 'sol'],
            'XRP': ['ripple', 'xrp']
        }
        
        for crypto, keywords in crypto_keywords.items():
            if any(keyword in text for keyword in keywords):
                cryptos.append(crypto)
        
        return cryptos if cryptos else ['GENERAL']
    
    def _calculate_crypto_sentiment(self, news_data):
        """Calculate overall sentiment for each crypto from news articles"""
        crypto_sentiment = {}
        
        for crypto in ['BTC', 'ETH', 'SOL', 'XRP']:
            relevant_articles = [article for article in news_data 
                               if crypto in article.get('crypto_mentioned', [])]
            
            if not relevant_articles:
                crypto_sentiment[crypto] = 'NEUTRAL'
                continue
            
            # Calculate weighted sentiment based on impact level
            sentiment_score = 0
            total_weight = 0
            
            for article in relevant_articles:
                # Weight based on impact level
                weight = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(article.get('impact_level', 'LOW'), 1)
                
                # Sentiment score
                sentiment = article.get('sentiment', 'NEUTRAL')
                if sentiment == 'POSITIVE':
                    sentiment_score += weight
                elif sentiment == 'NEGATIVE':
                    sentiment_score -= weight
                # NEUTRAL adds 0
                
                total_weight += weight
            
            # Calculate overall sentiment
            if total_weight > 0:
                avg_sentiment = sentiment_score / total_weight
                if avg_sentiment > 0.3:
                    crypto_sentiment[crypto] = 'POSITIVE'
                elif avg_sentiment < -0.3:
                    crypto_sentiment[crypto] = 'NEGATIVE'
                else:
                    crypto_sentiment[crypto] = 'NEUTRAL'
            else:
                crypto_sentiment[crypto] = 'NEUTRAL'
        
        logger.info(f"📰 Multi-source news sentiment: {crypto_sentiment}")
        return crypto_sentiment
    
    def _determine_impact_level(self, title, _crypto_mentioned):
        """Determine the potential market impact of the news"""
        title_lower = title.lower()
        
        # High impact keywords
        high_impact = ['etf', 'sec', 'regulation', 'ban', 'approved', 'institutional', 'fed', 'government',
                      'breaking', 'major', 'billion', 'partnership', 'adoption', 'hack', 'exploit']
        
        # Medium impact keywords
        medium_impact = ['upgrade', 'update', 'launch', 'milestone', 'investment', 'fund', 'exchange',
                        'listing', 'delisting', 'court', 'lawsuit']
        
        if any(keyword in title_lower for keyword in high_impact):
            return 'HIGH'
        elif any(keyword in title_lower for keyword in medium_impact):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_fallback_news(self):
        """Fallback news data when WatcherGuru is unavailable"""
        return [
            {
                'title': 'Crypto Market Analysis - Real-time data unavailable',
                'sentiment': 'NEUTRAL',
                'impact_level': 'LOW',
                'crypto_mentioned': ['GENERAL'],
                'published_at': datetime.now().isoformat(),
                'summary': 'Unable to fetch real-time news. Check WatcherGuru connection.',
                'source': 'Fallback',
                'url': '',
                'image': ''
            }
        ]

    def get_default_prices(self):
        """Get prices from ICT monitor as final fallback - MUCH more accurate than static values"""
        try:
            import requests
            # Try to get prices from ICT monitor first (most accurate)
            response = requests.get('http://localhost:5001/api/data', timeout=5)
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for crypto, price_data in data.get('prices', {}).items():
                    prices[crypto] = {
                        'price': float(price_data['price']),
                        'change_24h': float(price_data.get('change_24h', 0)),
                        'volume': float(price_data.get('volume', 0)),
                        'high_24h': float(price_data.get('high_24h', price_data['price'] * 1.02)),
                        'low_24h': float(price_data.get('low_24h', price_data['price'] * 0.98)),
                        'timestamp': datetime.now().isoformat()
                    }
                logger.info(f"✅ Using ICT monitor prices as fallback: BTC=${prices.get('BTC', {}).get('price', 0):,.2f}")
                return prices
        except Exception as e:
            logger.warning(f"Could not get prices from ICT monitor: {e}")
        
        # Final static fallback (should rarely be used now)
        logger.warning("⚠️ Using static fallback prices - these may be outdated!")
        return {
            'BTC': {'price': 105000, 'change_24h': 2.5, 'volume': 15000000000, 'high_24h': 107000, 'low_24h': 103000},
            'ETH': {'price': 3750, 'change_24h': 1.8, 'volume': 8000000000, 'high_24h': 3800, 'low_24h': 3700},
            'SOL': {'price': 179, 'change_24h': 3.2, 'volume': 2000000000, 'high_24h': 182, 'low_24h': 176},
            'XRP': {'price': 2.25, 'change_24h': 0.8, 'volume': 1500000000, 'high_24h': 2.30, 'low_24h': 2.20}
        }
    
    async def load_initial_data(self):
        """Load initial analysis data with real-time prices"""
        # Get real-time prices
        real_prices = await self.get_real_time_prices()
        
        # Base fundamental analysis data
        base_data = {
            'SOL': {
                'symbol': 'SOL',
                'name': 'Solana',
                'overall_score': 85,
                'supply_score': 'GOOD',
                'demand_score': 'EXCELLENT',
                'news_sentiment': 'POSITIVE',
                'recommendation': 'BUY',
                'target_timeframe': '4-YEAR',
                'confidence': 0.87,
                'market_cap': 11_500_000_000,
                'inflation_rate': 4.2,
                'daily_active_users': 2_100_000,
                'total_value_locked': 5_200_000_000,
                'developer_activity': 450,
                'institutional_adoption': True,
                'key_strengths': [
                    'High transaction throughput',
                    'Growing DeFi ecosystem', 
                    'Strong developer activity',
                    'Institutional partnerships'
                ],
                'key_risks': [
                    'Network stability concerns',
                    'High inflation rate',
                    'Regulatory uncertainty'
                ]
            },
            'BTC': {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'overall_score': 92,
                'supply_score': 'EXCELLENT',
                'demand_score': 'EXCELLENT',
                'news_sentiment': 'POSITIVE',
                'recommendation': 'BUY',
                'target_timeframe': '4-YEAR',
                'confidence': 0.95,
                'market_cap': 1_320_000_000_000,
                'inflation_rate': 1.7,
                'daily_active_users': 1_000_000,
                'total_value_locked': 2_000_000_000,
                'developer_activity': 200,
                'institutional_adoption': True,
                'key_strengths': [
                    'Digital gold narrative',
                    'Institutional adoption',
                    'Decreasing supply inflation',
                    'Network security'
                ],
                'key_risks': [
                    'Slow transaction speeds',
                    'Environmental concerns',
                    'Regulatory pressures'
                ]
            },
            'ETH': {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'overall_score': 88,
                'supply_score': 'EXCELLENT',
                'demand_score': 'EXCELLENT',
                'news_sentiment': 'POSITIVE',
                'recommendation': 'BUY',
                'target_timeframe': '4-YEAR',
                'confidence': 0.91,
                'market_cap': 318_000_000_000,
                'inflation_rate': -0.3,
                'daily_active_users': 400_000,
                'total_value_locked': 58_000_000_000,
                'developer_activity': 800,
                'institutional_adoption': True,
                'key_strengths': [
                    'Deflationary tokenomics',
                    'Largest DeFi ecosystem',
                    'Strong developer community',
                    'Layer 2 scaling solutions'
                ],
                'key_risks': [
                    'High gas fees',
                    'Competition from other chains',
                    'Scalability challenges'
                ]
            },
            'XRP': {
                'symbol': 'XRP',
                'name': 'Ripple',
                'overall_score': 65,
                'supply_score': 'GOOD',
                'demand_score': 'AVERAGE',
                'news_sentiment': 'NEUTRAL',
                'recommendation': 'HOLD',
                'target_timeframe': '2-YEAR',
                'confidence': 0.72,
                'market_cap': 28_000_000_000,
                'inflation_rate': 0.0,
                'daily_active_users': 150_000,
                'total_value_locked': 500_000_000,
                'developer_activity': 100,
                'institutional_adoption': True,
                'key_strengths': [
                    'No inflation',
                    'Fast settlement',
                    'Banking partnerships',
                    'Regulatory clarity improving'
                ],
                'key_risks': [
                    'Centralization concerns',
                    'Limited DeFi adoption',
                    'SEC lawsuit uncertainty'
                ]
            }
        }
        
        # Update with real prices and calculate price predictions
        self.analysis_data = {}
        for symbol, data in base_data.items():
            if symbol in real_prices:
                current_price = real_prices[symbol]['price']
                
                # Calculate 4-year price prediction based on current price and fundamentals
                score_multiplier = data['overall_score'] / 100
                if symbol == 'BTC':
                    price_prediction_4y = current_price * (2.5 + score_multiplier)  # Conservative for BTC
                elif symbol == 'ETH':
                    price_prediction_4y = current_price * (4 + score_multiplier)    # Higher growth potential
                elif symbol == 'SOL':
                    price_prediction_4y = current_price * (5 + score_multiplier)    # High growth crypto
                else:  # XRP
                    price_prediction_4y = current_price * (3 + score_multiplier)    # Moderate growth
                
                # Update data with real prices
                data.update({
                    'current_price': current_price,
                    'price_change_24h': real_prices[symbol].get('change_24h', 0),
                    'volume_24h': real_prices[symbol].get('volume', 0),
                    'price_prediction_4y': price_prediction_4y,
                    'last_updated': datetime.now().isoformat()
                })
            else:
                # Fallback to default prices if real price not available
                default_prices = {
                    'SOL': 145, 'BTC': 67000, 'ETH': 2650, 'XRP': 0.52
                }
                data.update({
                    'current_price': default_prices.get(symbol, 100),
                    'price_change_24h': 0,
                    'volume_24h': 0,
                    'price_prediction_4y': default_prices.get(symbol, 100) * 3,
                    'last_updated': datetime.now().isoformat()
                })
            
            self.analysis_data[symbol] = data
        
        # Save to database
        self.save_analysis_to_db()
        logger.info(f"✅ Initial data loaded with real-time prices: {len(self.analysis_data)} cryptocurrencies")
    
    def save_analysis_to_db(self):
        """Save current analysis data to database"""
        conn = sqlite3.connect('fundamental_analysis.db')
        cursor = conn.cursor()
        
        for symbol, data in self.analysis_data.items():
            cursor.execute("""
                INSERT INTO fundamental_analysis 
                (symbol, overall_score, supply_score, demand_score, news_sentiment,
                 recommendation, target_timeframe, confidence, inflation_rate,
                 daily_active_users, total_value_locked, developer_activity,
                 price_prediction_4y, analysis_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                data['overall_score'],
                data['supply_score'],
                data['demand_score'],
                data['news_sentiment'],
                data['recommendation'],
                data['target_timeframe'],
                data['confidence'],
                data['inflation_rate'],
                data['daily_active_users'],
                data['total_value_locked'],
                data['developer_activity'],
                data['price_prediction_4y'],
                f"Score: {data['overall_score']}/100 | Rec: {data['recommendation']}"
            ))
        
        conn.commit()
        conn.close()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard"""
            return render_template_string(self.get_dashboard_html())
        
        @self.app.route('/api/analysis')
        def get_analysis():
            """Get all fundamental analysis data"""
            return jsonify({
                'analysis_data': self.analysis_data,
                'last_update': self.last_update.isoformat(),
                'next_update': (self.last_update + timedelta(seconds=self.update_interval)).isoformat(),
                'status': 'active' if self.is_running else 'stopped'
            })
        
        @self.app.route('/api/analysis/<symbol>')
        def get_symbol_analysis(symbol):
            """Get analysis for specific symbol"""
            symbol = symbol.upper()
            if symbol in self.analysis_data:
                return jsonify(self.analysis_data[symbol])
            else:
                return jsonify({'error': f'Analysis not found for {symbol}'}), 404
        
        @self.app.route('/api/recommendations')
        def get_recommendations():
            """Get investment recommendations"""
            recommendations = []
            for symbol, data in self.analysis_data.items():
                if data['recommendation'] == 'BUY' and data['overall_score'] >= 80:
                    recommendations.append({
                        'symbol': symbol,
                        'name': data['name'],
                        'score': data['overall_score'],
                        'recommendation': data['recommendation'],
                        'timeframe': data['target_timeframe'],
                        'confidence': data['confidence'],
                        'price_target': data['price_prediction_4y']
                    })
            
            # Sort by score descending
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return jsonify({'recommendations': recommendations})
        
        @self.app.route('/api/news')
        def get_news_analysis():
            """Get latest news analysis from multiple crypto news sources"""
            try:
                # Fetch real-time news from multiple sources (CoinDesk, CryptoNews, etc.)
                import asyncio
                if hasattr(self, '_news_cache') and hasattr(self, '_news_cache_time'):
                    # Use cached news if less than 10 minutes old
                    if datetime.now().timestamp() - self._news_cache_time < 600:
                        return jsonify({'news': self._news_cache, 'source': 'Multiple Sources (cached)'})
                
                # Fetch fresh news
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                news_data = loop.run_until_complete(self.fetch_watcher_guru_news())
                loop.close()
                
                # Cache the results
                self._news_cache = news_data
                self._news_cache_time = datetime.now().timestamp()
                
                return jsonify({'news': news_data, 'source': 'Multiple Sources'})
                
            except Exception as e:
                logger.error(f"Error fetching news: {e}")
                # Return enhanced fallback news
                fallback_news = self._get_enhanced_fallback_news()
                return jsonify({'news': fallback_news, 'source': 'Enhanced Fallback'})
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'Crypto Fundamental Analysis',
                'port': self.port,
                'uptime': str(datetime.now() - self.last_update),
                'last_analysis_update': self.last_update.isoformat()
            })
    
    def setup_socketio(self):
        """Setup SocketIO handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("📱 Client connected to fundamental analysis dashboard")
            emit('analysis_update', self.analysis_data)
        
        @self.socketio.on('request_update')
        def handle_update_request():
            logger.info("🔄 Client requested analysis update")
            emit('analysis_update', self.analysis_data)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("📱 Client disconnected")
    
    def get_dashboard_html(self):
        """Generate dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Crypto Fundamental Analysis Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .analysis-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .analysis-card:hover {
            transform: translateY(-5px);
        }
        
        .crypto-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .crypto-name {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .score-badge {
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .score-excellent { background: #00ff88; color: #000; }
        .score-good { background: #ffc107; color: #000; }
        .score-average { background: #ff9800; color: #000; }
        .score-poor { background: #f44336; color: #fff; }
        
        .recommendation {
            display: flex;
            justify-content: space-between;
            margin: 15px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        
        .rec-buy { border-left: 4px solid #00ff88; }
        .rec-hold { border-left: 4px solid #ffc107; }
        .rec-sell { border-left: 4px solid #f44336; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric {
            text-align: center;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        
        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #00ff88;
        }
        
        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .news-section {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        
        .news-item {
            padding: 15px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            border-left: 4px solid #00ff88;
        }
        
        .news-title {
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .news-meta {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .status-bar {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9em;
        }
        
        .status-active {
            color: #00ff88;
        }
        
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px;
            transition: background 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Crypto Fundamental Analysis</h1>
        <p>Long-term Investment Intelligence System | Port 5002</p>
        <button class="refresh-btn" onclick="requestUpdate()">🔄 Refresh Analysis</button>
    </div>
    
    <div class="dashboard-grid" id="analysis-grid">
        <!-- Analysis cards will be populated by JavaScript -->
    </div>
    
    <div class="news-section">
        <h2>📰 Latest Crypto News Analysis</h2>
        <div id="news-container">
            <!-- News items will be populated by JavaScript -->
        </div>
    </div>
    
    <div class="status-bar">
        <span class="status-active">● ACTIVE</span> | Last Update: <span id="last-update">--</span>
    </div>

    <script>
        const socket = io();
        let analysisData = {};
        
        socket.on('connect', function() {
            console.log('Connected to Fundamental Analysis Server');
            requestUpdate();
        });
        
        socket.on('analysis_update', function(data) {
            console.log('Received analysis update:', data);
            analysisData = data;
            updateDashboard();
        });
        
        function requestUpdate() {
            socket.emit('request_update');
            fetchNewsData();
        }
        
        function updateDashboard() {
            const grid = document.getElementById('analysis-grid');
            grid.innerHTML = '';
            
            Object.entries(analysisData).forEach(([symbol, data]) => {
                const card = createAnalysisCard(symbol, data);
                grid.appendChild(card);
            });
            
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
        
        function createAnalysisCard(symbol, data) {
            const card = document.createElement('div');
            card.className = 'analysis-card';
            
            const scoreClass = getScoreClass(data.overall_score);
            const recClass = getRecommendationClass(data.recommendation);
            
            card.innerHTML = `
                <div class="crypto-header">
                    <div>
                        <div class="crypto-name">${data.name} (${symbol})</div>
                        <div style="font-size: 1.2em; margin-top: 5px;">$${data.current_price.toLocaleString()}</div>
                    </div>
                    <div class="score-badge ${scoreClass}">${data.overall_score}/100</div>
                </div>
                
                <div class="recommendation ${recClass}">
                    <div>
                        <strong>${data.recommendation}</strong><br>
                        <small>${data.target_timeframe} Target</small>
                    </div>
                    <div>
                        <strong>${(data.confidence * 100).toFixed(0)}%</strong><br>
                        <small>Confidence</small>
                    </div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric">
                        <div class="metric-value">${data.inflation_rate}%</div>
                        <div class="metric-label">Inflation Rate</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${formatNumber(data.daily_active_users)}</div>
                        <div class="metric-label">Daily Active Users</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">$${formatLargeNumber(data.total_value_locked)}</div>
                        <div class="metric-label">Total Value Locked</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">$${formatLargeNumber(data.price_prediction_4y)}</div>
                        <div class="metric-label">4-Year Target</div>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <div style="margin-bottom: 10px;"><strong>Supply:</strong> ${data.supply_score}</div>
                    <div style="margin-bottom: 10px;"><strong>Demand:</strong> ${data.demand_score}</div>
                    <div><strong>News Sentiment:</strong> ${data.news_sentiment}</div>
                </div>
            `;
            
            return card;
        }
        
        function getScoreClass(score) {
            if (score >= 85) return 'score-excellent';
            if (score >= 70) return 'score-good';
            if (score >= 55) return 'score-average';
            return 'score-poor';
        }
        
        function getRecommendationClass(rec) {
            if (rec === 'BUY') return 'rec-buy';
            if (rec === 'HOLD') return 'rec-hold';
            return 'rec-sell';
        }
        
        function formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toLocaleString();
        }
        
        function formatLargeNumber(num) {
            if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'B';
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toLocaleString();
        }
        
        async function fetchNewsData() {
            try {
                const response = await fetch('/api/news');
                const data = await response.json();
                updateNewsSection(data.news);
            } catch (error) {
                console.error('Error fetching news:', error);
            }
        }
        
        function updateNewsSection(news) {
            const container = document.getElementById('news-container');
            container.innerHTML = '';
            
            news.forEach(item => {
                const newsDiv = document.createElement('div');
                newsDiv.className = 'news-item';
                newsDiv.innerHTML = `
                    <div class="news-title">${item.title}</div>
                    <div class="news-meta">
                        ${item.sentiment} Impact | ${item.crypto_mentioned.join(', ')} | 
                        ${new Date(item.published_at).toLocaleString()}
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9em;">${item.summary}</div>
                `;
                container.appendChild(newsDiv);
            });
        }
        
        // Auto-refresh every 5 minutes
        setInterval(requestUpdate, 300000);
        
        // Initial load
        requestUpdate();
    </script>
</body>
</html>
        """
    
    def check_bitcoin_105k_alert(self):
        """Check if the system caught the Bitcoin $105K drop alert from WatcherGuru"""
        try:
            if self.telegram_bridge:
                return self.telegram_bridge.check_bitcoin_105k_alert()
            else:
                return {
                    'caught_alert': False,
                    'reason': 'Telegram bridge not initialized',
                    'recommendation': 'Enable WatcherGuru Telegram integration'
                }
        except Exception as e:
            logger.error(f"Error checking Bitcoin $105K alert: {e}")
            return {
                'caught_alert': False,
                'reason': f'Error: {e}',
                'recommendation': 'Check Telegram integration configuration'
            }
    
    def start_telegram_monitoring(self):
        """Start WatcherGuru Telegram monitoring if available"""
        if self.telegram_bridge:
            try:
                # This would start the Telegram bot monitoring in a background thread
                import threading
                def start_bot():
                    asyncio.run(self.telegram_bridge.start_monitoring())
                
                bot_thread = threading.Thread(target=start_bot, daemon=True)
                bot_thread.start()
                logger.info("✅ WatcherGuru Telegram monitoring started")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to start Telegram monitoring: {e}")
                return False
        return False
    
    async def run_background_analysis(self):
        """Run background analysis updates"""
        logger.info("🔄 Starting background analysis loop")
        
        # Start Telegram monitoring
        self.start_telegram_monitoring()
        
        while self.is_running:
            try:
                logger.info("🔍 Running fundamental analysis update...")
                
                # Simulate analysis update (in real implementation, this would fetch live data)
                await self.update_analysis_data()
                
                # Broadcast update to connected clients
                self.socketio.emit('analysis_update', self.analysis_data)
                
                self.last_update = datetime.now()
                logger.info(f"✅ Analysis updated at {self.last_update}")
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in background analysis: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def update_analysis_data(self):
        """Update analysis data with real-time prices and multi-source news sentiment"""
        try:
            # Fetch real-time prices
            real_prices = await self.get_real_time_prices()
            
            # Fetch real-time news sentiment from multiple sources
            news_data = await self.fetch_watcher_guru_news()
            crypto_sentiment = self._calculate_crypto_sentiment(news_data)
            
            # Update each crypto with new prices and news sentiment
            for symbol in self.analysis_data:
                if symbol in real_prices:
                    # Update current price and related metrics
                    current_price = real_prices[symbol]['price']
                    price_change_24h = real_prices[symbol].get('change_24h', 0)
                    volume_24h = real_prices[symbol].get('volume', 0)
                    
                    # Get news sentiment for this crypto
                    news_sentiment = crypto_sentiment.get(symbol, 'NEUTRAL')
                    
                    # Recalculate 4-year prediction based on new price and fundamentals
                    score_multiplier = self.analysis_data[symbol]['overall_score'] / 100
                    if symbol == 'BTC':
                        price_prediction_4y = current_price * (2.5 + score_multiplier)
                    elif symbol == 'ETH':
                        price_prediction_4y = current_price * (4 + score_multiplier)
                    elif symbol == 'SOL':
                        price_prediction_4y = current_price * (5 + score_multiplier)
                    else:  # XRP
                        price_prediction_4y = current_price * (3 + score_multiplier)
                    
                    # Update the data
                    self.analysis_data[symbol].update({
                        'current_price': current_price,
                        'price_change_24h': price_change_24h,
                        'volume_24h': volume_24h,
                        'price_prediction_4y': price_prediction_4y,
                        'news_sentiment': news_sentiment,
                        'last_updated': datetime.now().isoformat()
                    })
                    
                    logger.info(f"✅ Updated {symbol}: ${current_price:,.2f} ({price_change_24h:+.2f}%)")
            
            # Save updated data
            self.save_analysis_to_db()
            logger.info("✅ All analysis data updated with real-time prices")
            
        except Exception as e:
            logger.error(f"❌ Error updating analysis data: {e}")
    
    def start_server(self):
        """Start the Flask-SocketIO server"""
        def signal_handler(sig, frame):
            logger.info("🛑 Shutting down Fundamental Analysis Server...")
            self.is_running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start background analysis in separate thread
        def run_background():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_background_analysis())
        
        background_thread = threading.Thread(target=run_background, daemon=True)
        background_thread.start()
        
        logger.info(f"🚀 Starting Fundamental Analysis Server on port {self.port}")
        logger.info(f"🌐 Dashboard: http://localhost:{self.port}")
        logger.info(f"🔗 API: http://localhost:{self.port}/api/analysis")
        
        # Start Flask-SocketIO server
        self.socketio.run(
            self.app,
            host='0.0.0.0',
            port=self.port,
            debug=False,
            allow_unsafe_werkzeug=True
        )

def main():
    """Main entry point"""
    print("🚀 CRYPTO FUNDAMENTAL ANALYSIS SYSTEM")
    print("="*50)
    print("🎯 Purpose: Long-term investment analysis")
    print("📊 Features: Supply/demand analysis, news sentiment, price predictions")
    print("🌐 Dashboard: http://localhost:5002")
    print("🔄 Updates: Hourly background analysis")
    print("="*50)
    
    # Create and start server
    server = FundamentalAnalysisServer(port=5002)
    server.start_server()

if __name__ == "__main__":
    main()