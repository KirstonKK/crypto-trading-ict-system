#!/usr/bin/env python3
"""
Trading Database Manager - SQLite Integration
Replaces hardcoded data with persistent database storage
"""

import sqlite3
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import os

class TradingDatabase:
    def __init__(self, db_path: str = "data/trading.db"):
        """Initialize the trading database"""
        self.db_path = db_path
        # Ensure directory exists (only if there's a directory path)
        dir_path = os.path.dirname(db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
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
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    trade_type TEXT NOT NULL, -- 'PAPER' or 'LIVE'
                    status TEXT NOT NULL,     -- 'ACTIVE', 'COMPLETED', 'CANCELLED'
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    quantity REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    scan_count INTEGER DEFAULT 0,
                    signals_generated INTEGER DEFAULT 0,
                    trades_executed INTEGER DEFAULT 0,
                    active_trades INTEGER DEFAULT 0,
                    completed_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    paper_balance REAL DEFAULT 100,
                    live_balance REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_type TEXT NOT NULL, -- 'TRADE', 'SYSTEM', 'ANALYSIS'
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    signal_id TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
                )
            ''')
            
            conn.commit()
    
    def add_signal(self, signal_data: Dict[str, Any]) -> str:
        """Add a new signal to database"""
        signal_id = signal_data.get('signal_id', f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO signals 
                (signal_id, symbol, direction, entry_price, stop_loss, take_profit,
                 confluence_score, timeframes, ict_concepts, session, market_regime,
                 directional_bias, signal_strength, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_id,
                signal_data['symbol'],
                signal_data['direction'],
                signal_data['entry_price'],
                signal_data['stop_loss'],
                signal_data['take_profit'],
                signal_data['confluence_score'],
                json.dumps(signal_data.get('timeframes', [])),
                json.dumps(signal_data.get('ict_concepts', [])),
                signal_data.get('session', 'Unknown'),
                signal_data.get('market_regime', 'Unknown'),
                signal_data.get('directional_bias', 'Neutral'),
                signal_data.get('signal_strength', 'Medium'),
                signal_data.get('status', 'ACTIVE'),
                signal_data.get('notes', '')
            ))
            conn.commit()
        
        # Ensure daily reset check before updating signal count
        self._check_and_reset_for_new_day()
        self._update_daily_stats('signals_generated', 1)
        return signal_id
    
    def add_trade(self, signal_id: str, trade_data: Dict[str, Any]) -> int:
        """Add a new trade to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO trades 
                (signal_id, trade_type, status, entry_price, current_price,
                 stop_loss, take_profit, quantity, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_id,
                trade_data.get('trade_type', 'PAPER'),
                trade_data.get('status', 'ACTIVE'),
                trade_data['entry_price'],
                trade_data.get('current_price', trade_data['entry_price']),
                trade_data['stop_loss'],
                trade_data['take_profit'],
                trade_data.get('quantity', 1.0),
                trade_data.get('pnl', 0.0)
            ))
            trade_id = cursor.lastrowid
            conn.commit()
        
        if trade_data.get('status') == 'ACTIVE':
            self._update_daily_stats('active_trades', 1)
        elif trade_data.get('status') == 'COMPLETED':
            self._update_daily_stats('completed_trades', 1)
            self._update_daily_stats('trades_executed', 1)
        
        return trade_id
    
    def update_trade(self, trade_id: int, updates: Dict[str, Any]):
        """Update trade status and PnL"""
        with sqlite3.connect(self.db_path) as conn:
            # Get current trade data
            current = conn.execute(
                'SELECT status, pnl FROM trades WHERE id = ?', (trade_id,)
            ).fetchone()
            
            if not current:
                return False
            
            old_status, old_pnl = current
            
            # Update trade
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [trade_id]
            
            conn.execute(f'''
                UPDATE trades 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            conn.commit()
            
            # Update daily stats if status changed
            new_status = updates.get('status', old_status)
            if old_status == 'ACTIVE' and new_status == 'COMPLETED':
                self._update_daily_stats('active_trades', -1)
                self._update_daily_stats('completed_trades', 1)
                
                # Update PnL
                pnl_change = updates.get('pnl', old_pnl) - old_pnl
                self._update_daily_stats('total_pnl', pnl_change)
        
        return True
    
    def get_signals_today(self) -> List[Dict[str, Any]]:
        """Get all signals generated today"""
        today = date.today().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM signals 
                WHERE created_date = ? 
                ORDER BY entry_time DESC
            ''', (today,))
            
            signals = []
            for row in cursor.fetchall():
                signal = dict(row)
                signal['timeframes'] = json.loads(signal['timeframes'])
                signal['ict_concepts'] = json.loads(signal['ict_concepts'])
                signals.append(signal)
            
            return signals
    
    def get_active_trades(self) -> List[Dict[str, Any]]:
        """Get all active trades"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT t.*, s.symbol, s.direction 
                FROM trades t
                JOIN signals s ON t.signal_id = s.signal_id
                WHERE t.status = 'ACTIVE'
                ORDER BY t.created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _check_and_reset_for_new_day(self):
        """Check if it's a new day and reset daily counters while preserving balance"""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if today's record exists
            cursor = conn.execute(
                'SELECT paper_balance, live_balance FROM daily_stats WHERE date = ?', 
                (today,)
            )
            row = cursor.fetchone()
            
            if not row:
                # New day - get previous balance (DO NOT RESET BALANCE!)
                cursor = conn.execute(
                    'SELECT paper_balance, live_balance FROM daily_stats ORDER BY date DESC LIMIT 1'
                )
                prev_row = cursor.fetchone()
                
                # PRESERVE THE EXACT BALANCE - never reset it
                prev_paper_balance = prev_row[0] if prev_row else 100.0
                prev_live_balance = prev_row[1] if prev_row else 0.0
                
                conn.execute('''
                    INSERT INTO daily_stats 
                    (date, scan_count, signals_generated, total_pnl, win_rate, 
                     paper_balance, live_balance) 
                    VALUES (?, 0, 0, 0, 0, ?, ?)
                ''', (today, prev_paper_balance, prev_live_balance))
                
                self.logger.info(f"🗓️ NEW DAY: Reset counters to 0, PRESERVED balance ${prev_paper_balance:.2f} from previous trading")
                conn.commit()

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get today's statistics"""
        # First check if we need to reset for new day
        self._check_and_reset_for_new_day()
        
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM daily_stats WHERE date = ?', 
                (today,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    'date': row[1],
                    'scan_count': row[2],
                    'signals_generated': row[3],
                    'trades_executed': row[4],
                    'active_trades': row[5],
                    'completed_trades': row[6],
                    'total_pnl': row[7],
                    'win_rate': row[8],
                    'paper_balance': row[9],
                    'live_balance': row[10]
                }
            else:
                # Shouldn't happen after reset check, but fallback
                return {
                    'date': today.isoformat(),
                    'scan_count': 0,
                    'signals_generated': 0,
                    'total_pnl': 0.0,
                    'win_rate': 0.0,
                    'paper_balance': 100.0,
                    'live_balance': 0.0
                }
    
    def _ensure_daily_stats_exists(self, target_date: str):
        """Ensure daily stats record exists for given date"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO daily_stats (date) VALUES (?)
            ''', (target_date,))
            conn.commit()
    
    def _update_daily_stats(self, field: str, increment: float):
        """Update a field in today's daily stats"""
        # Ensure daily reset check is done first
        self._check_and_reset_for_new_day()
        
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f'''
                UPDATE daily_stats 
                SET {field} = {field} + ?, updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            ''', (increment, today))
            conn.commit()
    
    def add_journal_entry(self, entry_type: str, title: str, content: str, signal_id: str = None):
        """Add journal entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO journal_entries (entry_type, title, content, signal_id)
                VALUES (?, ?, ?, ?)
            ''', (entry_type, title, content, signal_id))
            conn.commit()
    
    def get_journal_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent journal entries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM journal_entries 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def migrate_existing_data(self, session_data_path: str):
        """Migrate existing JSON data to database"""
        self.logger.info("🔄 Migrating existing data to database...")
        
        # Read session summary
        try:
            with open(session_data_path, 'r') as f:
                session_data = json.load(f)
            
            # Update daily stats with session data
            perf = session_data.get('system_performance', {})
            today = date.today().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO daily_stats 
                    (date, scan_count, signals_generated, trades_executed, 
                     active_trades, total_pnl, paper_balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    today,
                    perf.get('total_scans', 0),
                    perf.get('signals_generated', 0),
                    perf.get('paper_trades_executed', 0),
                    perf.get('live_trades_active', 0),
                    perf.get('pnl', 0),
                    perf.get('current_paper_balance', 100)
                ))
                conn.commit()
            
            # Add journal entry about lost trades
            self.add_journal_entry(
                'SYSTEM',
                'System Restart - Data Recovery',
                f"Restored session data: {perf.get('signals_generated', 0)} signals generated, "
                f"{perf.get('paper_trades_executed', 0)} trades executed, "
                f"{perf.get('live_trades_active', 0)} active trades lost in restart. "
                f"PnL: ${perf.get('pnl', 0):.2f}"
            )
            
            self.logger.info(f"✅ Migrated {perf.get('signals_generated', 0)} signals and trading data")
            
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
    
    def get_scan_count(self) -> int:
        """Get current scan count"""
        stats = self.get_daily_stats()
        return stats.get('scan_count', 0)
    
    def increment_scan_count(self):
        """Increment scan count"""
        # Ensure daily reset is checked first
        self._check_and_reset_for_new_day()
        self._update_daily_stats('scan_count', 1)
    
    def update_balance(self, new_balance: float, balance_type: str = 'paper'):
        """Update account balance"""
        # Ensure daily reset check is done first
        self._check_and_reset_for_new_day()
        
        field = f'{balance_type}_balance'
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f'''
                UPDATE daily_stats 
                SET {field} = ?, updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            ''', (new_balance, today))
            conn.commit()
    
    def get_signals_today(self) -> List[Dict[str, Any]]:
        """Get all signals generated today"""
        today = date.today().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM signals 
                WHERE DATE(entry_time) = ?
                ORDER BY entry_time DESC
            ''', (today,))
            
            columns = [description[0] for description in cursor.description]
            signals = []
            
            for row in cursor.fetchall():
                signal_dict = dict(zip(columns, row))
                # Parse JSON fields
                if signal_dict.get('timeframes'):
                    try:
                        signal_dict['timeframes'] = json.loads(signal_dict['timeframes'])
                    except:
                        signal_dict['timeframes'] = []
                
                if signal_dict.get('ict_concepts'):
                    try:
                        signal_dict['ict_concepts'] = json.loads(signal_dict['ict_concepts'])
                    except:
                        signal_dict['ict_concepts'] = []
                
                signals.append(signal_dict)
            
            return signals
    
    def get_trades_today(self) -> List[Dict[str, Any]]:
        """Get all trades from today"""
        today = date.today().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT t.*, s.symbol 
                FROM trades t
                JOIN signals s ON t.signal_id = s.signal_id
                WHERE DATE(t.created_at) = ?
                ORDER BY t.created_at DESC
            ''', (today,))
            
            columns = [description[0] for description in cursor.description]
            trades = []
            
            for row in cursor.fetchall():
                trade_dict = dict(zip(columns, row))
                trades.append(trade_dict)
            
            return trades