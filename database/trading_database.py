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
    
    def _get_connection(self):
        """Get database connection (for health checks)
        
        Returns:
            sqlite3.Connection: Active database connection
        """
        # Check if connection is closed or None
        try:
            if self.conn is None:
                self._connect()
            else:
                # Test if connection is alive by executing a simple query
                self.conn.execute("SELECT 1")
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            # Connection is closed or invalid, reconnect
            self._connect()
        
        return self.conn
    
    def _init_tables(self):
        """Initialize required database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Signals table - matches actual schema
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
        
        # Scan history table - matches actual schema
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
        
        # Daily stats table - matches actual schema
        cursor.execute('''
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
        
        # Paper trades table - matches actual schema
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
        
        self.conn.commit()
        logger.info("✅ Database tables initialized")
    
    def _ensure_connection(self):
        """Ensure database connection is active before operations"""
        try:
            if self.conn is None:
                self._connect()
            else:
                # Test connection with a simple query
                self.conn.execute("SELECT 1")
        except (sqlite3.ProgrammingError, sqlite3.OperationalError, AttributeError):
            # Connection is closed or invalid, reconnect
            self._connect()
    
    def get_daily_stats(self) -> Dict:
        """Get or create today's daily stats"""
        self._ensure_connection()
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
    
    def get_scan_count(self) -> int:
        """Get today's scan count
        
        Returns:
            int: Number of scans performed today
        """
        self._ensure_connection()
        stats = self.get_daily_stats()
        return stats.get('scan_count', 0)
    
    def increment_scan_count(self):
        """Increment today's scan count"""
        self._ensure_connection()
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
    
    def add_signal(self, signal_data: Dict) -> str:
        """Add a new signal to the database"""
        import uuid
        self._ensure_connection()
        cursor = self.conn.cursor()
        
        # Generate signal_id if not provided
        if 'signal_id' not in signal_data:
            signal_data['signal_id'] = f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        cursor.execute('''
            INSERT INTO signals (
                signal_id, symbol, direction, entry_price, stop_loss, take_profit,
                confluence_score, timeframes, ict_concepts, session, market_regime,
                directional_bias, signal_strength, status, entry_time, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data.get('signal_id'),
            signal_data.get('symbol'),
            signal_data.get('direction'),
            signal_data.get('entry_price'),
            signal_data.get('stop_loss'),
            signal_data.get('take_profit'),
            signal_data.get('confluence_score', 0),
            signal_data.get('timeframes', ''),
            signal_data.get('ict_concepts', ''),
            signal_data.get('session', 'UNKNOWN'),
            signal_data.get('market_regime', 'UNKNOWN'),
            signal_data.get('directional_bias', 'NEUTRAL'),
            signal_data.get('signal_strength', 0),
            signal_data.get('status', 'ACTIVE'),
            signal_data.get('entry_time', datetime.now().isoformat()),
            date.today().isoformat()
        ))
        
        self.conn.commit()
        return signal_data['signal_id']
    
    def get_signals_today(self) -> List[Dict]:
        """Get all signals from today"""
        self._ensure_connection()
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            WHERE created_date = ?
            ORDER BY entry_time DESC
        ''', (today,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals"""
        self._ensure_connection()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            WHERE status = 'ACTIVE'
            ORDER BY entry_time DESC
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_closed_signals_today(self) -> List[Dict]:
        """Get all closed signals from today"""
        self._ensure_connection()
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            WHERE created_date = ? AND status IN ('CLOSED', 'COMPLETED', 'EXPIRED')
            ORDER BY entry_time DESC
        ''', (today,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_signal_status(self, signal_id: int, status: str, pnl: float = None, exit_price: float = None):
        """Update signal status and optional PnL"""
        self._ensure_connection()
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
        self._ensure_connection()
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
        self._ensure_connection()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO scan_history (scan_number, signals_generated)
            VALUES (?, ?)
        ''', (scan_number, signals_found))
        
        self.conn.commit()
    
    def get_journal_entries_today(self) -> List[Dict]:
        """Get journal entries (closed trades) from today"""
        return self.get_closed_signals_today()
    
    def migrate_existing_data(self, json_file_path: str):
        """Migrate data from JSON file if needed (stub for compatibility)"""
        logger.info(f"Skipping migration from {json_file_path} (database-first mode)")
        pass
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email (stub for authentication)
        
        Args:
            email: User email address
            
        Returns:
            User dict if found, None otherwise
        """
        # Stub implementation - authentication not used in production
        return None
    
    def create_user(self, email: str, password_hash: str, is_admin: bool = False) -> int:
        """Create a new user (stub for authentication)
        
        Args:
            email: User email
            password_hash: Hashed password
            is_admin: Whether user is admin
            
        Returns:
            User ID
        """
        # Stub implementation - authentication not used in production
        return 1
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
