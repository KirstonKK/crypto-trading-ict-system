#!/usr/bin/env python3
"""
Safe Database Cleanup Script
Removes legacy signals and paper trades generated before the conservative threshold fix
while preserving persistence functionality and system integrity
"""

import sqlite3
import sys
from datetime import datetime, timedelta
import json
import os

def backup_database():
    """Create a backup of the database before cleanup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'trading_data_backup_{timestamp}.db'
    
    try:
        # Copy the database file
        import shutil
        shutil.copy2('trading_data.db', backup_name)
        print(f'✅ Database backed up to: {backup_name}')
        return backup_name
    except Exception as e:
        print(f'❌ Failed to backup database: {e}')
        return None

def analyze_cleanup_scope():
    """Analyze what data will be affected by cleanup"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print('🔍 CLEANUP SCOPE ANALYSIS')
        print('=' * 40)
        
        # Check current time for reference
        today = datetime.now().strftime('%Y-%m-%d')
        print(f'Current date: {today}')
        
        # Analyze signals table
        try:
            # Get total signals
            cursor.execute('SELECT COUNT(*) FROM signals')
            total_signals = cursor.fetchone()[0]
            
            # Get signals from today
            cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) >= ?", (today,))
            today_signals = cursor.fetchone()[0]
            
            # Get signals before today (candidates for cleanup)
            cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) < ?", (today,))
            old_signals = cursor.fetchone()[0]
            
            print(f'📊 SIGNALS ANALYSIS:')
            print(f'  Total signals: {total_signals}')
            print(f'  Signals from today ({today}): {today_signals}')
            print(f'  Signals before today (cleanup candidates): {old_signals}')
            
            # Show examples of old signals
            if old_signals > 0:
                cursor.execute("""
                    SELECT symbol, signal_type, entry_time, 
                           COALESCE(bias_strength, 'NULL') as bias_strength,
                           COALESCE(confluence_score, 'NULL') as confluence_score
                    FROM signals 
                    WHERE date(entry_time) < ?
                    ORDER BY entry_time DESC 
                    LIMIT 10
                """, (today,))
                old_signal_examples = cursor.fetchall()
                print(f'\\n📈 Examples of old signals to be removed:')
                for signal in old_signal_examples:
                    symbol, signal_type, entry_time, bias, confluence = signal
                    print(f'  {entry_time}: {symbol} {signal_type} (Bias: {bias}, Confluence: {confluence})')
                    
        except Exception as e:
            print(f'❌ Error analyzing signals: {e}')
        
        # Analyze paper_trades table
        try:
            # Get total trades
            cursor.execute('SELECT COUNT(*) FROM paper_trades')
            total_trades = cursor.fetchone()[0]
            
            # Get trades from today
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) >= ?", (today,))
            today_trades = cursor.fetchone()[0]
            
            # Get trades before today
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) < ?", (today,))
            old_trades = cursor.fetchone()[0]
            
            print(f'\\n💼 PAPER TRADES ANALYSIS:')
            print(f'  Total paper trades: {total_trades}')
            print(f'  Trades from today ({today}): {today_trades}')
            print(f'  Trades before today (cleanup candidates): {old_trades}')
            
            # Show examples of old trades
            if old_trades > 0:
                cursor.execute("""
                    SELECT symbol, trade_type, entry_time, status
                    FROM paper_trades 
                    WHERE date(entry_time) < ?
                    ORDER BY entry_time DESC 
                    LIMIT 10
                """, (today,))
                old_trade_examples = cursor.fetchall()
                print(f'\\n📈 Examples of old trades to be removed:')
                for trade in old_trade_examples:
                    symbol, trade_type, entry_time, status = trade
                    print(f'  {entry_time}: {symbol} {trade_type} ({status})')
        
        except Exception as e:
            print(f'❌ Error analyzing paper trades: {e}')
        
        # Check daily_stats (should be preserved)
        try:
            cursor.execute('SELECT COUNT(*) FROM daily_stats')
            total_daily_stats = cursor.fetchone()[0]
            print(f'\\n📊 DAILY STATS (will be preserved): {total_daily_stats} records')
            
            # Show recent daily stats
            cursor.execute('SELECT date, scan_count, signals_generated FROM daily_stats ORDER BY date DESC LIMIT 5')
            recent_stats = cursor.fetchall()
            print('Recent daily stats:')
            for date_str, scans, signals in recent_stats:
                print(f'  {date_str}: {scans} scans, {signals} signals')
                
        except Exception as e:
            print(f'❌ Error analyzing daily stats: {e}')
        
        conn.close()
        return old_signals, old_trades
        
    except Exception as e:
        print(f'❌ Error during analysis: {e}')
        return 0, 0

