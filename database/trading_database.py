#!/usr/bin/env python3
"""
Trading Database Wrapper
Provides database operations for the trading system
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class TradingDatabase:
    """Trading database wrapper for SQLite operations"""
    
    def __init__(self, db_path: str = "data/trading.db"):
        """Initialize database connection
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_tables()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✅ Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def _init_tables(self):
        """Initialize required database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                confidence REAL,
                status TEXT DEFAULT 'active',
                pnl REAL DEFAULT 0,
                entry_time TEXT,
                exit_time TEXT,
                exit_price REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Scan history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scan_number INTEGER NOT NULL,
                symbols_scanned TEXT NOT NULL,
                signals_found INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Daily stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                scan_count INTEGER DEFAULT 0,
                signals_generated INTEGER DEFAULT 0,
                paper_balance REAL DEFAULT 100.0,
                total_pnl REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Paper trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                position_size REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT DEFAULT 'open',
                pnl REAL DEFAULT 0,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                notes TEXT,
                FOREIGN KEY (signal_id) REFERENCES signals(id)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Database tables initialized")
    
    def get_daily_stats(self) -> Dict:
        """Get or create today's daily stats"""
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        else:
            # Create today's stats
            cursor.execute('''
                INSERT INTO daily_stats (date, scan_count, signals_generated, paper_balance, total_pnl)
                VALUES (?, 0, 0, 100.0, 0.0)
            ''', (today,))
            self.conn.commit()
            return {
                'scan_count': 0,
                'signals_generated': 0,
                'paper_balance': 100.0,
                'total_pnl': 0.0
            }
    
    def increment_scan_count(self):
        """Increment today's scan count"""
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE daily_stats 
            SET scan_count = scan_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        ''', (today,))
        
        if cursor.rowcount == 0:
            # Create if doesn't exist
            cursor.execute('''
                INSERT INTO daily_stats (date, scan_count)
                VALUES (?, 1)
            ''', (today,))
        
        self.conn.commit()
    
    def add_signal(self, signal_data: Dict):
        """Add a new trading signal"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO signals (
                timestamp, symbol, signal_type, entry_price, stop_loss, take_profit, 
                confidence, status, entry_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data.get('timestamp', datetime.now().isoformat()),
            signal_data['symbol'],
            signal_data['type'],
            signal_data['entry_price'],
            signal_data.get('stop_loss'),
            signal_data.get('take_profit'),
            signal_data.get('confidence', 0.0),
            'active',
            signal_data.get('entry_time', datetime.now().isoformat())
        ))
        
        # Increment signals generated count
        today = date.today().isoformat()
        cursor.execute('''
            UPDATE daily_stats 
            SET signals_generated = signals_generated + 1
            WHERE date = ?
        ''', (today,))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_signals_today(self) -> List[Dict]:
        """Get all signals from today"""
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            WHERE date(timestamp) = ?
            ORDER BY timestamp DESC
        ''', (today,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            WHERE status = 'active'
            ORDER BY timestamp DESC
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_closed_signals_today(self) -> List[Dict]:
        """Get all closed signals from today"""
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            WHERE date(timestamp) = ? AND status = 'closed'
            ORDER BY timestamp DESC
        ''', (today,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_signal_status(self, signal_id: int, status: str, pnl: float = None, exit_price: float = None):
        """Update signal status and optional PnL"""
        cursor = self.conn.cursor()
        
        if pnl is not None and exit_price is not None:
            cursor.execute('''
                UPDATE signals 
                SET status = ?, pnl = ?, exit_price = ?, exit_time = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, pnl, exit_price, signal_id))
        else:
            cursor.execute('''
                UPDATE signals 
                SET status = ?
                WHERE id = ?
            ''', (status, signal_id))
        
        self.conn.commit()
    
    def update_balance(self, balance: float, account_type: str = 'paper'):
        """Update account balance"""
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE daily_stats 
            SET paper_balance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        ''', (balance, today))
        
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO daily_stats (date, paper_balance)
                VALUES (?, ?)
            ''', (today, balance))
        
        self.conn.commit()
    
    def add_scan_record(self, scan_number: int, symbols: List[str], signals_found: int):
        """Record a scan in scan history"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO scan_history (timestamp, scan_number, symbols_scanned, signals_found)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            scan_number,
            ','.join(symbols),
            signals_found
        ))
        
        self.conn.commit()
    
    def get_journal_entries_today(self) -> List[Dict]:
        """Get journal entries (closed trades) from today"""
        return self.get_closed_signals_today()
    
    def migrate_existing_data(self, json_file_path: str):
        """Migrate data from JSON file if needed (stub for compatibility)"""
        logger.info(f"Skipping migration from {json_file_path} (database-first mode)")
        pass
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
