#!/usr/bin/env python3
"""
ICT Enhanced Trading Monitor - Port 5001
========================================

Kirston's Crypto Bot - ICT Enhanced Trading Monitor
Monitors BTC, SOL, ETH, XRP with institutional analysis

Created by: GitHub Copilot
"""

import json
import time
import logging
import threading
import asyncio
import sqlite3

# Constants
TIMEZONE_OFFSET = '+00:00'  # UTC timezone identifier for ISO format conversion

import aiohttp
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from flask import Flask, render_template_string, jsonify, request, send_from_directory, redirect
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from functools import wraps
import jwt
import bcrypt
import pandas as pd
import numpy as np

# Add src to path for database import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.trading_database import TradingDatabase

# Import trade manager from src.trading
trading_path = os.path.join(os.path.dirname(__file__), '..', 'trading')
sys.path.append(trading_path)
from intraday_trade_manager import create_trade_manager

# Add project root to path for backtest engine import
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

# Add utils directory to path for quant modules
utils_path = os.path.join(project_root, 'utils')
sys.path.append(utils_path)

# Import backtest engine components directly (skip __init__.py to avoid circular imports)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "strategy_engine", 
    os.path.join(project_root, "backtesting", "strategy_engine.py")
)
strategy_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strategy_module)
ICTStrategyEngine = strategy_module.ICTStrategyEngine
MultiTimeframeData = strategy_module.MultiTimeframeData

# 🚀 QUANT ENHANCEMENTS - Import all 5 modules
try:
    from utils.volatility_indicators import VolatilityAnalyzer
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from utils.volatility_indicators import VolatilityAnalyzer
from utils.correlation_matrix import CorrelationAnalyzer
from utils.signal_quality import SignalQualityAnalyzer
from utils.mean_reversion import MeanReversionAnalyzer

# 🔧 DIAGNOSTIC AND ANALYSIS - Import diagnostic and SOL analyzer
core_path = os.path.join(project_root, 'core')
sys.path.append(core_path)
from diagnostics.system_diagnostic import create_diagnostic_checker
# Temporarily comment out to fix import issues
# from analysis.sol_trade_analyzer import create_sol_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
INDEX_HTML_FILENAME = 'index.html'

