#!/usr/bin/env python3
"""
Database Population Enhancement for ML Model Training
====================================================

This script enhances the database to collect comprehensive data for ML training
across different dates, sessions, and market conditions.
"""

import sqlite3
import json
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from src.database.trading_database import TradingDatabase

class MLEnhancedDatabase(TradingDatabase):
    """Enhanced database for ML model training with comprehensive data collection"""
    
    def __init__(self, db_path: str = "./trading_data_ml.db"):
        super().__init__(db_path)
        self.create_ml_tables()
    
    def create_ml_tables(self):
        """Create additional tables for ML training data"""
        
        with sqlite3.connect(self.db_path) as conn:
            
            # Market scans tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS market_scans (
                    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    scan_type TEXT DEFAULT 'ROUTINE',
                    market_session TEXT,
                    market_regime TEXT,
                    btc_dominance REAL,
                    fear_greed_index INTEGER,
                    volatility_index REAL,
                    scan_duration_ms INTEGER,
                    signals_generated INTEGER DEFAULT 0,
                    quality_distribution TEXT,
                    symbols_scanned TEXT,
                    timeframes_analyzed TEXT
                )
            ''')
            
            # Market conditions per symbol/timeframe
            conn.execute('''
                CREATE TABLE IF NOT EXISTS market_conditions (
                    condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    price REAL,
                    volume REAL,
                    volatility REAL,
                    rsi REAL,
                    market_structure TEXT,
                    liquidity_swept BOOLEAN DEFAULT 0,
                    order_blocks_count INTEGER DEFAULT 0,
                    fvg_count INTEGER DEFAULT 0,
                    session_high REAL,
                    session_low REAL,
                    institutional_level REAL,
                    price_position REAL,
                    volume_profile TEXT,
                    FOREIGN KEY (scan_id) REFERENCES market_scans (scan_id)
                )
            ''')
            
            # Comprehensive ML features
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ml_features (
                    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    
                    -- Price Action Features
                    price_position REAL,
                    volume_profile TEXT,
                    order_flow_imbalance REAL,
                    volatility_regime TEXT,
                    trend_strength REAL,
                    
                    -- ICT Features
                    order_block_strength REAL,
                    fvg_quality_score REAL,
                    liquidity_density REAL,
                    market_structure_score REAL,
                    confluence_factors TEXT,
                    session_alignment REAL,
                    
                    -- Temporal Features
                    session_time_remaining INTEGER,
                    time_since_last_signal INTEGER,
                    day_of_week INTEGER,
                    hour_of_day INTEGER,
                    minute_of_hour INTEGER,
                    session_overlap BOOLEAN,
                    
                    -- Market Context
                    btc_correlation REAL,
                    sector_momentum REAL,
                    news_sentiment REAL,
                    funding_rate REAL,
                    open_interest_change REAL,
                    whale_activity REAL,
                    
                    -- Target Variables
                    signal_generated BOOLEAN DEFAULT 0,
                    signal_quality TEXT,
                    signal_type TEXT,
                    signal_confidence REAL,
                    
                    FOREIGN KEY (scan_id) REFERENCES market_scans (scan_id)
                )
            ''')
            
            # Signal outcomes for performance tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS signal_outcomes (
                    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    outcome_type TEXT,
                    time_to_outcome INTEGER,
                    max_favorable_excursion REAL,
                    max_adverse_excursion REAL,
                    fill_quality TEXT,
                    market_impact TEXT,
                    lessons_learned TEXT,
                    profit_factor REAL,
                    win_loss TEXT,
                    
                    FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON market_scans(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_conditions_symbol ON market_conditions(symbol, timeframe)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_features_symbol ON ml_features(symbol, timeframe)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_outcomes_signal ON signal_outcomes(signal_id)')
    
    def start_scan(self, scan_type: str = 'ROUTINE') -> int:
        """Start a new market scan and return scan_id"""
        
        current_session = self._get_current_session()
        market_regime = self._detect_market_regime()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO market_scans 
                (scan_type, market_session, market_regime, btc_dominance, 
                 fear_greed_index, volatility_index)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                scan_type,
                current_session,
                market_regime,
                self._get_btc_dominance(),
                self._get_fear_greed_index(),
                self._get_volatility_index()
            ))
            
            return cursor.lastrowid
    
    def complete_scan(self, scan_id: int, signals_generated: int, scan_duration_ms: int, 
                     quality_distribution: dict, symbols_scanned: list, timeframes: list):
        """Complete scan with results"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE market_scans 
                SET signals_generated = ?, scan_duration_ms = ?, 
                    quality_distribution = ?, symbols_scanned = ?, timeframes_analyzed = ?
                WHERE scan_id = ?
            ''', (
                signals_generated,
                scan_duration_ms,
                json.dumps(quality_distribution),
                json.dumps(symbols_scanned),
                json.dumps(timeframes),
                scan_id
            ))
    
    def add_market_conditions(self, scan_id: int, symbol: str, timeframe: str, conditions: dict):
        """Add market conditions for a symbol/timeframe"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO market_conditions
                (scan_id, symbol, timeframe, price, volume, volatility, rsi,
                 market_structure, liquidity_swept, order_blocks_count, fvg_count,
                 session_high, session_low, institutional_level, price_position, volume_profile)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_id, symbol, timeframe,
                conditions.get('price', 0),
                conditions.get('volume', 0),
                conditions.get('volatility', 0),
                conditions.get('rsi', 0),
                conditions.get('market_structure', 'UNKNOWN'),
                conditions.get('liquidity_swept', False),
                conditions.get('order_blocks_count', 0),
                conditions.get('fvg_count', 0),
                conditions.get('session_high', 0),
                conditions.get('session_low', 0),
                conditions.get('institutional_level', 0),
                conditions.get('price_position', 0),
                json.dumps(conditions.get('volume_profile', []))
            ))
    
    def add_ml_features(self, scan_id: int, symbol: str, timeframe: str, features: dict):
        """Add comprehensive ML features"""
        
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO ml_features
                (scan_id, symbol, timeframe, price_position, volume_profile, 
                 order_flow_imbalance, volatility_regime, trend_strength,
                 order_block_strength, fvg_quality_score, liquidity_density,
                 market_structure_score, confluence_factors, session_alignment,
                 session_time_remaining, time_since_last_signal, day_of_week,
                 hour_of_day, minute_of_hour, session_overlap,
                 btc_correlation, sector_momentum, news_sentiment, funding_rate,
                 open_interest_change, whale_activity, signal_generated,
                 signal_quality, signal_type, signal_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_id, symbol, timeframe,
                features.get('price_position', 0),
                json.dumps(features.get('volume_profile', [])),
                features.get('order_flow_imbalance', 0),
                features.get('volatility_regime', 'NORMAL'),
                features.get('trend_strength', 0),
                features.get('order_block_strength', 0),
                features.get('fvg_quality_score', 0),
                features.get('liquidity_density', 0),
                features.get('market_structure_score', 0),
                json.dumps(features.get('confluence_factors', [])),
                features.get('session_alignment', 0),
                features.get('session_time_remaining', 0),
                features.get('time_since_last_signal', 0),
                now.weekday(),
                now.hour,
                now.minute,
                features.get('session_overlap', False),
                features.get('btc_correlation', 0),
                features.get('sector_momentum', 0),
                features.get('news_sentiment', 0),
                features.get('funding_rate', 0),
                features.get('open_interest_change', 0),
                features.get('whale_activity', 0),
                features.get('signal_generated', False),
                features.get('signal_quality', None),
                features.get('signal_type', None),
                features.get('signal_confidence', 0)
            ))
    
    def add_signal_outcome(self, signal_id: str, outcome_data: dict):
        """Track signal outcomes for ML learning"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO signal_outcomes
                (signal_id, outcome_type, time_to_outcome, max_favorable_excursion,
                 max_adverse_excursion, fill_quality, market_impact, lessons_learned,
                 profit_factor, win_loss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_id,
                outcome_data.get('outcome_type', 'UNKNOWN'),
                outcome_data.get('time_to_outcome', 0),
                outcome_data.get('max_favorable_excursion', 0),
                outcome_data.get('max_adverse_excursion', 0),
                outcome_data.get('fill_quality', 'UNKNOWN'),
                outcome_data.get('market_impact', 'NONE'),
                outcome_data.get('lessons_learned', ''),
                outcome_data.get('profit_factor', 0),
                outcome_data.get('win_loss', 'UNKNOWN')
            ))
    
    def get_ml_training_data(self, days: int = 30, symbol: str = None) -> dict:
        """Get comprehensive ML training data for specified period"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get features data
            features_query = '''
                SELECT * FROM ml_features 
                WHERE timestamp >= ?
            '''
            params = [start_date]
            
            if symbol:
                features_query += ' AND symbol = ?'
                params.append(symbol)
            
            features_query += ' ORDER BY timestamp DESC'
            
            features_df = pd.read_sql_query(features_query, conn, params=params)
            
            # Get outcomes data
            outcomes_query = '''
                SELECT so.*, s.symbol, s.entry_time 
                FROM signal_outcomes so
                JOIN signals s ON so.signal_id = s.signal_id
                WHERE s.entry_time >= ?
            '''
            
            outcomes_params = [start_date]
            if symbol:
                outcomes_query += ' AND s.symbol = ?'
                outcomes_params.append(symbol)
            
            outcomes_df = pd.read_sql_query(outcomes_query, conn, params=outcomes_params)
            
            # Get market conditions
            conditions_query = '''
                SELECT mc.*, ms.market_session, ms.market_regime
                FROM market_conditions mc
                JOIN market_scans ms ON mc.scan_id = ms.scan_id
                WHERE mc.timestamp >= ?
            '''
            
            conditions_params = [start_date]
            if symbol:
                conditions_query += ' AND mc.symbol = ?'
                conditions_params.append(symbol)
            
            conditions_df = pd.read_sql_query(conditions_query, conn, params=conditions_params)
        
        return {
            'features': features_df,
            'outcomes': outcomes_df,
            'conditions': conditions_df,
            'metadata': {
                'start_date': start_date,
                'end_date': datetime.now(),
                'symbol_filter': symbol,
                'total_records': len(features_df)
            }
        }
    
    def _get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now().hour
        if 8 <= hour < 16:
            return 'LONDON'
        elif 13 <= hour < 22:
            return 'NYC' 
        else:
            return 'ASIA'
    
    def _detect_market_regime(self) -> str:
        """Detect current market regime"""
        # Simplified - would use actual market data
        return 'TRENDING'
    
    def _get_btc_dominance(self) -> float:
        """Get BTC dominance (placeholder)"""
        return 42.5
    
    def _get_fear_greed_index(self) -> int:
        """Get Fear & Greed index (placeholder)"""
        return 55
    
    def _get_volatility_index(self) -> float:
        """Get volatility index (placeholder)"""
        return 0.025

