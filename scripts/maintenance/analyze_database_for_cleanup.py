#!/usr/bin/env python3
"""
Database Analysis Script for Legacy Signal Cleanup
Analyzes the current database state to identify signals and trades that need cleanup
"""

import sqlite3
import sys
from datetime import datetime, timedelta
import json

def analyze_database():
    """Analyze the database and identify cleanup candidates"""
    try:
        conn = sqlite3.connect('databases/trading_data.db')
        cursor = conn.cursor()
        
        print('🔍 DATABASE ANALYSIS FOR CLEANUP')
        print('=' * 60)
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f'📋 Tables found: {tables}')
        
        # Analyze signals table
        if 'signals' in tables:
            print('\n📊 SIGNALS TABLE ANALYSIS')
            print('-' * 30)
            
            # Get table schema
            cursor.execute("PRAGMA table_info(signals)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f'Columns: {columns}')
            
            # Total count
            cursor.execute('SELECT COUNT(*) FROM signals')
            total_signals = cursor.fetchone()[0]
            print(f'Total signals: {total_signals}')
            
            # Recent signals analysis
            cursor.execute('''
                SELECT symbol, signal_type, entry_time, 
                       COALESCE(bias_strength, 'NULL') as bias_strength, 
                       COALESCE(confluence_score, 'NULL') as confluence_score 
                FROM signals 
                ORDER BY entry_time DESC 
                LIMIT 15
            ''')
            recent_signals = cursor.fetchall()
            print(f'\n📈 Last 15 signals:')
            for i, signal in enumerate(recent_signals, 1):
                symbol, signal_type, entry_time, bias_strength, confluence = signal
                print(f'  {i:2d}. {entry_time}: {symbol} {signal_type} (Bias: {bias_strength}, Confluence: {confluence})')
            
            # Identify low quality signals if quality columns exist
            if 'bias_strength' in columns and 'confluence_score' in columns:
                cursor.execute('''
                    SELECT COUNT(*) FROM signals 
                    WHERE (bias_strength < 0.6 OR confluence_score < 0.7)
                    AND bias_strength IS NOT NULL AND confluence_score IS NOT NULL
                ''')
                low_quality = cursor.fetchone()[0]
                print(f'\n⚠️  Low quality signals (bias<0.6 OR confluence<0.7): {low_quality}')
                
                # Show examples of low quality signals
                cursor.execute('''
                    SELECT symbol, signal_type, entry_time, bias_strength, confluence_score
                    FROM signals 
                    WHERE (bias_strength < 0.6 OR confluence_score < 0.7)
                    AND bias_strength IS NOT NULL AND confluence_score IS NOT NULL
                    ORDER BY entry_time DESC
                    LIMIT 10
                ''')
                low_quality_examples = cursor.fetchall()
                if low_quality_examples:
                    print('\n🔍 Examples of low quality signals:')
                    for signal in low_quality_examples:
                        symbol, signal_type, entry_time, bias, confluence = signal
                        print(f'  {entry_time}: {symbol} {signal_type} (Bias: {bias:.3f}, Confluence: {confluence:.3f})')
        
        # Analyze paper_trades table
        if 'paper_trades' in tables:
            print('\n💼 PAPER TRADES TABLE ANALYSIS')
            print('-' * 30)
            
            # Get table schema
            cursor.execute("PRAGMA table_info(paper_trades)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f'Columns: {columns}')
            
            # Total count
            cursor.execute('SELECT COUNT(*) FROM paper_trades')
            total_trades = cursor.fetchone()[0]
            print(f'Total paper trades: {total_trades}')
            
            # Recent trades
            cursor.execute('''
                SELECT symbol, trade_type, entry_time, status
                FROM paper_trades 
                ORDER BY entry_time DESC 
                LIMIT 10
            ''')
            recent_trades = cursor.fetchall()
            print(f'\n📈 Last 10 paper trades:')
            for i, trade in enumerate(recent_trades, 1):
                symbol, trade_type, entry_time, status = trade
                print(f'  {i:2d}. {entry_time}: {symbol} {trade_type} ({status})')
            
            # Analyze by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM paper_trades 
                GROUP BY status
                ORDER BY count DESC
            ''')
            status_counts = cursor.fetchall()
            print(f'\nTrades by status:')
            for status, count in status_counts:
                print(f'  {status}: {count}')
        
        # Time range analysis
        print('\n📅 TIME RANGE ANALYSIS')
        print('-' * 30)
        
        if 'signals' in tables:
            cursor.execute('SELECT MIN(entry_time), MAX(entry_time) FROM signals')
            signal_range = cursor.fetchone()
            if signal_range[0]:
                print(f'Signals: {signal_range[0]} to {signal_range[1]}')
        
        if 'paper_trades' in tables:
            cursor.execute('SELECT MIN(entry_time), MAX(entry_time) FROM paper_trades')
            trade_range = cursor.fetchone()
            if trade_range[0]:
                print(f'Trades: {trade_range[0]} to {trade_range[1]}')
        
        # Today's activity
        today = datetime.now().strftime('%Y-%m-%d')
        print(f'\n📊 TODAY\'S ACTIVITY ({today})')
        print('-' * 30)
        
        if 'signals' in tables:
            cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?", (today,))
            today_signals = cursor.fetchone()[0]
            print(f'Signals today: {today_signals}')
        
        if 'paper_trades' in tables:
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) = ?", (today,))
            today_trades = cursor.fetchone()[0]
            print(f'Paper trades today: {today_trades}')
        
        conn.close()
        
        print('\n✅ Database analysis complete!')
        return True
        
    except Exception as e:
        print(f'❌ Error analyzing database: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_database()