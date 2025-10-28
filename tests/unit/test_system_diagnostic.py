#!/usr/bin/env python3
"""
Unit tests for System Diagnostic Module
========================================

Tests the diagnostic checker functionality.
"""

import pytest
import sqlite3
import os
import tempfile
from datetime import datetime, date
from core.diagnostics.system_diagnostic import SystemDiagnostic, create_diagnostic_checker


class TestSystemDiagnostic:
    """Test cases for SystemDiagnostic class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize database with required tables
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create required tables
        cursor.execute('''
            CREATE TABLE signals (
                id INTEGER PRIMARY KEY,
                signal_id TEXT,
                symbol TEXT,
                direction TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                confluence_score REAL,
                timeframes TEXT,
                ict_concepts TEXT,
                session TEXT,
                market_regime TEXT,
                directional_bias TEXT,
                signal_strength TEXT,
                status TEXT,
                entry_time TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE paper_trades (
                id INTEGER PRIMARY KEY,
                signal_id TEXT,
                symbol TEXT,
                direction TEXT,
                entry_price REAL,
                position_size REAL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT,
                risk_amount REAL,
                entry_time TIMESTAMP,
                current_price REAL,
                unrealized_pnl REAL,
                realized_pnl REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE daily_stats (
                id INTEGER PRIMARY KEY,
                date DATE,
                scan_count INTEGER,
                signals_generated INTEGER,
                paper_balance REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)
    
    def test_diagnostic_initialization(self, temp_db):
        """Test diagnostic system initialization."""
        diagnostic = SystemDiagnostic(db_path=temp_db)
        assert diagnostic.db_path == temp_db
        assert diagnostic.logger is not None
    
    def test_factory_function(self, temp_db):
        """Test factory function creates valid instance."""
        diagnostic = create_diagnostic_checker(db_path=temp_db)
        assert isinstance(diagnostic, SystemDiagnostic)
        assert diagnostic.db_path == temp_db
    
    def test_database_health_check_success(self, temp_db):
        """Test database health check with valid database."""
        diagnostic = SystemDiagnostic(db_path=temp_db)
        result = diagnostic._check_database_health()
        
        assert result['status'] == 'OK'
        assert 'Database is healthy' in result['message']
        assert 'integrity' in result['details']
        assert result['details']['integrity'] == 'ok'
        assert 'tables' in result['details']
    
    def test_database_health_check_missing_db(self):
        """Test database health check with missing database."""
        diagnostic = SystemDiagnostic(db_path='/nonexistent/path.db')
        result = diagnostic._check_database_health()
        
        assert result['status'] == 'ERROR'
        assert 'not found' in result['message']
    
    def test_trading_performance_check(self, temp_db):
        """Test trading performance metrics check."""
        # Add sample trade data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        cursor.execute('''
            INSERT INTO paper_trades 
            (signal_id, symbol, direction, entry_price, position_size,
             stop_loss, take_profit, status, risk_amount, entry_time,
             current_price, unrealized_pnl, realized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('SIG1', 'BTCUSDT', 'BUY', 100.0, 1.0, 95.0, 105.0, 
              'CLOSED', 1.0, today, 105.0, 0.0, 5.0))
        
        conn.commit()
        conn.close()
        
        diagnostic = SystemDiagnostic(db_path=temp_db)
        result = diagnostic._check_trading_performance()
        
        assert result['status'] in ['OK', 'WARNING']
        assert 'details' in result
        assert 'total_trades_today' in result['details']
        assert result['details']['total_trades_today'] >= 1
    
    def test_signal_quality_check(self, temp_db):
        """Test signal quality metrics check."""
        # Add sample signal data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        cursor.execute('''
            INSERT INTO signals
            (signal_id, symbol, direction, entry_price, stop_loss, take_profit,
             confluence_score, timeframes, ict_concepts, session, market_regime,
             directional_bias, signal_strength, status, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('SIG1', 'BTCUSDT', 'BUY', 100.0, 95.0, 105.0, 0.75,
              '["5m","15m"]', '["FVG","OB"]', 'NY', 'TRENDING', 
              'BULLISH', 'HIGH', 'ACTIVE', today))
        
        conn.commit()
        conn.close()
        
        diagnostic = SystemDiagnostic(db_path=temp_db)
        result = diagnostic._check_signal_quality()
        
        assert result['status'] in ['OK', 'WARNING']
        assert 'details' in result
        assert 'signals_today' in result['details']
        assert result['details']['signals_today'] >= 1
    
    def test_risk_management_check(self, temp_db):
        """Test risk management compliance check."""
        # Add sample data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        cursor.execute('''
            INSERT INTO paper_trades
            (signal_id, symbol, direction, entry_price, position_size,
             stop_loss, take_profit, status, risk_amount, entry_time,
             current_price, unrealized_pnl, realized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('SIG1', 'BTCUSDT', 'BUY', 100.0, 1.0, 95.0, 105.0,
              'OPEN', 1.0, today, 101.0, 1.0, 0.0))
        
        cursor.execute('''
            INSERT INTO daily_stats
            (date, scan_count, signals_generated, paper_balance)
            VALUES (?, ?, ?, ?)
        ''', (today, 10, 5, 100.0))
        
        conn.commit()
        conn.close()
        
        diagnostic = SystemDiagnostic(db_path=temp_db)
        result = diagnostic._check_risk_management()
        
        assert result['status'] in ['OK', 'WARNING']
        assert 'details' in result
        assert 'current_balance' in result['details']
        assert 'avg_risk_per_trade' in result['details']
    
    def test_active_trades_check(self, temp_db):
        """Test active trades status check."""
        # Add active trade
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        today = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO paper_trades
            (signal_id, symbol, direction, entry_price, position_size,
             stop_loss, take_profit, status, risk_amount, entry_time,
             current_price, unrealized_pnl, realized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('SIG1', 'SOLUSDT', 'BUY', 150.0, 1.0, 145.0, 155.0,
              'OPEN', 1.0, today, 151.0, 1.0, 0.0))
        
        conn.commit()
        conn.close()
        
        diagnostic = SystemDiagnostic(db_path=temp_db)
        result = diagnostic._check_active_trades()
        
        assert result['status'] in ['OK', 'WARNING']
        assert 'details' in result
        assert 'active_trades_count' in result['details']
        assert result['details']['active_trades_count'] >= 1
    
    def test_full_diagnostic_run(self, temp_db):
        """Test complete diagnostic run."""
        # Add some sample data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        cursor.execute('''
            INSERT INTO daily_stats
            (date, scan_count, signals_generated, paper_balance)
            VALUES (?, ?, ?, ?)
        ''', (today, 10, 5, 100.0))
        
        conn.commit()
        conn.close()
        
        diagnostic = SystemDiagnostic(db_path=temp_db)
        results = diagnostic.run_full_diagnostic()
        
        assert 'timestamp' in results
        assert 'overall_status' in results
        assert results['overall_status'] in ['HEALTHY', 'WARNING', 'ERROR']
        assert 'checks' in results
        assert 'database' in results['checks']
        assert 'trading_performance' in results['checks']
        assert 'signal_quality' in results['checks']
        assert 'risk_management' in results['checks']
        assert 'active_trades' in results['checks']
        assert 'system_metrics' in results['checks']
        assert 'issues' in results
        assert 'issue_count' in results


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