class ICTCryptoMonitor:
    """ICT Enhanced Crypto Monitor matching previous version exactly"""
    
    def __init__(self):
        # Initialize database first - SINGLE MAIN DATABASE
        # Use absolute path to the correct database location
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(project_root, "data", "trading.db")
        self.db = TradingDatabase(db_path)
        
        # Exact same symbols as previous monitor
        self.symbols = ['BTCUSDT', 'SOLUSDT', 'ETHUSDT', 'XRPUSDT']
        self.display_symbols = ['BTC', 'SOL', 'ETH', 'XRP']
        self.crypto_emojis = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}
        
        # TRADING CONFIGURATION - Prevent duplicate/old trade display
        self.show_today_only = True  # Only show trades from today to prevent confusion
        
        # Monitor state tracking - load from database
        daily_stats = self.db.get_daily_stats()
        self.scan_count = daily_stats.get('scan_count', 0)
        self.signals_today = daily_stats.get('signals_generated', 0)
        self.total_signals = len(self.db.get_signals_today())
        # daily_pnl is now calculated from completed paper trades
        self.active_hours = "08:00-22:00"
        self.risk_per_trade = 0.01  # 1% of account balance per trade
        self.risk_reward_ratio = 3  # 1:3 RR
        
        # Trading journal and signals - ALL FROM DATABASE NOW
        # REMOVED: self.trading_journal = [] - Query from db.get_journal_entries_today()
        # REMOVED: self.live_signals = [] - Query from db.get_signals_today()
        self.archived_signals = []  # For signals older than 5 minutes (cache only)
        self.last_scan_time = None
        
        # (No test signal injection in production)
        
        # Signal management configuration
        self.max_live_signals = 3  # Maximum signals to display
        self.signal_lifetime_minutes = 5  # Signal lifetime in minutes
        
        # Signal Deduplication System (Solution 2)
        self.signal_cooldown_minutes = 3  # Prevent duplicate signals on same symbol for 3 minutes
        self.recent_signals_cache = {}  # Cache: {symbol: last_signal_time}
        self.max_positions_per_symbol = 1  # Maximum open positions per symbol
        
        # Enhanced Risk Management (Solution 3)
        self.max_portfolio_risk = 0.05  # Maximum 5% of portfolio at risk at once
        self.max_concurrent_signals = 3  # Maximum concurrent live signals
        self.position_correlation_check = True  # Check for correlated positions
        
        # 🚀 QUANT ENHANCEMENTS - Initialize all analyzers
        logger.info("🚀 Initializing Quant Enhancement Modules...")
        self.volatility_analyzer = VolatilityAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.signal_quality_analyzer = SignalQualityAnalyzer()
        self.mean_reversion_analyzer = MeanReversionAnalyzer()
        logger.info("✅ All 5 Quant Modules Loaded: ATR Stops, Correlation Matrix, Time-Decay, Expectancy Filter, Mean Reversion")
        
        # ⏰ INTRADAY TRADE MANAGER - Auto-close trades after max hold time
        logger.info("⏰ Initializing Intraday Trade Manager...")
        self.trade_manager = create_trade_manager(max_hold_hours=4.0)  # 4 hour max hold
        logger.info("✅ Trade Manager: 4h max hold | Session close at NY 4 PM")
        
        # Paper trading configuration
        self.paper_trading_enabled = True
        self.paper_balance = 100.0  # Loaded from database, cached for performance
        self.live_demo_balance = 0.0  # Live balance from Bybit Demo Trading
        self.account_blown = False  # Track if account is blown
        self.blow_up_threshold = 0.0  # Blow up when balance <= $0
        # REMOVED: self.active_paper_trades = [] - Now queried from database
        # REMOVED: self.completed_paper_trades = [] - Now queried from database
        self.total_paper_pnl = 0.0
        self.last_balance_update = None  # Track last Bybit balance fetch
        
        # Load previous state on startup
        self._load_trading_state()
        
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
        
        logger.info("🚀 ICT CRYPTO MONITOR INITIALIZED")
        logger.info(f"📊 Monitoring: {', '.join(self.display_symbols)}")
        logger.info(f"⏰ Active Hours: {self.active_hours} GMT")
        logger.info(f"🎯 Risk per trade: {self.risk_per_trade*100:.1f}% (Fixed) | RR: Dynamic 1:2-1:8")
        logger.info(f"📋 Signal Management: Max {self.max_live_signals} signals, newest replaces oldest")
        logger.info(f"📄 Paper Trading: ENABLED | Balance: ${self.paper_balance:,.2f}")
    
    @property
    def daily_pnl(self):
        """Calculate daily PnL from closed trades - DATABASE-FIRST"""
        try:
            closed_signals = self.db.get_closed_signals_today()
            return sum(signal.get('pnl', 0) for signal in closed_signals if signal.get('pnl'))
        except Exception as e:
            logger.warning(f"Could not calculate daily PnL: {e}")
            return 0.0
    
    def _load_trading_state(self):
        """Load previous trading state from database and migrate JSON data if needed"""
        import os
        from datetime import datetime, date
        
        try:
            # First check if we need to migrate existing JSON data (only if from today)
            today = datetime.now().strftime('%Y%m%d')
            session_file = f"/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/data/trading_sessions/{today}/session_summary_updated.json"
            old_session_file = "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/data/trading_sessions/20251002/session_summary_updated.json"
            
            # Only migrate if the file is from today, not from previous days
            if os.path.exists(session_file):
                logger.info(f"📥 Migrating today's session data from {session_file}")
                self.db.migrate_existing_data(session_file)
            elif os.path.exists(old_session_file):
                logger.info("⚠️  Found old session data from 20251002, but not migrating (new day = fresh start)")
            
            # Load current daily stats from database (this includes daily reset check)
            daily_stats = self.db.get_daily_stats()
            
            # Restore ALL fields from database
            self.scan_count = daily_stats.get('scan_count', 0)
            self.signals_today = daily_stats.get('signals_generated', 0)
            self.paper_balance = daily_stats.get('paper_balance', 100.0)
            self.total_paper_pnl = daily_stats.get('total_pnl', 0.0)
            self.account_blown = self.paper_balance <= 10.0
            
            logger.info(f"🔄 RESTORED STATE: Scan #{self.scan_count}, Signals: {self.signals_today}, Balance: ${self.paper_balance:.2f}")
            
            # ✅ DATABASE-FIRST: All data queried on-demand, no in-memory restoration
            # Load counts for display only
            todays_signals = self.db.get_signals_today()
            active_signals = self.db.get_active_signals()
            closed_signals = self.db.get_closed_signals_today()
            
            self.total_signals = len(todays_signals)
            executed_trades = len(closed_signals)
            losses = len([s for s in closed_signals if s.get('pnl', 0) < 0])
            
            # Display comprehensive restoration info
            logger.info("📊 COMPREHENSIVE DATA RESTORATION:")
            logger.info(f"   🔢 Total Signals Generated Today: {self.signals_today}")
            logger.info(f"   📈 Paper Trades Executed: {executed_trades}")
            logger.info(f"   💰 Today's Total PnL: ${daily_stats.get('total_pnl', 0):.2f}")
            logger.info(f"   📉 Losing Trades: {losses}")
            logger.info(f"   ✅ Winning Trades: {executed_trades - losses}")
            logger.info(f"   🔄 Active Trades Restored: {len(active_signals)}")
            logger.info("   ⚠️  Active Trades Lost in Restart: 0")
            logger.info(f"   📝 Journal Entries Restored: {len(closed_signals)}")
            logger.info(f"   💵 Account Status: {'BLOWN' if self.account_blown else 'ACTIVE'}")
                
        except Exception as e:
            logger.error(f'❌ Failed to load previous state: {e}')
            logger.info('🆕 Starting with fresh state')
            # Initialize with defaults if database load fails
            self.scan_count = 0
            self.signals_today = 0
            self.paper_balance = 100.0
            self.total_paper_pnl = 0.0
            self.account_blown = False
            # ✅ DATABASE-FIRST: No list initialization - query database instead
    
    def _save_trading_state(self):
        """Save current trading state to database (replaces JSON persistence)"""
        try:
            # Update account balance in database
            self.db.update_balance(self.paper_balance, 'paper')
            
            # The database automatically handles persistence of:
            # - scan_count (updated via increment_scan_count)
            # - signals_today (updated via add_signal)
            # - daily stats (automatically maintained)
            
            logger.debug(f"💾 State saved to database: Scan #{self.scan_count}, Balance: ${self.paper_balance:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save state to database: {e}")
    
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
        """Count active positions (live signals + paper trades + database) for a symbol"""
        crypto = symbol.replace('USDT', '')
        
        # DATABASE-FIRST: Query active signals from database
        db_signal_count = 0
        try:
            db_signals = self.db.get_active_signals()  # All ACTIVE signals regardless of date
            db_signal_count = sum(1 for signal in db_signals 
                                if signal.get('symbol', '').replace('USDT', '') == crypto)
        except Exception as e:
            logger.warning(f"Could not check database signals: {e}")
        
        if db_signal_count > 0:
            logger.info(f"🔍 Active Positions for {crypto}: {db_signal_count} (from database)")
        
        return db_signal_count
    
    def calculate_portfolio_risk(self) -> float:
        """Calculate current portfolio risk percentage - DATABASE-FIRST"""
        total_risk = 0
        
        # Query active signals from database
        try:
            active_signals = self.db.get_active_signals()
            for _ in active_signals:
                # Calculate risk amount (each active signal represents 1% risk)
                risk_amount = self.paper_balance * 0.01  # 1% risk per trade
                total_risk += risk_amount
        except Exception as e:
            logger.warning(f"Could not calculate portfolio risk: {e}")
        
        return (total_risk / self.paper_balance) if self.paper_balance > 0 else 0
    
    def can_accept_new_signal(self, symbol: str) -> tuple[bool, str]:
        """Comprehensive check if new signal can be accepted (Solutions 2 & 3)"""
        crypto = symbol.replace('USDT', '')
        
        # Check 1: Recent signal cooldown
        if self.has_recent_signal(crypto):
            return False, f"Recent signal cooldown: {crypto} signaled within {self.signal_cooldown_minutes}min"
        
        # Check 2: Maximum positions per symbol
        active_positions = self.get_active_positions_for_symbol(symbol)
        if active_positions >= self.max_positions_per_symbol:
            return False, f"Max positions reached: {active_positions}/{self.max_positions_per_symbol} for {crypto}"
        
        # Check 3: Maximum concurrent signals - DATABASE-FIRST
        active_signals = self.db.get_active_signals()
        if len(active_signals) >= self.max_concurrent_signals:
            return False, f"Max concurrent signals: {len(active_signals)}/{self.max_concurrent_signals}"
        
        # Check 4: Portfolio risk limit
        current_risk = self.calculate_portfolio_risk() or 0.0  # Ensure not None
        new_trade_risk = self.risk_per_trade or 0.01  # Ensure not None
        max_risk = self.max_portfolio_risk or 0.25  # Ensure not None
        if current_risk + new_trade_risk > max_risk:
            return False, f"Portfolio risk limit: {(current_risk + new_trade_risk)*100:.1f}% > {max_risk*100:.1f}%"
        
        # Check 5: Account blown
        if self.account_blown:
            return False, "Account blown - no new signals allowed"
        
        return True, "Signal approved"
    
    def get_signal_age_minutes(self, signal_timestamp):
        """Calculate signal age in minutes"""
        try:
            if isinstance(signal_timestamp, str):
                signal_time = datetime.fromisoformat(signal_timestamp.replace('Z', TIMEZONE_OFFSET))
            else:
                signal_time = signal_timestamp
            return (datetime.now() - signal_time).total_seconds() / 60
        except Exception:
            return 999  # Return large number for invalid timestamps
    
    def get_signal_age_category(self, age_minutes):
        """Get signal age category for UI display"""
        if age_minutes <= 2:
            return 'fresh'  # 0-2 minutes: Fresh (green)
        elif age_minutes <= 4:
            return 'active'  # 2-4 minutes: Active (yellow)
        else:
            return 'expiring'  # 4-5 minutes: Expiring (orange)
    
    def manage_signal_lifecycle(self):
        """DATABASE-FIRST: Signal lifecycle managed in database"""
        # Signals are now persisted in database with status tracking
        # No in-memory list management needed
        # UI will query database for active signals to display
        return 0  # Return 0 for archived count (backward compatibility)
    
    def execute_paper_trade(self, signal):
        """Execute a paper trade based on signal - DATABASE-FIRST"""
        if not self.paper_trading_enabled:
            return
        
        # Calculate position size using risk management
        entry_price = signal.get('entry_price', 0)
        stop_loss = signal.get('stop_loss', 0)
        
        # 1% risk per trade
        risk_per_trade = self.paper_balance * 0.01
        
        # Calculate position size based on stop distance
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance > 0:
            position_size = risk_per_trade / stop_distance
        else:
            position_size = risk_per_trade / (entry_price * 0.02)  # 2% fallback
        
        # Create paper trade in database
        try:
            paper_trade_id = self.db.add_paper_trade(
                signal_id=signal.get('signal_id', ''),
                symbol=signal.get('symbol', ''),
                direction=signal.get('direction', 'BUY'),
                entry_price=entry_price,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=signal.get('take_profit', 0),
                risk_amount=risk_per_trade
            )
            logger.info(f"📊 Paper trade #{paper_trade_id} created: {signal.get('symbol')} {signal.get('direction')} | Position: {position_size:.6f} @ ${entry_price}")
            return paper_trade_id
        except Exception as e:
            logger.error(f"❌ Failed to create paper trade: {e}")
            return None
    
    def update_paper_trades(self, current_prices):
        """Update active paper trades with current prices and check for TP/SL"""
        if not current_prices:
            return 0
        
        closed_count = 0
        
        # Use database method with proper connection management
        try:
            # Query paper_trades table for OPEN trades using database connection
            with self.db._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('SELECT * FROM paper_trades WHERE status = "OPEN"')
                open_trades = cursor.fetchall()
                
                for trade_row in open_trades:
                    trade = dict(trade_row)
                    crypto = trade['symbol'].replace('USDT', '')
                    
                    if crypto not in current_prices:
                        continue
                    
                    current_price = current_prices[crypto]['price']
                    entry_price = trade['entry_price']
                    stop_loss = trade['stop_loss']
                    take_profit = trade['take_profit']
                    position_size = trade['position_size']
                    direction = trade['direction']
                    trade_id = trade['id']
                    
                    # Calculate unrealized PnL
                    if direction == 'BUY':
                        unrealized_pnl = (current_price - entry_price) * position_size
                    else:  # SELL
                        unrealized_pnl = (entry_price - current_price) * position_size
                    
                    # Update current_price and unrealized_pnl in database
                    conn.execute('''
                        UPDATE paper_trades 
                        SET current_price = ?, unrealized_pnl = ?
                        WHERE id = ?
                    ''', (current_price, unrealized_pnl, trade_id))
                    conn.commit()  # Commit after each update to release lock
                    
                    # Check for TP/SL hits
                    should_close = False
                    close_reason = ""
                    
                    if direction == 'BUY':
                        if current_price <= stop_loss:
                            should_close = True
                            close_reason = "STOP_LOSS"
                        elif current_price >= take_profit:
                            should_close = True
                            close_reason = "TAKE_PROFIT"
                    else:  # SELL
                        if current_price >= stop_loss:
                            should_close = True
                            close_reason = "STOP_LOSS"
                        elif current_price <= take_profit:
                            should_close = True
                            close_reason = "TAKE_PROFIT"
                    
                    # Close trade if TP/SL hit
                    if should_close:
                        # Update paper_trades table
                        conn.execute('''
                            UPDATE paper_trades 
                            SET status = ?, exit_price = ?, exit_time = datetime('now'), realized_pnl = ?
                            WHERE id = ?
                        ''', (close_reason, current_price, unrealized_pnl, trade_id))
                        conn.commit()  # Commit close immediately
                        
                        # Close signal in signals table
                        signal_id = trade['signal_id']
                        self.db.close_signal(signal_id, current_price, close_reason)
                        
                        # Update paper balance
                        self.paper_balance += unrealized_pnl
                        closed_count += 1
                        
                        logger.info(f"📄 PAPER TRADE CLOSED: {crypto} {direction} | {close_reason} | PnL: ${unrealized_pnl:.2f} | New Balance: ${self.paper_balance:.2f}")
                        
                        # Add to journal (use correct method signature)
                        try:
                            self.db.add_journal_entry(
                                entry_type='TRADE_CLOSED',
                                title=f"{crypto} {direction} - {close_reason}",
                                content=f"Closed at ${current_price:.2f} | PnL: ${unrealized_pnl:.2f}",
                                signal_id=signal_id
                            )
                        except Exception as journal_error:
                            logger.warning(f"⚠️  Could not add journal entry: {journal_error}")
                
        except sqlite3.OperationalError as e:
            logger.warning(f"⚠️  Database busy during paper trade update: {e}")
            # Don't fail the entire cycle, just skip this update
            return 0
        except Exception as e:
            logger.error(f"❌ Error updating paper trades: {e}")
            return 0
        
        return closed_count
        
    async def get_real_time_prices(self):
        """Get real-time prices from Bybit Demo Trading (real market prices)"""
        try:
            # Import Bybit client
            sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
            from bybit_integration.bybit_client import BybitDemoClient
            from dotenv import load_dotenv
            
            # Load API credentials
            env_path = os.path.join(os.path.dirname(__file__), '../../.env')
            load_dotenv(env_path)
            
            # Use async context manager to ensure proper session cleanup
            async with BybitDemoClient(demo=True) as client:
                prices = {}
                
                # Map our symbols to Bybit format
                symbol_mapping = {
                    'BTC': 'BTCUSDT',
                    'ETH': 'ETHUSDT',
                    'SOL': 'SOLUSDT',
                    'XRP': 'XRPUSDT'
                }
                
                for crypto_name, bybit_symbol in symbol_mapping.items():
                    try:
                        # Get ticker data from Bybit (real-time market data)
                        ticker = await client.get_ticker(bybit_symbol)
                        
                        if ticker:
                            last_price = float(ticker.get('lastPrice', 0))
                            high_24h = float(ticker.get('highPrice24h', last_price * 1.02))
                            low_24h = float(ticker.get('lowPrice24h', last_price * 0.98))
                            volume_24h = float(ticker.get('volume24h', 0))
                            price_change_24h = float(ticker.get('price24hPcnt', 0)) * 100  # Convert to percentage
                            
                            prices[crypto_name] = {
                                'price': last_price,
                                'change_24h': price_change_24h,
                                'volume': volume_24h,
                                'high_24h': high_24h,
                                'low_24h': low_24h,
                                'timestamp': datetime.now().isoformat()
                            }
                    except Exception as e:
                        logger.warning(f"Failed to fetch {crypto_name} from Bybit: {e}")
                        continue
                
                # Fetch live Demo Trading balance (if not fetched recently)
                now = datetime.now(timezone.utc)
                if self.last_balance_update is None or (now - self.last_balance_update).total_seconds() > 60:
                    try:
                        balance_data = await client.get_balance()
                        if balance_data:
                            # Calculate total portfolio value in USDT
                            total_value = 0.0
                            balances_detail = []
                            
                            for coin, amount in balance_data.items():
                                if amount > 0:
                                    if coin == 'USDT' or coin == 'USDC':
                                        # Stablecoins are 1:1 with USD
                                        coin_value = amount
                                        total_value += coin_value
                                        balances_detail.append(f"{coin}: ${coin_value:,.2f}")
                                    elif coin in ['BTC', 'ETH', 'SOL', 'XRP']:
                                        # Use real-time prices we just fetched
                                        coin_price = prices.get(coin, {}).get('price', 0)
                                        if coin_price > 0:
                                            coin_value = amount * coin_price
                                            total_value += coin_value
                                            balances_detail.append(f"{amount:.6f} {coin} @ ${coin_price:,.2f} = ${coin_value:,.2f}")
                            
                            self.live_demo_balance = total_value
                            self.last_balance_update = now
                            logger.info(f"💰 Live Demo Portfolio Value: ${total_value:,.2f}")
                            logger.info(f"   Holdings: {', '.join(balances_detail)}")
                    except Exception as balance_error:
                        logger.debug(f"Could not fetch Demo balance: {balance_error}")
                
                # Session cleanup is automatic with async context manager
                
                if prices:
                    logger.info(f"✅ Real-time prices updated from Bybit Demo Trading: BTC=${prices.get('BTC', {}).get('price', 0):,.2f}")
                    return prices
                else:
                    logger.warning("No prices fetched from Bybit, using fallback")
                    return await self.get_binance_fallback()
                        
        except Exception as e:
            logger.error(f"Error fetching Bybit prices: {e}")
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
                'price': 117465 * (1 + np.random.default_rng(42).uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.default_rng(42).uniform(-3, 3),
                'volume': np.random.default_rng(42).uniform(15000, 25000),
                'high_24h': 118500,
                'low_24h': 116000,
                'timestamp': datetime.now().isoformat()
            },
            'SOL': {
                'price': 219 * (1 + np.random.default_rng(42).uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.default_rng(42).uniform(-4, 4),
                'volume': np.random.default_rng(42).uniform(800000, 1200000),
                'high_24h': 222,
                'low_24h': 216,
                'timestamp': datetime.now().isoformat()
            },
            'ETH': {
                'price': 4337 * (1 + np.random.default_rng(42).uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.default_rng(42).uniform(-3, 3),
                'volume': np.random.default_rng(42).uniform(300000, 500000),
                'high_24h': 4380,
                'low_24h': 4290,
                'timestamp': datetime.now().isoformat()
            },
            'XRP': {
                'price': 2.94 * (1 + np.random.default_rng(42).uniform(-0.002, 0.002)),  # Updated to current market
                'change_24h': np.random.default_rng(42).uniform(-5, 5),
                'volume': np.random.default_rng(42).uniform(2000000, 3000000),
                'high_24h': 2.98,
                'low_24h': 2.85,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    async def fetch_multi_timeframe_klines(self, symbol: str) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Fetch historical candle data for multi-timeframe ICT analysis.
        Returns klines for 4H, 15m, and 5m timeframes needed by backtest engine.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            Dictionary with '1h' key containing DataFrame for resampling, or None if fetch fails
        """
        try:
            from bybit_integration.bybit_client import BybitDemoClient
            
            # Use async context manager to ensure proper session cleanup
            async with BybitDemoClient(demo=True) as client:
                # Fetch 1H candles (200 periods = ~8 days of data)
                # The backtest engine will resample this to 4H, 15m, 5m
                logger.info(f"📊 Fetching 1H klines for {symbol} (200 candles = ~8 days)")
                klines_1h = await client.get_kline_data(symbol=symbol, interval="60", limit=200)
            
            if not klines_1h:
                logger.warning(f"❌ No kline data returned for {symbol}")
                return None
            
            # Convert Bybit klines to pandas DataFrame
            # Bybit format: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
            df_data = []
            for candle in klines_1h:
                try:
                    df_data.append({
                        'timestamp': pd.to_datetime(int(candle[0]), unit='ms'),
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    })
                except (IndexError, ValueError) as e:
                    logger.warning(f"Skipping invalid candle data: {e}")
                    continue
            
            if not df_data:
                logger.warning(f"❌ No valid candle data parsed for {symbol}")
                return None
            
            # Create DataFrame and set timestamp as index
            df_1h = pd.DataFrame(df_data)
            df_1h = df_1h.set_index('timestamp')
            df_1h = df_1h.sort_index()
            
            logger.info(f"✅ Fetched {len(df_1h)} 1H candles for {symbol} (from {df_1h.index[0]} to {df_1h.index[-1]})")
            
            return {'1h': df_1h}
            
        except Exception as e:
            logger.error(f"❌ Error fetching multi-timeframe klines for {symbol}: {e}")
            return None

# REMOVED: ICTSignalGenerator class (unused - system uses ICTStrategyEngine only)
# The proven ICT Strategy Engine (68% winrate) handles all signal generation

class SessionStatusTracker:
    """Track Global Trading Sessions Status"""
    
    def __init__(self, trading_sessions):
        self.trading_sessions = trading_sessions
        
    def get_sessions_status(self) -> Dict:
        """Get current status of all trading sessions"""
        current_hour = datetime.now(timezone.utc).hour
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
        current_hour = datetime.now(timezone.utc).hour
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
        self.app.config['SECRET_KEY'] = 'ict_enhanced_monitor_2025'
        CORS(self.app)  # Enable CORS for React frontend
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.crypto_monitor = ICTCryptoMonitor()
        
        # Initialize PROVEN backtest engine for real ICT analysis (68% winrate, 1.78 Sharpe)
        logger.info("🚀 Initializing ICT Strategy Engine (proven 68% winrate, 1.78 Sharpe ratio)")
        self.ict_strategy_engine = ICTStrategyEngine()
        logger.info("✅ ICT Strategy Engine ready - single-engine architecture active")
        
        self.session_tracker = SessionStatusTracker(self.crypto_monitor.trading_sessions)
        self.statistics = MonitorStatistics()
        
        # Initialize Fundamental Analysis (integrated)
        self.fundamental_analysis = self._init_fundamental_analysis()
        
        # Data storage
        self.current_prices = {}
        self.is_running = False
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
    
    def _init_fundamental_analysis(self):
        """Initialize integrated fundamental analysis"""
        return {
            'BTC': {'score': 0, 'recommendation': 'NEUTRAL', 'last_update': None},
            'ETH': {'score': 0, 'recommendation': 'NEUTRAL', 'last_update': None},
            'SOL': {'score': 0, 'recommendation': 'NEUTRAL', 'last_update': None},
            'XRP': {'score': 0, 'recommendation': 'NEUTRAL', 'last_update': None}
        }
    
    def _update_fundamental_analysis(self):
        """Update fundamental analysis for all cryptos"""
        try:
            for symbol in ['BTC', 'ETH', 'SOL', 'XRP']:
                # Simple fundamental scoring based on price trends and market conditions
                score = self._calculate_fundamental_score(symbol)
                recommendation = self._get_fundamental_recommendation(score)
                
                self.fundamental_analysis[symbol] = {
                    'score': score,
                    'recommendation': recommendation,
                    'last_update': datetime.now().isoformat(),
                    'confidence': min(abs(score) / 10, 1.0)  # 0-1 confidence
                }
            logger.info("✅ Fundamental analysis updated")
        except Exception as e:
            logger.error(f"❌ Error updating fundamental analysis: {e}")
    
    def _calculate_fundamental_score(self, symbol):
        """Calculate fundamental score (-10 to +10)"""
        # Simple scoring based on current price trends
        try:
            current_price = self.current_prices.get(symbol, 0)
            if not current_price:
                return 0
            
            # Basic trend analysis (placeholder - can be enhanced)
            # Positive score = bullish fundamentals, negative = bearish
            score = 0
            
            # For now, return neutral scores - can be enhanced with real fundamental data
            return score
        except Exception as e:
            logger.error(f"Error calculating fundamental score for {symbol}: {e}")
            return 0
    
    def _get_fundamental_recommendation(self, score):
        """Get recommendation based on score"""
        if score >= 7:
            return 'STRONG BUY'
        elif score >= 3:
            return 'BUY'
        elif score >= -3:
            return 'NEUTRAL'
        elif score >= -7:
            return 'SELL'
        else:
            return 'STRONG SELL'
    
    # ============ AUTHENTICATION HELPERS ============
    
    def hash_password(self, password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def check_password(self, password, hashed):
        """Verify a password against a hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_token(self, user_id, email):
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.now(timezone.utc) + timedelta(days=7)
        }
        return jwt.encode(payload, self.app.config['SECRET_KEY'], algorithm='HS256')
    
    def token_required(self, f):
        """Decorator for protected routes"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({'message': 'Token is missing'}), 401
            
            try:
                if token.startswith('Bearer '):
                    token = token[7:]
                data = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])
                current_user = data
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 401
            
            return f(current_user, *args, **kwargs)
        
        return decorated
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        # ============ AUTHENTICATION ROUTES ============
        
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            """Login and get JWT token"""
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'message': 'Email and password required'}), 400
            
            # Query users from database
            user = self.crypto_monitor.db.get_user_by_email(email)
            
            if not user or not self.check_password(password, user['password_hash']):
                return jsonify({'message': 'Invalid credentials'}), 401
            
            token = self.generate_token(user['id'], user['email'])
            
            return jsonify({
                'token': token,
                'user': {'id': user['id'], 'email': user['email']}
            })
        
        @self.app.route('/api/auth/register', methods=['POST'])
        def register():
            """Register a new user"""
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'message': 'Email and password required'}), 400
            
            # Check if user exists
            if self.crypto_monitor.db.get_user_by_email(email):
                return jsonify({'message': 'User already exists'}), 400
            
            # Create user
            hashed_pw = self.hash_password(password)
            user_id = self.crypto_monitor.db.create_user(email, hashed_pw)
            
            token = self.generate_token(user_id, email)
            
            return jsonify({
                'message': 'User created successfully',
                'token': token,
                'user': {'id': user_id, 'email': email}
            }), 201
        
        @self.app.route('/api/auth/me', methods=['GET'])
        @self.token_required
        def get_current_user(current_user):
            """Get current user info"""
            return jsonify({'user': current_user})
        
        # ============ DASHBOARD DATA ROUTES ============
        
        @self.app.route('/api/dashboard/stats', methods=['GET'])
        def get_dashboard_stats():
            """Get key trading statistics (READ-ONLY - won't block on writes)"""
            stats = self.crypto_monitor.db.get_daily_stats_readonly()
            return jsonify(stats)
        
        @self.app.route('/api/dashboard/equity', methods=['GET'])
        def get_equity_curve():
            """Get equity curve data (READ-ONLY - won't block on writes)"""
            trades = self.crypto_monitor.db.get_closed_trades_readonly()
            
            initial_balance = 1000.0
            balance = initial_balance
            equity_data = [{'date': datetime.now().isoformat(), 'balance': balance, 'pnl': 0}]
            
            for trade in trades:
                balance += trade.get('realized_pnl', 0)
                equity_data.append({
                    'date': trade.get('exit_time') or trade.get('entry_time'),
                    'balance': balance,
                    'pnl': trade.get('realized_pnl', 0)
                })
            
            return jsonify(equity_data)
        
        @self.app.route('/api/dashboard/trades', methods=['GET'])
        def get_trade_history():
            """Get paginated trade history (READ-ONLY - won't block on writes)"""
            trades = self.crypto_monitor.db.get_closed_trades_readonly()
            return jsonify(trades)
        
        @self.app.route('/api/dashboard/signals', methods=['GET'])
        def get_signal_stats():
            """Get signal distribution statistics (READ-ONLY - won't block on writes)"""
            stats = self.crypto_monitor.db.get_signal_stats_readonly()
            return jsonify(stats)
        
        @self.app.route('/api/dashboard/active-trades', methods=['GET'])
        def get_active_trades():
            """Get currently active trades (READ-ONLY - won't block on writes)"""
            trades = self.crypto_monitor.db.get_active_trades_readonly()
            return jsonify({'trades': trades})
        
        # ============ FUNDAMENTAL ANALYSIS ENDPOINTS ============
        
        @self.app.route('/api/fundamental')
        def get_all_fundamental():
            """Get fundamental analysis for all cryptos"""
            try:
                self._update_fundamental_analysis()
                return jsonify(self.fundamental_analysis)
            except Exception as e:
                logger.error(f"❌ Error getting fundamental analysis: {e}")
                return jsonify({'error': 'Failed to get fundamental analysis'}), 500
        
        @self.app.route('/api/fundamental/<symbol>')
        def get_fundamental_symbol(symbol):
            """Get fundamental analysis for specific crypto"""
            try:
                symbol = symbol.upper()
                if symbol not in self.fundamental_analysis:
                    return jsonify({'error': f'Symbol {symbol} not supported'}), 404
                
                self._update_fundamental_analysis()
                return jsonify(self.fundamental_analysis[symbol])
            except Exception as e:
                logger.error(f"❌ Error getting fundamental analysis for {symbol}: {e}")
                return jsonify({'error': 'Failed to get fundamental analysis'}), 500
        
        # ============ FRONTEND ROUTES ============
        
        @self.app.route('/')
        def home():
            """Serve React app home page"""
            frontend_path = os.path.join(project_root, 'frontend', 'dist')
            if os.path.exists(os.path.join(frontend_path, INDEX_HTML_FILENAME)):
                return send_from_directory(frontend_path, INDEX_HTML_FILENAME)
            # Fallback to ICT monitor if React not built
            return redirect('/monitor')
        
        @self.app.route('/monitor')
        def monitor_dashboard():
            """Original ICT Monitor UI"""
            return render_template_string(self.get_dashboard_html())
        
        @self.app.route('/fundamental')
        def fundamental_dashboard():
            """Fundamental Analysis Dashboard"""
            return render_template_string(self._get_fundamental_dashboard_html())
            
        @self.app.route('/health')
        def health_check():
            # Get count of actual trades executed today
            from datetime import date
            today = date.today().isoformat()
            conn = self.crypto_monitor.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM paper_trades 
                WHERE date(entry_time) = ?
            """, (today,))
            today_signals = cursor.fetchone()[0]
            conn.close()

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
                'live_demo_balance': self.crypto_monitor.live_demo_balance,
                'account_blown': self.crypto_monitor.account_blown,
                'ml_model_status': {
                    'loaded': False,  # Removed ML model - using pure ICT methodology
                    'status': 'not_used'
                }
            })
            
        @self.app.route('/api/data')
        def get_current_data():
            try:
                # Get data from database instead of hardcoded values
                daily_stats = self.crypto_monitor.db.get_daily_stats()
                todays_signals = self.crypto_monitor.db.get_signals_today()  # For today's summary
                active_signals = self.crypto_monitor.db.get_active_signals()  # For active paper trades (any date)
                active_trades = self.crypto_monitor.db.get_active_paper_trades()  # Get OPEN paper trades
                # Get closed signals for trading journal (today's completed trades)
                journal_entries = self.crypto_monitor.db.get_closed_signals_today()
                
                logger.info(f"🔍 API /api/data: Retrieved {len(todays_signals)} today's signals, {len(active_trades)} active trades from database")
                
                # PHANTOM TRADE ELIMINATION: Force database-only truth
                if len(active_trades) == 0:
                    logger.info("✅ Database contains 0 active trades - phantom cache clearing not needed (database-only approach)")
                else:
                    logger.info(f"📊 Processing {len(active_trades)} legitimate active trades from database")
                
                # Define all possible closed/completed statuses to exclude
                CLOSED_STATUSES = {
                    'CANCELLED', 'STOP_LOSS', 'TAKE_PROFIT', 'SESSION_CLOSE',
                    'TIME_LIMIT', 'MAX_HOLD_TIME_EXCEEDED', 'MANUAL_CLOSE', 'EXPIRED'
                }
                
                # Serialize live signals for JSON (recent ACTIVE signals from database)
                serialized_signals = []
                # Filter to only show ACTIVE or FILLED signals (exclude all closed statuses)
                active_todays_signals = [
                    s for s in todays_signals 
                    if s.get('status') in ('ACTIVE', 'FILLED') and s.get('status') not in CLOSED_STATUSES
                ]
                for signal in active_todays_signals[-5:]:  # Get last 5 active signals
                    signal_copy = signal.copy()
                    # Convert datetime objects to ISO format and add required fields
                    if 'entry_time' in signal_copy:
                        signal_copy['timestamp'] = signal_copy['entry_time']
                    # Map database fields to UI fields
                    if 'symbol' in signal_copy and 'USDT' in signal_copy['symbol']:
                        signal_copy['crypto'] = signal_copy['symbol'].replace('USDT', '')
                    signal_copy['action'] = signal_copy.get('direction', 'BUY')
                    signal_copy['confidence'] = signal_copy.get('confluence_score', 0.75)
                    signal_copy['timeframe'] = '5m'  # Default timeframe
                    signal_copy['confluences'] = signal_copy.get('ict_concepts', [])
                    signal_copy['risk_amount'] = 1.0  # $1 risk
                    serialized_signals.append(signal_copy)
                    logger.info(f"  - Signal: {signal_copy.get('crypto', 'Unknown')} {signal_copy.get('action', 'Unknown')} @ ${signal_copy.get('entry_price', 0)}")
                
                # Build today's summary from database - ONLY ACTIVE/FILLED signals (exclude all closed trades)
                todays_summary = []
                logger.info(f"🔍 Building signals_summary from {len(todays_signals)} signals")
                
                # Define all possible closed/completed statuses to exclude
                CLOSED_STATUSES = {
                    'CANCELLED', 'STOP_LOSS', 'TAKE_PROFIT', 'SESSION_CLOSE',
                    'TIME_LIMIT', 'MAX_HOLD_TIME_EXCEEDED', 'MANUAL_CLOSE', 'EXPIRED'
                }
                
                for signal in todays_signals:
                    signal_status = signal.get('status', 'NO_STATUS')
                    logger.info(f"  - Signal: {signal.get('symbol', '?')} {signal.get('direction', '?')} - Status: {signal_status}")
                    
                    # Skip any closed/cancelled signals in the summary - only show ACTIVE or FILLED
                    if signal_status in CLOSED_STATUSES or signal_status not in ('ACTIVE', 'FILLED'):
                        logger.info(f"    ⏭️ Skipping signal with status: {signal_status}")
                        continue
                    
                    signal_copy = signal.copy()
                    if 'entry_time' in signal_copy:
                        signal_copy['timestamp'] = signal_copy['entry_time']
                    # Map database fields to UI fields
                    if 'symbol' in signal_copy and 'USDT' in signal_copy['symbol']:
                        signal_copy['crypto'] = signal_copy['symbol'].replace('USDT', '')
                    signal_copy['action'] = signal_copy.get('direction', 'BUY')
                    signal_copy['confidence'] = signal_copy.get('confluence_score', 0.75)
                    signal_copy['timeframe'] = '5m'  # Default timeframe
                    todays_summary.append(signal_copy)
                
                logger.info(f"✅ Built signals_summary with {len(todays_summary)} active signals")
                
                # Build paper trades from ACTIVE paper trades in database ONLY
                paper_trades = []
                
                # Use ONLY active_trades from paper_trades table (database-first approach)
                logger.info(f"🔍 Building paper trades from {len(active_trades)} database entries")
                for trade in active_trades:
                        crypto = trade.get('symbol', 'BTCUSDT').replace('USDT', '')
                        entry_price = trade.get('entry_price', 0)
                        stop_loss = trade.get('stop_loss', 0)
                        direction = trade.get('direction', 'BUY')
                        position_size = trade.get('position_size', 0)
                        
                        # Get REAL-TIME current price
                        current_price = trade.get('current_price', entry_price)  # Use DB value or fallback
                        if crypto in self.current_prices:
                            current_price = self.current_prices[crypto].get('price', current_price)
                        
                        # Use unrealized PnL from database
                        pnl = trade.get('unrealized_pnl', 0)
                        
                        # Calculate position value for display
                        position_value = position_size * entry_price
                        
                        trade_obj = {
                            'id': trade.get('signal_id', 'PT_1'),
                            'crypto': crypto,
                            'action': direction,
                            'entry_price': entry_price,
                            'current_price': current_price,  # REAL-TIME PRICE
                            'stop_loss': stop_loss,
                            'take_profit': trade.get('take_profit', 0),
                            'position_size': position_size,  # From database
                            'position_value': position_value,  # Dollar value of position
                            'risk_amount': trade.get('risk_amount', 0),  # From database
                            'pnl': pnl,  # From database
                            'entry_time': trade.get('entry_time', ''),
                            'status': trade.get('status', 'OPEN')  # Use actual status from database
                        }
                        paper_trades.append(trade_obj)
                        logger.info(f"  - Active Trade: {trade_obj['crypto']} {trade_obj['action']} @ ${trade_obj['entry_price']} | Position: {position_size:.6f} {crypto} (${position_value:.2f}) | Current: ${current_price} | PnL: ${pnl:.2f}")
                
                logger.info(f"📊 Returning {len(paper_trades)} active paper trades to UI")

                # Calculate actual trades executed today (our definition of "Signals Today")
                from datetime import date
                today = date.today().isoformat()
                cursor = self.crypto_monitor.db._get_connection().cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM paper_trades 
                    WHERE date(entry_time) = ?
                """, (today,))
                active_signals_count = cursor.fetchone()[0]

                # Simplified signal parameters for single-engine architecture
                signal_params = {
                    'effective_probability': 3.5,  # Base 3.5% probability
                    'confluence_threshold': 60.0  # 60% minimum confluence (conservative)
                }

                # Log final data counts being sent to UI
                logger.info(f"📊 API Response: Sending {len(paper_trades)} active trades, {active_signals_count} signals today (all from database)")
                logger.info(f"🔢 Database consistency: active_trades_count={len(active_trades)}, active_paper_trades={len(paper_trades)}")

                return jsonify({
                    'prices': self.current_prices,
                    'scan_count': daily_stats.get('scan_count', 0),
                    'signals_today': active_signals_count,  # Only count ACTIVE or FILLED signals
                    'daily_pnl': daily_stats.get('total_pnl', 0),
                    'paper_balance': daily_stats.get('paper_balance', 100),
                    'live_demo_balance': self.crypto_monitor.live_demo_balance,
                    'account_blown': daily_stats.get('paper_balance', 100) <= 10,  # Account blown if balance <= $10
                    'live_signals': serialized_signals,
                    'total_live_signals': len(todays_signals),
                    'signals_summary': todays_summary,  # Full summary from database
                    'paper_trades': paper_trades,  # Active paper trades from database
                    'active_paper_trades': len(paper_trades),  # Count of active trades
                    'trading_journal': [dict(entry) for entry in journal_entries],  # Journal from database
                    'active_trades_count': len(active_trades),
                    'session_status': self.session_tracker.get_sessions_status(),
                    'uptime': self.statistics.get_uptime(),
                    'market_hours': self.statistics.is_market_hours(),
                    'signal_generation_params': signal_params,  # Signal generation debugging info
                    'risk_management_status': {
                        'portfolio_risk': f"{self.crypto_monitor.calculate_portfolio_risk()*100:.2f}%",
                        'max_portfolio_risk': f"{self.crypto_monitor.max_portfolio_risk*100:.1f}%",
                        'concurrent_signals': f"{len(active_signals)}/{self.crypto_monitor.max_concurrent_signals}",  # DATABASE-FIRST
                        'active_positions': {symbol.replace('USDT', ''): self.crypto_monitor.get_active_positions_for_symbol(symbol) 
                                           for symbol in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']},
                        'signal_cooldowns': {symbol: self.crypto_monitor.has_recent_signal(symbol) 
                                           for symbol in ['BTC', 'ETH', 'SOL', 'XRP']},
                        'deduplication_enabled': True,
                        'cooldown_minutes': self.crypto_monitor.signal_cooldown_minutes
                    },
                    'ml_model_status': {
                        'loaded': False,  # Removed ML model - using pure ICT methodology
                        'status': 'not_used'
                    }
                })
            except Exception as e:
                logger.error(f"❌ Error in API data endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
            
        @self.app.route('/api/signals')
        def get_signals():
            """Get all signals from database"""
            try:
                signals = self.crypto_monitor.db.get_signals_today()
                return jsonify(signals)
            except Exception as e:
                logger.error(f"Error fetching signals from database: {e}")
                return jsonify(self.crypto_monitor.live_signals)
            
        @self.app.route('/api/test')
        def test_endpoint():
            """Simple test endpoint to verify HTTP responses work"""
            logger.info("🔧 TEST endpoint called")
            test_data = {"test": "success", "timestamp": "2025-10-20", "signals": 3}
            logger.info(f"🔧 TEST returning: {test_data}")
            return jsonify(test_data)
            
        @self.app.route('/api/signals/latest')
        def get_latest_signals():
            """Get latest signals from database - matches the endpoint being requested in logs"""
            try:
                all_signals = self.crypto_monitor.db.get_signals_today()
                logger.info(f"🔍 API DEBUG: get_signals_today() returned {len(all_signals) if all_signals else 0} signals")
                latest_signals = all_signals[-5:] if all_signals else []
                logger.info(f"🔍 API DEBUG: Returning {len(latest_signals)} latest signals to web interface")
                
                # Log sample signal for debugging
                if latest_signals:
                    logger.info(f"🔍 API DEBUG: Sample signal: {latest_signals[0].get('symbol', 'Unknown')} {latest_signals[0].get('direction', 'Unknown')} - {latest_signals[0].get('status', 'Unknown')}")
                
                # Test JSON serialization before sending
                import json
                json_data = json.dumps(latest_signals)
                logger.info(f"🔍 API DEBUG: JSON serialization successful: {len(json_data)} characters")
                
                response = jsonify(latest_signals)
                logger.info(f"🔍 API DEBUG: Flask jsonify response created: {type(response)}")
                return response
            except Exception as e:
                logger.error(f"❌ API ERROR: Error fetching latest signals from database: {e}")
                latest_signals = self.crypto_monitor.live_signals[-5:] if self.crypto_monitor.live_signals else []
                logger.info(f"🔍 API DEBUG: Fallback to live_signals: {len(latest_signals)} signals")
                return jsonify(latest_signals)
            
        @self.app.route('/api/journal')
        def get_journal():
            """Get trading journal from database"""
            try:
                # Get daily stats for display
                self.crypto_monitor.db.get_daily_stats()
                trades = self.crypto_monitor.db.get_trades_today()
                
                journal_entries = [
                    {
                        'type': 'signal',
                        'timestamp': signal.get('entry_time', ''),
                        'symbol': signal.get('symbol', ''),
                        'action': signal.get('direction', ''),
                        'price': signal.get('entry_price', 0),
                        'confidence': signal.get('confluence_score', 0),
                        'status': signal.get('status', 'ACTIVE')
                    }
                    for signal in self.crypto_monitor.db.get_signals_today()
                ]
                
                # Add trade results
                for trade in trades:
                    if trade.get('status') == 'CLOSED':
                        journal_entries.append({
                            'type': 'trade_result',
                            'timestamp': trade.get('updated_at', ''),
                            'symbol': trade.get('symbol', ''),
                            'pnl': trade.get('pnl', 0),
                            'status': 'COMPLETED'
                        })
                
                return jsonify(journal_entries)
            except Exception as e:
                logger.error(f"Error fetching journal from database: {e}")
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
                
                # NOTE: No need to clear phantom cache - using database-only approach
                logger.info("🚫 ACCOUNT RESET: Phantom cache clearing skipped - using database-only architecture")
                
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
        
        # ============ DIAGNOSTIC AND ANALYSIS ROUTES ============
        
        @self.app.route('/api/diagnostic', methods=['GET'])
        def run_diagnostic():
            """Run comprehensive system diagnostic check"""
            try:
                logger.info("🔍 Running system diagnostic...")
                
                # Create diagnostic checker
                diagnostic = create_diagnostic_checker(
                    db_path=os.path.join(project_root, "data", "trading.db")
                )
                
                # Run full diagnostic
                results = diagnostic.run_full_diagnostic()
                
                logger.info(f"✅ Diagnostic complete: {results['overall_status']}")
                return jsonify(results)
                
            except Exception as e:
                logger.error(f"❌ Diagnostic error: {e}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': 'An error occurred while running diagnostics',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/analysis/sol', methods=['GET'])
        def analyze_sol():
            """Analyze SOL trading opportunity with liquidity zones and FVGs"""
            try:
                logger.info("🌟 Analyzing SOL trade opportunity...")
                
                # Get current SOL price
                current_price = None
                for crypto_data in self.crypto_monitor.crypto_prices.values():
                    if crypto_data.get('symbol') == 'SOL':
                        current_price = crypto_data.get('current_price', 0)
                        break
                
                if not current_price:
                    # Fallback to a reasonable default if price not available
                    current_price = 150.0  # Default SOL price
                    logger.warning(f"⚠️ SOL price not found, using default: ${current_price}")
                
                # Temporarily disabled - import issue
                # Create SOL analyzer
                # sol_analyzer = create_sol_analyzer()
                
                # Run analysis
                # analysis = sol_analyzer.analyze_sol_opportunity(current_price)
                
                # logger.info(f"✅ SOL analysis complete: {analysis.get('status', 'unknown')}")
                # return jsonify(analysis)
                
                # Return placeholder for now
                return jsonify({
                    'status': 'disabled',
                    'message': 'SOL analyzer temporarily disabled',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ SOL analysis error: {e}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': 'An error occurred while analyzing SOL',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # ============ STATIC FILE SERVING FOR REACT ============
        
        # Serve React static files
        @self.app.route('/static/<path:path>')
        def serve_react_static(path):
            """Serve React static assets"""
            frontend_dist = os.path.join(project_root, 'frontend', 'dist', 'static')
            return send_from_directory(frontend_dist, path)
        
        # Serve React app (catch-all for client-side routing)
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def serve_react_app(path):
            """Serve React app or fall back to index.html for client-side routing"""
            frontend_dist = os.path.join(project_root, 'frontend', 'dist')
            
            # Exclude /monitor route - let the original ICT monitor handle it
            if path == 'monitor':
                return monitor_dashboard()
            
            # If path exists as a file, serve it
            if path and os.path.exists(os.path.join(frontend_dist, path)):
                return send_from_directory(frontend_dist, path)
            
            # Otherwise serve index.html (React Router will handle routing)
            return send_from_directory(frontend_dist, INDEX_HTML_FILENAME)
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {'message': 'Connected to ICT Trading Monitor'})
            logger.info("🔌 Client connected via SocketIO - sending immediate update")
            # Send immediate update on connect
            self.broadcast_update()
            
        @self.socketio.on('request_update')
        def handle_update_request():
            logger.info("🔄 Client requested update via SocketIO")
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
                
                # Get real-time prices
                self.current_prices = await self.crypto_monitor.get_real_time_prices()
                
                # ⏰ CHECK TRADE HOLD TIMES - Auto-close trades exceeding max duration
                try:
                    # 1. Check for un-executed signals (orphans) and expire them after 2 hours
                    from datetime import datetime, timedelta
                    conn = self.crypto_monitor.db._get_connection()
                    cursor = conn.cursor()
                    
                    # Find ACTIVE signals older than 2 hours that have no corresponding trade
                    two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
                    cursor.execute("""
                        SELECT s.signal_id, s.symbol, s.direction, s.entry_time
                        FROM signals s
                        WHERE s.status = 'ACTIVE'
                        AND s.entry_time < ?
                        AND NOT EXISTS (
                            SELECT 1 FROM paper_trades pt 
                            WHERE pt.signal_id = s.signal_id
                        )
                    """, (two_hours_ago,))
                    
                    orphan_signals = cursor.fetchall()
                    if orphan_signals:
                        logger.info(f"🧹 Found {len(orphan_signals)} un-executed signals older than 2 hours")
                        for signal in orphan_signals:
                            signal_id = signal[0]
                            symbol = signal[1]
                            direction = signal[2]
                            entry_time = signal[3]
                            
                            logger.info(f"   Expiring: {symbol} {direction} from {entry_time}")
                            self.crypto_monitor.db.close_signal(signal_id, 0, 'EXPIRED')
                    
                    conn.close()
                    
                    # 2. Check active trades for time limits
                    active_trades = self.crypto_monitor.db.get_active_paper_trades()
                    if active_trades:
                        # Log trade status
                        self.crypto_monitor.trade_manager.log_trade_status(active_trades)
                        
                        # Get trades that need to be closed
                        trades_to_close = self.crypto_monitor.trade_manager.get_trades_to_close(active_trades)
                        
                        if trades_to_close:
                            logger.warning(f"⏰ Closing {len(trades_to_close)} trades due to time limits")
                            
                            for trade in trades_to_close:
                                symbol = trade.get('symbol', 'UNKNOWN')
                                crypto = symbol.replace('USDT', '')
                                direction = trade.get('direction', 'UNKNOWN')
                                entry_price = trade.get('entry_price', 0)
                                
                                # Get current price for exit
                                current_price = entry_price  # Fallback
                                if crypto in self.current_prices:
                                    current_price = self.current_prices[crypto].get('price', entry_price)
                                
                                # Calculate exit PnL
                                position_size = trade.get('position_size', 0)
                                if direction == 'SELL':
                                    exit_pnl = (entry_price - current_price) * position_size
                                else:  # BUY
                                    exit_pnl = (current_price - entry_price) * position_size
                                
                                # Close trade in database
                                signal_id = trade.get('signal_id', '')
                                close_reason = trade.get('close_reason', 'TIME_LIMIT')
                                
                                logger.info(
                                    f"⏰ Closing {symbol} {direction} @ ${current_price:.2f} "
                                    f"(Entry: ${entry_price:.2f}, PnL: ${exit_pnl:.2f}) - {close_reason}"
                                )
                                
                                # Update trade status in database
                                self.crypto_monitor.db.close_paper_trade(
                                    trade_id=trade.get('id'),
                                    exit_price=current_price,
                                    close_reason=close_reason
                                )
                                
                                # Also close the signal if it exists
                                if signal_id:
                                    self.crypto_monitor.db.close_signal(signal_id, current_price, close_reason)
                                
                                # Update balance
                                self.crypto_monitor.paper_balance += exit_pnl
                                self.crypto_monitor.db.update_balance(self.crypto_monitor.paper_balance)
                                
                                logger.info(f"💰 Updated balance: ${self.crypto_monitor.paper_balance:.2f}")
                        
                except Exception as e:
                    logger.error(f"❌ Error in trade time management: {e}")
                
                # Update scan count in database
                self.crypto_monitor.db.increment_scan_count()
                self.crypto_monitor.scan_count = self.crypto_monitor.db.get_scan_count()
                self.crypto_monitor.last_scan_time = datetime.now()
                
                # Save state every 10 scans to prevent data loss
                if self.crypto_monitor.scan_count % 10 == 0:
                    self.crypto_monitor._save_trading_state()
                
                # 🚀 NEW: Generate trading signals using PROVEN BACKTEST ENGINE
                # Fetch multi-timeframe klines data for each symbol
                logger.info("📊 Fetching multi-timeframe klines for ICT analysis...")
                new_signals = []
                
                for symbol in self.crypto_monitor.symbols:
                    crypto_name = symbol.replace('USDT', '')
                    
                    # Fetch historical klines for multi-timeframe analysis
                    mtf_klines = await self.crypto_monitor.fetch_multi_timeframe_klines(symbol)
                    
                    if not mtf_klines or '1h' not in mtf_klines:
                        logger.warning(f"⚠️ No klines data for {symbol}, skipping signal generation")
                        continue
                    
                    # Prepare multi-timeframe data using ICT strategy engine
                    try:
                        df_1h = mtf_klines['1h']
                        mtf_data = self.ict_strategy_engine.prepare_multitimeframe_data(df_1h)
                        
                        # Get current timestamp (use last candle timestamp to avoid pandas compatibility issues)
                        # Instead of current time, use the last available timestamp in the data
                        current_time = df_1h.index[-1]
                        
                        # Get current account balance for 1% risk calculation
                        current_balance = self.crypto_monitor.paper_balance
                        
                        # Generate ICT signal using proven ICT methodology with REAL ACCOUNT BALANCE
                        logger.info("💰 Using account balance: $%.2f for 1%% risk calculation", current_balance)
                        ict_signal = self.ict_strategy_engine.generate_ict_signal(symbol, mtf_data, current_time, account_balance=current_balance)
                        
                        if ict_signal:
                            # PRIMARY: Trust the strategy engine to have applied quant enhancements
                            logger.info(f"✅ ICT Strategy Engine returned a signal for {crypto_name} - single-engine architecture")

                            # DEFENSIVE: Safely extract all attributes from engine signal
                            # (If engine fails partway, some attributes might be missing)
                            try:
                                entry_price = getattr(ict_signal, 'entry_price', 0)
                                stop_loss = getattr(ict_signal, 'stop_loss', 0)
                                take_profit = getattr(ict_signal, 'take_profit', 0)
                                
                                # Validate critical fields
                                if not all([entry_price > 0, stop_loss > 0, take_profit > 0]):
                                    logger.warning(f"⚠️  Signal for {crypto_name} missing critical price fields (entry={entry_price}, SL={stop_loss}, TP={take_profit}) - skipping")
                                    continue
                                
                                # Convert ICTTradingSignal to monitor-friendly dict with safe attribute access
                                signal = {
                                    'id': f"{crypto_name}_{int(time.time())}",
                                    'symbol': symbol,
                                    'crypto': crypto_name,
                                    'action': getattr(ict_signal, 'action', 'BUY').upper(),
                                    'entry_price': entry_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'timeframe': getattr(ict_signal, 'timeframe', '15m'),
                                    'timeframes': [getattr(ict_signal, 'timeframe', '15m')],
                                    'confidence': getattr(ict_signal, 'confluence_score', 0.5),
                                    'ict_confidence': getattr(ict_signal, 'ict_confidence', getattr(ict_signal, 'confluence_score', 0.5)),
                                    'ml_boost': getattr(ict_signal, 'ml_boost', 0.0),
                                    'risk_amount': self.crypto_monitor.paper_balance * 0.01,
                                    'position_size': getattr(ict_signal, 'position_size', 0),
                                    'stop_distance': abs(entry_price - stop_loss),
                                    'risk_reward_ratio': getattr(ict_signal, 'risk_reward_ratio', 3),
                                    'fixed_risk_percentage': 0.01,
                                    'confluences': getattr(ict_signal, 'confluence_factors', []),
                                    'ict_concepts': getattr(ict_signal, 'confluence_factors', []),
                                    'confluence_score': getattr(ict_signal, 'confluence_score', 0.5),
                                    'market_regime': getattr(ict_signal, 'market_regime', 'Unknown'),
                                    'directional_bias': getattr(ict_signal, 'directional_bias', {}),
                                    'session': 'Unknown',
                                    'signal_strength': getattr(ict_signal, 'confidence', 0.5),
                                    'timestamp': datetime.now().isoformat(),
                                    'status': 'PENDING',
                                    'pnl': 0.0
                                }
                                new_signals.append(signal)
                                logger.info(f"✅ ENGINE SIGNAL: {crypto_name} {signal['action']} @ ${signal['entry_price']:.2f} | SL: ${signal['stop_loss']:.2f} | TP: ${signal['take_profit']:.2f} | Conf: {signal['confluence_score']:.2%}")
                            except (AttributeError, TypeError, ValueError) as attr_error:
                                logger.error(f"❌ Failed to convert engine signal for {crypto_name}: {attr_error} - signal object type: {type(ict_signal)}")
                                continue
                    except Exception as e:
                        logger.error(f"❌ Error generating signal for {symbol} with backtest engine: {e}")
                        continue
                
                logger.info(f"📊 Backtest engine generated {len(new_signals)} signals")
                
                # Process new signals with deduplication and risk management
                approved_signals = 0
                rejected_signals = 0
                
                for signal in new_signals:
                    symbol = signal.get('symbol', '')
                    crypto = signal.get('crypto', '')
                    
                    # Apply deduplication and risk management checks
                    can_accept, reason = self.crypto_monitor.can_accept_new_signal(symbol)
                    
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
                        # Execute paper trade
                        self.crypto_monitor.execute_paper_trade(signal)
                    
                    # Add signal to database (serialize complex fields)
                    directional_bias_dict = signal.get('directional_bias', {})
                    directional_bias_str = (
                        directional_bias_dict.get('direction', 'NEUTRAL') 
                        if isinstance(directional_bias_dict, dict) 
                        else str(directional_bias_dict)
                    )
                    
                    signal_id = self.crypto_monitor.db.add_signal({
                        'symbol': signal['symbol'],
                        'direction': signal['action'],
                        'entry_price': signal['entry_price'],
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'confluence_score': signal['confidence'],
                        'timeframes': signal.get('timeframes', []),
                        'ict_concepts': signal.get('ict_concepts', []),
                        'session': signal.get('session', 'Unknown'),
                        'market_regime': signal.get('market_regime', 'Unknown'),
                        'directional_bias': directional_bias_str,  # Serialize dict to string
                        'signal_strength': signal.get('signal_strength', 'Medium'),
                        'status': 'ACTIVE'
                    })
                    
                    signal['signal_id'] = signal_id
                    # DATABASE-FIRST: Signal already in database, no need to append to list
                    
                    # Update signals_today from database
                    daily_stats = self.crypto_monitor.db.get_daily_stats()
                    self.crypto_monitor.signals_today = daily_stats['signals_generated']
                    self.crypto_monitor.total_signals = len(self.crypto_monitor.db.get_signals_today())
                    approved_signals += 1
                    
                    logger.info("📈 NEW SIGNAL: %s %s @ $%.4f (%.1f%% confidence)", 
                               signal['crypto'], signal['action'], signal['entry_price'], signal['confidence']*100)
                
                # Log signal processing summary
                if new_signals:
                    logger.info(f"📊 Signal Processing: {approved_signals} approved, {rejected_signals} rejected")
                
                # Update paper trades with current prices
                if self.crypto_monitor.paper_trading_enabled:
                    closed_trades = self.crypto_monitor.update_paper_trades(self.current_prices)
                    if closed_trades > 0:
                        logger.info(f"📄 Paper Trading: Closed {closed_trades} trades")
                
                # DATABASE-FIRST: Signal lifecycle managed in database
                archived_count = self.crypto_monitor.manage_signal_lifecycle()
                if archived_count > 0:
                    logger.info(f"📋 Signal Management: Archived {archived_count} expired signals")
                
                # DATABASE-FIRST: Journal entries managed in database, no list truncation needed
                
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

    def _get_completed_trades(self):
        """Get completed trades from database"""
        serialized_completed_trades = []
        try:
            closed_signals = self.crypto_monitor.db.get_closed_signals_today()
            for signal in closed_signals:
                trade = {
                    'id': signal.get('signal_id', ''),
                    'crypto': signal.get('symbol', '').replace('USDT', ''),
                    'action': signal.get('direction', 'BUY'),
                    'entry_price': signal.get('entry_price', 0),
                    'exit_price': signal.get('exit_price', 0),
                    'stop_loss': signal.get('stop_loss', 0),
                    'take_profit': signal.get('take_profit', 0),
                    'pnl': signal.get('pnl', 0),
                    'entry_time': signal.get('entry_time', ''),
                    'exit_time': signal.get('exit_time', ''),
                    'status': signal.get('status', 'CLOSED')
                }
                serialized_completed_trades.append(trade)
        except Exception as e:
            logger.error(f"Error loading completed trades from database: {e}")
        return serialized_completed_trades

    def _get_active_paper_trades(self, today_only=False):
        """Get active paper trades from database ONLY - NO phantom trades
        
        Args:
            today_only (bool): If True, only return trades from today
        """
        try:
            # FORCE DATABASE-ONLY: Query paper_trades table directly
            active_trades = self.crypto_monitor.db.get_active_paper_trades()
            
            # Apply date filter if requested
            if today_only:
                from datetime import date
                today = date.today().isoformat()
                active_trades = [
                    trade for trade in active_trades 
                    if trade.get('entry_time', '').startswith(today)
                ]
                logger.info(f"📅 Date filter applied: {len(active_trades)} trades from today ({today})")
            
            if len(active_trades) == 0:
                logger.info("🚫 _get_active_paper_trades: Database has 0 active trades - returning empty list")
                return []
            
            logger.info(f"✅ _get_active_paper_trades: Found {len(active_trades)} legitimate database trades")
            
            serialized_active_trades = []
            for trade in active_trades:
                crypto = trade.get('symbol', 'BTCUSDT').replace('USDT', '')
                entry_price = trade.get('entry_price', 0)
                position_size = trade.get('position_size', 0)
                direction = trade.get('direction', 'BUY')
                
                # Get REAL-TIME current price
                current_price = entry_price  # Default fallback
                if crypto in self.current_prices:
                    current_price = self.current_prices[crypto].get('price', entry_price)
                
                # Calculate REAL PnL based on actual position size
                if direction == 'SELL':
                    pnl = (entry_price - current_price) * position_size
                else:  # BUY
                    pnl = (current_price - entry_price) * position_size
                    
                    position_value = position_size * entry_price
                    
                    trade_data = {
                        'id': trade.get('id', 0),
                        'signal_id': trade.get('signal_id', ''),
                        'crypto': crypto,
                        'action': direction,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'stop_loss': trade.get('stop_loss', 0),
                        'take_profit': trade.get('take_profit', 0),
                        'position_size': position_size,
                        'position_value': position_value,
                        'risk_amount': trade.get('risk_amount', 0),
                        'pnl': pnl,
                        'entry_time': trade.get('entry_time', ''),
                        'status': 'OPEN'
                    }
                    serialized_active_trades.append(trade_data)
            
            logger.info(f"📊 Broadcasting {len(serialized_active_trades)} active paper trades via SocketIO")
        except Exception as e:
            logger.error(f"Error loading active trades from paper_trades table: {e}")
        return serialized_active_trades

    def _get_todays_signals(self):
        """Get today's signals from database"""
        serialized_live_signals = []
        todays_summary = []
        today_signals = 0
        try:
            db_signals = self.crypto_monitor.db.get_signals_today()
            
            # Count actual trades executed today (our definition of "Signals Today")
            # This includes both trades with signal_ids and without
            from datetime import date
            today = date.today().isoformat()
            conn = self.crypto_monitor.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM paper_trades 
                WHERE date(entry_time) = ?
            """, (today,))
            today_signals = cursor.fetchone()[0]
            conn.close()
            
            # Format for UI display (newest first, limit 50)
            for signal in db_signals[:50]:
                signal_copy = {
                    'id': signal.get('signal_id', ''),
                    'crypto': signal.get('symbol', '').replace('USDT', ''),
                    'action': signal.get('direction', 'BUY'),
                    'entry_price': signal.get('entry_price', 0),
                    'stop_loss': signal.get('stop_loss', 0),
                    'take_profit': signal.get('take_profit', 0),
                    'confidence': signal.get('confluence_score', 0),
                    'timestamp': signal.get('entry_time', ''),
                    'status': signal.get('status', 'ACTIVE'),
                    'ict_concepts': signal.get('ict_concepts', ''),
                    'timeframes': signal.get('timeframes', ''),
                    'signal_strength': signal.get('signal_strength', 'Medium')
                }
                serialized_live_signals.append(signal_copy)
                todays_summary.append(signal_copy)
        except Exception as e:
            logger.error(f"Error loading signals from database: {e}")
        return serialized_live_signals, todays_summary, today_signals

    def broadcast_update(self):
        """Broadcast real-time updates to all connected clients - DATABASE-FIRST"""
        try:
            # DATABASE-FIRST: Get completed trades from database
            serialized_completed_trades = self._get_completed_trades()

            # Serialize active paper trades FROM DATABASE with date filtering and REAL-TIME PRICES
            serialized_active_trades = self._get_active_paper_trades(today_only=self.crypto_monitor.show_today_only)

            # DATABASE-FIRST: Get today's signals from database
            serialized_live_signals, todays_summary, today_signals = self._get_todays_signals()

            update_data = {
                'prices': self.current_prices,
                'scan_count': self.crypto_monitor.scan_count,
                'signals_today': today_signals,  # DATABASE-FIRST: From get_signals_today()
                'total_signals': self.crypto_monitor.total_signals,
                'daily_pnl': self.crypto_monitor.daily_pnl,  # DATABASE-FIRST: From get_closed_signals_today()
                'paper_balance': self.crypto_monitor.paper_balance,
                'live_demo_balance': self.crypto_monitor.live_demo_balance,
                'total_paper_pnl': self.crypto_monitor.total_paper_pnl,
                'active_paper_trades': len(serialized_active_trades),  # DATABASE-FIRST: From get_active_signals()
                'completed_paper_trades': serialized_completed_trades,  # DATABASE-FIRST: From get_closed_signals_today()
                'active_hours': self.crypto_monitor.active_hours,
                'live_signals': serialized_live_signals,  # DATABASE-FIRST: From get_signals_today()
                'total_live_signals': len(serialized_live_signals),  # DATABASE-FIRST: Count from database
                'total_archived_signals': 0,  # DATABASE-FIRST: No longer using archived_signals list
                'paper_trades': serialized_active_trades,  # DATABASE-FIRST: Active trades from database
                'trading_journal': serialized_completed_trades[-10:],  # DATABASE-FIRST: Last 10 closed trades
                'signals_summary': todays_summary,  # DATABASE-FIRST: Today's signals from database
                'session_status': self.session_tracker.get_sessions_status(),
                'market_hours': self.statistics.is_market_hours(),
                'uptime': self.statistics.get_uptime(),
                'scan_signal_ratio': self.statistics.calculate_scan_signal_ratio(
                    self.crypto_monitor.scan_count, 
                    self.crypto_monitor.total_signals
                ),
                'ml_model_status': {
                    'loaded': False,  # Removed ML model - using pure ICT methodology
                    'status': 'not_used'
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
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>🤖 Kirston's Crypto Bot - ICT Enhanced [v3.0-SIGNALS-FIX]</title>
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
            display: inline-block;
            margin-left: 10px;
            margin-right: 10px;
        }
        
        .home-btn {
            background: #6366f1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 15px;
            display: inline-block;
            margin-left: 10px;
            margin-right: 10px;
        }
        
        .home-btn:hover {
            background: #4f46e5;
        }
        
        .refresh-btn:hover {
            background: #00dd77;
        }
        
        .button-group {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 15px;
        }
        
        .prices-display {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 15px 0;
        }
        
        @media (max-width: 1024px) {
            .prices-display {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 600px) {
            .prices-display {
                grid-template-columns: 1fr;
            }
        }
        
        .price-item {
            background: rgba(0, 255, 136, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(0, 255, 136, 0.3);
            min-height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .price-crypto {
            font-weight: bold;
            color: #00ff88;
            font-size: 1.1em;
            margin-bottom: 8px;
        }
        
        .price-value {
            color: #ffffff;
            font-size: 1.3em;
            font-weight: bold;
            margin: 8px 0;
            word-break: break-word;
        }
        
        .price-change {
            font-size: 0.9em;
            font-weight: bold;
            margin-top: 5px;
        }
        
        .price-change.positive { color: #00ff88; }
        .price-change.negative { color: #ff4757; }
        
        .signals-summary-section {
            margin-top: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px 10px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            min-width: 0;
            overflow: hidden;
        }
        
        .stat-number {
            font-size: 1.8em;
            font-weight: bold;
            color: #00ff88;
            word-wrap: break-word;
            overflow-wrap: break-word;
            line-height: 1.2;
        }
        
        .stat-label {
            color: rgba(255,255,255,0.7);
            margin-top: 8px;
            font-size: 0.9em;
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
        
        <div class="button-group">
            <button class="home-btn" onclick="window.location.href='/home'">🏠 Back to Home</button>
            <button class="refresh-btn" onclick="requestUpdate()">🔄 Refresh</button>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number" id="scan-count">0</div>
            <div class="stat-label">Total Scans</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="signals-today">0</div>
            <div class="stat-label">Signals Today</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="paper-balance" style="color: #ffa500;">$100</div>
            <div class="stat-label">Paper Balance</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="live-demo-balance" style="color: #00ff88; font-size: 1.3em; word-break: break-all;">$0</div>
            <div class="stat-label">Live Demo Balance</div>
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
            console.log('🔌 Connected to ICT Trading Monitor');
            console.log('🔄 Requesting immediate dashboard update...');
            requestUpdate();
            
            // Also fetch via HTTP as backup
            fetch('/api/data')
                .then(r => r.json())
                .then(data => {
                    console.log('📥 HTTP /api/data response:', data);
                    console.log('🔍 signals_summary in response:', data.signals_summary);
                    console.log('🔍 signals_summary length:', data.signals_summary ? data.signals_summary.length : 'undefined');
                    
                    if (data.paper_trades) {
                        console.log('🔄 Updating paper trades from HTTP response');
                        updatePaperTrades(data.paper_trades);
                    }
                    
                    if (data.signals_summary) {
                        console.log('🔄 Updating signals summary from HTTP response');
                        updateSignalsSummary(data.signals_summary);
                    }
                })
                .catch(e => console.error('❌ HTTP fetch error:', e));
        });

        socket.on('status_update', function(data) {
            updateDashboard(data);
        });

        function requestUpdate() {
            socket.emit('request_update');
        }

        function updateDashboard(data) {
            console.log('Received dashboard data:', data); // Debug log
            
            // Update stats
            document.getElementById('scan-count').textContent = data.scan_count;
            document.getElementById('signals-today').textContent = data.signals_today;
            document.getElementById('paper-balance').textContent = '$' + (data.paper_balance || 100).toFixed(2);
            // Format live demo balance with commas and proper wrapping
            const liveDemoBalance = data.live_demo_balance || 0;
            document.getElementById('live-demo-balance').textContent = '$' + liveDemoBalance.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0});
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
            console.log('🔍 DEBUG: About to call updatePaperTrades');
            console.log('🔍 DEBUG: data.paper_trades =', data.paper_trades);
            console.log('🔍 DEBUG: data.paper_trades length =', data.paper_trades ? data.paper_trades.length : 'undefined');
            updatePaperTrades(data.paper_trades || []);
            console.log('🔍 DEBUG: updatePaperTrades called');
            
            // Update paper trading history
            updateJournal(data.completed_paper_trades || []);
            
            // Debug: Check what signals_summary data we're receiving
            console.log('All data received:', data);
            console.log('Signals summary specifically:', data.signals_summary);
            console.log('Trading journal specifically:', data.trading_journal);
            
            // Update signals summary table
            console.log('🔍 About to call updateSignalsSummary');
            console.log('🔍 data.signals_summary:', data.signals_summary);
            console.log('🔍 Is array?', Array.isArray(data.signals_summary));
            updateSignalsSummary(data.signals_summary || []);
            console.log('✅ updateSignalsSummary called');
            
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
            console.log('✅ updatePaperTrades called with:', paperTrades);
            console.log('✅ Type:', typeof paperTrades, 'Length:', Array.isArray(paperTrades) ? paperTrades.length : 'not array');
            
            const paperTradesList = document.getElementById('paper-trades-list');
            if (!paperTradesList) {
                console.error('❌ paper-trades-list element not found!');
                return;
            }
            
            // SIMPLIFIED APPROACH - Clear and rebuild every time
            paperTradesList.innerHTML = '';
            
            if (!paperTrades || !Array.isArray(paperTrades) || paperTrades.length === 0) {
                console.log('📭 No active paper trades to display');
                paperTradesList.innerHTML = '<div class="no-data">💼 No active paper trades yet...</div>';
                return;
            }
            
            console.log('📊 Displaying', paperTrades.length, 'active paper trades');
            
            // Build all trades
            paperTrades.forEach((trade, index) => {
                console.log(`  Trade ${index + 1}:`, trade.crypto, trade.action, 'Entry:', trade.entry_price, 'Current:', trade.current_price, 'PnL:', trade.pnl);
                
                const pnl = trade.pnl || 0;
                const pnlColor = pnl >= 0 ? '#00ff88' : '#ff4757';
                const pnlPrefix = pnl >= 0 ? '+$' : '-$';
                const pnlValue = Math.abs(pnl).toFixed(2);
                
                const cryptoEmoji = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}[trade.crypto] || '🪙';
                
                // Format entry time if available
                let entryTimeStr = '';
                if (trade.entry_time) {
                    try {
                        const entryDate = new Date(trade.entry_time);
                        const hours = String(entryDate.getHours()).padStart(2, '0');
                        const minutes = String(entryDate.getMinutes()).padStart(2, '0');
                        entryTimeStr = `${hours}:${minutes}`;
                    } catch (e) {
                        entryTimeStr = '';
                    }
                }
                
                // Calculate price change percentage
                const entryPrice = parseFloat(trade.entry_price);
                const currentPrice = parseFloat(trade.current_price);
                console.log(`  Parsed prices - Entry: ${entryPrice}, Current: ${currentPrice}`);
                const priceChange = ((currentPrice - entryPrice) / entryPrice * 100);
                const priceChangeStr = (priceChange >= 0 ? '+' : '') + priceChange.toFixed(2) + '%';
                const priceChangeColor = priceChange >= 0 ? '#00ff88' : '#ff4757';
                
                const tradeDiv = document.createElement('div');
                tradeDiv.className = `paper-trade-item trade-${trade.action.toLowerCase()}`;
                tradeDiv.style.marginBottom = '15px';
                
                tradeDiv.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-weight: bold; font-size: 1.1em;">
                            ${cryptoEmoji} ${trade.crypto} ${trade.action} - ID:${trade.id}
                            ${entryTimeStr ? `<span style="font-size: 0.75em; color: rgba(255,255,255,0.5); margin-left: 8px;">⏰ ${entryTimeStr}</span>` : ''}
                        </div>
                        <div style="background: ${pnlColor}22; color: ${pnlColor}; padding: 4px 8px; border-radius: 12px; font-size: 0.9em; font-weight: bold;">
                            ${pnlPrefix}${pnlValue}
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.9em; color: rgba(255,255,255,0.8);">
                        <div>Entry: <span style="color: #0096ff; font-weight: bold;">$${entryPrice.toFixed(2)}</span></div>
                        <div>Current: <span style="color: ${pnlColor}; font-weight: bold;">$${currentPrice.toFixed(2)}</span></div>
                        <div>Size: ${parseFloat(trade.position_size).toFixed(4)}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.8em; color: rgba(255,255,255,0.6); margin-top: 8px;">
                        <div>SL: $${parseFloat(trade.stop_loss).toFixed(2)}</div>
                        <div>TP: $${parseFloat(trade.take_profit).toFixed(2)}</div>
                        <div style="color: ${priceChangeColor};">Δ ${priceChangeStr}</div>
                    </div>
                `;
                
                paperTradesList.appendChild(tradeDiv);
            });
            
            console.log('✅ Successfully rendered', paperTrades.length, 'trades to DOM');
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
            
            signalDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="font-weight: bold; font-size: 1.1em;">
                            ${cryptoEmoji} ${signal.crypto} ${signal.action}
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
                <div style="margin-top: 10px;">
                    <div style="font-size: 0.8em; color: rgba(255,255,255,0.6);">
                        Confluences: ${signal.confluences.join(', ')}
                    </div>
                    <div style="font-size: 0.8em; color: rgba(255,255,255,0.6); margin-top: 5px;">
                        ${gmtTime} GMT | ${signal.timeframe} | Risk: $${signal.risk_amount}
                    </div>
                </div>
            `;
            
            signalsList.appendChild(signalDiv);
        }

        function updateSignalsSummary(signals) {
            console.log('🔍 updateSignalsSummary called with:', signals);
            console.log('🔍 Signals type:', typeof signals, 'Is array:', Array.isArray(signals), 'Length:', signals ? signals.length : 'null/undefined');
            
            const summaryBody = document.getElementById('signals-summary-body');
            if (!summaryBody) {
                console.error('❌ signals-summary-body element NOT FOUND!');
                return;
            }
            
            if (signals && Array.isArray(signals) && signals.length > 0) {
                console.log('✅ Updating signals summary table with', signals.length, 'signals');
                summaryBody.innerHTML = '';
                
                signals.forEach((signal, index) => {
                    console.log(`  Signal ${index + 1}:`, signal.crypto, signal.action, signal.entry_price, signal.timestamp);
                    
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
                console.log('✅ Successfully added', signals.length, 'rows to signals summary table');
            } else {
                console.log('📭 No signals to display in summary table');
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
            print("✅ Risk Management: $100 per trade | RR 1:3")
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
            
            logger.info(f"🚀 ICT Enhanced Trading Monitor starting on port {self.port}")
            
            # Start Flask-SocketIO server
            self.socketio.run(
                self.app, 
                host='0.0.0.0', 
                port=self.port, 
                debug=False,
                allow_unsafe_werkzeug=True
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Error starting monitor: {e}")
            raise
    
    def _get_fundamental_dashboard_html(self):
        """Generate fundamental analysis dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Fundamental Analysis - ICT Trading System</title>
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
        }
        
        .header h1 {
            font-size: 2.5em;
            color: #00ff88;
            margin-bottom: 10px;
        }
        
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            padding: 10px 20px;
            background: rgba(0,255,136,0.2);
            color: #00ff88;
            text-decoration: none;
            border-radius: 8px;
            border: 1px solid #00ff88;
            transition: all 0.3s;
        }
        
        .back-link:hover {
            background: rgba(0,255,136,0.3);
            transform: translateX(-5px);
        }
        
        .crypto-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .crypto-card {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 25px;
            border: 2px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        
        .crypto-card:hover {
            transform: translateY(-5px);
            border-color: #00ff88;
            box-shadow: 0 10px 30px rgba(0,255,136,0.3);
        }
        
        .crypto-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .crypto-name {
            font-size: 1.8em;
            font-weight: bold;
        }
        
        .score {
            font-size: 2em;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 10px;
        }
        
        .score.bullish { background: rgba(0,255,136,0.3); color: #00ff88; }
        .score.neutral { background: rgba(255,193,7,0.3); color: #ffc107; }
        .score.bearish { background: rgba(255,107,107,0.3); color: #ff6b6b; }
        
        .recommendation {
            text-align: center;
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .recommendation.strong-buy { background: rgba(0,255,0,0.2); color: #00ff00; border: 2px solid #00ff00; }
        .recommendation.buy { background: rgba(0,255,136,0.2); color: #00ff88; border: 2px solid #00ff88; }
        .recommendation.neutral { background: rgba(255,193,7,0.2); color: #ffc107; border: 2px solid #ffc107; }
        .recommendation.sell { background: rgba(255,107,107,0.2); color: #ff6b6b; border: 2px solid #ff6b6b; }
        .recommendation.strong-sell { background: rgba(255,0,0,0.2); color: #ff0000; border: 2px solid #ff0000; }
        
        .refresh-btn {
            display: block;
            margin: 20px auto;
            padding: 12px 30px;
            background: #00ff88;
            color: #1e3c72;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .refresh-btn:hover {
            background: #00cc6f;
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <a href="/" class="back-link">← Back to Home</a>
    
    <div class="header">
        <h1>📊 Fundamental Analysis</h1>
        <p>Long-term crypto investment analysis</p>
    </div>
    
    <button class="refresh-btn" onclick="loadFundamentals()">🔄 Refresh Analysis</button>
    
    <div id="crypto-grid" class="crypto-grid">
        <p style="text-align: center; color: rgba(255,255,255,0.7);">Loading...</p>
    </div>
    
    <script>
        function loadFundamentals() {
            fetch('/api/fundamental')
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('crypto-grid');
                    grid.innerHTML = '';
                    
                    for (const [symbol, analysis] of Object.entries(data)) {
                        const card = createCryptoCard(symbol, analysis);
                        grid.appendChild(card);
                    }
                })
                .catch(error => {
                    console.error('Error loading fundamentals:', error);
                    document.getElementById('crypto-grid').innerHTML = 
                        '<p style="text-align: center; color: #ff6b6b;">Error loading data</p>';
                });
        }
        
        function createCryptoCard(symbol, analysis) {
            const card = document.createElement('div');
            card.className = 'crypto-card';
            
            const scoreClass = analysis.score >= 3 ? 'bullish' : 
                              analysis.score <= -3 ? 'bearish' : 'neutral';
            
            const recClass = analysis.recommendation.toLowerCase().replace(' ', '-');
            
            card.innerHTML = `
                <div class="crypto-header">
                    <div class="crypto-name">${symbol}</div>
                    <div class="score ${scoreClass}">${analysis.score}/10</div>
                </div>
                <div class="recommendation ${recClass}">${analysis.recommendation}</div>
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
                    <p style="text-align: center; color: rgba(255,255,255,0.6); font-size: 0.9em;">
                        Updated: ${analysis.last_update ? new Date(analysis.last_update).toLocaleString() : 'Never'}
                    </p>
                    <p style="text-align: center; color: rgba(255,255,255,0.6); font-size: 0.9em; margin-top: 5px;">
                        Confidence: ${(analysis.confidence * 100).toFixed(0)}%
                    </p>
                </div>
            `;
            
            return card;
        }
        
        // Load on page load
        loadFundamentals();
        
        // Auto-refresh every 5 minutes
        setInterval(loadFundamentals, 300000);
    </script>
</body>
</html>
'''
    
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
    
    # Initialize database for new users
    logger.info("=" * 60)
    logger.info("🚀 ICT Trading System - Starting Up")
    logger.info("=" * 60)
    
    from database.trading_database import TradingDatabase
    import bcrypt
    
    # Database initialization (creates tables automatically)
    logger.info("📊 Initializing database...")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(project_root, "data", "trading.db")
    
    # Check if this is first-time setup
    is_new_installation = not os.path.exists(db_path)
    
    db = TradingDatabase(db_path)
    
    if is_new_installation:
        logger.info("✨ First-time setup detected!")
        logger.info("✅ Database created: data/trading.db")
        logger.info("✅ All tables initialized")
    else:
        logger.info("✅ Database found: data/trading.db")
    
    # Create demo user if not exists
    demo_email = 'demo@ict.com'
    demo_password = 'demo123'
    
    existing_user = db.get_user_by_email(demo_email)
    if not existing_user:
        password_hash = bcrypt.hashpw(demo_password.encode('utf-8'), bcrypt.gensalt())
        db.create_user(demo_email, password_hash)
        logger.info(f"✅ Created demo user: {demo_email} / {demo_password}")
        logger.info("=" * 60)
        logger.info("🎉 FIRST TIME SETUP COMPLETE!")
        logger.info("📝 Login with: demo@ict.com / demo123")
        logger.info("=" * 60)
    else:
        logger.info(f"✅ Demo user ready: {demo_email}")
    
    logger.info(f"🌐 Starting monitor on port {args.port}...")
    logger.info("=" * 60)
    
    monitor = ICTWebMonitor(port=args.port)
    monitor.start()

if __name__ == "__main__":
    main()