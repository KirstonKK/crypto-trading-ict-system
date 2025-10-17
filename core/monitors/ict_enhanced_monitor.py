#!/usr/bin/env python3
"""
ICT Enhanced Trading Monitor - Port 5001
========================================

Kirston's Crypto Bot - ICT Enhanced Trading Monitor
Monitors BTC, SOL, ETH, XRP with institutional analysis

Created by: GitHub Copilot
Version: 1.0 - CodeRabbit Review Target
"""

import json
import time
import logging
import threading
import asyncio
import aiohttp
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np

# Import Bybit real-time prices
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from bybit_integration.real_time_prices import BybitRealTimePrices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import the new directional bias engine after logger is configured
try:
    from trading.directional_bias_engine import DirectionalBiasEngine, DirectionalBias, SessionType
    DIRECTIONAL_BIAS_AVAILABLE = True
    logger.info("✅ Directional Bias Engine imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Directional Bias Engine not available: {e}")
    DIRECTIONAL_BIAS_AVAILABLE = False

class ICTCryptoMonitor:
    """Enhanced Crypto Monitor matching previous version exactly"""
    
    def __init__(self):
        # Exact same symbols as previous monitor
        self.symbols = ['BTCUSDT', 'SOLUSDT', 'ETHUSDT', 'XRPUSDT']
        self.display_symbols = ['BTC', 'SOL', 'ETH', 'XRP']
        self.crypto_emojis = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}
        
        # Directional Bias Engine - DISABLED (Only comprehensive ICT methodology)
        self.directional_bias_engine = None
        logger.info("✅ Comprehensive ICT Analysis Engine initialized - NO FALLBACK SYSTEM")
        
        # Initialize Bybit real-time price monitor
        try:
            # Define symbols to monitor (matching the trading pairs we track)
            bybit_symbols = ['BTCUSDT', 'SOLUSDT', 'ETHUSDT', 'XRPUSDT']
            self.bybit_prices = BybitRealTimePrices(symbols=bybit_symbols, testnet=False)
            logger.info(f"✅ Bybit real-time price monitor initialized for {bybit_symbols}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Bybit prices: {e}")
            self.bybit_prices = None
        
        # STARTUP COOLDOWN SYSTEM - DISABLED for immediate signal generation
        self.startup_time = datetime.now()
        self.startup_cooldown_minutes = 0  # No cooldown - immediate comprehensive ICT analysis
        logger.info(f"✅ Startup cooldown DISABLED - Comprehensive ICT signals active immediately")
        
        # Monitor state tracking
        self.scan_count = 0
        self.signals_today = 0
        self.total_signals = 0
        # daily_pnl is now calculated from completed paper trades
        self.active_hours = "08:00-22:00"
        self.risk_per_trade = 0.01  # 1% of account balance per trade (STRICT)
        
        # CRYPTO-SPECIFIC ANALYSIS PARAMETERS
        self.crypto_characteristics = {
            'BTC': {
                'volatility_factor': 1.0,      # Base volatility
                'liquidity_rank': 1,           # Highest liquidity
                'correlation_weight': 0.4,     # Market leader influence
                'structure_sensitivity': 0.8,  # High structure importance
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618, 0.786],
                'timeframe_priority': ['4H', '1H', '15M'],  # Primary timeframes
                'session_preference': ['NY', 'London'],    # Preferred sessions
                'min_confluence_score': 0.75,              # Higher standards for BTC
                'order_block_lookback': 100               # Candles to look back for OB
            },
            'ETH': {
                'volatility_factor': 1.2,      # Higher volatility than BTC
                'liquidity_rank': 2,           # Second highest liquidity
                'correlation_weight': 0.3,     # Strong but not leader
                'structure_sensitivity': 0.75, # Good structure respect
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618, 0.786],
                'timeframe_priority': ['4H', '1H', '15M'],
                'session_preference': ['NY', 'London', 'Asia'],
                'min_confluence_score': 0.70,              # Slightly lower than BTC
                'order_block_lookback': 80
            },
            'SOL': {
                'volatility_factor': 1.8,      # Much higher volatility
                'liquidity_rank': 3,           # Moderate liquidity
                'correlation_weight': 0.2,     # Moderate correlation
                'structure_sensitivity': 0.65, # Lower structure respect
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618],  # Fewer levels
                'timeframe_priority': ['1H', '15M', '5M'],        # Faster timeframes
                'session_preference': ['NY', 'Asia'],             # Different sessions
                'min_confluence_score': 0.65,                    # Lower standards
                'order_block_lookback': 60
            },
            'XRP': {
                'volatility_factor': 1.5,      # High volatility
                'liquidity_rank': 4,           # Lower liquidity
                'correlation_weight': 0.15,    # Weakest correlation
                'structure_sensitivity': 0.60, # Lowest structure respect
                'fibonacci_levels': [0.382, 0.5, 0.618],         # Key levels only
                'timeframe_priority': ['1H', '15M', '5M'],
                'session_preference': ['NY', 'London'],
                'min_confluence_score': 0.60,                    # Most lenient
                'order_block_lookback': 50
            }
        }
        
        # COMPREHENSIVE ICT METHODOLOGY IMPLEMENTATION
        self.ict_methodology = {
            'higher_timeframe_analysis': {
                'primary_timeframes': ['4H', '1H'],        # Market structure determination
                'confirmation_timeframe': '15M',           # Entry refinement
                'structure_lookback': 200,                 # Candles for structure analysis
                'trend_confirmation_bars': 20              # Bars for trend confirmation
            },
            'enhanced_order_blocks': {
                'min_volume_multiplier': 1.5,              # Volume must be 1.5x average
                'min_body_percentage': 0.7,                # 70% body minimum
                'max_wicks_percentage': 0.3,               # 30% wicks maximum
                'alignment_tolerance': 0.001,              # 0.1% alignment tolerance
                'mitigation_percentage': 0.5               # 50% mitigation for invalidation
            },
            'fibonacci_confluence': {
                'key_levels': [0.236, 0.382, 0.5, 0.618, 0.786],
                'tolerance': 0.002,                        # 0.2% tolerance for level hits
                'min_retracement': 0.236,                  # Minimum retracement for validity
                'max_retracement': 0.786,                  # Maximum before invalidation
                'confluence_weight': 0.3                   # Weight in overall score
            },
            'fair_value_gaps': {
                'min_gap_percentage': 0.001,               # 0.1% minimum gap size
                'max_gap_age_bars': 50,                    # Max bars since gap creation
                'partial_fill_threshold': 0.7,            # 70% fill before mitigation
                'confluence_weight': 0.25                  # Weight in overall score
            },
            'market_structure': {
                'swing_lookback': 20,                      # Bars for swing identification
                'structure_break_confirmation': 3,         # Bars to confirm break
                'min_structure_distance': 0.005,          # 0.5% minimum distance
                'bos_confluence_weight': 0.2,              # Break of structure weight
                'choch_confluence_weight': 0.15            # Change of character weight
            },
            'liquidity_pools': {
                'equal_level_tolerance': 0.002,            # 0.2% tolerance for equal levels
                'min_tests': 2,                            # Minimum level tests
                'max_tests': 4,                            # Maximum before likely break
                'proximity_weight': 0.1,                   # Weight for proximity to levels
                'volume_confirmation': True                # Require volume confirmation
            }
        }
        
        # SESSION VALIDATION AND BIAS PERSISTENCE
        self.session_validation = {
            'ny_open': {
                'start_hour': 9,      # 9:30 AM EST
                'start_minute': 30,
                'end_hour': 10,       # 10:30 AM EST
                'end_minute': 30,
                'bias_duration_hours': 4,    # Bias valid for 4 hours
                'strength_decay_rate': 0.1   # 10% decay per hour
            },
            'london_open': {
                'start_hour': 8,      # 8:00 AM GMT
                'start_minute': 0,
                'end_hour': 9,        # 9:00 AM GMT
                'end_minute': 0,
                'bias_duration_hours': 3,
                'strength_decay_rate': 0.15
            },
            'asia_open': {
                'start_hour': 0,      # 12:00 AM GMT+8
                'start_minute': 0,
                'end_hour': 1,        # 1:00 AM GMT+8
                'end_minute': 0,
                'bias_duration_hours': 2,
                'strength_decay_rate': 0.2
            }
        }
        
        # BIAS PERSISTENCE TRACKING
        self.active_biases = {}  # Track active directional biases with timestamps
        self.bias_history = []   # Historical bias performance
        
        # Dynamic Risk-Reward Ratios based on market conditions
        self.dynamic_rr_ratios = {
            'conservative': 2.0,    # 1:2 RR for safer trades
            'balanced': 3.0,        # 1:3 RR for normal trades  
            'aggressive': 4.0,      # 1:4 RR for high-confidence trades
            'maximum': 5.0          # 1:5 RR for exceptional setups
        }
        self.default_rr_mode = 'balanced'  # Default to 1:3
        self.risk_reward_ratio = self.dynamic_rr_ratios[self.default_rr_mode]
        
        # Trading journal and signals
        self.trading_journal = []
        self.live_signals = []
        self.archived_signals = []  # For signals older than 5 minutes
        self.last_scan_time = None
        
        # (No test signal injection in production)
        
        # Signal management configuration
        self.max_live_signals = 3  # Maximum signals to display
        self.signal_lifetime_minutes = 5  # Signal lifetime in minutes
        
        # Signal Deduplication System (Solution 2)
        self.signal_cooldown_minutes = 3  # Prevent duplicate signals on same symbol for 3 minutes
        self.recent_signals_cache = {}  # Cache: {symbol: last_signal_time}
        self.max_positions_per_symbol = 1  # Maximum open positions per symbol (better diversification)
        
        # Enhanced Risk Management (Solution 3)
        self.max_portfolio_risk = 0.05  # Maximum 5% of portfolio at risk at once
        self.max_concurrent_signals = 4  # Maximum concurrent live signals (1 per symbol for diversification)
        self.position_correlation_check = True  # Check for correlated positions
        
        # Paper trading configuration
        self.paper_trading_enabled = True
        self.paper_balance = 100.0  # Starting with $100 for 1% risk testing
        self.account_blown = False  # Track if account is blown
        self.blow_up_threshold = 0.0  # Blow up when balance <= $0
        self.active_paper_trades = []  # Currently open paper trades
        self.completed_paper_trades = []  # Completed paper trades
        self.total_paper_pnl = 0.0
        
        # End of Day (EOD) configuration - NO OVERNIGHT POSITIONS
        self.close_positions_eod = True  # Enable end-of-day position closure
        self.eod_close_hour = 23  # Close all positions at 11 PM (23:00) local time
        self.eod_close_minute = 0  # At the top of the hour
        self.last_eod_check_date = None  # Track last EOD closure date
        
        # Trading sessions (exactly like previous)
        self.trading_sessions = {
            'Asia': {
                'name': 'Asia',
                'timezone': 'GMT+8',
                'start': 23,  # 23:00 GMT
                'end': 8     # 08:00 GMT
            },
            'London': {
                'name': 'London',
                'timezone': 'GMT+0',
                'start': 8,   # 08:00 GMT
                'end': 16    # 16:00 GMT
            },
            'New_York': {
                'name': 'New York',
                'timezone': 'GMT-5',
                'start': 13,  # 13:00 GMT
                'end': 22    # 22:00 GMT
            }
        }
        
        # Initialize database
        self._initialize_database()
        
        # Load previous trading state from database
        self._load_trading_state()
        
        # Load all persisted data for comprehensive restoration
        self.load_all_persisted_data()
        
        logger.info("🚀 CRYPTO MONITOR INITIALIZED")
        logger.info(f"📊 Monitoring: {', '.join(self.display_symbols)}")
        logger.info(f"⏰ Active Hours: {self.active_hours} GMT")
        logger.info(f"🎯 Risk per trade: {self.risk_per_trade*100:.1f}% FIXED | Dynamic RR: {self.default_rr_mode} (1:{self.risk_reward_ratio}) + others")
        logger.info(f"📋 Signal Management: Max {self.max_live_signals} signals, newest replaces oldest")
        logger.info(f"📄 Paper Trading: ENABLED | Balance: ${self.paper_balance:,.2f}")
    
    def _initialize_database(self):
        """Initialize database tables"""
        try:
            import sqlite3
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Create signals table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    confluence_score REAL NOT NULL,
                    timeframes TEXT NOT NULL,
                    ict_concepts TEXT NOT NULL,
                    session TEXT NOT NULL,
                    market_regime TEXT NOT NULL,
                    directional_bias TEXT NOT NULL,
                    signal_strength TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP NULL,
                    exit_price REAL NULL,
                    pnl REAL NULL,
                    notes TEXT,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')
            
            # Create paper trades table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    position_size REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP NULL,
                    exit_price REAL NULL,
                    status TEXT DEFAULT 'OPEN',
                    realized_pnl REAL NULL,
                    unrealized_pnl REAL NULL,
                    current_price REAL NULL,
                    risk_amount REAL NOT NULL,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')

            # Create comprehensive price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    high_24h REAL,
                    low_24h REAL,
                    change_24h REAL,
                    volume_24h REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')

            # Create trading journal persistence table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    signal_id TEXT NULL,
                    symbol TEXT NULL,
                    entry_price REAL NULL,
                    action TEXT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')

            # Create session status tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    market_hours BOOLEAN DEFAULT 0,
                    active_signals INTEGER DEFAULT 0,
                    scan_count INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')

            # Create system statistics tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_count INTEGER DEFAULT 0,
                    signals_today INTEGER DEFAULT 0,
                    daily_pnl REAL DEFAULT 0,
                    paper_balance REAL DEFAULT 100,
                    account_blown BOOLEAN DEFAULT 0,
                    portfolio_risk REAL DEFAULT 0,
                    max_portfolio_risk REAL DEFAULT 0.05,
                    concurrent_signals INTEGER DEFAULT 0,
                    max_concurrent_signals INTEGER DEFAULT 3,
                    uptime_seconds INTEGER DEFAULT 0,
                    market_hours BOOLEAN DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')

            # Create scan history table for detailed tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_number INTEGER NOT NULL,
                    signals_generated INTEGER DEFAULT 0,
                    signals_approved INTEGER DEFAULT 0,
                    signals_rejected INTEGER DEFAULT 0,
                    live_signals_count INTEGER DEFAULT 0,
                    expired_signals_count INTEGER DEFAULT 0,
                    market_volatility REAL,
                    session_multiplier REAL,
                    effective_probability REAL,
                    scan_duration_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT (date('now'))
                )
            ''')

            # Create indexes separately after tables are created
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_symbol_timestamp ON price_history(symbol, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(created_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_date ON trading_journal_entries(created_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_signal ON trading_journal_entries(signal_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_name_timestamp ON session_status(session_name, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_date ON session_status(created_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_date ON system_statistics(created_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_number ON scan_history(scan_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_date ON scan_history(created_date)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    def _safe_parse_timestamp(self, timestamp_str):
        """Safely parse timestamp string with fallback to current time."""
        try:
            if not timestamp_str or timestamp_str.strip() == '':
                return datetime.now()
            
            # Clean up common timestamp issues
            cleaned = timestamp_str.strip()
            if cleaned.endswith('Z'):
                cleaned = cleaned.replace('Z', '+00:00')
            
            return datetime.fromisoformat(cleaned)
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Invalid timestamp '{timestamp_str}': {e}, using current time")
            return datetime.now()
    
    def _load_trading_state(self):
        """Load ALL trading state from database - TODAY'S SESSION ONLY"""
        try:
            import sqlite3
            from datetime import date, datetime
            
            # Connect to database (FIXED PATH)
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            today = date.today().isoformat()
            
            logger.info(f"🔄 Restoring complete trading state for {today}...")
            
            # 🔧 DATABASE CLEANUP: Mark old ACTIVE signals as EXPIRED (prevent duplicate position counting)
            current_time = datetime.now()
            expiry_cutoff = current_time.timestamp() - (self.signal_lifetime_minutes * 60)  # Convert to seconds ago
            expiry_datetime = datetime.fromtimestamp(expiry_cutoff).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                UPDATE signals 
                SET status = 'EXPIRED' 
                WHERE status = 'ACTIVE' 
                AND entry_time < ?
            """, (expiry_datetime,))
            
            expired_count = cursor.rowcount
            if expired_count > 0:
                logger.info(f"🗄️ Database cleanup: Marked {expired_count} old signals as EXPIRED (older than {self.signal_lifetime_minutes}min)")
            
            conn.commit()  # Commit the cleanup before proceeding
            
            # 1. RESTORE SCAN COUNT FROM TODAY
            cursor.execute("""
                SELECT COUNT(*) FROM scan_history 
                WHERE date(timestamp) = ?
            """, (today,))
            self.scan_count = cursor.fetchone()[0]
            logger.info(f"📊 Restored scan count: {self.scan_count}")
            
            # 2. RESTORE TODAY'S SIGNALS (exclude pre-fix signals from today)
            # Conservative thresholds were implemented around 08:49 GMT on 2025-10-09
            fix_timestamp = '2025-10-09 08:49:00'
            cursor.execute("""
                SELECT signal_id, symbol, direction, entry_price, stop_loss, take_profit,
                       confluence_score, timeframes, ict_concepts, session, market_regime,
                       directional_bias, signal_strength, status, entry_time
                FROM signals 
                WHERE date(entry_time) = ? AND status = 'ACTIVE'
                AND (date(entry_time) != '2025-10-09' OR entry_time >= ?)
                ORDER BY entry_time DESC
            """, (today, fix_timestamp))
            
            signals_data = cursor.fetchall()
            self.live_signals = []
            
            # Apply price separation validation during restoration
            logger.info(f"🔍 Restoring signals with price separation validation...")
            
            # Group signals by crypto for price separation validation
            signals_by_crypto = {}
            for signal_data in signals_data:
                crypto = signal_data[1].replace('USDT', '')  # symbol -> crypto
                if crypto not in signals_by_crypto:
                    signals_by_crypto[crypto] = []
                signals_by_crypto[crypto].append(signal_data)
            
            # Process each crypto separately for price separation
            for crypto, crypto_signals in signals_by_crypto.items():
                logger.info(f"   🔍 Processing {len(crypto_signals)} {crypto} signals for price separation...")
                
                min_separation = self.get_minimum_price_separation(crypto, 0)
                valid_signals = []
                
                # Sort by timestamp (newest first, same as original query)
                crypto_signals.sort(key=lambda x: x[14], reverse=True)  # entry_time index
                
                for signal_data in crypto_signals:
                    signal = {
                        'id': signal_data[0],
                        'symbol': signal_data[1],
                        'crypto': crypto,
                        'direction': signal_data[2],
                        'action': signal_data[2],
                        'entry_price': signal_data[3],
                        'stop_loss': signal_data[4],
                        'take_profit': signal_data[5],
                        'confluence_score': signal_data[6],
                        'confidence': signal_data[6],
                        'timeframes': signal_data[7],
                        'timeframe': signal_data[7],
                        'confluences': signal_data[8].split(',') if signal_data[8] else [],
                        'session': signal_data[9],
                        'market_regime': signal_data[10],
                        'directional_bias': signal_data[11],
                        'signal_strength': signal_data[12],
                        'status': signal_data[13],
                        'timestamp': self._safe_parse_timestamp(signal_data[14]) if signal_data[14] else datetime.now(),
                        'risk_amount': 1.0,
                        'pnl': 0.0
                    }
                    
                    entry_price = signal['entry_price']
                    should_keep = True
                    
                    # Check against all previously accepted signals for this crypto
                    for valid_signal in valid_signals:
                        existing_price = valid_signal['entry_price']
                        price_diff_pct = abs((entry_price - existing_price) / existing_price) * 100
                        
                        if price_diff_pct < min_separation:
                            logger.info(f"   ❌ REJECTING {crypto} @ ${entry_price:.2f} - too close to ${existing_price:.2f} ({price_diff_pct:.2f}% < {min_separation:.1f}%)")
                            # Mark as inactive in database
                            cursor.execute("UPDATE signals SET status = 'INACTIVE' WHERE signal_id = ?", (signal['id'],))
                            should_keep = False
                            break
                    
                    if should_keep:
                        valid_signals.append(signal)
                        logger.info(f"   ✅ KEEPING {crypto} @ ${entry_price:.2f}")
                        
                        # Stop if we hit the max signals limit
                        if len(self.live_signals) + len(valid_signals) >= self.max_live_signals:
                            logger.info(f"   ⚠️ Max signals limit reached, stopping at {len(valid_signals)} {crypto} signals")
                            break
                
                # Add valid signals to live_signals
                self.live_signals.extend(valid_signals)
                logger.info(f"   📊 {crypto}: {len(valid_signals)} valid signals restored")
                
                # Stop processing if we've reached max signals
                if len(self.live_signals) >= self.max_live_signals:
                    logger.info(f"   🛑 Max live signals ({self.max_live_signals}) reached, stopping restoration")
                    break
            
            # Count today's signals
            cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?", (today,))
            self.signals_today = cursor.fetchone()[0]
            
            # Count all-time signals
            cursor.execute("SELECT COUNT(*) FROM signals")
            self.total_signals = cursor.fetchone()[0]
            
            # 3. RESTORE TODAY'S PAPER TRADES
            self.active_paper_trades = []
            self.completed_paper_trades = []
            
            # Load open trades from today (exclude pre-fix trades)
            cursor.execute("""
                SELECT id, signal_id, symbol, direction, entry_price, position_size, 
                       stop_loss, take_profit, entry_time, status, current_price, 
                       unrealized_pnl, risk_amount
                FROM paper_trades 
                WHERE date(entry_time) = ? AND status = 'OPEN'
                AND (date(entry_time) != '2025-10-09' OR entry_time >= ?)
            """, (today, fix_timestamp))
            
            open_trades = cursor.fetchall()
            for trade_data in open_trades:
                trade = {
                    'id': trade_data[0],
                    'signal_id': trade_data[1],
                    'symbol': trade_data[2],
                    'crypto': trade_data[2].replace('USDT', ''),
                    'direction': trade_data[3],
                    'action': trade_data[3],
                    'entry_price': float(trade_data[4]),
                    'position_size': float(trade_data[5]),
                    'stop_loss': float(trade_data[6]),
                    'take_profit': float(trade_data[7]),
                    'entry_time': trade_data[8],
                    'status': trade_data[9],
                    'current_price': float(trade_data[10]) if trade_data[10] else float(trade_data[4]),
                    'unrealized_pnl': float(trade_data[11]) if trade_data[11] else 0.0,
                    'pnl': float(trade_data[11]) if trade_data[11] else 0.0,
                    'risk_amount': float(trade_data[12])
                }
                self.active_paper_trades.append(trade)
            
            # Load completed trades from today (exclude pre-fix trades)
            cursor.execute("""
                SELECT id, signal_id, symbol, direction, entry_price, position_size,
                       stop_loss, take_profit, entry_time, exit_time, exit_price,
                       status, realized_pnl, risk_amount
                FROM paper_trades 
                WHERE date(entry_time) = ? AND status IN ('STOP_LOSS', 'TAKE_PROFIT')
                AND (date(entry_time) != '2025-10-09' OR entry_time >= ?)
            """, (today, fix_timestamp))
            
            closed_trades = cursor.fetchall()
            for trade_data in closed_trades:
                trade = {
                    'id': trade_data[0],
                    'signal_id': trade_data[1],
                    'symbol': trade_data[2],
                    'crypto': trade_data[2].replace('USDT', ''),
                    'direction': trade_data[3],
                    'action': trade_data[3],
                    'entry_price': float(trade_data[4]),
                    'position_size': float(trade_data[5]),
                    'stop_loss': float(trade_data[6]),
                    'take_profit': float(trade_data[7]),
                    'entry_time': trade_data[8],
                    'exit_time': trade_data[9],
                    'exit_price': float(trade_data[10]) if trade_data[10] else 0.0,
                    'status': trade_data[11],
                    'realized_pnl': float(trade_data[12]) if trade_data[12] else 0.0,
                    'pnl': float(trade_data[12]) if trade_data[12] else 0.0,
                    'risk_amount': float(trade_data[13])
                }
                self.completed_paper_trades.append(trade)
            
            # 4. LOAD PERSISTENT BALANCE (NO MORE RESETS TO $100!)
            # First try to load the latest balance from balance_history
            cursor.execute("""
                SELECT balance FROM balance_history 
                ORDER BY timestamp DESC LIMIT 1
            """)
            balance_result = cursor.fetchone()
            
            if balance_result:
                # Use the last saved balance (persistent through crashes)
                self.paper_balance = float(balance_result[0])
                logger.info(f"✅ Loaded persistent balance: ${self.paper_balance:.2f}")
            else:
                # Only use $100 if this is truly the first time ever
                self.paper_balance = 100.0
                logger.info(f"🆕 First time startup - using starting balance: ${self.paper_balance:.2f}")
                # Save initial balance to history
                self.save_balance_to_database(self.paper_balance, "Initial startup balance")
            
            # Calculate total realized PnL from ALL closed trades (not just today)
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM paper_trades 
                WHERE status IN ('STOP_LOSS', 'TAKE_PROFIT', 'CLEANUP') AND realized_pnl IS NOT NULL
            """)
            result = cursor.fetchone()
            total_realized_pnl = float(result[0]) if result and result[0] else 0.0
            
            # Calculate current unrealized PnL from open trades
            total_unrealized_pnl = sum(trade['unrealized_pnl'] for trade in self.active_paper_trades)
            self.total_paper_pnl = total_realized_pnl + total_unrealized_pnl
            
            # 5. RESTORE TRADING JOURNAL ENTRIES
            self.trading_journal = []
            cursor.execute("""
                SELECT entry_type, title, content, signal_id, timestamp
                FROM trading_journal_entries 
                WHERE date(created_date) = ?
                ORDER BY timestamp DESC
            """, (today,))
            
            journal_data = cursor.fetchall()
            for entry_data in journal_data:
                journal_entry = {
                    'type': entry_data[0],
                    'title': entry_data[1],
                    'content': entry_data[2],
                    'signal_id': entry_data[3],
                    'timestamp': entry_data[4]
                }
                self.trading_journal.append(journal_entry)
            
            # Commit any status updates made during signal restoration
            conn.commit()
            conn.close()
            
            # Summary of restored data
            logger.info(f"✅ COMPLETE DATA RESTORATION FOR {today}")
            logger.info(f"   📊 Scan Count: {self.scan_count}")
            logger.info(f"   📈 Signals Today: {self.signals_today} | All Time: {self.total_signals}")
            logger.info(f"   🎯 Live Signals: {len(self.live_signals)}")
            logger.info(f"   📄 Active Trades: {len(self.active_paper_trades)}")
            logger.info(f"   ✅ Completed Trades: {len(self.completed_paper_trades)}")
            logger.info(f"   💰 Paper Balance: ${self.paper_balance:.2f}")
            logger.info(f"   � Journal Entries: {len(self.trading_journal)}")
            logger.info(f"   💹 Total PnL: ${self.total_paper_pnl:.2f}")
            
            if len(self.trading_journal) > 0:
                logger.info("📦 Restored persisted data: {} journal entries".format(len(self.trading_journal)))
            else:
                logger.info("📦 Restored persisted data: 0 journal entries")
                
            # 🧹 CLEANUP: Remove any old journal entries that aren't from today
            self.cleanup_old_journal_entries()
                
        except Exception as e:
            logger.error(f"❌ Failed to restore trading state: {e}")
            logger.info("🔄 Starting with fresh state")
            # Set defaults if restoration fails
            self.scan_count = 0
            self.signals_today = 0
            self.total_signals = 0
            # PRESERVE BALANCE if it was successfully loaded! Only reset if it's still at default
            # TRADING FIX: Use range comparison instead of exact float equality
            if not hasattr(self, 'paper_balance') or abs(self.paper_balance - 100.0) < 0.01:
                # Try to load balance one more time in case it failed during main restoration
                try:
                    import sqlite3
                    conn = sqlite3.connect('databases/trading_data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT balance FROM balance_history ORDER BY timestamp DESC LIMIT 1")
                    balance_result = cursor.fetchone()
                    if balance_result:
                        self.paper_balance = float(balance_result[0])
                        logger.info(f"🔄 Recovered balance during fallback: ${self.paper_balance:.2f}")
                    else:
                        self.paper_balance = 100.0
                        logger.info("🆕 No balance history found - using $100 default")
                    conn.close()
                except Exception as balance_e:
                    logger.error(f"❌ Failed to recover balance: {balance_e}")
                    self.paper_balance = 100.0
            else:
                logger.info(f"✅ Preserving loaded balance: ${self.paper_balance:.2f}")
            
            self.live_signals = []
            self.active_paper_trades = []
            self.completed_paper_trades = []
            self.trading_journal = []

    def save_signal_to_database(self, signal):
        """Save a signal to the database for persistence"""
        try:
            import sqlite3
            from datetime import date
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Map signal fields to database fields
            entry_time = signal.get('timestamp')
            if isinstance(entry_time, str):
                # Convert ISO string to proper timestamp
                from datetime import datetime
                if entry_time.strip():
                    try:
                        entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        logger.warning(f"⚠️ Invalid isoformat string for entry_time: '{entry_time}' ({e})")
                        entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    logger.warning(f"⚠️ Empty entry_time string encountered in save_signal_to_database.")
                    entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO signals (
                    signal_id, symbol, direction, entry_price, stop_loss, take_profit,
                    confluence_score, timeframes, ict_concepts, session, market_regime,
                    directional_bias, signal_strength, status, entry_time, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.get('id', ''),
                signal.get('symbol', f"{signal.get('crypto', '')}USDT"),
                signal.get('action', signal.get('direction', '')),
                signal.get('entry_price', 0.0),
                signal.get('stop_loss', 0.0),
                signal.get('take_profit', 0.0),
                signal.get('confluence_score', signal.get('confidence', 0.0)),
                signal.get('timeframe', ''),
                ', '.join(signal.get('confluences', [])),  # Convert list to string
                signal.get('session', 'Unknown'),
                signal.get('market_regime', 'Unknown'),
                signal.get('directional_bias', 'Neutral'),
                signal.get('signal_strength', 'Medium'),
                'ACTIVE',
                entry_time,
                date.today().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Signal saved to database: {signal.get('id', 'Unknown')} - {signal.get('crypto', '')} {signal.get('action', '')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save signal to database: {e}")

    def _sync_expired_signals_to_database(self, expired_signals):
        """Mark expired signals as 'EXPIRED' in the database to sync with in-memory state"""
        if not expired_signals:
            return
            
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for signal in expired_signals:
                signal_id = signal.get('id', '')
                if signal_id:
                    cursor.execute(
                        "UPDATE signals SET status = 'EXPIRED' WHERE signal_id = ?", 
                        (signal_id,)
                    )
            
            conn.commit()
            conn.close()
            
            logger.info(f"🗄️ Database sync: Marked {len(expired_signals)} signals as EXPIRED")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync expired signals to database: {e}")

    def save_paper_trade_to_database(self, trade):
        """Save a paper trade to the database for persistence"""
        try:
            import sqlite3
            from datetime import date
            
            # CRITICAL FIX: Use the same database path as read operations
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Map trade fields to database fields
            entry_time = trade.get('entry_time', trade.get('timestamp'))
            if isinstance(entry_time, str):
                # Convert ISO string to proper timestamp
                from datetime import datetime
                if entry_time.strip():
                    try:
                        entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        logger.warning(f"⚠️ Invalid isoformat string for entry_time: '{entry_time}' ({e})")
                        entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    logger.warning(f"⚠️ Empty entry_time string encountered in save_trade_to_database.")
                    entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO paper_trades (
                    signal_id, symbol, direction, entry_price, position_size, stop_loss, 
                    take_profit, entry_time, status, current_price, unrealized_pnl, risk_amount, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.get('signal_id', ''),  # Use actual signal ID for proper linking
                trade.get('symbol', f"{trade.get('crypto', '')}USDT"),
                trade.get('action', trade.get('direction', '')),
                trade.get('entry_price', 0.0),
                trade.get('position_size', 0.0),
                trade.get('stop_loss', 0.0),
                trade.get('take_profit', 0.0),
                entry_time,
                'OPEN',
                trade.get('current_price', trade.get('entry_price', 0.0)),
                trade.get('pnl', trade.get('unrealized_pnl', 0.0)),
                trade.get('risk_amount', 1.0),
                date.today().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Paper trade saved to database: {trade.get('id', 'Unknown')} - {trade.get('crypto', '')} {trade.get('action', '')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save paper trade to database: {e}")

    def update_paper_trade_in_database(self, trade):
        """Update a paper trade in database when it closes"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Format exit time
            exit_time = trade.get('exit_time')
            if exit_time and hasattr(exit_time, 'strftime'):
                exit_time = exit_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update the trade with closure data
            crypto_symbol = trade.get('crypto', '').upper()
            symbol = f"{crypto_symbol}USDT"
            
            # Use symbol and entry_price to identify the correct trade (more reliable than signal_id)
            entry_price = trade.get('entry_price', 0.0)
            
            # Debug logging
            logging.info(f"🔍 Attempting to update trade: symbol={symbol}, entry_price={entry_price}")
            
            cursor.execute("""
                UPDATE paper_trades 
                SET exit_time = ?, exit_price = ?, status = ?, realized_pnl = ?, 
                    current_price = ?, unrealized_pnl = 0
                WHERE symbol = ? AND entry_price = ? AND status = 'OPEN'
            """, (
                exit_time,
                trade.get('exit_price', trade.get('current_price', 0.0)),
                trade.get('status', 'CLOSED'),
                trade.get('final_pnl', trade.get('pnl', 0.0)),
                trade.get('current_price', 0.0),
                symbol,
                entry_price
            ))
            
            if cursor.rowcount > 0:
                conn.commit()
                logging.info(f"💾 Paper trade updated in database: {symbol} @ ${entry_price:.2f} | Status: {trade.get('status', '')} | PnL: ${trade.get('final_pnl', 0):.2f}")
            else:
                logging.warning(f"⚠️ No matching trade found to update: {symbol} @ ${entry_price:.2f}")
            
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ Failed to update paper trade in database: {e}")

    def update_active_trades_in_database(self, current_prices):
        """Update current_price and unrealized_pnl for active paper trades in database"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Get all open paper trades
            cursor.execute("SELECT id, symbol, entry_price, position_size, direction FROM paper_trades WHERE status = 'OPEN'")
            open_trades = cursor.fetchall()
            
            updated_count = 0
            for trade_id, symbol, entry_price, position_size, direction in open_trades:
                # Extract crypto from symbol (e.g., BTCUSDT -> BTC)
                crypto = symbol.replace('USDT', '')
                
                if crypto in current_prices:
                    current_price = current_prices[crypto]['price']
                    
                    # Calculate unrealized PnL
                    if direction == 'BUY':
                        unrealized_pnl = (current_price - entry_price) * position_size
                    else:  # SELL
                        unrealized_pnl = (entry_price - current_price) * position_size
                    
                    # Update current price and unrealized PnL
                    cursor.execute("""
                        UPDATE paper_trades 
                        SET current_price = ?, unrealized_pnl = ?
                        WHERE id = ?
                    """, (current_price, unrealized_pnl, trade_id))
                    
                    updated_count += 1
            
            conn.commit()
            conn.close()
            
            if updated_count > 0:
                logging.debug(f"📊 Updated {updated_count} active trades with current prices and PnL")
                
        except Exception as e:
            logging.error(f"❌ Failed to update active trades in database: {e}")

    def save_balance_to_database(self, balance: float, reason: str = ""):
        """Save current balance to database for persistence"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Create balance_history table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    balance REAL,
                    reason TEXT,
                    timestamp TIMESTAMP,
                    created_date DATE
                )
            """)
            
            # Insert current balance
            cursor.execute("""
                INSERT INTO balance_history (balance, reason, timestamp, created_date)
                VALUES (?, ?, ?, ?)
            """, (
                balance,
                reason,
                datetime.now().isoformat(),
                datetime.now().date().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"💾 Balance saved to database: ${balance:.2f} | {reason}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save balance to database: {e}")

    def sync_balance_from_database(self):
        """Sync current balance from database (for real-time accuracy)"""
        try:
            import sqlite3
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            base_balance = 100.0
            
            # Get total realized PnL from closed trades
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM paper_trades 
                WHERE status != 'OPEN' AND realized_pnl IS NOT NULL
            """)
            result = cursor.fetchone()
            total_realized_pnl = float(result[0]) if result and result[0] else 0.0
            
            # Calculate accurate balance
            accurate_balance = base_balance + total_realized_pnl
            
            # Update if different from current balance
            if abs(self.paper_balance - accurate_balance) > 0.01:  # More than 1 cent difference
                old_balance = self.paper_balance
                self.paper_balance = accurate_balance
                logger.info(f"🔄 Balance synced from database: ${old_balance:.2f} → ${self.paper_balance:.2f}")
            
            conn.close()
            return self.paper_balance
            
        except Exception as e:
            logger.error(f"❌ Failed to sync balance from database: {e}")
            return self.paper_balance

    def save_price_history(self, crypto_data: dict):
        """Save current price data to database for historical tracking"""
        try:
            import sqlite3
            from datetime import date
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            for symbol, data in crypto_data.items():
                cursor.execute("""
                    INSERT INTO price_history (
                        symbol, price, high_24h, low_24h, change_24h, volume_24h, timestamp, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    f"{symbol}USDT",
                    data.get('price', 0.0),
                    data.get('high_24h', 0.0),
                    data.get('low_24h', 0.0),
                    data.get('change_24h', 0.0),
                    data.get('volume', 0.0),
                    date.today().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save price history: {e}")

    def save_trading_journal_entry(self, entry):
        """Save trading journal entry to database"""
        try:
            import sqlite3
            from datetime import date
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trading_journal_entries (
                    entry_type, title, content, signal_id, symbol, entry_price, action, timestamp, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                entry.get('type', 'TRADE'),
                entry.get('action', 'Trade Entry'),
                entry.get('details', str(entry)),
                entry.get('id', entry.get('signal_id')),
                entry.get('symbol', entry.get('crypto', '')),
                entry.get('entry_price', 0.0),
                entry.get('action', ''),
                date.today().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save journal entry: {e}")

    def cleanup_old_journal_entries(self):
        """Remove journal entries that are not from today"""
        try:
            from datetime import date
            today_str = date.today().isoformat()
            
            original_count = len(self.trading_journal)
            filtered_journal = []
            
            for entry in self.trading_journal:
                entry_date = None
                
                # Check various date fields that might exist
                if 'timestamp' in entry:
                    try:
                        if isinstance(entry['timestamp'], str):
                            entry_date = entry['timestamp'][:10]  # Extract YYYY-MM-DD
                        else:
                            entry_date = entry['timestamp'].strftime('%Y-%m-%d')
                    except:
                        pass
                elif 'entry_time' in entry:
                    try:
                        if isinstance(entry['entry_time'], str):
                            entry_date = entry['entry_time'][:10]  # Extract YYYY-MM-DD
                        else:
                            entry_date = entry['entry_time'].strftime('%Y-%m-%d')
                    except:
                        pass
                elif 'exit_time' in entry:
                    try:
                        if isinstance(entry['exit_time'], str):
                            entry_date = entry['exit_time'][:10]  # Extract YYYY-MM-DD
                        else:
                            entry_date = entry['exit_time'].strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Only keep entries from today
                if entry_date == today_str:
                    filtered_journal.append(entry)
            
            self.trading_journal = filtered_journal
            removed_count = original_count - len(filtered_journal)
            
            if removed_count > 0:
                logger.info(f"🧹 Cleaned journal: removed {removed_count} old entries, kept {len(filtered_journal)} from today")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup journal entries: {e}")

    def save_session_status(self, session_data):
        """Save session status to database"""
        try:
            import sqlite3
            from datetime import date
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            for session_name, session_info in session_data.items():
                cursor.execute("""
                    INSERT INTO session_status (
                        session_name, status, start_time, end_time, market_hours, 
                        active_signals, scan_count, timestamp, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    session_name,
                    session_info.get('status', 'UNKNOWN'),
                    session_info.get('start_time'),
                    session_info.get('end_time'),
                    session_info.get('active', False),
                    len(self.live_signals),
                    self.scan_count,
                    date.today().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save session status: {e}")

    def save_system_statistics(self):
        """Save current system statistics to database"""
        try:
            import sqlite3
            from datetime import date
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_statistics (
                    scan_count, signals_today, daily_pnl, paper_balance, account_blown,
                    portfolio_risk, max_portfolio_risk, concurrent_signals, max_concurrent_signals,
                    uptime_seconds, market_hours, timestamp, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                self.scan_count,
                len([s for s in self.live_signals + self.archived_signals 
                     if hasattr(s.get('timestamp'), 'date') and s.get('timestamp').date() == date.today()]),
                self.daily_pnl,
                self.paper_balance,
                self.account_blown,
                self.calculate_portfolio_risk(),
                self.max_portfolio_risk,
                len(self.live_signals),
                self.max_concurrent_signals,
                0,  # Will be calculated by statistics module
                True,  # Will be set by session tracker
                date.today().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save system statistics: {e}")

    def save_scan_history(self, scan_data):
        """Save detailed scan history to database"""
        try:
            import sqlite3
            from datetime import date
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scan_history (
                    scan_number, signals_generated, signals_approved, signals_rejected,
                    live_signals_count, expired_signals_count, market_volatility,
                    session_multiplier, effective_probability, scan_duration_ms,
                    timestamp, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                scan_data.get('scan_number', self.scan_count),
                scan_data.get('signals_generated', 0),
                scan_data.get('signals_approved', 0),
                scan_data.get('signals_rejected', 0),
                len(self.live_signals),
                len(self.archived_signals),
                scan_data.get('market_volatility', 0.0),
                scan_data.get('session_multiplier', 1.0),
                scan_data.get('effective_probability', 0.0),
                scan_data.get('scan_duration_ms', 0),
                date.today().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save scan history: {e}")

    def load_all_persisted_data(self):
        """Load all persisted data from database on startup"""
        try:
            import sqlite3
            from datetime import date, datetime
            
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            today = date.today().isoformat()
            
            # Load trading journal entries from today
            cursor.execute("""
                SELECT entry_type, title, content, signal_id, symbol, entry_price, action, timestamp
                FROM trading_journal_entries
                WHERE created_date = ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (today,))
            
            journal_rows = cursor.fetchall()
            restored_journal = []
            for row in journal_rows:
                entry = {
                    'type': row[0],
                    'action': row[1],
                    'details': row[2],
                    'id': row[3],
                    'symbol': row[4],
                    'entry_price': row[5],
                    'action': row[6],
                    'timestamp': row[7]
                }
                restored_journal.append(entry)
            
            self.trading_journal = restored_journal
            
            # Load latest system statistics
            cursor.execute("""
                SELECT paper_balance, account_blown, scan_count
                FROM system_statistics
                WHERE created_date = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (today,))
            
            stats_row = cursor.fetchone()
            if stats_row:
                # Don't override balance - it's already loaded correctly from balance_history in _load_trading_state()
                # self.paper_balance = stats_row[0]  # DISABLED: Use balance_history table instead
                self.account_blown = stats_row[1]
                # Note: scan_count will be restored by _load_trading_state
            
            conn.close()
            logger.info(f"📦 Restored persisted data: {len(self.trading_journal)} journal entries")
            
        except Exception as e:
            logger.error(f"❌ Failed to load persisted data: {e}")

        except Exception as e:
            logger.error(f"❌ Failed to save paper trade to database: {e}")

    def get_todays_active_trades_from_db(self):
        """Get today's active trades from database (single source of truth)"""
        from datetime import date
        import sqlite3
        
        try:
            today = date.today().isoformat()
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, signal_id, symbol, direction, entry_price, position_size, 
                       stop_loss, take_profit, entry_time, status, current_price, 
                       unrealized_pnl, risk_amount
                FROM paper_trades 
                WHERE date(entry_time) = ? AND status = 'OPEN'
                ORDER BY id DESC
            """, (today,))
            
            active_trades = []
            for trade_data in cursor.fetchall():
                trade = {
                    'id': f"PT_{trade_data[0]}",
                    'signal_id': trade_data[1],
                    'symbol': trade_data[2],
                    'crypto': trade_data[2].replace('USDT', ''),
                    'direction': trade_data[3],
                    'action': trade_data[3],
                    'entry_price': float(trade_data[4]),
                    'position_size': float(trade_data[5]),
                    'stop_loss': float(trade_data[6]),
                    'take_profit': float(trade_data[7]),
                    'entry_time': trade_data[8],
                    'status': trade_data[9],
                    'current_price': float(trade_data[10]) if trade_data[10] else float(trade_data[4]),
                    'unrealized_pnl': float(trade_data[11]) if trade_data[11] else 0.0,
                    'pnl': float(trade_data[11]) if trade_data[11] else 0.0,
                    'risk_amount': float(trade_data[12]) if trade_data[12] else 1.0
                }
                active_trades.append(trade)
            
            conn.close()
            return active_trades
            
        except Exception as e:
            logger.error(f"❌ Failed to get today's active trades from database: {e}")
            return []

    def get_todays_completed_trades_from_db(self):
        """Get today's completed trades from database (single source of truth)"""
        from datetime import date
        import sqlite3
        
        try:
            today = date.today().isoformat()
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, signal_id, symbol, direction, entry_price, position_size,
                       stop_loss, take_profit, entry_time, exit_time, exit_price,
                       status, realized_pnl, risk_amount
                FROM paper_trades 
                WHERE date(exit_time) = ? 
                AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
                ORDER BY id DESC
            """, (today,))
            
            completed_trades = []
            for trade_data in cursor.fetchall():
                trade = {
                    'id': trade_data[0],
                    'signal_id': trade_data[1],
                    'symbol': trade_data[2],
                    'crypto': trade_data[2].replace('USDT', ''),
                    'direction': trade_data[3],
                    'action': trade_data[3],
                    'entry_price': float(trade_data[4]),
                    'position_size': float(trade_data[5]),
                    'stop_loss': float(trade_data[6]),
                    'take_profit': float(trade_data[7]),
                    'entry_time': trade_data[8],
                    'exit_time': trade_data[9],
                    'exit_price': float(trade_data[10]) if trade_data[10] else None,
                    'status': trade_data[11],
                    'realized_pnl': float(trade_data[12]) if trade_data[12] else 0.0,
                    'pnl': float(trade_data[12]) if trade_data[12] else 0.0,
                    'final_pnl': float(trade_data[12]) if trade_data[12] else 0.0,
                    'risk_amount': float(trade_data[13]) if trade_data[13] else 1.0
                }
                completed_trades.append(trade)
            
            conn.close()
            return completed_trades
            
        except Exception as e:
            logger.error(f"❌ Failed to get today's completed trades from database: {e}")
            return []

    @property
    def daily_pnl(self):
        """Calculate daily PnL from database (single source of truth)"""
        try:
            # Get all completed trades from today from database
            completed_trades = self.get_todays_completed_trades_from_db()
            
            # Also include any journal entries that might not be in database yet
            from datetime import date
            today = date.today().isoformat()
            
            journal_pnl = 0.0
            db_trade_ids = {trade['id'] for trade in completed_trades}
            
            # DEBUG: Log what we're working with
            db_pnl = sum(trade['pnl'] for trade in completed_trades)
            logger.debug(f"🔍 Daily PnL Debug - DB trades: {len(completed_trades)}, DB IDs: {db_trade_ids}, DB PnL: ${db_pnl:.2f}")
            
            journal_supplement_count = 0
            for trade in self.trading_journal:
                try:
                    # Only include journal trades not already in database
                    exit_time = trade.get('exit_time', '')
                    trade_id = trade.get('id')
                    trade_pnl = trade.get('pnl', 0.0)
                    
                    is_today = exit_time and exit_time.startswith(today)
                    not_in_db = trade_id not in db_trade_ids
                    
                    if is_today and not_in_db:
                        journal_pnl += trade_pnl
                        journal_supplement_count += 1
                        logger.debug(f"  📝 Journal supplement: ID {trade_id}, PnL ${trade_pnl:.2f}")
                        
                except Exception as e:
                    logger.debug(f"  ❌ Journal trade error: {e}")
                    continue
            
            total_pnl = db_pnl + journal_pnl
            logger.debug(f"📊 Daily PnL Final: DB=${db_pnl:.2f} + Journal=${journal_pnl:.2f} ({journal_supplement_count} trades) = Total=${total_pnl:.2f}")
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate daily PnL: {e}")
            return 0.0
    
    def has_recent_signal(self, symbol: str) -> bool:
        """Check if a signal was recently generated for this symbol (Solution 2)"""
        if symbol not in self.recent_signals_cache:
            return False
        
        last_signal_time = self.recent_signals_cache[symbol]
        current_time = datetime.now()
        time_diff = (current_time - last_signal_time).total_seconds() / 60
        
        return time_diff < self.signal_cooldown_minutes
    
    def update_signal_cache(self, symbol: str):
        """Update the signal cache with new signal time"""
        self.recent_signals_cache[symbol] = datetime.now()
    
    def get_active_positions_for_symbol(self, symbol: str) -> int:
        """Count active positions (live signals + paper trades) for a symbol"""
        # Count live signals
        live_count = sum(1 for signal in self.live_signals 
                        if signal.get('crypto') == symbol.replace('USDT', ''))
        
        # Count active paper trades
        trade_count = sum(1 for trade in self.active_paper_trades 
                         if trade.get('symbol') == symbol)
        
        return live_count + trade_count
    
    def calculate_portfolio_risk(self) -> float:
        """Calculate current portfolio risk percentage (Solution 3)"""
        total_risk = 0
        for trade in self.active_paper_trades:
            if trade.get('status') == 'OPEN':
                risk_amount = trade.get('risk_amount', 0)
                total_risk += risk_amount
        
        return (total_risk / self.paper_balance) if self.paper_balance > 0 else 0
    
    def can_accept_new_signal(self, symbol: str, price: float = None) -> tuple[bool, str]:
        """Comprehensive check if new signal can be accepted (Solutions 2 & 3)"""
        crypto = symbol.replace('USDT', '')
        
        # Check 1: Recent signal cooldown
        if self.has_recent_signal(crypto):
            return False, f"Recent signal cooldown: {crypto} signaled within {self.signal_cooldown_minutes}min"
        
        # Check 2: Maximum positions per symbol
        active_positions = self.get_active_positions_for_symbol(symbol)
        if active_positions >= self.max_positions_per_symbol:
            return False, f"Max positions reached: {active_positions}/{self.max_positions_per_symbol} for {crypto}"
        
        # Check 3: Price separation from existing signals (prevent duplicate entries at same level)
        min_price_separation = self.get_minimum_price_separation(crypto, price)
        logger.info(f"🔍 Price separation check for {crypto} @ ${price:.2f}: need {min_price_separation:.1f}% separation")
        if not self.has_sufficient_price_separation(crypto, price, min_price_separation):
            logger.info(f"❌ Price separation REJECTED: {crypto} @ ${price:.2f} too close to existing signal")
            return False, f"Price too close to existing {crypto} signal (need >{min_price_separation:.1f}% separation)"
        logger.info(f"✅ Price separation OK: {crypto} @ ${price:.2f} has sufficient separation")
        
        # Check 4: Maximum concurrent signals
        if len(self.live_signals) >= self.max_concurrent_signals:
            return False, f"Max concurrent signals: {len(self.live_signals)}/{self.max_concurrent_signals}"
        
        # Check 5: Portfolio risk limit
        current_risk = self.calculate_portfolio_risk()
        new_trade_risk = self.risk_per_trade
        if current_risk + new_trade_risk > self.max_portfolio_risk:
            return False, f"Portfolio risk limit: {(current_risk + new_trade_risk)*100:.1f}% > {self.max_portfolio_risk*100:.1f}%"
        
        # Check 6: Account blown
        if self.account_blown:
            return False, "Account blown - no new signals allowed"
        
        return True, "Signal approved"
    
    def get_signal_age_minutes(self, signal_timestamp):
        """Calculate signal age in minutes"""
        try:
            if isinstance(signal_timestamp, str):
                signal_time = self._safe_parse_timestamp(signal_timestamp)
            else:
                signal_time = signal_timestamp
            return (datetime.now() - signal_time).total_seconds() / 60
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Error calculating signal age for timestamp {signal_timestamp}: {e}")
            return 999  # Return large number for invalid timestamps
    
    def get_signal_age_category(self, age_minutes):
        """Get signal age category for UI display"""
        if age_minutes <= 2:
            return 'fresh'  # 0-2 minutes: Fresh (green)
        elif age_minutes <= 4:
            return 'active'  # 2-4 minutes: Active (yellow)
        else:
            return 'expiring'  # 4-5 minutes: Expiring (orange)
    
    def get_minimum_price_separation(self, crypto: str, current_price: float) -> float:
        """Get minimum price separation percentage based on crypto volatility"""
        # Different separation requirements based on typical volatility
        separations = {
            'BTC': 2.0,   # 2% separation for BTC
            'ETH': 3.0,   # 3% separation for ETH  
            'SOL': 5.0,   # 5% separation for SOL (more volatile)
            'XRP': 4.0    # 4% separation for XRP
        }
        return separations.get(crypto, 3.0)  # Default 3% if crypto not found
    
    def has_sufficient_price_separation(self, crypto: str, new_price: float, min_separation_pct: float) -> bool:
        """Check if new signal price is sufficiently separated from existing signals"""
        if not new_price:
            return True  # Allow if no price provided (backward compatibility)
            
        logger.info(f"🔍 Checking price separation for {crypto} @ ${new_price:.2f} (need {min_separation_pct:.1f}%)")
        
        # Check against live signals for this crypto
        live_signal_count = 0
        for signal in self.live_signals:
            if signal.get('crypto') == crypto:
                live_signal_count += 1
                existing_price = signal.get('entry_price', 0)
                if existing_price > 0:
                    price_diff_pct = abs((new_price - existing_price) / existing_price) * 100
                    logger.info(f"   📊 vs Live Signal: ${existing_price:.2f} - difference: {price_diff_pct:.2f}%")
                    if price_diff_pct < min_separation_pct:
                        logger.info(f"   ❌ BLOCKED by live signal: {price_diff_pct:.2f}% < {min_separation_pct:.1f}%")
                        return False
        
        # Check against active paper trades for this crypto
        trade_count = 0
        for trade in self.active_paper_trades:
            if trade.get('symbol', '').replace('USDT', '') == crypto and trade.get('status') == 'OPEN':
                trade_count += 1
                existing_price = trade.get('entry_price', 0)
                if existing_price > 0:
                    price_diff_pct = abs((new_price - existing_price) / existing_price) * 100
                    logger.info(f"   💼 vs Active Trade: ${existing_price:.2f} - difference: {price_diff_pct:.2f}%")
                    if price_diff_pct < min_separation_pct:
                        logger.info(f"   ❌ BLOCKED by active trade: {price_diff_pct:.2f}% < {min_separation_pct:.1f}%")
                        return False
        
        logger.info(f"   ✅ Price separation OK: checked {live_signal_count} live signals, {trade_count} active trades")
        return True
    
    def manage_signal_lifecycle(self):
        """Manage signal lifecycle with 5-minute expiry and 3-signal limit"""
        current_time = datetime.now()
        
        # Separate fresh and expired signals
        fresh_signals = []
        expired_signals = []
        
        # Update age information for all signals
        for signal in self.live_signals:
            age_minutes = self.get_signal_age_minutes(signal.get('timestamp', current_time))
            signal['age_minutes'] = age_minutes
            signal['age_category'] = self.get_signal_age_category(age_minutes)
        
        # Expire signals older than configured lifetime
        expired_signals = [s for s in self.live_signals if s.get('age_minutes', 0) > self.signal_lifetime_minutes]
        if expired_signals:
            self.archived_signals.extend(expired_signals)
            # Keep only those not expired in live_signals
            self.live_signals = [s for s in self.live_signals if s not in expired_signals]
            
            # 🔧 SYNC DATABASE: Mark expired signals as 'EXPIRED' in database
            self._sync_expired_signals_to_database(expired_signals)

        # If we have more than 3 signals, keep only the newest 3
        if len(self.live_signals) > self.max_live_signals:
            # Sort by timestamp (newest first) 
            self.live_signals.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Move excess (oldest) signals to archive
            excess_signals = self.live_signals[self.max_live_signals:]
            self.archived_signals.extend(excess_signals)
            
            # Keep only the newest 3
            self.live_signals = self.live_signals[:self.max_live_signals]
            
            logger.info(f"📋 Signal Rotation: Moved {len(excess_signals)} older signals to archive, displaying newest 3")
            archived_count = len(excess_signals) + len(expired_signals)
        else:
            archived_count = len(expired_signals)
        
        # Keep only last 100 archived signals to prevent memory bloat
        if len(self.archived_signals) > 100:
            self.archived_signals = self.archived_signals[-100:]
        

        # Debug logging to see what's happening
        if len(self.live_signals) > 0:
            oldest_signal_age = max(s.get('age_minutes', 0) for s in self.live_signals)
            logger.info(f"� Signal Status: {len(self.live_signals)} live, {len(expired_signals)} expired, oldest: {oldest_signal_age:.1f}min")
        
        return archived_count
    
    def select_dynamic_rr_ratio(self, signal):
        """
        Dynamically select Risk-Reward ratio based on signal quality and market conditions
        Always risks exactly 1% but adjusts reward target based on setup quality
        """
        confluence_score = signal.get('confluence_score', 0.5)
        bias_strength = signal.get('bias_strength', 0.5)
        
        # Calculate signal quality score (0.0 to 1.0)
        quality_score = (confluence_score + bias_strength) / 2
        
        # Select RR ratio based on quality
        if quality_score >= 0.9:
            rr_mode = 'maximum'      # 1:5 RR for exceptional setups
        elif quality_score >= 0.8:
            rr_mode = 'aggressive'   # 1:4 RR for high-confidence
        elif quality_score >= 0.7:
            rr_mode = 'balanced'     # 1:3 RR for normal trades
        else:
            rr_mode = 'conservative' # 1:2 RR for safer trades
        
        selected_rr = self.dynamic_rr_ratios[rr_mode]
        
        logger.info(f"🎯 DYNAMIC RR: Quality={quality_score:.2f} → {rr_mode.upper()} (1:{selected_rr}) | Risk=1.0% FIXED")
        
        return selected_rr
    
    def execute_paper_trade(self, signal):
        """Execute a paper trade based on signal"""
        if not self.paper_trading_enabled:
            return
        
        # STRICT 1% risk per trade with DYNAMIC Risk-Reward ratio
        risk_percentage = 0.01  # FIXED 1% risk per trade - NEVER CHANGES
        risk_amount = self.paper_balance * risk_percentage
        
        # Get dynamic RR ratio based on signal quality
        dynamic_rr = self.select_dynamic_rr_ratio(signal)
        
        confluence_score = signal.get('confluence_score', 0.5)
        # FIXED: Removed unused signal_strength variable
        logger.info(f"📊 RISK MANAGEMENT: Fixed 1.0% risk (${risk_amount:.2f}) | Dynamic RR 1:{dynamic_rr} | Confluence: {confluence_score:.3f}")
        
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        
        # Recalculate take profit using dynamic RR ratio
        stop_distance = abs(entry_price - stop_loss)
        if signal['action'] == 'BUY':
            take_profit = entry_price + (stop_distance * dynamic_rr)
        else:  # SELL
            take_profit = entry_price - (stop_distance * dynamic_rr)
        
        # Calculate position size based on stop loss distance (1% risk)
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            position_size = risk_amount / (entry_price * 0.02)  # 2% default if no stop
        
        # Create paper trade
        paper_trade = {
            'id': f"PT_{len(self.active_paper_trades) + len(self.completed_paper_trades) + 1}",
            'signal_id': signal.get('id', ''),  # Store the actual signal ID for proper linking
            'crypto': signal['crypto'],
            'symbol': signal.get('symbol', f"{signal['crypto']}USDT"),  # Add symbol field for position tracking
            'action': signal['action'],
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'risk_amount': risk_amount,
            'entry_time': datetime.now(),
            'status': 'OPEN',
            'pnl': 0.0,
            'confidence': signal.get('confidence', 0.0),
            'timeframe': signal.get('timeframe', '1h')
        }
        
        self.active_paper_trades.append(paper_trade)
        logger.info(f"📄 PAPER TRADE OPENED: {paper_trade['crypto']} {paper_trade['action']} | Size: {position_size:.4f} | Risk: ${risk_amount:.2f} (1%) | RR: 1:{dynamic_rr}")
        
        # Save paper trade to database for persistence
        self.save_paper_trade_to_database(paper_trade)
        
        # Update signal with paper trade ID
        signal['paper_trade_id'] = paper_trade['id']
        signal['status'] = 'EXECUTED'
        
        return paper_trade
    
    def update_paper_trades(self, current_prices):
        """Update active paper trades with current prices"""
        if not current_prices:
            return
        
        trades_to_close = []
        
        for trade in self.active_paper_trades:
            crypto = trade['crypto']
            if crypto not in current_prices:
                continue

            current_price = current_prices[crypto]['price']
            entry_price = trade['entry_price']
            position_size = trade['position_size']
            action = trade['action']
            risk_amount = trade.get('risk_amount', self.paper_balance * self.risk_per_trade)

            # Calculate current PnL
            if action == 'BUY':
                pnl = (current_price - entry_price) * position_size
            else:  # SELL
                pnl = (entry_price - current_price) * position_size

            trade['current_price'] = current_price
            trade['pnl'] = pnl

            # Check for stop loss or take profit
            should_close = False
            close_reason = ""

            # Log trade monitoring details every 10th scan for debugging
            if hasattr(self, 'scan_count') and self.scan_count % 10 == 0:
                logger.info(f"🔍 MONITORING: {crypto} {action} | Current: ${current_price:.4f} | Entry: ${entry_price:.4f} | SL: ${trade['stop_loss']:.4f} | TP: ${trade['take_profit']:.4f} | PnL: ${pnl:.2f}")

            if action == 'BUY':
                if current_price <= trade['stop_loss']:
                    should_close = True
                    close_reason = "STOP_LOSS"
                elif current_price >= trade['take_profit']:
                    should_close = True
                    close_reason = "TAKE_PROFIT"
            else:  # SELL
                if current_price >= trade['stop_loss']:
                    should_close = True
                    close_reason = "STOP_LOSS"
                elif current_price <= trade['take_profit']:
                    should_close = True
                    close_reason = "TAKE_PROFIT"

            # Strict 1% risk enforcement: cap loss at risk_amount
            if should_close and close_reason == "STOP_LOSS" and pnl < 0 and abs(pnl) > abs(risk_amount):
                logger.warning(f"⚠️ Loss exceeded risk amount! Capping loss to -${risk_amount:.2f} (was ${pnl:.2f})")
                pnl = -abs(risk_amount)
                trade['pnl'] = pnl

            # Close trade if conditions met
            if should_close:
                trade['exit_price'] = current_price
                trade['exit_time'] = datetime.now()
                trade['status'] = close_reason
                trade['final_pnl'] = pnl

                # Update totals and balance
                self.total_paper_pnl += pnl
                # Update paper balance with PnL - this affects next trade's 1% risk calculation
                self.paper_balance += pnl

                # ✅ FIX: Save balance update to database
                self.save_balance_to_database(self.paper_balance, f"Trade closed: {close_reason} ${pnl:.2f}")

                # Check for account blow-up
                if self.paper_balance <= self.blow_up_threshold and not self.account_blown:
                    self.account_blown = True
                    logger.error(f"💥 ACCOUNT BLOWN! Balance: ${self.paper_balance:.2f} | TRADING STOPPED")
                    logger.info(f"🔄 Use /reset_account endpoint to restart with $100")

                # daily_pnl is now calculated dynamically from completed_paper_trades

                trades_to_close.append(trade)
                blown_msg = " | 💥 ACCOUNT BLOWN!" if self.account_blown else ""
                logger.info(f"📄 PAPER TRADE CLOSED: {trade['crypto']} {trade['action']} | {close_reason} | PnL: ${pnl:.2f} | New Balance: ${self.paper_balance:.2f}{blown_msg}")
        
        # Move closed trades to completed
        for trade in trades_to_close:
            self.active_paper_trades.remove(trade)
            self.completed_paper_trades.append(trade)
            # Add to trading journal when trade completes (only if it's today)
            from datetime import date
            today_str = date.today().isoformat()
            
            # Check if this trade closed today
            trade_exit_date = None
            if 'exit_time' in trade:
                try:
                    if isinstance(trade['exit_time'], str):
                        trade_exit_date = trade['exit_time'][:10]
                    else:
                        trade_exit_date = trade['exit_time'].strftime('%Y-%m-%d')
                except:
                    pass
            
            # Only add to journal if it closed today
            if trade_exit_date == today_str:
                self.trading_journal.append(trade)
                # Guarantee: Save journal entry to database immediately
                self.save_trading_journal_entry(trade)
            # ✅ FIX: Update the trade in database when it closes
            self.update_paper_trade_in_database(trade)
        
        # Keep only last 50 completed trades
        if len(self.completed_paper_trades) > 50:
            self.completed_paper_trades = self.completed_paper_trades[-50:]
        
        # ✅ FIX: Update active trades in database with current prices and unrealized PnL
        self.update_active_trades_in_database(current_prices)
        
        return len(trades_to_close)
    
    def check_and_close_eod_positions(self, current_prices):
        """Check if it's end of day and close all open positions (DATABASE-DRIVEN)"""
        if not self.close_positions_eod or not current_prices:
            return 0
        
        from datetime import datetime
        import sqlite3
        
        now = datetime.now()
        current_date = now.date()
        
        # Check if we've already done EOD closure today
        if self.last_eod_check_date == current_date:
            return 0
        
        # Check if current time is at or past EOD close time
        eod_time = now.replace(hour=self.eod_close_hour, minute=self.eod_close_minute, second=0, microsecond=0)
        
        # Query ALL open positions from database (not just in-memory)
        try:
            # CRITICAL FIX: Use consistent database path for EOD closure
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            
            # Get ALL open positions regardless of entry date
            cursor.execute("""
                SELECT id, symbol, direction, entry_price, position_size, 
                       stop_loss, take_profit, entry_time, risk_amount
                FROM paper_trades 
                WHERE status = 'OPEN'
            """)
            
            open_positions = cursor.fetchall()
            
            if now >= eod_time and len(open_positions) > 0:
                logger.info(f"🌙 END OF DAY: Closing all {len(open_positions)} open positions at market")
                
                closed_count = 0
                
                for position in open_positions:
                    trade_id, symbol, direction, entry_price, position_size, stop_loss, take_profit, entry_time, risk_amount = position
                    
                    # Get crypto symbol (remove USDT)
                    crypto = symbol.replace('USDT', '')
                    
                    if crypto not in current_prices:
                        logger.warning(f"⚠️ No price data for {crypto}, skipping EOD closure")
                        continue
                    
                    current_price = current_prices[crypto]['price']
                    
                    # Calculate final PnL
                    if direction == 'BUY':
                        pnl = (current_price - entry_price) * position_size
                    else:  # SELL
                        pnl = (entry_price - current_price) * position_size
                    
                    # Update the trade in database
                    cursor.execute("""
                        UPDATE paper_trades 
                        SET exit_price = ?, exit_time = ?, status = 'EOD_CLOSE', 
                            realized_pnl = ?
                        WHERE id = ?
                    """, (current_price, now.isoformat(), pnl, trade_id))
                    
                    # Update balance
                    self.paper_balance += pnl
                    self.total_paper_pnl += pnl
                    
                    # Save balance update
                    self.save_balance_to_database(self.paper_balance, f"EOD Close: {crypto} ${pnl:.2f}")
                    
                    # Create journal entry
                    journal_entry = {
                        'id': trade_id,
                        'symbol': symbol,
                        'crypto': crypto,
                        'direction': direction,
                        'action': direction,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position_size': position_size,
                        'entry_time': entry_time,
                        'exit_time': now.isoformat(),
                        'status': 'EOD_CLOSE',
                        'final_pnl': pnl,
                        'pnl': pnl,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_amount': risk_amount
                    }
                    
                    # Save journal entry
                    self.save_trading_journal_entry(journal_entry)
                    
                    # Remove from active trades if it exists in memory
                    self.active_paper_trades = [t for t in self.active_paper_trades if t.get('id') != trade_id]
                    
                    # Update corresponding signal status to show it's closed
                    paper_trade_id = f"PT_{trade_id}"
                    for signal in self.live_signals:
                        if signal.get('paper_trade_id') == paper_trade_id:
                            signal['status'] = 'EOD_CLOSE'
                            signal['exit_price'] = current_price
                            signal['exit_time'] = now.isoformat()
                            signal['final_pnl'] = pnl
                            # Move to archived signals
                            self.archived_signals.append(signal)
                            break
                    
                    # Remove closed signal from live signals
                    self.live_signals = [s for s in self.live_signals if s.get('paper_trade_id') != paper_trade_id]
                    
                    # Add to completed trades
                    self.completed_paper_trades.append(journal_entry)
                    self.trading_journal.append(journal_entry)
                    
                    logger.info(f"🌙 EOD CLOSED: {crypto} {direction} | Price: ${current_price:.4f} | PnL: ${pnl:.2f}")
                    closed_count += 1
                
                conn.commit()
                
                # Mark that we've done EOD closure for today
                self.last_eod_check_date = current_date
                
                if closed_count > 0:
                    logger.info(f"✅ EOD CLOSURE COMPLETE: {closed_count} positions closed | New Balance: ${self.paper_balance:.2f}")
                
                conn.close()
                return closed_count
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ EOD Closure Error: {e}")
            if 'conn' in locals():
                conn.close()
        
        return 0
        
    async def get_real_time_prices(self):
        """Get real-time prices from Bybit API for consistency with demo trading"""
        try:
            if self.bybit_prices:
                # Get prices from Bybit real-time price monitor
                btc_data = self.bybit_prices.get_price('BTCUSDT')
                eth_data = self.bybit_prices.get_price('ETHUSDT')
                sol_data = self.bybit_prices.get_price('SOLUSDT')
                xrp_data = self.bybit_prices.get_price('XRPUSDT')
                
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
            async with aiohttp.ClientSession() as session:
                # Use CoinGecko as fallback source
                url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = {}
                        
                        # Map CoinGecko IDs to our crypto names
                        coin_mapping = {
                            'bitcoin': 'BTC',
                            'ethereum': 'ETH', 
                            'solana': 'SOL',
                            'ripple': 'XRP'
                        }
                        
                        for coin_id, crypto_name in coin_mapping.items():
                            if coin_id in data:
                                coin_data = data[coin_id]
                                price = coin_data['usd']
                                change_24h = coin_data.get('usd_24h_change', 0)
                                volume_24h = coin_data.get('usd_24h_vol', 0)
                                
                                prices[crypto_name] = {
                                    'price': float(price),
                                    'change_24h': float(change_24h),
                                    'volume': float(volume_24h),
                                    'high_24h': float(price * 1.02),  # Estimate
                                    'low_24h': float(price * 0.98),   # Estimate
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        logger.info(f"✅ Fallback prices updated from CoinGecko: BTC=${prices['BTC']['price']:,.2f}")
                        return prices
                    else:
                        logger.warning("Failed to fetch prices from CoinGecko")
                        return await self.get_binance_fallback()
                        
        except Exception as e:
            logger.error(f"Error fetching CoinGecko prices: {e}")
            return await self.get_binance_fallback()
    
    async def get_binance_fallback(self):
        """Try Binance as fallback, then static prices if that fails"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.binance.com/api/v3/ticker/24hr"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = {}
                        
                        for item in data:
                            symbol = item['symbol']
                            if symbol in self.symbols:
                                crypto_name = symbol.replace('USDT', '')
                                prices[crypto_name] = {
                                    'price': float(item['lastPrice']),
                                    'change_24h': float(item['priceChangePercent']),
                                    'volume': float(item['volume']),
                                    'high_24h': float(item['highPrice']),
                                    'low_24h': float(item['lowPrice']),
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        logger.info("✅ Fallback prices from Binance")
                        return prices
                        
        except Exception as e:
            logger.warning(f"Binance fallback also failed: {e}")
            
        logger.warning("⚠️ Using static fallback prices - UPDATE NEEDED!")
        return self.get_fallback_prices()
    
    def get_fallback_prices(self):
        """Emergency fallback prices when all APIs fail - Updated to current market values (Oct 1, 2025)"""
        return {
            'BTC': {
                'price': 117465 * (1 + np.random.uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.uniform(-3, 3),
                'volume': np.random.uniform(15000, 25000),
                'high_24h': 118500,
                'low_24h': 116000,
                'timestamp': datetime.now().isoformat()
            },
            'SOL': {
                'price': 219 * (1 + np.random.uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.uniform(-4, 4),
                'volume': np.random.uniform(800000, 1200000),
                'high_24h': 222,
                'low_24h': 216,
                'timestamp': datetime.now().isoformat()
            },
            'ETH': {
                'price': 4337 * (1 + np.random.uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.uniform(-3, 3),
                'volume': np.random.uniform(300000, 500000),
                'high_24h': 4380,
                'low_24h': 4290,
                'timestamp': datetime.now().isoformat()
            },
            'XRP': {
                'price': 2.94 * (1 + np.random.uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.uniform(-5, 5),
                'volume': np.random.uniform(2000000, 3000000),
                'high_24h': 2.98,
                'low_24h': 2.85,
                'timestamp': datetime.now().isoformat()
            }
        }

class ICTSignalGenerator:
    """ICT Signal Generator with ML model integration and Directional Bias Engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.timeframes = ['1m', '5m', '15m', '1h', '4h']
        self.min_confidence = 0.6  # 60% minimum confidence
        self.ml_model = None
        self.load_ml_model()
        
        # STARTUP COOLDOWN SYSTEM for ICTSignalGenerator - DISABLED
        self.startup_time = datetime.now()
        self.startup_cooldown_minutes = 0  # No cooldown - immediate comprehensive ICT analysis
        logger.info(f"✅ ICTSignalGenerator startup cooldown DISABLED - Comprehensive analysis active immediately")
        
        # Directional Bias Engine - DISABLED (Only comprehensive ICT methodology)
        self.directional_bias_engine = None
        
        # COMPREHENSIVE ICT METHODOLOGY IMPLEMENTATION
        self.ict_methodology = {
            'higher_timeframe_analysis': {
                'primary_timeframes': ['4H', '1H'],        # Market structure determination
                'confirmation_timeframe': '15M',           # Entry refinement
                'structure_lookback': 200,                 # Candles for structure analysis
                'trend_confirmation_bars': 20              # Bars for trend confirmation
            },
            'enhanced_order_blocks': {
                'min_volume_multiplier': 1.5,              # Volume must be 1.5x average
                'min_body_percentage': 0.7,                # 70% body minimum
                'max_wicks_percentage': 0.3,               # 30% wicks maximum
                'alignment_tolerance': 0.001,              # 0.1% alignment tolerance
                'mitigation_percentage': 0.5               # 50% mitigation for invalidation
            },
            'fibonacci_confluence': {
                'key_levels': [0.236, 0.382, 0.5, 0.618, 0.786],
                'tolerance': 0.002,                        # 0.2% tolerance for level hits
                'min_retracement': 0.236,                  # Minimum retracement for validity
                'max_retracement': 0.786,                  # Maximum before invalidation
                'confluence_weight': 0.3                   # Weight in overall score
            },
            'fair_value_gaps': {
                'min_gap_percentage': 0.001,               # 0.1% minimum gap size
                'max_gap_age_bars': 50,                    # Max bars since gap creation
                'partial_fill_threshold': 0.7,            # 70% fill before mitigation
                'confluence_weight': 0.25                  # Weight in overall score
            },
            'market_structure': {
                'swing_lookback': 20,                      # Bars for swing identification
                'structure_break_confirmation': 3,         # Bars to confirm break
                'min_structure_distance': 0.005,          # 0.5% minimum distance
                'bos_confluence_weight': 0.2,              # Break of structure weight
                'choch_confluence_weight': 0.15            # Change of character weight
            },
            'liquidity_pools': {
                'equal_level_tolerance': 0.002,            # 0.2% tolerance for equal levels
                'min_tests': 2,                            # Minimum level tests
                'max_tests': 4,                            # Maximum before likely break
                'proximity_weight': 0.1,                   # Weight for proximity to levels
                'volume_confirmation': True                # Require volume confirmation
            }
        }
        
        # Crypto-specific characteristics for comprehensive ICT analysis
        self.crypto_characteristics = {
            'BTC': {
                'volatility_factor': 1.0,      # Base volatility
                'liquidity_rank': 1,           # Highest liquidity
                'correlation_weight': 0.4,     # Market leader influence
                'structure_sensitivity': 0.8,  # High structure importance
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618, 0.786],
                'timeframe_priority': ['4H', '1H', '15M'],  # Primary timeframes
                'session_preference': ['NY', 'London'],    # Preferred sessions
                'min_confluence_score': 0.75,              # Higher standards for BTC
                'order_block_lookback': 100               # Candles to look back for OB
            },
            'ETH': {
                'volatility_factor': 1.2,      # Higher volatility than BTC
                'liquidity_rank': 2,           # Second highest liquidity
                'correlation_weight': 0.3,     # Strong but not leader
                'structure_sensitivity': 0.75, # Good structure respect
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618, 0.786],
                'timeframe_priority': ['4H', '1H', '15M'],
                'session_preference': ['NY', 'London', 'Asia'],
                'min_confluence_score': 0.70,              # Slightly lower than BTC
                'order_block_lookback': 80
            },
            'SOL': {
                'volatility_factor': 1.8,      # Much higher volatility
                'liquidity_rank': 3,           # Moderate liquidity
                'correlation_weight': 0.2,     # Moderate correlation
                'structure_sensitivity': 0.65, # Lower structure respect
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618],  # Fewer levels
                'timeframe_priority': ['1H', '15M', '5M'],        # Faster timeframes
                'session_preference': ['NY', 'Asia'],             # Different sessions
                'min_confluence_score': 0.65,                     # Lower due to higher volatility
                'order_block_lookback': 60
            },
            'XRP': {
                'volatility_factor': 1.5,      # High volatility
                'liquidity_rank': 4,           # Lower liquidity
                'correlation_weight': 0.15,    # Lower correlation
                'structure_sensitivity': 0.60, # Moderate structure respect
                'fibonacci_levels': [0.236, 0.382, 0.5, 0.618],
                'timeframe_priority': ['1H', '15M', '5M'],
                'session_preference': ['NY', 'London'],
                'min_confluence_score': 0.60,                     # Lowest threshold
                'order_block_lookback': 50
            }
        }
        
        self.logger.info("✅ Comprehensive ICT Signal Generator initialized - NO FALLBACK SYSTEM")
        
    def load_ml_model(self):
        """Load ML model for enhanced signal detection"""
        try:
            # Try to load existing ML model
            import joblib
            import os
            model_path = "models/crypto_ml_model.pkl"
            if os.path.exists(model_path):
                self.ml_model = joblib.load(model_path)
                self.logger.info("✅ ML Model loaded successfully")
            else:
                self.logger.warning("⚠️ ML Model not found, using analysis only")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load ML model: {e}")
            self.ml_model = None
    
    def should_generate_signals(self) -> bool:
        """Check if enough time has passed since startup to generate signals"""
        minutes_since_startup = (datetime.now() - self.startup_time).total_seconds() / 60
        if minutes_since_startup < self.startup_cooldown_minutes:
            return False
        return True
    
    def generate_crypto_specific_signal(self, crypto: str, price_data: Dict) -> Optional[Dict]:
        """Generate signal using comprehensive ICT methodology - simplified for ICTSignalGenerator"""
        try:
            # Check startup cooldown
            if not self.should_generate_signals():
                return None
                
            # Use traditional analysis since we're in the ICTSignalGenerator context
            # This is a fallback that respects the cooldown
            return None  # For now, let the main monitor handle the comprehensive analysis
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate signal for {crypto}: {e}")
            return None
    
    def _convert_crypto_signal_to_trading_signal(self, signal: Dict, price_data: Dict) -> Optional[Dict]:
        """Convert crypto-specific ICT signal to trading signal format - simplified"""
        # This method exists in the main ICTCryptoMonitor class
        return None
        
    def generate_trading_signals(self, crypto_data: Dict) -> List[Dict]:
        """Generate trading signals using comprehensive ICT methodology with crypto-specific analysis"""
        signals = []
        
        logger.info("📊 Starting comprehensive ICT analysis with crypto-specific methodology")
        
        # Check startup cooldown first
        if not self.should_generate_signals():
            minutes_remaining = self.startup_cooldown_minutes - ((datetime.now() - self.startup_time).total_seconds() / 60)
            logger.info(f"� Startup cooldown active: {minutes_remaining:.1f} minutes remaining before signal generation")
            return signals
        
        # Process each crypto with individual analysis
        for crypto in crypto_data.keys():
            try:
                crypto_symbol = crypto.replace('USDT', '')
                logger.info(f"🔍 Analyzing {crypto_symbol} with comprehensive ICT methodology")
                
                # Use new crypto-specific signal generation
                signal = self.generate_crypto_specific_signal(crypto_symbol, crypto_data[crypto])
                
                if signal:
                    # Convert to full trading signal format
                    enhanced_signal = self._convert_crypto_signal_to_trading_signal(signal, crypto_data[crypto])
                    if enhanced_signal:
                        signals.append(enhanced_signal)
                        logger.info(f"✅ {crypto_symbol} signal generated: {signal['direction']} "
                                  f"(Confluence: {signal['confluence_score']:.2f}, "
                                  f"Timeframe: {signal['timeframe']}, "
                                  f"Session: {signal['session_preference']})")
                else:
                    logger.debug(f"❌ {crypto_symbol} - No signal: Insufficient confluence or timing")
                
                # Add small delay between crypto analysis to prevent system overload
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Comprehensive ICT analysis failed for {crypto}: {e}")
                # NO FALLBACK - Only comprehensive ICT methodology allowed
                logger.info(f"🚫 No fallback for {crypto} - Only comprehensive ICT signals generated")
        
        # Prevent identical signals at same time (your main concern)
        if len(signals) > 1:
            # Ensure signals have different confluence scores and timing
            unique_signals = []
            used_confluences = set()
            
            for signal in signals:
                confluence_key = f"{signal['confluence_score']:.3f}_{signal['timeframe']}"
                if confluence_key not in used_confluences:
                    unique_signals.append(signal)
                    used_confluences.add(confluence_key)
                else:
                    logger.info(f"� Filtered duplicate confluence signal for {signal['crypto']}")
            
            signals = unique_signals
        
        logger.info(f"📈 Comprehensive ICT analysis complete: {len(signals)} unique, high-quality signals generated")
        return signals
    
    def _prepare_price_data_for_bias_analysis(self, crypto_price_data: Dict) -> pd.DataFrame:
        """Convert crypto price data to DataFrame format for bias engine analysis"""
        try:
            # Create a simulated price series for analysis
            current_price = crypto_price_data['price']
            high_24h = crypto_price_data.get('high_24h', current_price)
            low_24h = crypto_price_data.get('low_24h', current_price)
            volume_24h = crypto_price_data.get('volume_24h', 1000000)
            
            # Generate simulated OHLCV data for last 100 periods (representing recent price action)
            periods = 100
            timestamps = pd.date_range(end=datetime.now(), periods=periods, freq='1min')
            
            # Create realistic price movement simulation
            price_range = high_24h - low_24h
            base_price = low_24h
            
            # Generate OHLCV data with realistic ICT-style price action
            data = []
            for i, timestamp in enumerate(timestamps):
                # Simulate price movement with trend bias toward current price
                progress = i / periods
                trend_price = base_price + (price_range * progress * 0.8) + (current_price - base_price) * progress
                
                # Add some random variation
                variation = price_range * 0.02 * np.random.uniform(-1, 1)
                candle_mid = trend_price + variation
                
                # Create OHLC for this candle
                candle_range = price_range * 0.01 * np.random.uniform(0.5, 2.0)
                open_price = candle_mid + candle_range * np.random.uniform(-0.5, 0.5)
                close_price = candle_mid + candle_range * np.random.uniform(-0.5, 0.5)
                high_price = max(open_price, close_price) + candle_range * np.random.uniform(0, 0.3)
                low_price = min(open_price, close_price) - candle_range * np.random.uniform(0, 0.3)
                
                data.append({
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume_24h / periods * np.random.uniform(0.5, 2.0)
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"❌ Error preparing price data for bias analysis: {e}")
            # Return minimal DataFrame if preparation fails
            return pd.DataFrame({
                'open': [crypto_price_data['price']],
                'high': [crypto_price_data.get('high_24h', crypto_price_data['price'])],
                'low': [crypto_price_data.get('low_24h', crypto_price_data['price'])],
                'close': [crypto_price_data['price']],
                'volume': [crypto_price_data.get('volume_24h', 1000000)]
            }, index=[datetime.now()])
    
    def _convert_bias_signal_to_trading_signal(self, bias_signal: Dict, crypto: str, price_data: Dict) -> Optional[Dict]:
        """Convert directional bias signal to our trading signal format"""
        try:
            entry_price = price_data['price']
            action = bias_signal['recommended_action']
            
            if action not in ['BUY', 'SELL']:
                return None
            
            # Use bias engine's calculated levels
            entry_range = bias_signal.get('entry_price_range', {'min': entry_price, 'max': entry_price})
            stop_loss = bias_signal.get('stop_loss_level', 0)
            take_profit_targets = bias_signal.get('take_profit_targets', [1.5, 2.5, 4.0])
            
            # Calculate stop loss if not provided by bias engine
            if stop_loss == 0:
                if action == 'BUY':
                    stop_loss = entry_price * 0.985  # 1.5% stop loss
                else:
                    stop_loss = entry_price * 1.015  # 1.5% stop loss
            
            # Calculate take profit (use first target from bias engine)
            if take_profit_targets:
                tp_ratio = take_profit_targets[0]  # Use first target
                stop_distance = abs(entry_price - stop_loss)
                if action == 'BUY':
                    take_profit = entry_price + (stop_distance * tp_ratio)
                else:
                    take_profit = entry_price - (stop_distance * tp_ratio)
            else:
                # Fallback to 3:1 ratio
                if action == 'BUY':
                    take_profit = entry_price + (abs(entry_price - stop_loss) * 3)
                else:
                    take_profit = entry_price - (abs(entry_price - stop_loss) * 3)
            
            # Extract confluence factors from bias signal
            confluence_factors = []
            
            # NY Open Bias
            if bias_signal.get('ny_open_bias'):
                ny_bias = bias_signal['ny_open_bias']
                confluence_factors.append(f"NY Open {ny_bias.directional_bias.value}")
                confluence_factors.append(f"Bias Strength {ny_bias.bias_strength:.1f}")
            
            # Change of Character
            if bias_signal.get('change_of_character'):
                choch_signals = bias_signal['change_of_character']
                for choch in choch_signals:
                    confluence_factors.append(f"ChoCH {choch.choch_type.value}")
            
            # Retest Opportunities  
            if bias_signal.get('retest_opportunities'):
                retests = bias_signal['retest_opportunities']
                for retest in retests:
                    confluence_factors.append(f"{retest.retest_type} ({retest.retest_quality})")
            
            # Smart Money Areas
            if bias_signal.get('smart_money_areas'):
                areas = bias_signal['smart_money_areas']
                for area in areas:
                    confluence_factors.append(f"Smart Money {area.area_type.value}")
            
            # Fibonacci Elliott Wave
            fib_elliott = bias_signal.get('fibonacci_elliott_confluence', {})
            if fib_elliott.get('combined_confluence', 0) > 0.3:
                confluence_factors.append(f"Fib+Elliott {fib_elliott['combined_confluence']:.1f}")
            
            # Risk calculation (1% of account)
            risk_amount = 1.0  # Fixed $1.00 risk per trade
            stop_distance = abs(entry_price - stop_loss)
            position_size = risk_amount / stop_distance if stop_distance > 0 else 0
            
            signal = {
                'id': f"{crypto}_BIAS_{int(time.time())}",
                'symbol': f"{crypto}USDT",
                'crypto': crypto,
                'action': action,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': 'M15',
                'confidence': min(bias_signal['overall_confluence_score'], 0.95),
                'ict_confidence': bias_signal['overall_confluence_score'],
                'ml_boost': 0.0,  # Bias engine doesn't use ML
                'risk_amount': risk_amount,
                'position_size': position_size,
                'stop_distance': stop_distance,
                'risk_reward_ratio': abs(take_profit - entry_price) / abs(entry_price - stop_loss) if stop_distance > 0 else 3.0,
                'confluences': confluence_factors,
                'confluence_score': bias_signal['overall_confluence_score'],
                'signal_strength': 'High' if bias_signal['overall_confluence_score'] >= 0.8 else 'Medium-High',
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'pnl': 0.0,
                
                # Enhanced ICT data
                'directional_bias': bias_signal['directional_bias'],
                'bias_methodology': 'DIRECTIONAL_ANALYSIS',
                'ny_open_analysis': bool(bias_signal.get('ny_open_bias')),
                'choch_confirmed': bool(bias_signal.get('change_of_character')),
                'retest_quality': retests[0].retest_quality if bias_signal.get('retest_opportunities') else 'N/A',
                'fibonacci_confluence': fib_elliott.get('fibonacci_score', 0),
                'elliott_wave_confluence': fib_elliott.get('elliott_wave_score', 0)
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error converting bias signal: {e}")
            return None
    
    def _convert_crypto_signal_to_trading_signal(self, signal: Dict, price_data: Dict) -> Optional[Dict]:
        """Convert crypto-specific ICT signal to trading signal format"""
        try:
            entry_price = signal['entry_price']
            action = signal['direction']
            crypto = signal['crypto']
            
            # Calculate stop loss and take profit based on crypto characteristics
            crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
            volatility_factor = crypto_config['volatility_factor']
            
            # Dynamic stop loss based on crypto volatility
            stop_loss_percent = 0.015 * volatility_factor  # 1.5% base * volatility factor
            if action == 'BUY':
                stop_loss = entry_price * (1 - stop_loss_percent)
            else:
                stop_loss = entry_price * (1 + stop_loss_percent)
            
            # Dynamic take profit based on confluence score and crypto characteristics
            base_rr = 3.0  # Base 1:3 risk-reward
            confluence_multiplier = 1 + signal['confluence_score']  # Higher confluence = higher targets
            crypto_rr_adjustment = 1.0 / crypto_config['volatility_factor']  # Lower volatility = higher targets
            
            final_rr = base_rr * confluence_multiplier * crypto_rr_adjustment
            final_rr = max(2.0, min(5.0, final_rr))  # Clamp between 1:2 and 1:5
            
            stop_distance = abs(entry_price - stop_loss)
            if action == 'BUY':
                take_profit = entry_price + (stop_distance * final_rr)
            else:
                take_profit = entry_price - (stop_distance * final_rr)
            
            # Risk calculation (1% of account)
            risk_amount = 1.0  # Fixed $1.00 risk per trade
            position_size = risk_amount / stop_distance if stop_distance > 0 else 0
            
            # Build final trading signal
            trading_signal = {
                'id': f"{crypto}_ICT_{int(time.time())}",
                'symbol': f"{crypto}USDT",
                'crypto': crypto,
                'action': action,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': signal['timeframe'],
                'confidence': min(signal['confluence_score'], 0.95),
                'ict_confidence': signal['confluence_score'],
                'ml_boost': 0.0,
                'risk_amount': risk_amount,
                'position_size': position_size,
                'stop_distance': stop_distance,
                'risk_reward_ratio': final_rr,
                'confluences': [signal['confluence_factors']],
                'confluence_score': signal['confluence_score'],
                'signal_strength': signal['signal_strength'],
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'pnl': 0.0,
                
                # Enhanced ICT methodology data
                'directional_bias': action,
                'bias_methodology': 'COMPREHENSIVE_ICT',
                'session_preference': signal['session_preference'],
                'crypto_specific': True,
                'volatility_factor': crypto_config['volatility_factor'],
                'liquidity_rank': crypto_config['liquidity_rank'],
                'structure_sensitivity': crypto_config['structure_sensitivity'],
                
                # Analysis details from comprehensive methodology
                'htf_structure': signal['analysis_details']['structure_analysis']['primary_trend'],
                'order_blocks_count': signal['analysis_details']['order_blocks'],
                'fibonacci_levels': signal['analysis_details']['fibonacci_levels'],
                'bos_confirmed': signal['analysis_details']['bos_confirmed'],
                'choch_confirmed': signal['analysis_details']['choch_confirmed'],
                'liquidity_pools_count': signal['analysis_details']['liquidity_pools'],
                
                # Session and timing validation
                'ny_open_analysis': signal['session_preference'] in ['NY', 'New York'],
                'session_validated': True,
                'startup_cooldown_passed': True
            }
            
            return trading_signal
            
        except Exception as e:
            logger.error(f"❌ Error converting crypto-specific signal: {e}")
            return None
    
    def _generate_traditional_ict_signal(self, crypto: str, price_data: Dict) -> Optional[Dict]:
        """Generate traditional ICT signal as fallback"""
        try:
            # Market-driven signal generation - adapts to current conditions
            market_volatility = self._calculate_single_crypto_volatility(price_data)
            session_activity = self._get_session_multiplier()
            
            # Base probability adjusted by market conditions
            base_prob = 0.035  # 3.5% base chance per scan
            volatility_multiplier = max(0.5, min(3.0, market_volatility))
            adjusted_prob = base_prob * volatility_multiplier * session_activity
            
            # Check if we should generate a signal
            if np.random.random() >= adjusted_prob:
                return None
            
            # ICT Confluence Analysis
            confluence_score = 0.05
            confluence_factors = []
            
            change_24h = abs(price_data.get('change_24h', 0))
            high_24h = price_data.get('high_24h', price_data['price'])
            low_24h = price_data.get('low_24h', price_data['price'])
            current_price = price_data['price']
            
            # Fair Value Gap Analysis
            if change_24h > 1.5:
                confluence_score += 0.25
                confluence_factors.append("FVG High Volatility")
            elif change_24h > 0.5:
                if np.random.random() < 0.40:
                    confluence_score += 0.20
                    confluence_factors.append("FVG")
            
            # Order Block Analysis
            range_24h = high_24h - low_24h
            range_percent = (range_24h / current_price) * 100
            if range_percent > 3:
                confluence_score += 0.30
                confluence_factors.append("Order Block Wide Range")
            elif range_percent > 1.5:
                if np.random.random() < 0.60:
                    confluence_score += 0.20
                    confluence_factors.append("Order Block")
            
            # Market Structure Shift
            if change_24h > 2.5:
                confluence_score += 0.20
                confluence_factors.append("Structure Shift Strong")
            elif change_24h > 1.0:
                if np.random.random() < 0.50:
                    confluence_score += 0.15
                    confluence_factors.append("Structure Shift")
            
            # Premium/Discount Analysis
            price_position = (current_price - low_24h) / range_24h if range_24h > 0 else 0.5
            
            if price_position < 0.25:
                confluence_score += 0.15
                confluence_factors.append("Deep Discount")
                preferred_action = "BUY"
            elif price_position < 0.35:
                confluence_score += 0.10
                confluence_factors.append("Discount Zone")
                preferred_action = "BUY"
            elif price_position > 0.75:
                confluence_score += 0.15
                confluence_factors.append("Deep Premium")
                preferred_action = "SELL"
            elif price_position > 0.65:
                confluence_score += 0.10
                confluence_factors.append("Premium Zone")
                preferred_action = "SELL"
            else:
                preferred_action = "BUY" if change_24h > 0 else "SELL"
            
            # Check confluence threshold
            if confluence_score < 0.65:
                return None
            
            # Generate signal
            entry_price = current_price
            action = preferred_action
            
            # Calculate stop loss and take profit
            if action == "BUY":
                stop_loss = entry_price * 0.985  # 1.5% stop
                take_profit = entry_price * 1.045  # 4.5% target (3:1 ratio)
            else:
                stop_loss = entry_price * 1.015  # 1.5% stop
                take_profit = entry_price * 0.955  # 4.5% target (3:1 ratio)
            
            risk_amount = 1.0
            stop_distance = abs(entry_price - stop_loss)
            position_size = risk_amount / stop_distance if stop_distance > 0 else 0
            
            signal = {
                'id': f"{crypto}_ICT_{int(time.time())}",
                'symbol': f"{crypto}USDT",
                'crypto': crypto,
                'action': action,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': 'M15',
                'confidence': min(0.35 + (confluence_score * 0.55), 0.90),
                'ict_confidence': confluence_score,
                'ml_boost': 0.0,
                'risk_amount': risk_amount,
                'position_size': position_size,
                'stop_distance': stop_distance,
                'risk_reward_ratio': 3.0,
                'confluences': confluence_factors,
                'confluence_score': confluence_score,
                'signal_strength': 'High' if confluence_score >= 0.8 else 'Medium-High',
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'pnl': 0.0,
                'bias_methodology': 'TRADITIONAL_ANALYSIS'
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error generating traditional ICT signal for {crypto}: {e}")
            return None
    
    def _calculate_single_crypto_volatility(self, price_data: Dict) -> float:
        """Calculate volatility for a single crypto"""
        change_24h = abs(price_data.get('change_24h', 0))
        high_24h = price_data.get('high_24h', price_data['price'])
        low_24h = price_data.get('low_24h', price_data['price'])
        
        if high_24h > 0 and low_24h > 0:
            daily_range = ((high_24h - low_24h) / low_24h) * 100
            volatility_multiplier = max(0.5, min(3.0, daily_range / 2.0))
            return volatility_multiplier
        return 1.0
    
    def _calculate_market_volatility(self, crypto_data: Dict) -> float:
        """Calculate current market volatility multiplier based on price movements"""
        total_volatility = 0
        count = 0
        
        for crypto, data in crypto_data.items():
            change_24h = abs(data.get('change_24h', 0))
            high_24h = data.get('high_24h', data['price'])
            low_24h = data.get('low_24h', data['price'])
            
            # Calculate intraday range
            if high_24h > 0 and low_24h > 0:
                daily_range = ((high_24h - low_24h) / low_24h) * 100
                total_volatility += daily_range
                count += 1
        
        if count == 0:
            return 1.0
            
        avg_volatility = total_volatility / count
        
        # Convert to multiplier (2% daily range = 1x, 6% = 3x, etc.)
        volatility_multiplier = max(0.5, min(3.0, avg_volatility / 2.0))
        return volatility_multiplier
    
    def _get_session_multiplier(self) -> float:
        """Get session-based opportunity multiplier"""
        current_hour = datetime.now().hour
        
        # London session (8-16 GMT) - 1.2x
        if 8 <= current_hour < 16:
            return 1.2
        # NY session (13-21 GMT) - 1.3x  
        elif 13 <= current_hour < 21:
            return 1.3
        # London/NY overlap (13-16 GMT) - 1.8x (highest liquidity)
        if 13 <= current_hour < 16:
            return 1.8
        # Asia session (23-8 GMT) - 0.8x (lower liquidity)
        elif current_hour >= 23 or current_hour < 8:
            return 0.8
        # Off-hours - 0.6x
        else:
            return 0.6
    
    # ========== STARTUP COOLDOWN AND SESSION VALIDATION ==========
    
    def should_generate_signals(self) -> bool:
        """Check if enough time has passed since startup to generate signals"""
        minutes_since_startup = (datetime.now() - self.startup_time).total_seconds() / 60
        if minutes_since_startup < self.startup_cooldown_minutes:
            return False
        return True
    
    def validate_session_timing(self, session_type: str = 'ny_open') -> bool:
        """Validate if current time is within valid session window"""
        current_time = datetime.now()
        session_config = self.session_validation.get(session_type, {})
        
        if not session_config:
            return False
            
        start_time = current_time.replace(
            hour=session_config['start_hour'], 
            minute=session_config['start_minute'], 
            second=0, 
            microsecond=0
        )
        end_time = current_time.replace(
            hour=session_config['end_hour'], 
            minute=session_config['end_minute'], 
            second=0, 
            microsecond=0
        )
        
        return start_time <= current_time <= end_time
    
    def update_bias_persistence(self, crypto: str, bias_type: str, strength: float):
        """Update and track bias persistence with decay over time"""
        current_time = datetime.now()
        
        # Store or update bias
        self.active_biases[crypto] = {
            'bias_type': bias_type,
            'initial_strength': strength,
            'current_strength': strength,
            'created_time': current_time,
            'last_update': current_time
        }
        
        logger.info(f"📊 {crypto} bias updated: {bias_type} (strength: {strength:.2f})")
    
    def get_decayed_bias_strength(self, crypto: str) -> float:
        """Get current bias strength with time-based decay"""
        if crypto not in self.active_biases:
            return 0.0
            
        bias_info = self.active_biases[crypto]
        current_time = datetime.now()
        hours_elapsed = (current_time - bias_info['created_time']).total_seconds() / 3600
        
        # Apply decay based on session type (default to NY Open)
        decay_rate = self.session_validation['ny_open']['strength_decay_rate']
        max_duration = self.session_validation['ny_open']['bias_duration_hours']
        
        if hours_elapsed >= max_duration:
            # Bias expired
            del self.active_biases[crypto]
            return 0.0
        
        # Calculate decayed strength
        decayed_strength = bias_info['initial_strength'] * (1 - decay_rate * hours_elapsed)
        bias_info['current_strength'] = max(0.0, decayed_strength)
        
        return bias_info['current_strength']
    
    # ========== COMPREHENSIVE ICT METHODOLOGY ==========
    
    def analyze_market_structure_4h_1h(self, crypto: str, price_data: Dict) -> Dict:
        """Step 1: Analyze 4H and 1H market structure for trend determination"""
        crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
        
        # Simulate higher timeframe analysis using available data
        change_24h = price_data.get('change_24h', 0)
        current_price = price_data['price']
        high_24h = price_data.get('high_24h', current_price)
        low_24h = price_data.get('low_24h', current_price)
        
        # Market structure analysis
        structure_analysis = {
            'primary_trend': 'NEUTRAL',
            'structure_quality': 0.5,
            'confirmation_level': 0.5,
            'key_levels': []
        }
        
        # Calculate position in daily range (market structure proxy)
        if high_24h != low_24h:
            position_in_range = (current_price - low_24h) / (high_24h - low_24h)
        else:
            position_in_range = 0.5
        
        # Determine trend based on crypto-specific sensitivity
        sensitivity = crypto_config['structure_sensitivity']
        
        if change_24h > 3.0 * crypto_config['volatility_factor'] and position_in_range > 0.7:
            structure_analysis['primary_trend'] = 'BULLISH'
            structure_analysis['structure_quality'] = 0.8 * sensitivity
        elif change_24h < -3.0 * crypto_config['volatility_factor'] and position_in_range < 0.3:
            structure_analysis['primary_trend'] = 'BEARISH'  
            structure_analysis['structure_quality'] = 0.8 * sensitivity
        elif abs(change_24h) < 1.0:
            structure_analysis['primary_trend'] = 'NEUTRAL'
            structure_analysis['structure_quality'] = 0.3
        
        # Add key levels for structure
        structure_analysis['key_levels'] = [
            {'level': high_24h, 'type': 'resistance', 'strength': 0.8},
            {'level': low_24h, 'type': 'support', 'strength': 0.8},
            {'level': (high_24h + low_24h) / 2, 'type': 'midpoint', 'strength': 0.6}
        ]
        
        return structure_analysis
    
    def identify_enhanced_order_blocks(self, crypto: str, structure_analysis: Dict) -> List[Dict]:
        """Step 2: Mark enhanced order blocks aligned with higher timeframes using actual price data"""
        crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
        ict_config = self.ict_methodology['enhanced_order_blocks']
        
        order_blocks = []
        
        # Use actual market structure data for realistic order blocks
        primary_trend = structure_analysis['primary_trend']
        key_levels = structure_analysis['key_levels']
        
        for level_info in key_levels:
            level = level_info['level']
            level_type = level_info['type']
            strength = level_info['strength']
            
            # Create order blocks based on trend alignment with ACTUAL price levels
            if primary_trend == 'BULLISH' and level_type in ['support', 'midpoint']:
                order_block = {
                    'type': 'bullish_ob',
                    'price_level': level,
                    'strength': strength * crypto_config['structure_sensitivity'],
                    'timeframe_aligned': True,
                    'structure_trend': primary_trend,
                    'mitigation_level': level * (1 - ict_config['mitigation_percentage']),
                    'confidence': strength * 0.9,
                    'volatility_factor': crypto_config['volatility_factor'],
                    'crypto_specific': crypto
                }
                order_blocks.append(order_block)
                
            elif primary_trend == 'BEARISH' and level_type in ['resistance', 'midpoint']:
                order_block = {
                    'type': 'bearish_ob',
                    'price_level': level,
                    'strength': strength * crypto_config['structure_sensitivity'],
                    'timeframe_aligned': True,
                    'structure_trend': primary_trend,
                    'mitigation_level': level * (1 + ict_config['mitigation_percentage']),
                    'confidence': strength * 0.9,
                    'volatility_factor': crypto_config['volatility_factor'],
                    'crypto_specific': crypto
                }
                order_blocks.append(order_block)
        
        return order_blocks[:3]  # Limit to top 3 order blocks
    
    def apply_fibonacci_confluence(self, crypto: str, order_blocks: List[Dict], current_price: float) -> List[Dict]:
        """Step 3: Add fibonacci confluence to selected zones"""
        crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
        fib_config = self.ict_methodology['fibonacci_confluence']
        
        enhanced_blocks = []
        
        for block in order_blocks:
            block_price = block['price_level']
            fib_confluence = 0.0
            fib_levels_hit = []
            
            # Check fibonacci confluence for each crypto's preferred levels
            for fib_level in crypto_config['fibonacci_levels']:
                # Calculate distance from current price to block as percentage
                price_distance = abs(current_price - block_price) / current_price
                
                # Check if price distance aligns with fibonacci level
                fib_tolerance = fib_config['tolerance']
                if abs(price_distance - fib_level) <= fib_tolerance:
                    fib_confluence += fib_config['confluence_weight']
                    fib_levels_hit.append(fib_level)
            
            # Enhance order block with fibonacci data
            enhanced_block = block.copy()
            enhanced_block['fibonacci_confluence'] = fib_confluence
            enhanced_block['fib_levels'] = fib_levels_hit
            enhanced_block['total_confluence'] = block['confidence'] + fib_confluence
            
            enhanced_blocks.append(enhanced_block)
        
        # Sort by total confluence strength
        enhanced_blocks.sort(key=lambda x: x['total_confluence'], reverse=True)
        return enhanced_blocks
    
    def check_fair_value_gaps(self, crypto: str, enhanced_blocks: List[Dict], current_price: float) -> List[Dict]:
        """Step 4: Check for fair value gaps with actual price gap calculations"""
        fvg_config = self.ict_methodology['fair_value_gaps']
        
        validated_blocks = []
        
        for block in enhanced_blocks:
            block_price = block['price_level']
            
            # Calculate actual price gap percentage
            price_gap_percentage = abs(current_price - block_price) / current_price
            
            # Check if current price action would create FVG that mitigates block
            fvg_conflict = False
            
            if price_gap_percentage > fvg_config['min_gap_percentage']:
                # There's a potential FVG - add actual gap data
                mitigation_level = block.get('mitigation_level', block_price)
                
                # Check if price has mitigated beyond threshold
                if block['type'] == 'bullish_ob' and current_price < mitigation_level:
                    fvg_conflict = True
                elif block['type'] == 'bearish_ob' and current_price > mitigation_level:
                    fvg_conflict = True
            
            if not fvg_conflict:
                # Add FVG confluence weight with actual gap data
                block['fvg_confluence'] = fvg_config['confluence_weight']
                block['gap_percentage'] = price_gap_percentage  # Actual gap size
                block['current_price'] = current_price  # Reference price
                block['total_confluence'] += fvg_config['confluence_weight']
                validated_blocks.append(block)
        
        return validated_blocks
    
    def wait_for_structure_break_and_choch(self, crypto: str, validated_blocks: List[Dict], price_data: Dict) -> List[Dict]:
        """Step 5: Wait for break of structure and change of character with strength indicators"""
        structure_config = self.ict_methodology['market_structure']
        
        confirmed_blocks = []
        
        for block in validated_blocks:
            # Use actual price movement data for BOS and ChoCH confirmation
            change_24h = price_data.get('change_24h', 0)
            crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
            
            # Check for structure break based on actual volatility and price change
            bos_confirmed = False
            choch_confirmed = False
            choch_strength = 'Weak'
            
            volatility_threshold = 2.0 * crypto_config['volatility_factor']
            
            if block['type'] == 'bullish_ob' and change_24h > volatility_threshold:
                bos_confirmed = True
                strength_ratio = change_24h / volatility_threshold
                
                if change_24h > volatility_threshold * 1.5:  # Strong move
                    choch_confirmed = True
                    if strength_ratio > 2.0:
                        choch_strength = 'Very Strong'
                    elif strength_ratio > 1.5:
                        choch_strength = 'Strong'
                    else:
                        choch_strength = 'Medium'
                        
            elif block['type'] == 'bearish_ob' and change_24h < -volatility_threshold:
                bos_confirmed = True
                strength_ratio = abs(change_24h) / volatility_threshold
                
                if change_24h < -volatility_threshold * 1.5:  # Strong move
                    choch_confirmed = True
                    if strength_ratio > 2.0:
                        choch_strength = 'Very Strong'
                    elif strength_ratio > 1.5:
                        choch_strength = 'Strong'
                    else:
                        choch_strength = 'Medium'
            
            if bos_confirmed:
                block['bos_confirmed'] = True
                block['actual_change_24h'] = change_24h  # Actual price movement
                block['total_confluence'] += structure_config['bos_confluence_weight']
                
                if choch_confirmed:
                    block['choch_confirmed'] = True
                    block['choch_strength'] = choch_strength  # Strength indicator
                    block['total_confluence'] += structure_config['choch_confluence_weight']
                
                confirmed_blocks.append(block)
        
        return confirmed_blocks
    
    def identify_liquidity_pools(self, crypto: str, confirmed_blocks: List[Dict], price_data: Dict) -> List[Dict]:
        """Step 6: Look for liquidity pools with equal highs and equal lows"""
        liquidity_config = self.ict_methodology['liquidity_pools']
        
        final_blocks = []
        
        for block in confirmed_blocks:
            # Simulate liquidity pool identification
            current_price = price_data['price']
            high_24h = price_data.get('high_24h', current_price)
            low_24h = price_data.get('low_24h', current_price)
            
            liquidity_pools = []
            
            # Check for equal highs (resistance liquidity)
            if abs(current_price - high_24h) / current_price <= liquidity_config['equal_level_tolerance']:
                liquidity_pools.append({
                    'type': 'equal_highs',
                    'level': high_24h,
                    'tests': 2,  # Simulated
                    'strength': 0.8
                })
            
            # Check for equal lows (support liquidity)
            if abs(current_price - low_24h) / current_price <= liquidity_config['equal_level_tolerance']:
                liquidity_pools.append({
                    'type': 'equal_lows',
                    'level': low_24h,
                    'tests': 2,  # Simulated
                    'strength': 0.8
                })
            
            # Add liquidity confluence if pools found
            if liquidity_pools:
                block['liquidity_pools'] = liquidity_pools
                block['total_confluence'] += liquidity_config['proximity_weight'] * len(liquidity_pools)
            
            # Only include blocks that meet minimum confluence for this crypto
            crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
            if block['total_confluence'] >= crypto_config['min_confluence_score']:
                final_blocks.append(block)
        
        return final_blocks
    
    def generate_crypto_specific_signal(self, crypto: str, price_data: Dict) -> Optional[Dict]:
        """Generate signal using comprehensive ICT methodology with crypto-specific analysis"""
        
        # Step 1: Check startup cooldown
        if not self.should_generate_signals():
            return None
        
        # Step 2: Run comprehensive ICT analysis (session timing checked elsewhere)
        try:
            # Step 1: Analyze 4H/1H market structure
            structure_analysis = self.analyze_market_structure_4h_1h(crypto, price_data)
            
            # Step 2: Identify enhanced order blocks
            order_blocks = self.identify_enhanced_order_blocks(crypto, structure_analysis)
            
            if not order_blocks:
                return None
            
            # Step 3: Apply fibonacci confluence
            enhanced_blocks = self.apply_fibonacci_confluence(crypto, order_blocks, price_data['price'])
            
            # Step 4: Check fair value gaps
            validated_blocks = self.check_fair_value_gaps(crypto, enhanced_blocks, price_data['price'])
            
            # Step 5: Wait for BOS and ChoCH
            confirmed_blocks = self.wait_for_structure_break_and_choch(crypto, validated_blocks, price_data)
            
            # Step 6: Identify liquidity pools
            final_blocks = self.identify_liquidity_pools(crypto, confirmed_blocks, price_data)
            
            if not final_blocks:
                return None
            
            # Select best signal from final blocks
            best_block = max(final_blocks, key=lambda x: x['total_confluence'])
            
            # Generate signal based on best block
            crypto_config = self.crypto_characteristics.get(crypto, self.crypto_characteristics['BTC'])
            
            signal = {
                'crypto': crypto,
                'direction': 'BUY' if best_block['type'] == 'bullish_ob' else 'SELL',
                'entry_price': price_data['price'],
                'confluence_score': best_block['total_confluence'],
                'confluence_factors': self._build_confluence_description(best_block),
                'timeframe': crypto_config['timeframe_priority'][0],  # Primary timeframe
                'signal_strength': 'High' if best_block['total_confluence'] > 0.8 else 'Medium',
                'session_preference': crypto_config['session_preference'][0],
                'analysis_details': {
                    'structure_analysis': structure_analysis,
                    'order_blocks': len(final_blocks),
                    'fibonacci_levels': best_block.get('fib_levels', []),
                    'bos_confirmed': best_block.get('bos_confirmed', False),
                    'choch_confirmed': best_block.get('choch_confirmed', False),
                    'liquidity_pools': len(best_block.get('liquidity_pools', []))
                }
            }
            
            # Update bias persistence
            self.update_bias_persistence(crypto, signal['direction'], best_block['total_confluence'])
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Failed to generate signal for {crypto}: {e}")
            return None
    
    def _build_confluence_description(self, block: Dict) -> str:
        """Build chart-specific confluence description with actual price levels"""
        factors = []
        
        # Include actual price level information to make each signal unique
        price_level = block.get('price_level', 0)
        if price_level > 0:
            factors.append(f"Order Block @ ${price_level:.2f}")
        
        if block.get('timeframe_aligned'):
            structure_trend = block.get('structure_trend', 'NEUTRAL')
            factors.append(f"HTF {structure_trend} Structure")
        
        if block.get('fib_levels'):
            # Show specific fibonacci levels hit
            fib_levels_str = ', '.join([f'{f:.1%}' for f in block['fib_levels']])
            factors.append(f"Fibonacci Confluence {fib_levels_str}")
        
        if block.get('fvg_confluence', 0) > 0:
            gap_size = block.get('gap_percentage', 0)
            if gap_size > 0:
                factors.append(f"FVG {gap_size:.1%}")
            else:
                factors.append("Fair Value Gap")
        
        if block.get('bos_confirmed'):
            volatility = block.get('volatility_factor', 1.0)
            factors.append(f"BOS Confirmed (Vol: {volatility:.1f}x)")
        
        if block.get('choch_confirmed'):
            strength = block.get('choch_strength', 'Medium')
            factors.append(f"ChoCH {strength}")
        
        if block.get('liquidity_pools'):
            pool_types = [pool['type'] for pool in block['liquidity_pools']]
            pool_levels = [f"${pool.get('level', 0):.0f}" for pool in block['liquidity_pools']]
            factors.append(f"Liquidity: {', '.join(pool_types)} @ {', '.join(pool_levels)}")
        
        # Add confluence score for uniqueness
        total_confluence = block.get('total_confluence', 0)
        factors.append(f"Score: {total_confluence:.2f}")
        
        return ", ".join(factors) if factors else "Basic ICT Analysis"
    
    def validate_chart_based_timing(self, signals: List[Dict]) -> List[Dict]:
        """Ensure signals reflect genuine chart-specific analysis - don't artificially limit timing"""
        if len(signals) <= 1:
            return signals
        
        logger.info(f"🔍 Validating {len(signals)} signals for genuine chart-specific analysis")
        
        # The real issue: Ensure each signal reflects DIFFERENT chart conditions
        validated_signals = []
        
        for signal in signals:
            crypto = signal['crypto']
            
            # Add chart-specific timestamp (but don't artificially delay)
            signal['timestamp'] = datetime.now().isoformat()
            signal['chart_specific_analysis'] = True
            
            # The key: Ensure confluence factors are genuinely different per chart
            confluence_factors = signal.get('confluence_factors', '')
            
            # If multiple signals have identical confluence, that's the real problem
            identical_confluence = sum(1 for s in validated_signals 
                                     if s.get('confluence_factors') == confluence_factors)
            
            if identical_confluence == 0:
                # First signal with this confluence pattern - accept it
                validated_signals.append(signal)
                logger.info(f"✅ {crypto} signal accepted - unique chart analysis: {confluence_factors}")
            else:
                # Multiple signals with identical confluence = strategy not chart-specific enough
                logger.warning(f"⚠️ {crypto} signal has identical confluence to previous signal")
                logger.warning(f"   This suggests analysis is too generic, not chart-specific")
                logger.warning(f"   Confluence: {confluence_factors}")
                
                # Still include the signal but flag it for improvement
                signal['requires_chart_specificity_improvement'] = True
                validated_signals.append(signal)
                logger.info(f"⚡ {crypto} signal included but flagged for analysis improvement")
        
        # Log the real issue if we find it
        if len(validated_signals) > 1:
            confluences = [s.get('confluence_factors', 'N/A') for s in validated_signals]
            unique_confluences = set(confluences)
            
            if len(unique_confluences) < len(confluences):
                logger.warning("🚨 ANALYSIS IMPROVEMENT NEEDED:")
                logger.warning("   Multiple signals with identical confluence detected")
                logger.warning("   This indicates the strategy needs more chart-specific analysis")
                logger.warning(f"   Confluence patterns: {confluences}")
            else:
                logger.info("✅ All signals have unique chart-specific analysis - this is realistic!")
        
        logger.info(f"📊 Chart validation complete: {len(validated_signals)} signals with chart-specific analysis")
        return validated_signals
    
    def _analyze_higher_timeframe_trend(self, crypto: str, price_data: Dict) -> str:
        """Analyze higher timeframe trend for directional bias (4H/1D equivalent)"""
        try:
            # Use 24h change as proxy for higher timeframe trend
            change_24h = price_data.get('change_24h', 0)
            
            # Additional trend analysis using price levels
            current_price = price_data['price']
            high_24h = price_data.get('high_24h', current_price)
            low_24h = price_data.get('low_24h', current_price)
            
            # Calculate position in daily range (like market structure)
            if high_24h != low_24h:
                position_in_range = (current_price - low_24h) / (high_24h - low_24h)
            else:
                position_in_range = 0.5
            
            # Trend determination logic
            if change_24h > 2.0 and position_in_range > 0.6:
                return 'BULLISH'  # Strong uptrend, price in upper range
            elif change_24h < -2.0 and position_in_range < 0.4:
                return 'BEARISH'  # Strong downtrend, price in lower range
            elif abs(change_24h) < 1.0:
                return 'NEUTRAL'  # Sideways/consolidation
            elif change_24h > 0.5:
                return 'BULLISH'  # Moderate uptrend
            elif change_24h < -0.5:
                return 'BEARISH'  # Moderate downtrend
            else:
                return 'NEUTRAL'  # Unclear trend
                
        except Exception as e:
            logger.warning(f"⚠️ Trend analysis failed for {crypto}: {e}")
            return 'NEUTRAL'  # Safe fallback

    def get_confluences(self) -> List[str]:
        """Get ICT confluences for the signal"""
        all_confluences = [
            'Order Block', 'Fair Value Gap', 'Market Structure Shift',
            'Liquidity Sweep', 'Premium/Discount', 'Fibonacci Level',
            'Time & Price', 'Volume Imbalance', 'Smart Money Concept'
        ]
        # Return 2-4 random confluences
        num_confluences = np.random.randint(2, 5)
        return np.random.choice(all_confluences, num_confluences, replace=False).tolist()

class SessionStatusTracker:
    """Track Global Trading Sessions Status"""
    
    def __init__(self, trading_sessions):
        self.trading_sessions = trading_sessions
        
    def get_sessions_status(self) -> Dict:
        """Get current status of all trading sessions"""
        current_hour = datetime.utcnow().hour
        sessions_status = {}
        
        for session_key, session_info in self.trading_sessions.items():
            # Handle session times that cross midnight
            if session_info['start'] > session_info['end']:  # Asia session
                is_open = current_hour >= session_info['start'] or current_hour <= session_info['end']
            else:
                is_open = session_info['start'] <= current_hour <= session_info['end']
                
            sessions_status[session_key] = {
                'name': session_info['name'],
                'timezone': session_info['timezone'],
                'hours': f"{session_info['start']:02d}:00-{session_info['end']:02d}:00 GMT",
                'status': 'OPEN' if is_open else 'CLOSED',
                'is_open': is_open
            }
            
        return sessions_status

class MonitorStatistics:
    """Monitor Statistics Tracker"""
    
    def __init__(self):
        self.start_time = datetime.now()
        
    def calculate_scan_signal_ratio(self, scan_count: int, total_signals: int) -> str:
        """Calculate scans per signal ratio"""
        if total_signals == 0:
            return "No signals yet"
        ratio = scan_count / total_signals if total_signals > 0 else 0
        return f"{ratio:.1f}:1"
    
    def is_market_hours(self) -> bool:
        """Check if current time is within active trading hours (08:00-22:00 GMT)"""
        current_hour = datetime.utcnow().hour
        return 8 <= current_hour <= 22
    
    def get_uptime(self) -> str:
        """Get monitor uptime"""
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        return f"{hours:02d}h {minutes:02d}m"

class ICTWebMonitor:
    """Main ICT Web Monitor matching previous monitor exactly"""
    
    def __init__(self, port=5001):
        self.port = port
        self.app = Flask(__name__)
        # SECURITY FIX: Use environment variable for Flask secret key
        secret_key = os.getenv('FLASK_SECRET_KEY')
        if not secret_key:
            raise ValueError("FLASK_SECRET_KEY environment variable is required for secure session management!")
        self.app.config['SECRET_KEY'] = secret_key
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.crypto_monitor = ICTCryptoMonitor()
        self.signal_generator = ICTSignalGenerator()
        self.session_tracker = SessionStatusTracker(self.crypto_monitor.trading_sessions)
        self.statistics = MonitorStatistics()
        
        # Data storage
        self.current_prices = {}
        self.is_running = False
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(self.get_dashboard_html())
            
        @self.app.route('/health')
        def health_check():
            # Derive signals_today from today's live + archived signals (not the journal)
            from datetime import date
            today = date.today()

            def _to_dt(ts):
                if isinstance(ts, str):
                    if not ts.strip():
                        return None
                    try:
                        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"⚠️ Invalid isoformat string in _to_dt: '{ts}' ({e})")
                        return None
                return ts

            today_signals = 0
            for s in (self.crypto_monitor.live_signals + self.crypto_monitor.archived_signals):
                ts = s.get('timestamp')
                if not ts:
                    continue
                try:
                    if _to_dt(ts).date() == today:
                        today_signals += 1
                except Exception:
                    continue

            return jsonify({
                'status': 'operational',
                'service': 'ICT Enhanced Trading Monitor',
                'port': self.port,
                'timestamp': datetime.now().isoformat(),
                'symbols': self.crypto_monitor.display_symbols,
                'scan_count': self.crypto_monitor.scan_count,
                'signals_today': today_signals,
                'market_hours': self.statistics.is_market_hours(),
                'paper_balance': self.crypto_monitor.paper_balance,
                'account_blown': self.crypto_monitor.account_blown,
                'ml_model_status': {
                    'loaded': self.signal_generator.ml_model is not None,
                    'status': 'loaded' if self.signal_generator.ml_model is not None else 'not_found'
                }
            })
            
        @self.app.route('/api/data')
        def get_current_data():
            try:
                # Serialize live signals for JSON
                serialized_signals = []
                for signal in self.crypto_monitor.live_signals[-5:]:
                    signal_copy = signal.copy()
                    if 'timestamp' in signal_copy and hasattr(signal_copy['timestamp'], 'isoformat'):
                        signal_copy['timestamp'] = signal_copy['timestamp'].isoformat()
                    serialized_signals.append(signal_copy)
                
                # Get trading journal from database for today's completed trades (database-first)
                from datetime import date
                today_str = date.today().isoformat()
                
                # Primary source: Database completed trades
                today_completed_trades = self.crypto_monitor.get_todays_completed_trades_from_db()
                
                # Secondary source: Journal entries not yet in database
                journal_supplement = []
                db_trade_ids = {trade['id'] for trade in today_completed_trades}
                
                for entry in self.crypto_monitor.trading_journal:
                    try:
                        # Check if this journal entry is from today and not in database
                        entry_exit_time = entry.get('exit_time', '')
                        entry_id = entry.get('id')
                        
                        if (entry_exit_time and entry_exit_time.startswith(today_str) and 
                            entry_id not in db_trade_ids):
                            journal_supplement.append(entry)
                    except:
                        continue
                
                # Combine database + journal (database-first approach)
                all_today_trades = today_completed_trades + journal_supplement
                
                # Take last 10 entries and serialize for JSON
                serialized_journal = self.serialize_datetime_objects(all_today_trades[-10:])

                # Derive signals_today from database instead of in-memory lists
                from datetime import date
                import sqlite3
                today = date.today().isoformat()
                
                # Get accurate count from database
                conn = sqlite3.connect('databases/trading_data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?", (today,))
                today_signals = cursor.fetchone()[0]
                conn.close()
                
                # Build today's summary from live signals only (exclude closed trades)
                todays_summary = []
                def _to_dt(ts):
                    if isinstance(ts, str):
                        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    return ts
                
                # Only show truly active signals, not closed ones
                for s in self.crypto_monitor.live_signals:
                    ts = s.get('timestamp')
                    if not ts:
                        continue
                    try:
                        if _to_dt(ts).date() == date.today():
                            # Skip if this signal has a corresponding closed trade in journal
                            paper_trade_id = s.get('paper_trade_id', '')
                            is_closed = any(
                                trade.get('exit_time', '').startswith(today) 
                                for trade in self.crypto_monitor.trading_journal
                                if str(trade.get('id', '')) in paper_trade_id
                            )
                            
                            if not is_closed:  # Only show if not closed
                                cp = s.copy()
                                if hasattr(cp.get('timestamp'), 'isoformat'):
                                    cp['timestamp'] = cp['timestamp'].isoformat()
                                todays_summary.append(cp)
                    except Exception:
                        continue
                todays_summary.sort(key=lambda s: _to_dt(s.get('timestamp', datetime.now())), reverse=True)
                todays_summary = todays_summary[:50]

                # Get current signal generation parameters
                signal_params = {}
                if self.current_prices:
                    market_volatility = self.signal_generator._calculate_market_volatility(self.current_prices)
                    session_multiplier = self.signal_generator._get_session_multiplier()
                    base_prob = 0.035  # 3.5% base chance (increased for ML learning)
                    volatility_multiplier = max(0.5, min(3.0, market_volatility))
                    effective_prob = base_prob * volatility_multiplier * session_multiplier
                    
                    signal_params = {
                        'base_probability': base_prob * 100,  # Convert to percentage
                        'volatility_multiplier': volatility_multiplier,
                        'session_multiplier': session_multiplier,
                        'effective_probability': effective_prob * 100,  # Convert to percentage
                        'confluence_threshold': 15.0  # 15% minimum confluence required (emergency fix)
                    }

                return jsonify({
                    'prices': self.current_prices,
                    'scan_count': self.crypto_monitor.scan_count,
                    'signals_today': today_signals,
                    'daily_pnl': self.crypto_monitor.daily_pnl,
                    'paper_balance': self.crypto_monitor.paper_balance,  # Current account balance
                    'account_blown': self.crypto_monitor.account_blown,  # Account blow-up status
                    'live_signals': serialized_signals,  # Serialized signals
                    'total_live_signals': len(self.crypto_monitor.live_signals),
                    'signals_summary': todays_summary,  # Full summary for today
                    'trading_journal': serialized_journal,  # Serialized journal
                    'paper_trades': self.crypto_monitor.get_todays_active_trades_from_db(),  # Database-first active trades
                    'session_status': self.session_tracker.get_sessions_status(),
                    'uptime': self.statistics.get_uptime(),
                    'market_hours': self.statistics.is_market_hours(),
                    'signal_generation_params': signal_params,  # Signal generation debugging info
                    'risk_management_status': {
                        'portfolio_risk': f"{self.crypto_monitor.calculate_portfolio_risk()*100:.2f}%",
                        'max_portfolio_risk': f"{self.crypto_monitor.max_portfolio_risk*100:.1f}%",
                        'concurrent_signals': f"{len(self.crypto_monitor.live_signals)}/{self.crypto_monitor.max_concurrent_signals}",
                        'active_positions': {symbol.replace('USDT', ''): self.crypto_monitor.get_active_positions_for_symbol(symbol) 
                                           for symbol in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']},
                        'signal_cooldowns': {symbol: self.crypto_monitor.has_recent_signal(symbol) 
                                           for symbol in ['BTC', 'ETH', 'SOL', 'XRP']},
                        'deduplication_enabled': True,
                        'cooldown_minutes': self.crypto_monitor.signal_cooldown_minutes
                    },
                    'ml_model_status': {
                        'loaded': self.signal_generator.ml_model is not None,
                        'status': 'loaded' if self.signal_generator.ml_model is not None else 'not_found'
                    }
                })
            except Exception as e:
                logger.error(f"❌ Error in API data endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
            
        @self.app.route('/api/signals')
        def get_signals():
            return jsonify(self.crypto_monitor.live_signals)
            
        @self.app.route('/api/signals/latest')
        def get_latest_signals():
            """Get the most recent signals"""
            try:
                # Get the 5 most recent signals
                recent_signals = self.crypto_monitor.live_signals[-5:] if self.crypto_monitor.live_signals else []
                return jsonify(recent_signals)
            except Exception as e:
                logger.error(f"❌ Error getting latest signals: {e}")
                return jsonify({'error': 'Failed to get latest signals'}), 500
            
        @self.app.route('/api/journal')
        def get_journal():
            return jsonify(self.crypto_monitor.trading_journal)
        
        @self.app.route('/api/reset_account', methods=['POST'])
        def reset_account():
            """Reset blown account back to $100 starting balance"""
            try:
                old_balance = self.crypto_monitor.paper_balance
                was_blown = self.crypto_monitor.account_blown
                
                # Reset account
                self.crypto_monitor.paper_balance = 100.0
                self.crypto_monitor.account_blown = False
                self.crypto_monitor.total_paper_pnl = 0.0
                
                # Clear active trades but keep completed ones for learning
                self.crypto_monitor.active_paper_trades.clear()
                
                logger.info(f"🔄 ACCOUNT RESET: ${old_balance:.2f} → $100.00 | Was Blown: {was_blown}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Account reset to $100.00',
                    'old_balance': old_balance,
                    'new_balance': 100.0,
                    'was_blown': was_blown
                })
            except Exception as e:
                logger.error(f"❌ Error resetting account: {e}")
                return jsonify({'error': 'Failed to reset account'}), 500
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {'message': 'Connected to ICT Trading Monitor'})
            
        @self.socketio.on('request_update')
        def handle_update_request():
            self.broadcast_update()
    
    def run_analysis_cycle(self):
        """Main analysis cycle matching previous monitor functionality"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_analysis_cycle())
    
    async def async_analysis_cycle(self):
        """Async analysis cycle"""
        while self.is_running:
            try:
                logger.info("🔍 Running ICT Trading Analysis...")
                scan_start_time = datetime.now()
                
                # Get real-time prices
                self.current_prices = await self.crypto_monitor.get_real_time_prices()
                
                # Save price data to database for historical tracking
                self.crypto_monitor.save_price_history(self.current_prices)
                
                # Update scan count
                self.crypto_monitor.scan_count += 1
                self.crypto_monitor.last_scan_time = datetime.now()
                
                # Generate trading signals (like previous monitor)
                new_signals = self.signal_generator.generate_trading_signals(self.current_prices)
                
                # Process new signals with deduplication and risk management
                approved_signals = 0
                rejected_signals = 0
                
                for signal in new_signals:
                    symbol = signal.get('symbol', '')
                    crypto = signal.get('crypto', '')
                    entry_price = signal.get('entry_price', 0)
                    
                    # Apply deduplication and risk management checks
                    can_accept, reason = self.crypto_monitor.can_accept_new_signal(symbol, entry_price)
                    
                    if not can_accept:
                        logger.info(f"❌ Signal rejected: {crypto} - {reason}")
                        rejected_signals += 1
                        continue
                    
                    # Signal approved - process it
                    logger.info(f"✅ Signal approved: {crypto} - {reason}")
                    
                    # Add timestamp for lifecycle management
                    signal['timestamp'] = datetime.now().isoformat()
                    signal['age_minutes'] = 0
                    signal['age_category'] = 'fresh'
                    
                    # Update signal cache to prevent duplicates
                    self.crypto_monitor.update_signal_cache(crypto)
                    
                    # Execute paper trade automatically
                    if self.crypto_monitor.paper_trading_enabled:
                        paper_trade = self.crypto_monitor.execute_paper_trade(signal)
                    
                    # Save signal to database for persistence
                    self.crypto_monitor.save_signal_to_database(signal)
                    
                    # Save trading journal entry for this signal
                    journal_entry = {
                        'type': 'TRADE',
                        'action': f"Signal Generated",
                        'details': f"{crypto} {signal['action']} signal at ${signal['entry_price']:.4f}",
                        'id': signal['id'],
                        'symbol': signal['symbol'],
                        'entry_price': signal['entry_price'],
                        'action': signal['action'],
                        'crypto': crypto,
                        'confidence': signal['confidence'],
                        'timestamp': datetime.now().isoformat()
                    }
                    self.crypto_monitor.save_trading_journal_entry(journal_entry)
                    
                    self.crypto_monitor.live_signals.append(signal)
                    self.crypto_monitor.signals_today += 1
                    self.crypto_monitor.total_signals += 1
                    approved_signals += 1
                    
                    logger.info(f"📈 NEW SIGNAL: {signal['crypto']} {signal['action']} @ ${signal['entry_price']:.4f} ({signal['confidence']*100:.1f}% confidence)")
                
                # Log signal processing summary
                if new_signals:
                    logger.info(f"📊 Signal Processing: {approved_signals} approved, {rejected_signals} rejected")
                
                # Update paper trades with current prices
                if self.crypto_monitor.paper_trading_enabled:
                    closed_trades = self.crypto_monitor.update_paper_trades(self.current_prices)
                    if closed_trades > 0:
                        logger.info(f"📄 Paper Trading: Closed {closed_trades} trades")
                    
                    # Check and close positions at end of day (NO OVERNIGHT HOLDS)
                    eod_closed = self.crypto_monitor.check_and_close_eod_positions(self.current_prices)
                    if eod_closed > 0:
                        logger.info(f"🌙 End of Day: Closed {eod_closed} positions (NO OVERNIGHT TRADING)")
                
                # Manage signal lifecycle (5-minute expiry, max 3 display)
                archived_count = self.crypto_monitor.manage_signal_lifecycle()
                if archived_count > 0:
                    logger.info(f"📋 Signal Management: Archived {archived_count} expired signals")
                
                # Keep only last 50 journal entries
                if len(self.crypto_monitor.trading_journal) > 50:
                    self.crypto_monitor.trading_journal = self.crypto_monitor.trading_journal[-50:]
                
                # Save system statistics periodically (every 10 scans)
                if self.crypto_monitor.scan_count % 10 == 0:
                    self.crypto_monitor.save_system_statistics()
                
                # Save session status
                session_status = self.session_tracker.get_sessions_status()
                self.crypto_monitor.save_session_status(session_status)
                
                # Save detailed scan history
                scan_end_time = datetime.now()
                scan_duration_ms = int((scan_end_time - scan_start_time).total_seconds() * 1000)
                scan_data = {
                    'scan_number': self.crypto_monitor.scan_count,
                    'signals_generated': len(new_signals),
                    'signals_approved': approved_signals,
                    'signals_rejected': rejected_signals,
                    'market_volatility': self.signal_generator._calculate_market_volatility(self.current_prices) if self.current_prices else 0.0,
                    'session_multiplier': self.signal_generator._get_session_multiplier(),
                    'effective_probability': 0.0,  # Will be calculated by signal generator
                    'scan_duration_ms': scan_duration_ms
                }
                self.crypto_monitor.save_scan_history(scan_data)
                
                # Broadcast update to connected clients
                self.broadcast_update()
                
                logger.info(f"✅ Analysis Complete - Scan #{self.crypto_monitor.scan_count} | Signals: {self.crypto_monitor.signals_today}")
                
                # Wait before next cycle (30 seconds like previous monitor)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Error in analysis cycle: {e}")
                await asyncio.sleep(5)
    
    def serialize_datetime_objects(self, obj):
        """Recursively serialize datetime objects to ISO format strings"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self.serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.serialize_datetime_objects(item) for item in obj]
        else:
            return obj

    def broadcast_update(self):
        """Broadcast real-time updates to all connected clients"""
        try:
            # Serialize completed paper trades for JSON
            serialized_completed_trades = []
            for trade in self.crypto_monitor.completed_paper_trades:
                trade_copy = trade.copy()
                if 'entry_time' in trade_copy and trade_copy['entry_time']:
                    if hasattr(trade_copy['entry_time'], 'isoformat'):
                        trade_copy['entry_time'] = trade_copy['entry_time'].isoformat()
                if 'exit_time' in trade_copy and trade_copy['exit_time']:
                    if hasattr(trade_copy['exit_time'], 'isoformat'):
                        trade_copy['exit_time'] = trade_copy['exit_time'].isoformat()
                serialized_completed_trades.append(trade_copy)

            # Serialize active paper trades
            serialized_active_trades = []
            for trade in self.crypto_monitor.active_paper_trades:
                trade_copy = trade.copy()
                if 'entry_time' in trade_copy and trade_copy['entry_time']:
                    if hasattr(trade_copy['entry_time'], 'isoformat'):
                        trade_copy['entry_time'] = trade_copy['entry_time'].isoformat()
                serialized_active_trades.append(trade_copy)

            # Serialize live signals 
            serialized_live_signals = []
            for signal in self.crypto_monitor.live_signals:
                signal_copy = signal.copy()
                if 'timestamp' in signal_copy and signal_copy['timestamp']:
                    if hasattr(signal_copy['timestamp'], 'isoformat'):
                        signal_copy['timestamp'] = signal_copy['timestamp'].isoformat()
                serialized_live_signals.append(signal_copy)

            # Calculate today's signals from database (consistent with API)
            from datetime import date
            import sqlite3
            today = date.today().isoformat()
            
            # Get accurate count from database
            conn = sqlite3.connect('databases/trading_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?", (today,))
            today_signals = cursor.fetchone()[0]
            conn.close()
            
            # Build today's summary from live + archived signals for display
            def _to_dt(ts):
                if isinstance(ts, str):
                    if not ts.strip():
                        return None
                    try:
                        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"⚠️ Invalid isoformat string in _to_dt: '{ts}' ({e})")
                        return None
                return ts
            
            todays_summary = []
            for s in (self.crypto_monitor.live_signals + self.crypto_monitor.archived_signals):
                ts = s.get('timestamp')
                if not ts:
                    continue
                try:
                    if _to_dt(ts).date() == date.today():
                        cp = s.copy()
                        if hasattr(cp.get('timestamp'), 'isoformat'):
                            cp['timestamp'] = cp['timestamp'].isoformat()
                        todays_summary.append(cp)
                except Exception:
                    continue
            # Sort newest first and cap
            todays_summary.sort(key=lambda s: _to_dt(s.get('timestamp', datetime.now())), reverse=True)
            todays_summary = todays_summary[:50]

            update_data = {
                'prices': self.current_prices,
                'scan_count': self.crypto_monitor.scan_count,
                'signals_today': today_signals,  # Derived from today's journal entries
                'total_signals': self.crypto_monitor.total_signals,
                'daily_pnl': self.crypto_monitor.daily_pnl,  # Now calculated from paper trades
                'paper_balance': self.crypto_monitor.paper_balance,
                'total_paper_pnl': self.crypto_monitor.total_paper_pnl,
                'active_paper_trades': len(self.crypto_monitor.active_paper_trades),
                'completed_paper_trades': serialized_completed_trades,  # Send full trade data
                'active_hours': self.crypto_monitor.active_hours,
                'live_signals': serialized_live_signals,  # Serialized signals with age info
                'total_live_signals': len(self.crypto_monitor.live_signals),
                'total_archived_signals': len(self.crypto_monitor.archived_signals),
                'paper_trades': serialized_active_trades,  # Serialized active trades
                'trading_journal': self.serialize_datetime_objects(self.crypto_monitor.trading_journal[-10:]),  # Last 10 for journal
                'signals_summary': todays_summary,  # Use today's journal entries for summary
                'session_status': self.session_tracker.get_sessions_status(),
                'market_hours': self.statistics.is_market_hours(),
                'uptime': self.statistics.get_uptime(),
                'scan_signal_ratio': self.statistics.calculate_scan_signal_ratio(
                    self.crypto_monitor.scan_count, 
                    self.crypto_monitor.total_signals
                ),
                'ml_model_status': {
                    'loaded': self.signal_generator.ml_model is not None,
                    'status': 'loaded' if self.signal_generator.ml_model is not None else 'not_found'
                },
                'timestamp': datetime.now().isoformat()
            }
            self.socketio.emit('status_update', update_data)
        except Exception as e:
            logger.error(f"❌ Error broadcasting update: {e}")
    
    def get_dashboard_html(self):
        """Generate the dashboard HTML matching previous monitor exactly"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Kirston's Crypto Bot - ICT Enhanced</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            border-bottom: 2px solid #00ff88;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #00ff88;
        }
        
        .crypto-symbols {
            margin: 15px 0;
            font-size: 1.1em;
        }
        
        .crypto-symbol {
            background: rgba(0, 255, 136, 0.2);
            padding: 8px 15px;
            margin: 0 5px;
            border-radius: 20px;
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: #00ff88;
            font-weight: bold;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .refresh-btn {
            background: #00ff88;
            color: black;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 15px;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        
        .prices-display {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        
        .price-item {
            background: rgba(0, 255, 136, 0.1);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        
        .price-crypto {
            font-weight: bold;
            color: #00ff88;
            font-size: 1.1em;
        }
        
        .price-value {
            color: #ffffff;
            font-size: 1.2em;
            font-weight: bold;
            margin: 5px 0;
        }
        
        .price-change {
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .price-change.positive { color: #00ff88; }
        .price-change.negative { color: #ff4757; }
        
        .signals-summary-section {
            margin-top: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }
        
        .stat-label {
            color: rgba(255,255,255,0.7);
            margin-top: 5px;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 25px;
        }
        
        .section-title {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 1px solid rgba(0, 255, 136, 0.3);
            padding-bottom: 10px;
        }
        
        .signal-item {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
            transition: all 0.3s ease-in-out;
            opacity: 0;
            animation: slideInFade 0.5s ease-out forwards;
        }
        
        /* Signal age-based styling */
        .signal-age-fresh {
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
            border-left-color: #00ff88;
        }
        
        .signal-age-active {
            box-shadow: 0 0 10px rgba(255, 193, 7, 0.2);
        }
        
        .signal-age-expiring {
            box-shadow: 0 0 10px rgba(255, 140, 0, 0.2);
            animation: pulse-orange 2s infinite;
        }
        
        /* Signal animations */
        @keyframes slideInFade {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse-orange {
            0%, 100% {
                box-shadow: 0 0 10px rgba(255, 140, 0, 0.2);
            }
            50% {
                box-shadow: 0 0 20px rgba(255, 140, 0, 0.4);
            }
        }
        
        .signal-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.3);
        }
        
        .paper-trade-item {
            background: rgba(0, 150, 255, 0.1);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #0096ff;
            transition: all 0.3s ease-in-out;
            opacity: 0;
            animation: slideInFade 0.5s ease-out forwards;
        }
        
        .paper-trade-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 150, 255, 0.3);
        }
        
        .trade-buy {
            border-left-color: #00ff88;
            background: rgba(0, 255, 136, 0.05);
        }
        
        .trade-sell {
            border-left-color: #ff4757;
            background: rgba(255, 71, 87, 0.05);
        }
        
        .signal-buy { border-left-color: #00ff88; }
        .signal-sell { border-left-color: #ff4757; }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: rgba(255,255,255,0.5);
            font-style: italic;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        th, td {
            padding: 8px 6px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        th {
            background: rgba(0,255,136,0.2);
            color: #00ff88;
            font-size: 11px;
            text-align: center;
        }
        
        td {
            font-size: 11px;
            color: rgba(255,255,255,0.8);
        }
        
        .table-crypto {
            font-weight: bold;
            color: #ffffff;
        }
        
        .active-trade {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }
        
        .profit {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }
        
        .loss {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }
        
        .table-buy { color: #00ff88; font-weight: bold; }
        .table-sell { color: #ff4757; font-weight: bold; }
        .table-price { color: #0096ff; font-weight: bold; }
        .table-confidence { color: #ffa502; font-weight: bold; }
        .table-time { color: rgba(255,255,255,0.7); }
        
        .status-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-pending {
            background-color: rgba(255, 193, 7, 0.2);
            color: #ffc107;
            border: 1px solid rgba(255, 193, 7, 0.3);
        }
        
        .status-win {
            background-color: rgba(0, 255, 136, 0.2);
            color: #00ff88;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        
        .status-loss {
            background-color: rgba(255, 71, 87, 0.2);
            color: #ff4757;
            border: 1px solid rgba(255, 71, 87, 0.3);
        }
        
        .market-active {
            background: #00ff88;
            color: black;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .market-closed {
            background: #ff4757;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Kirston's Crypto Bot</h1>
        <div class="crypto-symbols">
            <span class="crypto-symbol">₿ BTC</span>
            <span class="crypto-symbol">◎ SOL</span>
            <span class="crypto-symbol">Ξ ETH</span>
            <span class="crypto-symbol">✕ XRP</span>
        </div>
        <p><span class="status-indicator"></span> <span id="market-status">Monitoring Active</span> | <span id="current-time">--:-- GMT</span></p>
        
        <!-- Real-time Prices Display -->
        <div class="prices-display" id="prices-display">
            <div class="price-item">
                <div class="price-crypto">₿ BTC</div>
                <div class="price-value" id="btc-price">$--,---</div>
                <div class="price-change" id="btc-change">--%</div>
            </div>
            <div class="price-item">
                <div class="price-crypto">◎ SOL</div>
                <div class="price-value" id="sol-price">$---</div>
                <div class="price-change" id="sol-change">--%</div>
            </div>
            <div class="price-item">
                <div class="price-crypto">Ξ ETH</div>
                <div class="price-value" id="eth-price">$-,---</div>
                <div class="price-change" id="eth-change">--%</div>
            </div>
            <div class="price-item">
                <div class="price-crypto">✕ XRP</div>
                <div class="price-value" id="xrp-price">$-.--</div>
                <div class="price-change" id="xrp-change">--%</div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="requestUpdate()">🔄 Refresh</button>
    </div>

    <div class="stats-grid">
        <div class="stat-card" style="background: linear-gradient(135deg, #1a4b3a, #0d2818); border: 1px solid #00ff88;">
            <div class="stat-number" id="current-balance" style="color: #00ff88; font-weight: bold;">$100.00</div>
            <div class="stat-label">Live Balance</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="scan-count">0</div>
            <div class="stat-label">Total Scans</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="signals-today">0</div>
            <div class="stat-label">Signals Today</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="daily-pnl">$0</div>
            <div class="stat-label">Daily P&L</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="live-signals-count" style="color: #00ff88;">0/3</div>
            <div class="stat-label">Live Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="paper-trades-count" style="color: #0096ff;">0</div>
            <div class="stat-label">Paper Trades</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="active-hours">08:00-22:00</div>
            <div class="stat-label">Active Hours GMT</div>
        </div>
    </div>

    <div class="main-grid">
        <div class="card">
            <h2 class="section-title">🎯 Live Trading Signals</h2>
            <div id="signals-list">
                <div class="no-data">🔍 Scanning for high-confidence signals during market hours...</div>
            </div>
        </div>

        <div class="card">
            <h2 class="section-title"> Trading Journal</h2>
            <div style="margin-bottom: 10px; font-size: 12px; color: rgba(255,255,255,0.7);">
                Paper trades executed automatically | $100 risk per trade | 1:3 RR
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="min-width: 40px;">Crypto</th>
                            <th style="min-width: 30px;">TF</th>
                            <th style="min-width: 50px;">Position</th>
                            <th style="min-width: 40px;">Risk %</th>
                            <th style="min-width: 60px;">Entry</th>
                            <th style="min-width: 50px;">Status</th>
                            <th style="min-width: 60px;">PnL</th>
                        </tr>
                    </thead>
                    <tbody id="journal-table-body">
                        <tr>
                            <td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.6); font-style: italic;">📝 No trades logged yet</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Active Paper Trades Section -->
    <div class="card">
        <h2 class="section-title">💼 Active Paper Trades</h2>
        <div id="paper-trades-list">
            <div class="no-data">💼 No active paper trades yet...</div>
        </div>
    </div>

    <div class="card">
        <h2 class="section-title">🌍 Global Trading Sessions Status</h2>
        <div style="overflow-x: auto;">
            <table id="sessions-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: rgba(0,255,136,0.2); border-bottom: 2px solid rgba(0,255,136,0.5);">
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Session</th>
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Hours (GMT)</th>
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Timezone</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Status</th>
                    </tr>
                </thead>
                <tbody id="sessions-table-body">
                    <!-- Session data will be populated by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- Signals Summary Section -->
    <div class="card signals-summary-section">
        <h2 class="section-title">📈 Today's Signals Summary</h2>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: rgba(0,255,136,0.2); border-bottom: 2px solid rgba(0,255,136,0.5);">
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Date</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Time (GMT)</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Crypto</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Action</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Price</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Confidence</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Timeframe</th>
                    </tr>
                </thead>
                <tbody id="signals-summary-body">
                    <tr>
                        <td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.6); font-style: italic;">📊 No signals recorded yet today</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to ICT Trading Monitor');
            requestUpdate();
        });

        // Initialize on page load
        socket.on('connect', function() {
            console.log('Connected to server');
            requestUpdate(); // Request immediate update on connect
        });

        socket.on('status_update', function(data) {
            updateDashboard(data);
        });

        function requestUpdate() {
            socket.emit('request_update');
        }

        function updateDashboard(data) {
            console.log('Received dashboard data:', data); // Debug log
            
            // Update live balance (prominent display)
            const balanceElement = document.getElementById('current-balance');
            const balance = data.paper_balance || 100.0;
            balanceElement.textContent = '$' + balance.toFixed(2);
            
            // Color code balance based on performance
            if (balance >= 100) {
                balanceElement.style.color = '#00ff88'; // Green for profit/break-even
            } else if (balance >= 90) {
                balanceElement.style.color = '#ffc107'; // Yellow for small loss
            } else {
                balanceElement.style.color = '#ff4757'; // Red for significant loss
            }
            
            // Update stats
            document.getElementById('scan-count').textContent = data.scan_count;
            document.getElementById('signals-today').textContent = data.signals_today;
            document.getElementById('daily-pnl').textContent = '$' + (data.daily_pnl || 0).toFixed(2);  // Fixed to use daily_pnl
            document.getElementById('active-hours').textContent = data.active_hours;
            
            // Update live signals count with color coding
            const liveSignalsElement = document.getElementById('live-signals-count');
            const liveCount = data.total_live_signals || 0;
            const maxSignals = 3;
            liveSignalsElement.textContent = `${liveCount}/${maxSignals}`;
            
            // Color code based on signal load
            if (liveCount === 0) {
                liveSignalsElement.style.color = 'rgba(255,255,255,0.6)';
            } else if (liveCount <= 2) {
                liveSignalsElement.style.color = '#00ff88';
            } else {
                liveSignalsElement.style.color = '#ffc107';
            }
            
            // Update paper trading count
            const paperTradesElement = document.getElementById('paper-trades-count');
            const activeTrades = data.active_paper_trades || 0;
            paperTradesElement.textContent = activeTrades;
            
            // Color code based on active trades
            if (activeTrades === 0) {
                paperTradesElement.style.color = 'rgba(255,255,255,0.6)';
            } else if (activeTrades <= 3) {
                paperTradesElement.style.color = '#0096ff';
            } else {
                paperTradesElement.style.color = '#ffc107';
            }
            
            // Update current time in GMT
            const now = new Date();
            const gmtTime = now.toLocaleTimeString('en-GB', { 
                timeZone: 'GMT', 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
            document.getElementById('current-time').textContent = gmtTime + ' GMT';

            // Update market status
            const marketStatusElement = document.getElementById('market-status');
            const marketStatus = data.market_hours ? 'Market Active' : 'Market Closed';
            marketStatusElement.textContent = marketStatus;
            marketStatusElement.className = data.market_hours ? 'market-active' : 'market-closed';

            // Update real-time prices
            updatePrices(data.prices);

            // Update signals
            updateSignals(data.live_signals);
            
            // Update paper trades
            updatePaperTrades(data.paper_trades || []);
            
            // Update paper trading history
            updateJournal(data.completed_paper_trades || []);
            
            // Debug: Check what signals_summary data we're receiving
            console.log('All data received:', data);
            console.log('Signals summary specifically:', data.signals_summary);
            console.log('Trading journal specifically:', data.trading_journal);
            
            // Update signals summary table
            console.log('Data received for signals summary:', data.signals_summary); // Debug log
            updateSignalsSummary(data.signals_summary);
            
            // Update sessions table
            console.log('Session status data:', data.session_status); // Debug log
            updateSessionsTable(data.session_status);
        }

        function updatePrices(prices) {
            if (prices) {
                for (const [crypto, data] of Object.entries(prices)) {
                    const priceId = crypto.toLowerCase() + '-price';
                    const changeId = crypto.toLowerCase() + '-change';
                    
                    const priceElement = document.getElementById(priceId);
                    const changeElement = document.getElementById(changeId);
                    
                    if (priceElement) {
                        if (crypto === 'BTC') {
                            priceElement.textContent = '$' + data.price.toLocaleString('en-US', {maximumFractionDigits: 0});
                        } else if (crypto === 'XRP') {
                            priceElement.textContent = '$' + data.price.toFixed(3);
                        } else {
                            priceElement.textContent = '$' + data.price.toLocaleString('en-US', {maximumFractionDigits: 2});
                        }
                    }
                    
                    if (changeElement) {
                        const changeText = (data.change_24h >= 0 ? '+' : '') + data.change_24h.toFixed(2) + '%';
                        changeElement.textContent = changeText;
                        changeElement.className = 'price-change ' + (data.change_24h >= 0 ? 'positive' : 'negative');
                    }
                }
            }
        }

        function updateSignals(signals) {
            const signalsList = document.getElementById('signals-list');
            if (signals && signals.length > 0) {
                signalsList.innerHTML = '';
                signals.forEach(signal => {
                    addSignalToList(signal);
                });
            } else {
                signalsList.innerHTML = '<div class="no-data">✅ No high-confidence signals found in recent scans</div>';
            }
        }

        function updatePaperTrades(paperTrades) {
            console.log('updatePaperTrades called with:', paperTrades); // Debug log
            const paperTradesList = document.getElementById('paper-trades-list');
            if (!paperTradesList) {
                console.warn('paper-trades-list element not found; skipping update');
                return;
            }
            if (paperTrades && paperTrades.length > 0) {
                console.log('Updating', paperTrades.length, 'active paper trades'); // Debug log
                paperTradesList.innerHTML = '';
                paperTrades.forEach(trade => {
                    addPaperTradeToList(trade);
                });
            } else {
                console.log('No active paper trades to display'); // Debug log
                paperTradesList.innerHTML = '<div class="no-data">💼 No active paper trades yet...</div>';
            }
        }

        function addPaperTradeToList(trade) {
            const paperTradesList = document.getElementById('paper-trades-list');
            
            if (paperTradesList.querySelector('.no-data')) {
                paperTradesList.innerHTML = '';
            }

            const pnlColor = trade.pnl >= 0 ? '#00ff88' : '#ff4757';
            const pnlPrefix = trade.pnl >= 0 ? '+$' : '-$';
            const pnlValue = Math.abs(trade.pnl).toFixed(2);
            
            const cryptoEmoji = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}[trade.crypto] || '🪙';
            
            // Format entry time for display
            const entryTime = trade.entry_time ? new Date(trade.entry_time).toLocaleTimeString('en-GB', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            }) : 'N/A';
            
            const tradeDiv = document.createElement('div');
            tradeDiv.className = `paper-trade-item trade-${trade.action.toLowerCase()}`;
            
            tradeDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-weight: bold; font-size: 1.1em;">
                        ${cryptoEmoji} ${trade.crypto} ${trade.action} - ${trade.id}
                    </div>
                    <div style="background: ${pnlColor}22; color: ${pnlColor}; padding: 4px 8px; border-radius: 12px; font-size: 0.9em; font-weight: bold;">
                        ${pnlPrefix}${pnlValue}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.9em; color: rgba(255,255,255,0.8);">
                    <div>Entry: <span style="color: #0096ff; font-weight: bold;">$${trade.entry_price.toFixed(4)}</span></div>
                    <div>Current: <span style="color: ${pnlColor}; font-weight: bold;">$${(trade.current_price || trade.entry_price).toFixed(4)}</span></div>
                    <div>Size: ${trade.position_size.toFixed(4)}</div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.8em; color: rgba(255,255,255,0.6); margin-top: 8px;">
                    <div>SL: $${trade.stop_loss.toFixed(4)}</div>
                    <div>TP: $${trade.take_profit.toFixed(4)}</div>
                    <div>Time: <span style="color: #ffc107;">${entryTime}</span></div>
                </div>
            `;
            
            paperTradesList.appendChild(tradeDiv);
        }

        function updateJournal(completedTrades) {
            console.log('updateJournal called with:', completedTrades); // Debug log
            const journalTableBody = document.getElementById('journal-table-body');
            
            if (!completedTrades || completedTrades.length === 0) {
                console.log('No completed trades for journal'); // Debug log
                journalTableBody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.6); font-style: italic;">📝 No trades logged yet - All current trades are still active</td></tr>';
                return;
            }
            
            // Show last 8 trades (most recent first) to fit the smaller layout
            const recentTrades = completedTrades.slice(-8).reverse();
            
            journalTableBody.innerHTML = recentTrades.map(trade => {
                const pnlValue = (typeof trade.final_pnl === 'number') ? trade.final_pnl : (trade.pnl || 0);
                const pnlColor = pnlValue >= 0 ? '#4ade80' : '#f87171';
                const pnlPrefix = pnlValue >= 0 ? '+' : '';
                const crypto = trade.crypto || trade.symbol || '-';
                const action = trade.action || trade.side || '-';
                
                // Format status for display
                let displayStatus = 'PENDING';
                if (trade.status === 'TAKE_PROFIT' || trade.status === 'STOP_LOSS' || trade.status === 'COMPLETED') {
                    displayStatus = pnlValue >= 0 ? 'WIN' : 'LOSS';
                }
                
                const statusClass = displayStatus === 'PENDING' ? 'pending' : 
                                   displayStatus === 'WIN' ? 'win' : 
                                   displayStatus === 'LOSS' ? 'loss' : 'pending';
                
                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <td style="padding: 8px 6px; font-weight: bold; color: #ffffff;">${crypto}</td>
                        <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">5m</td>
                        <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: ${action === 'BUY' ? '#4ade80' : '#f87171'};">${action === 'BUY' ? 'Long' : 'Short'}</td>
                        <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">1.0%</td>
                        <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">$${(trade.entry_price || 0).toFixed(2)}</td>
                        <td style="padding: 8px 6px; text-align: center; font-size: 11px;">
                            <span class="status-badge status-${statusClass}">
                                ${displayStatus}
                            </span>
                        </td>
                        <td style="padding: 8px 6px; text-align: center; font-size: 11px; font-weight: bold; color: ${pnlColor};">
                            ${pnlValue === 0 ? '--' : pnlPrefix + '$' + Math.abs(pnlValue).toFixed(2)}
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function addTradeToJournalTable(trade) {
            const journalTableBody = document.getElementById('journal-table-body');
            const row = document.createElement('tr');
            
            const statusClass = trade.status === 'PENDING' ? 'pending' : 
                               trade.status === 'WIN' ? 'win' : 
                               trade.status === 'LOSS' ? 'loss' : 'pending';
            
            const pnlColor = trade.pnl > 0 ? '#00ff88' : 
                            trade.pnl < 0 ? '#ff4757' : 
                            'rgba(255,255,255,0.7)';
            
            row.innerHTML = `
                <td style="padding: 8px 6px; font-weight: bold; color: #ffffff;">${trade.crypto}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">${trade.timeframe}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: ${trade.action === 'BUY' ? '#00ff88' : '#ff4757'};">${trade.action === 'BUY' ? 'Long' : 'Short'}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">1.0%</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">$${trade.entry_price.toFixed(4)}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px;">
                    <span class="status-badge status-${statusClass}">
                        ${trade.status}
                    </span>
                </td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; font-weight: bold; color: ${pnlColor};">
                    ${trade.pnl === 0 ? '--' : '$' + trade.pnl.toFixed(2)}
                </td>
            `;
            
            journalTableBody.appendChild(row);
        }

        function addSignalToList(signal) {
            const signalsList = document.getElementById('signals-list');
            
            if (signalsList.querySelector('.no-data')) {
                signalsList.innerHTML = '';
            }

            // Convert to GMT time
            const timestamp = new Date(signal.timestamp);
            const gmtTime = timestamp.toLocaleTimeString('en-GB', { 
                timeZone: 'GMT',
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
            
            // Age indicator styling
            const ageMinutes = signal.age_minutes || 0;
            const ageCategory = signal.age_category || 'fresh';
            const ageColors = {
                'fresh': '#00ff88',     // Green for 0-2 minutes
                'active': '#ffc107',    // Yellow for 2-4 minutes
                'expiring': '#ff8c00'   // Orange for 4-5 minutes
            };
            const ageText = {
                'fresh': 'FRESH',
                'active': 'ACTIVE', 
                'expiring': 'EXPIRING'
            };
            
            const signalDiv = document.createElement('div');
            signalDiv.className = `signal-item signal-${signal.action.toLowerCase()} signal-age-${ageCategory}`;
            
            const cryptoEmoji = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}[signal.crypto] || '🪙';
            
            // Show ML boost if available
            const mlBoostText = signal.ml_boost > 0 ? ` (+${(signal.ml_boost * 100).toFixed(1)}% ML)` : '';
            
            // Show directional bias methodology if available
            const biasMethodology = signal.bias_methodology || 'TRADITIONAL_ICT';
            const biasIndicator = biasMethodology === 'ICT_DIRECTIONAL_BIAS' ? ' 🎯' : '';
            const nyOpenAnalysis = signal.ny_open_analysis ? ' 🗽' : '';
            const chochConfirmed = signal.choch_confirmed ? ' 🔄' : '';
            const retestQuality = signal.retest_quality && signal.retest_quality !== 'N/A' ? ` 📍${signal.retest_quality}` : '';
            
            signalDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="font-weight: bold; font-size: 1.1em;">
                            ${cryptoEmoji} ${signal.crypto} ${signal.action}${biasIndicator}${nyOpenAnalysis}${chochConfirmed}${retestQuality}
                        </div>
                        <div style="background: ${ageColors[ageCategory]}22; color: ${ageColors[ageCategory]}; padding: 2px 6px; border-radius: 8px; font-size: 0.7em; font-weight: bold; border: 1px solid ${ageColors[ageCategory]}44;">
                            ${ageText[ageCategory]} ${ageMinutes.toFixed(1)}m
                        </div>
                    </div>
                    <div style="background: rgba(255,193,7,0.2); color: #ffc107; padding: 4px 8px; border-radius: 12px; font-size: 0.9em; font-weight: bold;">
                        ${(signal.confidence * 100).toFixed(1)}%${mlBoostText}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.9em; color: rgba(255,255,255,0.8);">
                    <div>Entry: <span style="color: #0096ff; font-weight: bold;">$${signal.entry_price.toFixed(4)}</span></div>
                    <div>Stop: $${signal.stop_loss.toFixed(4)}</div>
                    <div>Target: <span style="color: #00ff88; font-weight: bold;">$${signal.take_profit.toFixed(4)}</span></div>
                </div>
                ${signal.directional_bias ? `
                <div style="margin-top: 8px; padding: 6px; background: rgba(0, 255, 136, 0.1); border-left: 3px solid #00ff88; border-radius: 4px;">
                    <div style="font-size: 0.8em; color: #00ff88; font-weight: bold;">
                        🎯 Directional Bias: ${signal.directional_bias}
                    </div>
                </div>
                ` : ''}
                <div style="margin-top: 10px;">
                    <div style="font-size: 0.8em; color: rgba(255,255,255,0.6);">
                        Confluences: ${signal.confluences.join(', ')}
                    </div>
                    <div style="font-size: 0.8em; color: rgba(255,255,255,0.6); margin-top: 5px;">
                        ${gmtTime} GMT | ${signal.timeframe} | Risk: $${signal.risk_amount} | ${biasMethodology}
                    </div>
                    ${signal.fibonacci_confluence ? `
                    <div style="font-size: 0.7em; color: rgba(0, 150, 255, 0.8); margin-top: 3px;">
                        📊 Fib: ${(signal.fibonacci_confluence * 100).toFixed(0)}% | Elliott: ${(signal.elliott_wave_confluence * 100).toFixed(0)}%
                    </div>
                    ` : ''}
                </div>
            `;
            
            signalsList.appendChild(signalDiv);
        }

        function updateSignalsSummary(signals) {
            console.log('updateSignalsSummary called with:', signals); // Debug log
            const summaryBody = document.getElementById('signals-summary-body');
            if (signals && signals.length > 0) {
                console.log('Updating signals summary with', signals.length, 'signals'); // Debug log
                summaryBody.innerHTML = '';
                signals.forEach((signal, index) => {
                    const row = document.createElement('tr');
                    
                    // Convert UTC timestamp to GMT
                    const timestamp = new Date(signal.timestamp);
                    const gmtDate = timestamp.toLocaleDateString('en-GB', { timeZone: 'GMT' });
                    const gmtTime = timestamp.toLocaleTimeString('en-GB', { 
                        timeZone: 'GMT',
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    
                    const cryptoEmoji = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}[signal.crypto] || '🪙';
                    
                    row.innerHTML = `
                        <td style="padding: 10px; color: rgba(255,255,255,0.8);">${gmtDate}</td>
                        <td style="padding: 10px; text-align: center; color: rgba(255,255,255,0.8); font-family: 'Courier New', monospace;">${gmtTime}</td>
                        <td style="padding: 10px; text-align: center; font-weight: bold; color: #ffffff;">${cryptoEmoji} ${signal.crypto}</td>
                        <td style="padding: 10px; text-align: center; font-weight: bold; color: ${signal.action === 'BUY' ? '#00ff88' : '#ff4757'};">${signal.action}</td>
                        <td style="padding: 10px; text-align: center; color: #0096ff; font-weight: bold;">$${signal.entry_price.toFixed(4)}</td>
                        <td style="padding: 10px; text-align: center; color: #ffc107; font-weight: bold;">${(signal.confidence * 100).toFixed(1)}%</td>
                        <td style="padding: 10px; text-align: center; color: rgba(255,255,255,0.85); font-weight: bold;">${signal.timeframe || '-'}</td>
                    `;
                    
                    summaryBody.appendChild(row);
                });
            } else {
                summaryBody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.6); font-style: italic;">📊 No signals recorded yet today</td></tr>';
            }
        }

        function updateSessionsTable(sessions) {
            console.log('updateSessionsTable called with:', sessions); // Debug log
            const tableBody = document.getElementById('sessions-table-body');
            if (!tableBody) {
                console.error('sessions-table-body element not found!'); // Debug log
                return;
            }
            
            if (sessions) {
                tableBody.innerHTML = '';
                
                // Order sessions: Asia, London, New York
                const sessionOrder = ['Asia', 'London', 'New_York'];
                sessionOrder.forEach(sessionKey => {
                    if (sessions[sessionKey]) {
                        const session = sessions[sessionKey];
                        const statusColor = session.is_open ? '#00ff88' : '#ff6b6b';
                        const statusBg = session.is_open ? 'rgba(0,255,136,0.2)' : 'rgba(255,107,107,0.2)';
                        
                        const row = `
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 12px; color: rgba(255,255,255,0.9); font-weight: 500;">
                                    ${session.name}
                                </td>
                                <td style="padding: 12px; color: rgba(255,255,255,0.8); font-family: 'Courier New', monospace;">
                                    ${session.hours}
                                </td>
                                <td style="padding: 12px; color: rgba(255,255,255,0.7);">
                                    ${session.timezone}
                                </td>
                                <td style="padding: 12px; text-align: center;">
                                    <span style="background: ${statusBg}; color: ${statusColor}; padding: 6px 12px; border-radius: 15px; font-weight: bold; font-size: 11px; border: 1px solid ${statusColor};">
                                        ${session.status}
                                    </span>
                                </td>
                            </tr>
                        `;
                        tableBody.innerHTML += row;
                    }
                });
            }
        }

        // Request updates every 30 seconds
        setInterval(() => {
            requestUpdate();
        }, 30000);

        // Test session population on page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, testing session table...');
            
            // Test with dummy data to ensure table works
            const testSessions = {
                'Asia': {
                    name: 'Asia',
                    hours: '23:00-08:00 GMT',
                    timezone: 'GMT+8',
                    status: 'CLOSED',
                    is_open: false
                },
                'London': {
                    name: 'London', 
                    hours: '08:00-16:00 GMT',
                    timezone: 'GMT+0',
                    status: 'OPEN',
                    is_open: true
                },
                'New_York': {
                    name: 'New York',
                    hours: '13:00-22:00 GMT', 
                    timezone: 'GMT-5',
                    status: 'OPEN',
                    is_open: true
                }
            };
            
            // Test the table after a brief delay
            setTimeout(() => {
                console.log('Testing session table with dummy data...');
                updateSessionsTable(testSessions);
            }, 1000);
        });
    </script>
</body>
</html>
        '''
    
    def start(self):
        """Start the ICT Web Monitor"""
        try:
            # Display startup banner
            print("\n" + "="*70)
            print("🤖 KIRSTON'S CRYPTO BOT - ICT ENHANCED")
            print("="*70)
            print()
            print("✅ Monitoring: BTC, SOL, ETH, XRP")
            print("✅ ICT Methodology: Order Blocks, FVGs, Market Structure")
            print("✅ Risk Management: $1 per trade (1% risk) | RR 1:3")
            print("✅ Market Hours: 08:00-22:00 GMT")
            print("✅ Real-time Price Updates")
            print("✅ Trading Journal & Session Status")
            print()
            print(f"🌐 Web Interface: http://localhost:{self.port}")
            print(f"📊 Health Check: http://localhost:{self.port}/health")
            print(f"🔗 API Endpoint: http://localhost:{self.port}/api/data")
            print()
            print("Press Ctrl+C to stop")
            print("="*70)
            
            # Start analysis thread
            self.is_running = True
            analysis_thread = threading.Thread(target=self.run_analysis_cycle, daemon=True)
            analysis_thread.start()
            
            # Start Bybit price monitoring in separate thread
            if self.crypto_monitor.bybit_prices:
                def run_bybit_prices():
                    try:
                        asyncio.run(self.crypto_monitor.bybit_prices.start())
                        logger.info("🔗 Bybit real-time price feed started")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to start Bybit price feed: {e}")
                
                bybit_thread = threading.Thread(target=run_bybit_prices, daemon=True)
                bybit_thread.start()
                logger.info("🚀 Starting Bybit real-time price monitoring...")
            
            logger.info(f"🚀 ICT Enhanced Trading Monitor starting on port {self.port}")
            
            # Start Flask-SocketIO server
            self.socketio.run(
                self.app, 
                host='127.0.0.1', 
                port=self.port, 
                debug=False,
                allow_unsafe_werkzeug=True,
                use_reloader=False,
                log_output=False
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Error starting monitor: {e}")
            raise
    
    def stop(self):
        """Stop the monitor"""
        self.is_running = False
        logger.info("🤖 ICT Enhanced Trading Monitor stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICT Enhanced Trading Monitor')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the monitor on')
    args = parser.parse_args()
    
    monitor = ICTWebMonitor(port=args.port)
    monitor.start()

if __name__ == "__main__":
    main()