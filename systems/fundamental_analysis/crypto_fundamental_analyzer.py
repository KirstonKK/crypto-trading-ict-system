#!/usr/bin/env python3
"""
🚀 CRYPTO FUNDAMENTAL ANALYSIS ALGORITHM
=====================================

Long-term investment analyzer focusing on:
1. News sentiment analysis for crypto-impacting events
2. Supply analysis (inflation rates, token economics)
3. Demand analysis (DAU, TVL, adoption metrics)

Goal: Identify coins with high demand + low supply for 4-year holds
Example: SOL with 4.2% inflation + 2.1M DAU = Strong long-term candidate
"""

import requests
import sqlite3
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScoreCategory(Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    AVERAGE = "AVERAGE"
    POOR = "POOR"
    CRITICAL = "CRITICAL"

@dataclass
class SupplyMetrics:
    """Supply-side analysis metrics"""
    symbol: str
    inflation_rate: float  # Annual %
    max_supply: Optional[float]
    circulating_supply: float
    supply_growth_rate: float  # Annual %
    token_burns: bool  # Has token burning mechanism
    supply_score: str
    
@dataclass
class DemandMetrics:
    """Demand-side analysis metrics"""
    symbol: str
    daily_active_users: Optional[int]
    total_value_locked: Optional[float]  # USD
    transaction_volume: float  # 24h USD
    social_mentions: int
    developer_activity: int  # GitHub commits/month
    institutional_adoption: bool
    demand_score: str

@dataclass
class NewsImpact:
    """News sentiment and impact analysis"""
    title: str
    source: str
    sentiment: str  # POSITIVE, NEGATIVE, NEUTRAL
    impact_level: str  # HIGH, MEDIUM, LOW
    crypto_mentioned: List[str]
    timestamp: datetime
    summary: str

@dataclass
class FundamentalAnalysis:
    """Complete fundamental analysis result"""
    symbol: str
    supply_metrics: SupplyMetrics
    demand_metrics: DemandMetrics
    recent_news: List[NewsImpact]
    overall_score: int  # 0-100
    recommendation: str  # BUY, HOLD, SELL, AVOID
    target_timeframe: str  # 4-YEAR, 2-YEAR, 1-YEAR
    confidence: float  # 0.0-1.0
    analysis_date: datetime

class CryptoFundamentalAnalyzer:
    """Main fundamental analysis engine"""
    
    def __init__(self):
        self.db_path = 'crypto_fundamental_data.db'
        self.supported_coins = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'AVAX', 'MATIC']
        self.news_sources = {
            'coindesk': 'https://api.coindesk.com/v1/news',
            'cryptonews': 'https://cryptonews.com/api/news',
            'cointelegraph': 'https://cointelegraph.com/api/news'
        }
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database for fundamental data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Supply metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                inflation_rate REAL,
                max_supply REAL,
                circulating_supply REAL,
                supply_growth_rate REAL,
                token_burns BOOLEAN,
                supply_score TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Demand metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demand_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                daily_active_users INTEGER,
                total_value_locked REAL,
                transaction_volume REAL,
                social_mentions INTEGER,
                developer_activity INTEGER,
                institutional_adoption BOOLEAN,
                demand_score TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # News impact table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_impact (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT,
                sentiment TEXT,
                impact_level TEXT,
                crypto_mentioned TEXT, -- JSON array
                timestamp TIMESTAMP,
                summary TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fundamental analysis results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                overall_score INTEGER,
                recommendation TEXT,
                target_timeframe TEXT,
                confidence REAL,
                analysis_summary TEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Fundamental analysis database initialized")

    async def analyze_crypto_news(self, crypto_symbols: List[str]) -> List[NewsImpact]:
        """Analyze crypto-related news for sentiment and impact"""
        logger.info(f"🗞️ Analyzing news for {crypto_symbols}")
        
        news_impacts = []
        
        # Example news sources (you can integrate real APIs)
        sample_news = [
            {
                'title': 'Federal Reserve Signals Interest Rate Cuts Coming',
                'source': 'Financial Times',
                'sentiment': 'POSITIVE',
                'impact_level': 'HIGH',
                'crypto_mentioned': ['BTC', 'ETH', 'SOL'],
                'summary': 'Lower interest rates typically drive investment into risk assets like crypto'
            },
            {
                'title': 'Major Institution Adopts Solana for Payment Processing',
                'source': 'CoinDesk',
                'sentiment': 'POSITIVE', 
                'impact_level': 'MEDIUM',
                'crypto_mentioned': ['SOL'],
                'summary': 'Institutional adoption signals growing real-world utility'
            },
            {
                'title': 'Ethereum Layer 2 TVL Reaches New All-Time High',
                'source': 'The Block',
                'sentiment': 'POSITIVE',
                'impact_level': 'MEDIUM',
                'crypto_mentioned': ['ETH'],
                'summary': 'Growing L2 usage indicates strong ecosystem development'
            }
        ]
        
        for news in sample_news:
            if any(symbol in news['crypto_mentioned'] for symbol in crypto_symbols):
                impact = NewsImpact(
                    title=news['title'],
                    source=news['source'],
                    sentiment=news['sentiment'],
                    impact_level=news['impact_level'],
                    crypto_mentioned=news['crypto_mentioned'],
                    timestamp=datetime.now(),
                    summary=news['summary']
                )
                news_impacts.append(impact)
        
        return news_impacts

    async def analyze_supply_metrics(self, symbol: str) -> SupplyMetrics:
        """Analyze supply-side fundamentals"""
        logger.info(f"📊 Analyzing supply metrics for {symbol}")
        
        # Sample data (integrate with real APIs like CoinGecko, CoinMarketCap)
        supply_data = {
            'SOL': {
                'inflation_rate': 4.2,  # Annual %
                'max_supply': None,  # No max supply
                'circulating_supply': 470_000_000,
                'supply_growth_rate': 4.2,
                'token_burns': True  # Has fee burning
            },
            'BTC': {
                'inflation_rate': 1.7,  # Decreasing to 0.875% after next halving
                'max_supply': 21_000_000,
                'circulating_supply': 19_750_000,
                'supply_growth_rate': 1.7,
                'token_burns': False
            },
            'ETH': {
                'inflation_rate': -0.3,  # Deflationary due to EIP-1559
                'max_supply': None,
                'circulating_supply': 120_500_000,
                'supply_growth_rate': -0.3,
                'token_burns': True
            },
            'XRP': {
                'inflation_rate': 0.0,  # No new supply
                'max_supply': 100_000_000_000,
                'circulating_supply': 54_000_000_000,
                'supply_growth_rate': 0.0,
                'token_burns': False
            }
        }
        
        data = supply_data.get(symbol, {
            'inflation_rate': 5.0,
            'max_supply': None,
            'circulating_supply': 1_000_000_000,
            'supply_growth_rate': 5.0,
            'token_burns': False
        })
        
        # Calculate supply score
        supply_score = self._calculate_supply_score(data['inflation_rate'], data['token_burns'])
        
        return SupplyMetrics(
            symbol=symbol,
            inflation_rate=data['inflation_rate'],
            max_supply=data['max_supply'],
            circulating_supply=data['circulating_supply'],
            supply_growth_rate=data['supply_growth_rate'],
            token_burns=data['token_burns'],
            supply_score=supply_score
        )

    async def analyze_demand_metrics(self, symbol: str) -> DemandMetrics:
        """Analyze demand-side fundamentals"""
        logger.info(f"📈 Analyzing demand metrics for {symbol}")
        
        # Sample data (integrate with DeFiLlama, Dune Analytics, etc.)
        demand_data = {
            'SOL': {
                'daily_active_users': 2_100_000,  # Q3 2024 data
                'total_value_locked': 5_200_000_000,  # $5.2B TVL
                'transaction_volume': 150_000_000,  # 24h volume
                'social_mentions': 15_000,  # Daily mentions
                'developer_activity': 450,  # Monthly GitHub commits
                'institutional_adoption': True
            },
            'ETH': {
                'daily_active_users': 400_000,
                'total_value_locked': 58_000_000_000,  # $58B TVL
                'transaction_volume': 8_000_000_000,
                'social_mentions': 25_000,
                'developer_activity': 800,
                'institutional_adoption': True
            },
            'BTC': {
                'daily_active_users': 1_000_000,
                'total_value_locked': 2_000_000_000,  # Lightning Network + DeFi
                'transaction_volume': 15_000_000_000,
                'social_mentions': 40_000,
                'developer_activity': 200,
                'institutional_adoption': True
            }
        }
        
        data = demand_data.get(symbol, {
            'daily_active_users': 50_000,
            'total_value_locked': 100_000_000,
            'transaction_volume': 10_000_000,
            'social_mentions': 1_000,
            'developer_activity': 50,
            'institutional_adoption': False
        })
        
        # Calculate demand score
        demand_score = self._calculate_demand_score(data)
        
        return DemandMetrics(
            symbol=symbol,
            daily_active_users=data['daily_active_users'],
            total_value_locked=data['total_value_locked'],
            transaction_volume=data['transaction_volume'],
            social_mentions=data['social_mentions'],
            developer_activity=data['developer_activity'],
            institutional_adoption=data['institutional_adoption'],
            demand_score=demand_score
        )

    def _calculate_supply_score(self, inflation_rate: float, token_burns: bool) -> str:
        """Calculate supply attractiveness score"""
        score = 0
        
        # Lower inflation is better
        if inflation_rate <= 0:  # Deflationary
            score += 40
        elif inflation_rate <= 2:  # Very low inflation
            score += 35
        elif inflation_rate <= 4:  # Low inflation (like SOL)
            score += 25
        elif inflation_rate <= 6:  # Moderate inflation
            score += 15
        else:  # High inflation
            score += 5
        
        # Token burns add value
        if token_burns:
            score += 20
        
        # Categorize score
        if score >= 50:
            return ScoreCategory.EXCELLENT.value
        elif score >= 40:
            return ScoreCategory.GOOD.value
        elif score >= 25:
            return ScoreCategory.AVERAGE.value
        else:
            return ScoreCategory.POOR.value

    def _calculate_demand_score(self, data: Dict) -> str:
        """Calculate demand strength score"""
        score = 0
        
        # Daily Active Users (0-25 points)
        dau = data.get('daily_active_users', 0)
        if dau >= 1_000_000:
            score += 25
        elif dau >= 500_000:
            score += 20
        elif dau >= 100_000:
            score += 15
        elif dau >= 50_000:
            score += 10
        else:
            score += 5
        
        # Total Value Locked (0-25 points)
        tvl = data.get('total_value_locked', 0)
        if tvl >= 10_000_000_000:  # $10B+
            score += 25
        elif tvl >= 5_000_000_000:  # $5B+
            score += 20
        elif tvl >= 1_000_000_000:  # $1B+
            score += 15
        elif tvl >= 100_000_000:  # $100M+
            score += 10
        else:
            score += 5
        
        # Developer Activity (0-20 points)
        dev_activity = data.get('developer_activity', 0)
        if dev_activity >= 500:
            score += 20
        elif dev_activity >= 200:
            score += 15
        elif dev_activity >= 100:
            score += 10
        else:
            score += 5
        
        # Institutional Adoption (0-15 points)
        if data.get('institutional_adoption', False):
            score += 15
        
        # Social Mentions (0-15 points)
        mentions = data.get('social_mentions', 0)
        if mentions >= 20_000:
            score += 15
        elif mentions >= 10_000:
            score += 12
        elif mentions >= 5_000:
            score += 8
        else:
            score += 5
        
        # Categorize score
        if score >= 80:
            return ScoreCategory.EXCELLENT.value
        elif score >= 65:
            return ScoreCategory.GOOD.value
        elif score >= 45:
            return ScoreCategory.AVERAGE.value
        else:
            return ScoreCategory.POOR.value

    async def generate_fundamental_analysis(self, symbol: str) -> FundamentalAnalysis:
        """Generate complete fundamental analysis"""
        logger.info(f"🔍 Generating fundamental analysis for {symbol}")
        
        # Gather all metrics
        supply_metrics = await self.analyze_supply_metrics(symbol)
        demand_metrics = await self.analyze_demand_metrics(symbol)
        news_impacts = await self.analyze_crypto_news([symbol])
        
        # Calculate overall score (0-100)
        supply_weight = 0.4
        demand_weight = 0.5
        news_weight = 0.1
        
        supply_score_num = self._score_to_number(supply_metrics.supply_score)
        demand_score_num = self._score_to_number(demand_metrics.demand_score)
        news_score_num = self._calculate_news_score(news_impacts)
        
        overall_score = int(
            (supply_score_num * supply_weight) + 
            (demand_score_num * demand_weight) + 
            (news_score_num * news_weight)
        )
        
        # Generate recommendation
        recommendation, target_timeframe, confidence = self._generate_recommendation(
            overall_score, supply_metrics, demand_metrics
        )
        
        analysis = FundamentalAnalysis(
            symbol=symbol,
            supply_metrics=supply_metrics,
            demand_metrics=demand_metrics,
            recent_news=news_impacts,
            overall_score=overall_score,
            recommendation=recommendation,
            target_timeframe=target_timeframe,
            confidence=confidence,
            analysis_date=datetime.now()
        )
        
        # Save to database
        self._save_analysis(analysis)
        
        return analysis

    def _score_to_number(self, score_category: str) -> int:
        """Convert score category to number"""
        mapping = {
            ScoreCategory.EXCELLENT.value: 90,
            ScoreCategory.GOOD.value: 75,
            ScoreCategory.AVERAGE.value: 60,
            ScoreCategory.POOR.value: 40,
            ScoreCategory.CRITICAL.value: 20
        }
        return mapping.get(score_category, 50)

    def _calculate_news_score(self, news_impacts: List[NewsImpact]) -> int:
        """Calculate news sentiment score"""
        if not news_impacts:
            return 50  # Neutral
        
        positive_count = sum(1 for news in news_impacts if news.sentiment == 'POSITIVE')
        negative_count = sum(1 for news in news_impacts if news.sentiment == 'NEGATIVE')
        total_count = len(news_impacts)
        
        if positive_count > negative_count:
            return min(80, 50 + (positive_count * 10))
        elif negative_count > positive_count:
            return max(20, 50 - (negative_count * 10))
        else:
            return 50

    def _generate_recommendation(
        self, overall_score: int, supply_metrics: SupplyMetrics, demand_metrics: DemandMetrics
    ) -> Tuple[str, str, float]:
        """Generate investment recommendation"""
        
        # Example: SOL analysis
        # Supply: 4.2% inflation (GOOD) + Token burns (EXCELLENT) = GOOD supply score
        # Demand: 2.1M DAU (EXCELLENT) + High TVL (EXCELLENT) = EXCELLENT demand score
        # Overall: High score = BUY recommendation for 4-YEAR hold
        
        if overall_score >= 80:
            return "BUY", "4-YEAR", 0.9
        elif overall_score >= 70:
            return "BUY", "2-YEAR", 0.8
        elif overall_score >= 60:
            return "HOLD", "1-YEAR", 0.7
        elif overall_score >= 45:
            return "HOLD", "6-MONTH", 0.6
        else:
            return "AVOID", "SHORT-TERM", 0.4

    def _save_analysis(self, analysis: FundamentalAnalysis):
        """Save analysis to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save supply metrics
        cursor.execute("""
            INSERT INTO supply_metrics 
            (symbol, inflation_rate, max_supply, circulating_supply, supply_growth_rate, token_burns, supply_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.supply_metrics.symbol,
            analysis.supply_metrics.inflation_rate,
            analysis.supply_metrics.max_supply,
            analysis.supply_metrics.circulating_supply,
            analysis.supply_metrics.supply_growth_rate,
            analysis.supply_metrics.token_burns,
            analysis.supply_metrics.supply_score
        ))
        
        # Save demand metrics
        cursor.execute("""
            INSERT INTO demand_metrics 
            (symbol, daily_active_users, total_value_locked, transaction_volume, 
             social_mentions, developer_activity, institutional_adoption, demand_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.demand_metrics.symbol,
            analysis.demand_metrics.daily_active_users,
            analysis.demand_metrics.total_value_locked,
            analysis.demand_metrics.transaction_volume,
            analysis.demand_metrics.social_mentions,
            analysis.demand_metrics.developer_activity,
            analysis.demand_metrics.institutional_adoption,
            analysis.demand_metrics.demand_score
        ))
        
        # Save overall analysis
        analysis_summary = f"Supply: {analysis.supply_metrics.supply_score}, Demand: {analysis.demand_metrics.demand_score}"
        cursor.execute("""
            INSERT INTO fundamental_analysis 
            (symbol, overall_score, recommendation, target_timeframe, confidence, analysis_summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            analysis.symbol,
            analysis.overall_score,
            analysis.recommendation,
            analysis.target_timeframe,
            analysis.confidence,
            analysis_summary
        ))
        
        conn.commit()
        conn.close()

    def print_analysis_report(self, analysis: FundamentalAnalysis):
        """Print detailed analysis report"""
        print("\n" + "="*80)
        print("🚀 FUNDAMENTAL ANALYSIS REPORT - {analysis.symbol}")
        print("="*80)
        
        print("\n📊 OVERALL ASSESSMENT:")
        print("   Score: {analysis.overall_score}/100")
        print("   Recommendation: {analysis.recommendation}")
        print("   Target Timeframe: {analysis.target_timeframe}")
        print("   Confidence: {analysis.confidence:.1%}")
        
        print("\n📉 SUPPLY ANALYSIS:")
        print("   Inflation Rate: {analysis.supply_metrics.inflation_rate:.1f}% annually")
        print("   Supply Growth: {analysis.supply_metrics.supply_growth_rate:.1f}%")
        print("   Token Burns: {'✅ Yes' if analysis.supply_metrics.token_burns else '❌ No'}")
        print("   Supply Score: {analysis.supply_metrics.supply_score}")
        
        print("\n📈 DEMAND ANALYSIS:")
        print("   Daily Active Users: {analysis.demand_metrics.daily_active_users:,}" if analysis.demand_metrics.daily_active_users else "   DAU: Not available")
        print("   Total Value Locked: ${analysis.demand_metrics.total_value_locked/1_000_000_000:.1f}B" if analysis.demand_metrics.total_value_locked else "   TVL: Not available")
        print("   24h Volume: ${analysis.demand_metrics.transaction_volume/1_000_000:.1f}M")
        print("   Institutional Adoption: {'✅ Yes' if analysis.demand_metrics.institutional_adoption else '❌ No'}")
        print("   Demand Score: {analysis.demand_metrics.demand_score}")
        
        if analysis.recent_news:
            print("\n🗞️ RECENT NEWS IMPACT:")
            for news in analysis.recent_news[:3]:
                print("   • {news.title[:60]}...")
                print("     Sentiment: {news.sentiment} | Impact: {news.impact_level}")
        
        print("\n💡 ANALYSIS SUMMARY:")
        if analysis.recommendation == "BUY":
            print("   ✅ Strong fundamentals suggest {analysis.symbol} is a good {analysis.target_timeframe.lower()} hold")
            print("   📈 High demand + controlled supply = positive price potential")
        elif analysis.recommendation == "HOLD":
            print("   ⚠️ Mixed signals - monitor closely for {analysis.target_timeframe.lower()}")
        else:
            print("   ❌ Weak fundamentals - consider avoiding or short-term only")
        
        print("="*80)

async def main():
    """Main execution function"""
    print("🚀 CRYPTO FUNDAMENTAL ANALYSIS ALGORITHM")
    print("="*60)
    
    analyzer = CryptoFundamentalAnalyzer()
    
    # Analyze major cryptocurrencies
    cryptos_to_analyze = ['SOL', 'BTC', 'ETH', 'XRP']
    
    for crypto in cryptos_to_analyze:
        try:
            analysis = await analyzer.generate_fundamental_analysis(crypto)
            analyzer.print_analysis_report(analysis)
            time.sleep(1)  # Rate limiting
        except Exception as e:
            logger.error(f"❌ Error analyzing {crypto}: {e}")
    
    print("\n✅ Fundamental analysis complete!")
    print("📊 Results saved to: {analyzer.db_path}")

if __name__ == "__main__":
    asyncio.run(main())