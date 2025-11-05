#!/usr/bin/env python3
"""
Enhanced Database Analysis for ML Model Training
==============================================

This script shows how the database is populated and how to optimize it for ML training
with historical data analysis across different dates.

Current Scan Frequency:
- Monitor scans every 30 seconds
- Each scan analyzes 6 symbols (BTC, ETH, ADA, SOL, XRP, DOGE)
- Each symbol analyzed across 4 timeframes (1m, 5m, 15m, 1h, 4h)
- Potential database entries per scan: 6 symbols × 4 timeframes = 24 data points every 30s

Database Population Strategy:
"""

from src.database.trading_database import TradingDatabase
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import json

def analyze_current_database_population():
    """Analyze how frequently the database is being populated"""
    
    print("🔍 CURRENT DATABASE POPULATION ANALYSIS")
    print("=" * 60)
    
    db = TradingDatabase()
    
    # Get database statistics
    with sqlite3.connect(db.db_path) as conn:
        # Count signals by date
        cursor = conn.execute("""
            SELECT 
                DATE(entry_time) as date,
                COUNT(*) as signal_count,
                COUNT(DISTINCT symbol) as unique_symbols,
                COUNT(DISTINCT timeframes) as unique_timeframes
            FROM signals 
            GROUP BY DATE(entry_time)
            ORDER BY date DESC
            LIMIT 7
        """)
        
        daily_data = cursor.fetchall()
        
        print("\n📊 DAILY SIGNAL GENERATION (Last 7 Days):")
        print("Date           | Signals | Symbols | Timeframes")
        print("-" * 50)
        
        for row in daily_data:
            date, signals, symbols, timeframes = row
            print("{date:12} | {signals:7} | {symbols:7} | {timeframes:10}")
        
        # Count market data points
        cursor = conn.execute("""
            SELECT 
                symbol,
                COUNT(*) as total_signals,
                COUNT(DISTINCT DATE(entry_time)) as trading_days,
                ROUND(AVG(confluence_score), 3) as avg_confluence
            FROM signals 
            GROUP BY symbol
            ORDER BY total_signals DESC
        """)
        
        symbol_data = cursor.fetchall()
        
        print("\n📈 SYMBOL ANALYSIS:")
        print("Symbol    | Signals | Days | Avg Confluence")
        print("-" * 45)
        
        for row in symbol_data:
            symbol, signals, days, confluence = row
            print("{symbol:9} | {signals:7} | {days:4} | {confluence:12}")
    
    print("\n⏰ CURRENT SCAN FREQUENCY:")
    print("   📡 Monitor scans: Every 30 seconds")
    print("   🎯 Symbols monitored: 6 (BTC, ETH, ADA, SOL, XRP, DOGE)")
    print("   ⏱️  Timeframes: 5 (1m, 5m, 15m, 1h, 4h)")
    print("   💾 Max DB entries per scan: 30 (6 symbols × 5 timeframes)")
    print("   📊 Daily potential entries: 2,880 (30 entries × 96 scans/day)")
    
    return db

def optimize_for_ml_training():
    """Show how to optimize database for ML model training"""
    
    print("\n🤖 ML MODEL DATABASE OPTIMIZATION")
    print("=" * 60)
    
    db = TradingDatabase()
    
    # Enhanced database schema for ML training
    enhanced_schema = """
    -- Enhanced tables for ML training
    
    CREATE TABLE IF NOT EXISTS market_scans (
        scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        scan_type TEXT,  -- 'ROUTINE', 'EVENT_DRIVEN', 'MANUAL'
        market_session TEXT,  -- 'ASIA', 'LONDON', 'NYC', 'OVERLAP'
        market_regime TEXT,  -- 'TRENDING', 'RANGING', 'VOLATILE'
        btc_dominance REAL,
        fear_greed_index INTEGER,
        volatility_index REAL,
        scan_duration_ms INTEGER,
        signals_generated INTEGER,
        quality_distribution TEXT  -- JSON: {'premium': 2, 'high': 5, 'medium': 3}
    );
    
    CREATE TABLE IF NOT EXISTS market_conditions (
        condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        symbol TEXT,
        timeframe TEXT,
        price REAL,
        volume REAL,
        volatility REAL,
        rsi REAL,
        market_structure TEXT,  -- 'BULLISH_BOS', 'BEARISH_BOS', 'RANGING'
        liquidity_swept BOOLEAN,
        order_blocks_count INTEGER,
        fvg_count INTEGER,
        session_high REAL,
        session_low REAL,
        institutional_level REAL
    );
    
    CREATE TABLE IF NOT EXISTS signal_outcomes (
        outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        outcome_type TEXT,  -- 'TP_HIT', 'SL_HIT', 'PARTIAL_FILL', 'EXPIRED'
        time_to_outcome INTEGER,  -- seconds from signal to outcome
        max_favorable_excursion REAL,
        max_adverse_excursion REAL,
        fill_quality TEXT,  -- 'EXCELLENT', 'GOOD', 'POOR'
        market_impact TEXT,  -- 'NEWS', 'WHALE', 'TECHNICAL', 'SESSION_CHANGE'
        lessons_learned TEXT
    );
    
    CREATE TABLE IF NOT EXISTS ml_features (
        feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        symbol TEXT,
        timeframe TEXT,
        
        -- Price Action Features
        price_position REAL,  -- where price is relative to session range
        volume_profile TEXT,  -- JSON array of volume distribution
        order_flow_imbalance REAL,
        
        -- ICT Features  
        order_block_strength REAL,
        fvg_quality_score REAL,
        liquidity_density REAL,
        market_structure_score REAL,
        confluence_factors TEXT,  -- JSON array of all confluence factors
        
        -- Temporal Features
        session_time_remaining INTEGER,
        time_since_last_signal INTEGER,
        day_of_week INTEGER,
        hour_of_day INTEGER,
        
        -- Market Context
        btc_correlation REAL,
        sector_momentum REAL,
        news_sentiment REAL,
        funding_rate REAL,
        
        -- Target Variables (for supervised learning)
        signal_generated BOOLEAN,
        signal_quality TEXT,
        trade_outcome TEXT,
        profit_factor REAL
    );
    """
    
    print("📊 ENHANCED DATABASE SCHEMA FOR ML:")
    print("   🎯 market_scans: Track each 30s scan cycle")
    print("   🌊 market_conditions: Capture market state per symbol/timeframe")
    print("   ✅ signal_outcomes: Track signal performance and lessons")
    print("   🤖 ml_features: Comprehensive feature set for model training")
    
    return enhanced_schema

