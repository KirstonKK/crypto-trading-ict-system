#!/usr/bin/env python3
"""
Restore Scan Count from Database
================================

Restores the scan count from database records to fix the lost counter issue.
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def restore_scan_count():
    """Restore scan count from database records"""
    try:
        # Connect to database
        conn = sqlite3.connect('databases/trading_data.db')
        cursor = conn.cursor()
        
        # Get today's scan count
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as scan_count 
            FROM scan_history 
            WHERE date(timestamp) = ?
        """, (today,))
        
        result = cursor.fetchone()
        scan_count = result[0] if result else 0
        
        logger.info(f"📊 Database shows {scan_count} scans for today ({today})")
        
        # Get signal count for today
        cursor.execute("""
            SELECT COUNT(*) as signal_count 
            FROM signals 
            WHERE date(timestamp) = ?
        """, (today,))
        
        result = cursor.fetchone()
        signal_count = result[0] if result else 0
        
        logger.info(f"📈 Database shows {signal_count} signals for today")
        
        # Get latest system statistics
        cursor.execute("""
            SELECT * FROM system_statistics 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            logger.info(f"📋 Latest system stats: {result}")
        
        # Update daily stats with correct count
        cursor.execute("""
            INSERT OR REPLACE INTO daily_stats 
            (date, total_scans, signals_generated, scan_signal_ratio, session_multiplier, market_volatility) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (today, scan_count, signal_count, 
              f"{signal_count}/{scan_count}" if scan_count > 0 else "0/0",
              1.0, 1.0))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Scan count restored: {scan_count} scans, {signal_count} signals for today")
        
        return scan_count, signal_count
        
    except Exception as e:
        logger.error(f"❌ Error restoring scan count: {e}")
        return 0, 0

if __name__ == "__main__":
    print("🔄 RESTORING SCAN COUNT FROM DATABASE")
    print("=" * 50)
    
    scan_count, signal_count = restore_scan_count()
    
    print("=" * 50)
    print(f"✅ RESTORATION COMPLETE")
    print(f"📊 Today's Scans: {scan_count}")
    print(f"📈 Today's Signals: {signal_count}")
    print(f"📋 Ratio: {signal_count}/{scan_count}")