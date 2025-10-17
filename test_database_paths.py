#!/usr/bin/env python3

import sqlite3
from datetime import date

def test_database_path():
    """Test both database paths to confirm the fix"""
    today = date.today().isoformat()
    
    print("🗓️  Testing for date: {today}")
    
    # Test old path (should fail or return 0)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM paper_trades 
            WHERE date(exit_time) = ? 
            AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
            AND status != 'CLEANUP'
        """, (today,))
        old_result = cursor.fetchone()[0]
        conn.close()
        print("📊 Old path ('trading_data.db'): ${old_result:.2f}")
    except Exception as e:
        print("❌ Old path failed: {e}")
    
    # Test new path (should return -2.8)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM paper_trades 
            WHERE date(exit_time) = ? 
            AND status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
            AND status != 'CLEANUP'
        """, (today,))
        new_result = cursor.fetchone()[0]
        conn.close()
        print("✅ New path (DATABASE_PATH): ${new_result:.2f}")
        
        if new_result == -2.8:
            print("🎉 SUCCESS: The fix is working! Daily PnL should now show -$2.80")
        else:
            print("⚠️  Expected -$2.80, got ${new_result:.2f}")
            
    except Exception as e:
        print("❌ New path failed: {e}")

if __name__ == "__main__":
    test_database_path()