def show_data_collection_strategy():
    """Show optimal data collection strategy for ML"""
    
    print("\n📚 OPTIMAL DATA COLLECTION STRATEGY")
    print("=" * 60)
    
    strategy = {
        "scanning_frequency": {
            "current": "Every 30 seconds",
            "optimal_for_ml": "Every 15 seconds during active sessions",
            "rationale": "More granular data for pattern recognition"
        },
        
        "data_retention": {
            "signals": "Keep all signals forever (small size)",
            "market_conditions": "Keep 1 year of detailed data",
            "ml_features": "Keep 6 months for training, archive older",
            "scan_metadata": "Keep 3 months for optimization"
        },
        
        "feature_collection": {
            "every_scan": [
                "Price action metrics",
                "Volume profile",
                "Market structure state",
                "Session information",
                "Temporal features"
            ],
            "every_signal": [
                "Confluence factors",
                "ICT concept strengths",
                "Market regime classification",
                "Signal generation context"
            ],
            "every_outcome": [
                "Performance metrics",
                "Market impact analysis", 
                "Lessons learned",
                "Context preservation"
            ]
        },
        
        "storage_optimization": {
            "hot_data": "Last 7 days - SQLite for speed",
            "warm_data": "Last 90 days - Compressed tables",
            "cold_data": "Historical - Parquet files for ML training"
        }
    }
    
    print("⏱️  SCANNING FREQUENCY:")
    print("   Current: {strategy['scanning_frequency']['current']}")
    print("   ML Optimal: {strategy['scanning_frequency']['optimal_for_ml']}")
    print("   Rationale: {strategy['scanning_frequency']['rationale']}")
    
    print("\n💾 DATA RETENTION STRATEGY:")
    for data_type, retention in strategy['data_retention'].items():
        print("   {data_type}: {retention}")
    
    print("\n🎯 FEATURE COLLECTION:")
    for timing, features in strategy['feature_collection'].items():
        print("   {timing}:")
        for feature in features:
            print("     • {feature}")
    
    return strategy