def demonstrate_ml_data_collection():
    """Demonstrate ML data collection process"""
    
    print("🚀 DEMONSTRATING ML DATA COLLECTION")
    print("=" * 50)
    
    # Initialize ML database
    ml_db = MLEnhancedDatabase()
    
    # Simulate a scan cycle
    scan_id = ml_db.start_scan('ROUTINE')
    print(f"📊 Started scan #{scan_id}")
    
    symbols = ['BTC/USDT', 'ETH/USDT']
    timeframes = ['5m', '15m', '1h']
    
    signals_generated = 0
    quality_dist = {'premium': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    # Simulate data collection for each symbol/timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            
            # Market conditions
            conditions = {
                'price': 50000.0,
                'volume': 1000000,
                'volatility': 0.02,
                'rsi': 55.0,
                'market_structure': 'BULLISH_BOS',
                'liquidity_swept': False,
                'order_blocks_count': 3,
                'fvg_count': 2,
                'session_high': 50500.0,
                'session_low': 49500.0,
                'institutional_level': 50200.0,
                'price_position': 0.6,
                'volume_profile': [0.1, 0.3, 0.4, 0.2]
            }
            
            ml_db.add_market_conditions(scan_id, symbol, timeframe, conditions)
            
            # ML features
            features = {
                'price_position': 0.6,
                'volume_profile': [0.1, 0.3, 0.4, 0.2],
                'order_flow_imbalance': 0.15,
                'volatility_regime': 'NORMAL',
                'trend_strength': 0.75,
                'order_block_strength': 0.8,
                'fvg_quality_score': 0.7,
                'liquidity_density': 0.9,
                'market_structure_score': 0.85,
                'confluence_factors': ['ORDER_BLOCKS', 'FVG', 'LIQUIDITY'],
                'session_alignment': 0.9,
                'session_time_remaining': 3600,
                'time_since_last_signal': 900,
                'session_overlap': True,
                'btc_correlation': 0.95 if symbol != 'BTC/USDT' else 1.0,
                'sector_momentum': 0.6,
                'news_sentiment': 0.1,
                'funding_rate': 0.01,
                'open_interest_change': 0.05,
                'whale_activity': 0.3,
                'signal_generated': False,
                'signal_quality': None,
                'signal_type': None,
                'signal_confidence': 0
            }
            
            # Simulate signal generation (10% chance)
            if symbol == 'BTC/USDT' and timeframe == '5m':
                features.update({
                    'signal_generated': True,
                    'signal_quality': 'HIGH',
                    'signal_type': 'ORDER_BLOCK_LONG',
                    'signal_confidence': 0.87
                })
                signals_generated += 1
                quality_dist['high'] += 1
            
            ml_db.add_ml_features(scan_id, symbol, timeframe, features)
    
    # Complete scan
    ml_db.complete_scan(scan_id, signals_generated, 2500, quality_dist, symbols, timeframes)
    
    print(f"✅ Completed scan with {signals_generated} signals")
    print(f"📊 Quality distribution: {quality_dist}")
    
    # Show data retrieval
    training_data = ml_db.get_ml_training_data(days=1)
    
    print(f"\n📚 ML TRAINING DATA AVAILABLE:")
    print(f"   🎯 Features records: {len(training_data['features'])}")
    print(f"   ✅ Outcomes records: {len(training_data['outcomes'])}")
    print(f"   🌊 Conditions records: {len(training_data['conditions'])}")
    
    return ml_db

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              ML DATABASE ENHANCEMENT SYSTEM                     ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Demonstrate the ML data collection
    ml_db = demonstrate_ml_data_collection()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                      DATABASE POPULATED!                        ║
╠══════════════════════════════════════════════════════════════════╣
║  📊 Enhanced database with ML-ready features                    ║
║  🎯 Every 30s scan collects comprehensive data                  ║
║  📈 Historical data preserved for model training                ║
║  🤖 Ready for ML model development!                             ║
╚══════════════════════════════════════════════════════════════════╝
""")