def perform_cleanup(confirm=False):
    """Perform the actual cleanup of legacy data"""
    if not confirm:
        print('\\n⚠️  This is a DRY RUN - no data will be deleted')
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f'\\n🧹 PERFORMING CLEANUP (Dry Run: {not confirm})')
        print('=' * 50)
        
        # Clean up signals before today
        if confirm:
            cursor.execute("DELETE FROM signals WHERE date(entry_time) < ?", (today,))
            signals_deleted = cursor.rowcount
        else:
            cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) < ?", (today,))
            signals_deleted = cursor.fetchone()[0]
        
        print(f'📊 Signals {"deleted" if confirm else "would be deleted"}: {signals_deleted}')
        
        # Clean up paper trades before today
        if confirm:
            cursor.execute("DELETE FROM paper_trades WHERE date(entry_time) < ?", (today,))
            trades_deleted = cursor.rowcount
        else:
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) < ?", (today,))
            trades_deleted = cursor.fetchone()[0]
        
        print(f'💼 Paper trades {"deleted" if confirm else "would be deleted"}: {trades_deleted}')
        
        # Preserve daily_stats, scan_history, and other persistence data
        print(f'\\n✅ PRESERVED DATA:')
        cursor.execute('SELECT COUNT(*) FROM daily_stats')
        daily_stats_count = cursor.fetchone()[0]
        print(f'📊 Daily stats records: {daily_stats_count} (preserved)')
        
        try:
            cursor.execute('SELECT COUNT(*) FROM scan_history')
            scan_history_count = cursor.fetchone()[0]
            print(f'🔍 Scan history records: {scan_history_count} (preserved)')
        except Exception:
            print(f'🔍 Scan history: table not found (ok)')
        
        if confirm:
            conn.commit()
            print(f'\\n✅ Cleanup completed successfully!')
        else:
            print(f'\\n🔍 Dry run completed - use --confirm to execute cleanup')
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Error during cleanup: {e}')
        if confirm:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        return False

def verify_system_integrity():
    """Verify that persistence code and system functionality is intact"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print('\\n🔍 VERIFYING SYSTEM INTEGRITY')
        print('=' * 40)
        
        # Check that essential tables still exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        essential_tables = ['signals', 'paper_trades', 'daily_stats']
        missing_tables = [table for table in essential_tables if table not in tables]
        
        if missing_tables:
            print(f'❌ Missing essential tables: {missing_tables}')
            return False
        else:
            print(f'✅ All essential tables present: {essential_tables}')
        
        # Check that daily_stats is intact (critical for persistence)
        cursor.execute('SELECT COUNT(*) FROM daily_stats')
        daily_stats_count = cursor.fetchone()[0]
        if daily_stats_count > 0:
            print(f'✅ Daily stats intact: {daily_stats_count} records')
        else:
            print(f'⚠️  Daily stats empty - this might affect persistence')
        
        # Check that current day's data is preserved
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) >= ?", (today,))
        today_signals = cursor.fetchone()[0]
        print(f'✅ Today\'s signals preserved: {today_signals}')
        
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) >= ?", (today,))
        today_trades = cursor.fetchone()[0]
        print(f'✅ Today\'s trades preserved: {today_trades}')
        
        conn.close()
        print(f'\\n✅ System integrity verified!')
        return True
        
    except Exception as e:
        print(f'❌ Error verifying integrity: {e}')
        return False

def main():
    """Main cleanup function"""
    print('🧹 LEGACY SIGNAL & TRADE CLEANUP TOOL')
    print('=' * 60)
    print('This tool removes signals and paper trades generated before')
    print('the conservative threshold fix while preserving system integrity.')
    print()
    
    # Check if database exists
    if not os.path.exists('trading_data.db'):
        print('❌ trading_data.db not found!')
        return False
    
    # Analyze what will be cleaned up
    old_signals, old_trades = analyze_cleanup_scope()
    
    if old_signals == 0 and old_trades == 0:
        print('\\n✅ No legacy data found - database is already clean!')
        return True
    
    # Create backup
    print('\\n📋 Creating backup...')
    backup_file = backup_database()
    if not backup_file:
        print('❌ Failed to create backup - aborting for safety')
        return False
    
    # Ask for confirmation
    confirm = '--confirm' in sys.argv
    if not confirm:
        print('\\n⚠️  DRY RUN MODE')
        print('Add --confirm flag to actually perform cleanup')
        print('Example: python3 database_cleanup.py --confirm')
    
    # Perform cleanup
    success = perform_cleanup(confirm=confirm)
    
    if success and confirm:
        # Verify integrity after cleanup
        integrity_ok = verify_system_integrity()
        if integrity_ok:
            print(f'\\n🎉 CLEANUP SUCCESSFUL!')
            print(f'   Backup saved: {backup_file}')
            print(f'   System integrity verified')
            print(f'   Persistence functionality preserved')
        else:
            print(f'\\n⚠️  Cleanup completed but integrity check failed')
            print(f'   Consider restoring from backup: {backup_file}')
    
    return success

if __name__ == "__main__":
    main()