def create_ml_data_pipeline():
    """Create data pipeline for ML model training"""
    
    print("\n🚀 ML DATA PIPELINE IMPLEMENTATION")
    print("=" * 60)
    
    pipeline_code = '''
# Enhanced Monitor with ML Data Collection
class ICTEnhancedMonitorML(ICTEnhancedMonitor):
    
    def __init__(self):
        super().__init__()
        self.ml_features_buffer = []
        self.last_feature_extraction = datetime.now()
        
    async def _enhanced_analysis_cycle(self):
        """Enhanced analysis cycle with ML feature collection"""
        
        while self.active:
            scan_start = datetime.now()
            scan_id = self._start_scan_tracking()
            
            try:
                # Regular ICT analysis
                await self._run_ict_analysis()
                
                # ML Feature extraction every scan
                await self._extract_ml_features(scan_id)
                
                # Market condition recording
                await self._record_market_conditions(scan_id)
                
                # Scan completion tracking
                self._complete_scan_tracking(scan_id, scan_start)
                
                # Dynamic sleep based on market activity
                sleep_time = self._calculate_optimal_sleep()
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Enhanced analysis error: {e}")
                await asyncio.sleep(5)
    
    async def _extract_ml_features(self, scan_id):
        """Extract comprehensive ML features"""
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                
                # Get market data
                data = await self._get_market_data(symbol, timeframe)
                if data is None:
                    continue
                
                # Extract features
                features = {
                    'scan_id': scan_id,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': datetime.now(),
                    
                    # Price features
                    'price_position': self._calculate_price_position(data),
                    'volume_profile': self._extract_volume_profile(data),
                    'order_flow_imbalance': self._calculate_order_flow(data),
                    
                    # ICT features
                    'order_block_strength': self._measure_ob_strength(data),
                    'fvg_quality_score': self._measure_fvg_quality(data),
                    'liquidity_density': self._measure_liquidity_density(data),
                    'market_structure_score': self._score_market_structure(data),
                    
                    # Temporal features
                    'session_time_remaining': self._get_session_time_remaining(),
                    'time_since_last_signal': self._time_since_last_signal(symbol),
                    'day_of_week': datetime.now().weekday(),
                    'hour_of_day': datetime.now().hour,
                    
                    # Market context
                    'btc_correlation': self._calculate_btc_correlation(symbol),
                    'sector_momentum': self._calculate_sector_momentum(symbol),
                    'funding_rate': await self._get_funding_rate(symbol)
                }
                
                # Store features for ML training
                self.db.add_ml_features(features)
                
                # Buffer for real-time predictions
                self.ml_features_buffer.append(features)
                
                # Keep buffer manageable
                if len(self.ml_features_buffer) > 1000:
                    self.ml_features_buffer = self.ml_features_buffer[-500:]
    
    def _calculate_optimal_sleep(self):
        """Calculate optimal sleep time based on market activity"""
        
        current_session = self._get_current_session()
        volatility = self._get_current_volatility()
        
        base_sleep = 30  # seconds
        
        # Faster during active sessions
        if current_session in ['LONDON', 'NYC', 'OVERLAP']:
            base_sleep = 15
        
        # Faster during high volatility
        if volatility > 0.02:  # 2% volatility
            base_sleep *= 0.5
        elif volatility < 0.005:  # 0.5% volatility
            base_sleep *= 2
        
        return max(5, min(60, base_sleep))  # Between 5-60 seconds
    '''
    
    print("🔧 ENHANCED MONITOR FEATURES:")
    print("   📊 ML feature extraction every scan")
    print("   🎯 Market condition recording")
    print("   ⏱️  Dynamic scanning frequency")
    print("   💾 Optimized data buffering")
    print("   📈 Real-time volatility adjustment")
    
    return pipeline_code

def show_database_size_projections():
    """Show database size projections for different timeframes"""
    
    print("\n📏 DATABASE SIZE PROJECTIONS")
    print("=" * 60)
    
    # Current signal size estimate
    signal_size_kb = 2  # KB per signal record
    scan_metadata_kb = 1  # KB per scan record
    feature_record_kb = 5  # KB per ML feature record
    
    symbols = 6
    timeframes = 5
    scans_per_hour = 120  # Every 30s = 120 scans/hour
    
    # Daily projections
    daily_scans = scans_per_hour * 24
    daily_signals_max = daily_scans * symbols * 0.1  # 10% signal rate
    daily_features = daily_scans * symbols * timeframes
    
    projections = {
        "daily": {
            "scans": daily_scans,
            "signals": daily_signals_max,
            "features": daily_features,
            "size_mb": (daily_signals_max * signal_size_kb + 
                       daily_scans * scan_metadata_kb + 
                       daily_features * feature_record_kb) / 1024
        },
        "weekly": {},
        "monthly": {},
        "yearly": {}
    }
    
    # Calculate other periods
    for period, multiplier in [("weekly", 7), ("monthly", 30), ("yearly", 365)]:
        projections[period] = {
            "scans": projections["daily"]["scans"] * multiplier,
            "signals": projections["daily"]["signals"] * multiplier,
            "features": projections["daily"]["features"] * multiplier,
            "size_mb": projections["daily"]["size_mb"] * multiplier
        }
    
    print("📊 STORAGE REQUIREMENTS:")
    print("Period   | Scans   | Signals | Features | Size (MB)")
    print("-" * 55)
    
    for period, data in projections.items():
        print("{period:8} | {data['scans']:7.0f} | {data['signals']:7.0f} | {data['features']:8.0f} | {data['size_mb']:8.1f}")
    
    print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
    print("   🗜️  Compress older data (>30 days)")
    print("   📦 Archive to Parquet for ML training")
    print("   🧹 Clean up redundant features")
    print("   ⚡ Use indexed queries for performance")
    
    return projections

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║            DATABASE ANALYSIS FOR ML MODEL TRAINING              ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Run analysis
    db = analyze_current_database_population()
    schema = optimize_for_ml_training()
    strategy = show_data_collection_strategy()
    pipeline = create_ml_data_pipeline()
    projections = show_database_size_projections()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                            SUMMARY                               ║
╠══════════════════════════════════════════════════════════════════╣
║  🔄 Current Frequency: Every 30 seconds                         ║
║  📊 Daily Data Points: ~2,880 potential entries                 ║
║  💾 Daily Storage: ~{projections['daily']['size_mb']:.1f} MB                                    ║
║  🎯 ML Optimization: Enhanced schema + features                 ║
║  📈 Scalability: Automatic archiving + compression              ║
║                                                                  ║
║  🚀 READY FOR ML MODEL TRAINING!                                ║
╚══════════════════════════════════════════════════════════════════╝
""")