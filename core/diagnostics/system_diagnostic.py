#!/usr/bin/env python3
"""
System Diagnostic Module
========================

Comprehensive diagnostic system for the crypto trading algorithm.
Analyzes system health, performance metrics, and trading signal quality.

Author: GitHub Copilot
Date: October 2025
"""

import logging
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import os
import sys

logger = logging.getLogger(__name__)


class SystemDiagnostic:
    """
    Comprehensive system diagnostic checker for the trading system.
    Monitors health, performance, and trading metrics.
    """
    
    def __init__(self, db_path: str = "data/trading.db"):
        """
        Initialize diagnostic system.
        
        Args:
            db_path: Path to trading database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """
        Run comprehensive system diagnostic.
        
        Returns:
            Dictionary with diagnostic results
        """
        self.logger.info("🔍 Running system diagnostic...")
        
        diagnostic_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {}
        }
        
        # Run all diagnostic checks
        try:
            diagnostic_results['checks']['database'] = self._check_database_health()
            diagnostic_results['checks']['trading_performance'] = self._check_trading_performance()
            diagnostic_results['checks']['signal_quality'] = self._check_signal_quality()
            diagnostic_results['checks']['risk_management'] = self._check_risk_management()
            diagnostic_results['checks']['active_trades'] = self._check_active_trades()
            diagnostic_results['checks']['system_metrics'] = self._get_system_metrics()
            
            # Determine overall status
            issues = []
            for check_name, check_result in diagnostic_results['checks'].items():
                if check_result.get('status') == 'ERROR':
                    issues.append(f"{check_name}: {check_result.get('message', 'Unknown error')}")
                elif check_result.get('status') == 'WARNING':
                    issues.append(f"{check_name}: {check_result.get('message', 'Warning')}")
            
            if any(check['status'] == 'ERROR' for check in diagnostic_results['checks'].values()):
                diagnostic_results['overall_status'] = 'ERROR'
            elif any(check['status'] == 'WARNING' for check in diagnostic_results['checks'].values()):
                diagnostic_results['overall_status'] = 'WARNING'
            else:
                diagnostic_results['overall_status'] = 'HEALTHY'
            
            diagnostic_results['issues'] = issues
            diagnostic_results['issue_count'] = len(issues)
            
        except Exception as e:
            self.logger.error(f"❌ Diagnostic error: {e}", exc_info=True)
            diagnostic_results['overall_status'] = 'ERROR'
            diagnostic_results['error'] = str(e)
        
        return diagnostic_results
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and integrity."""
        try:
            if not os.path.exists(self.db_path):
                return {
                    'status': 'ERROR',
                    'message': f'Database file not found at {self.db_path}',
                    'details': {}
                }
            
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # Get table counts
            tables = {}
            for table_name in ['signals', 'paper_trades', 'daily_stats']:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                tables[table_name] = cursor.fetchone()[0]
            
            # Get database size
            db_size_bytes = os.path.getsize(self.db_path)
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            conn.close()
            
            return {
                'status': 'OK' if integrity == 'ok' else 'ERROR',
                'message': 'Database is healthy',
                'details': {
                    'integrity': integrity,
                    'size_mb': round(db_size_mb, 2),
                    'tables': tables
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Database error: {str(e)}',
                'details': {}
            }
    
    def _check_trading_performance(self) -> Dict[str, Any]:
        """Check trading performance metrics."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Get today's date
            today = date.today().isoformat()
            
            # Get paper trade statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_trades,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(realized_pnl) as total_pnl,
                    AVG(realized_pnl) as avg_pnl
                FROM paper_trades
                WHERE date(entry_time) = ?
            """, (today,))
            
            result = cursor.fetchone()
            total_trades = result[0] or 0
            open_trades = result[1] or 0
            winning_trades = result[2] or 0
            losing_trades = result[3] or 0
            total_pnl = result[4] or 0.0
            avg_pnl = result[5] or 0.0
            
            # Calculate win rate
            completed_trades = winning_trades + losing_trades
            win_rate = (winning_trades / completed_trades * 100) if completed_trades > 0 else 0.0
            
            conn.close()
            
            # Determine status
            status = 'OK'
            message = 'Trading performance is normal'
            
            if completed_trades > 0:
                if win_rate < 40:
                    status = 'WARNING'
                    message = f'Low win rate: {win_rate:.1f}%'
                elif total_pnl < -50:
                    status = 'WARNING'
                    message = f'Significant losses: ${total_pnl:.2f}'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'total_trades_today': total_trades,
                    'open_trades': open_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'avg_pnl': round(avg_pnl, 2)
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Performance check error: {str(e)}',
                'details': {}
            }
    
    def _check_signal_quality(self) -> Dict[str, Any]:
        """Check signal generation quality."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            # Get signal statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_signals,
                    AVG(confluence_score) as avg_confluence,
                    COUNT(DISTINCT symbol) as symbols_traded
                FROM signals
                WHERE date(entry_time) = ?
            """, (today,))
            
            result = cursor.fetchone()
            total_signals = result[0] or 0
            avg_confluence = result[1] or 0.0
            symbols_traded = result[2] or 0
            
            conn.close()
            
            # Determine status
            status = 'OK'
            message = 'Signal quality is acceptable'
            
            if total_signals == 0:
                status = 'WARNING'
                message = 'No signals generated today'
            elif avg_confluence < 0.6:
                status = 'WARNING'
                message = f'Low average signal quality: {avg_confluence:.2f}'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'signals_today': total_signals,
                    'avg_confluence_score': round(avg_confluence, 3),
                    'symbols_traded': symbols_traded
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Signal quality check error: {str(e)}',
                'details': {}
            }
    
    def _check_risk_management(self) -> Dict[str, Any]:
        """Check risk management compliance."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            # Check risk per trade (should be ~1% = $1 for $100 account)
            cursor.execute("""
                SELECT 
                    AVG(risk_amount) as avg_risk,
                    MAX(risk_amount) as max_risk,
                    COUNT(*) as total_trades
                FROM paper_trades
                WHERE date(entry_time) = ?
            """, (today,))
            
            result = cursor.fetchone()
            avg_risk = result[0] or 0.0
            max_risk = result[1] or 0.0
            total_trades = result[2] or 0
            
            # Get current balance
            cursor.execute("SELECT paper_balance FROM daily_stats ORDER BY date DESC LIMIT 1")
            balance_result = cursor.fetchone()
            current_balance = balance_result[0] if balance_result else 100.0
            
            conn.close()
            
            # Check if risk management is within bounds (1% = $1 per trade for $100 account)
            status = 'OK'
            message = 'Risk management is compliant'
            
            if total_trades > 0:
                expected_risk_1pct = current_balance * 0.01
                if avg_risk > expected_risk_1pct * 1.5:  # 50% tolerance
                    status = 'WARNING'
                    message = f'Average risk too high: ${avg_risk:.2f} (expected ~${expected_risk_1pct:.2f})'
                elif max_risk > expected_risk_1pct * 2:  # Max 2x tolerance
                    status = 'WARNING'
                    message = f'Maximum risk too high: ${max_risk:.2f}'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'current_balance': round(current_balance, 2),
                    'avg_risk_per_trade': round(avg_risk, 2),
                    'max_risk_per_trade': round(max_risk, 2),
                    'expected_risk_1pct': round(current_balance * 0.01, 2)
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Risk management check error: {str(e)}',
                'details': {}
            }
    
    def _check_active_trades(self) -> Dict[str, Any]:
        """Check active trades status."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Get active trades
            cursor.execute("""
                SELECT 
                    symbol,
                    direction,
                    entry_price,
                    current_price,
                    unrealized_pnl,
                    entry_time
                FROM paper_trades
                WHERE status = 'OPEN'
                ORDER BY entry_time DESC
            """)
            
            active_trades = []
            for row in cursor.fetchall():
                active_trades.append({
                    'symbol': row[0],
                    'direction': row[1],
                    'entry_price': row[2],
                    'current_price': row[3],
                    'unrealized_pnl': row[4],
                    'entry_time': row[5]
                })
            
            conn.close()
            
            status = 'OK'
            message = f'{len(active_trades)} active trade(s)'
            
            # Check for stale trades (open > 24 hours)
            stale_trades = 0
            for trade in active_trades:
                entry_time = datetime.fromisoformat(trade['entry_time'])
                hours_open = (datetime.now() - entry_time).total_seconds() / 3600
                if hours_open > 24:
                    stale_trades += 1
            
            if stale_trades > 0:
                status = 'WARNING'
                message = f'{stale_trades} stale trade(s) open > 24 hours'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'active_trades_count': len(active_trades),
                    'stale_trades_count': stale_trades,
                    'trades': active_trades[:5]  # Return up to 5 trades
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Active trades check error: {str(e)}',
                'details': {}
            }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get general system metrics."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Get daily stats
            cursor.execute("""
                SELECT 
                    scan_count,
                    signals_generated,
                    date
                FROM daily_stats
                ORDER BY date DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                scan_count = result[0] or 0
                signals_generated = result[1] or 0
                last_update = result[2]
            else:
                scan_count = 0
                signals_generated = 0
                last_update = None
            
            conn.close()
            
            return {
                'status': 'OK',
                'message': 'System metrics collected',
                'details': {
                    'scan_count_today': scan_count,
                    'signals_generated_today': signals_generated,
                    'last_stats_update': last_update,
                    'uptime_status': 'operational'
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'System metrics error: {str(e)}',
                'details': {}
            }


def create_diagnostic_checker(db_path: str = "data/trading.db") -> SystemDiagnostic:
    """
    Factory function to create diagnostic checker.
    
    Args:
        db_path: Path to trading database
        
    Returns:
        SystemDiagnostic instance
    """
    return SystemDiagnostic(db_path)
