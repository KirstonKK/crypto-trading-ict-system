#!/usr/bin/env python3

import sqlite3

DATABASE_PATH = 'databases/trading_data.db'

def check_database_schema():
    """Check the database schema and current data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(paper_trades)")
        columns = cursor.fetchall()
        
        print("📋 Paper trades table schema:")
        for _ in columns:
            print("  Checking columns...")
        
        # Get all trades today using correct column names
        cursor.execute("SELECT * FROM paper_trades LIMIT 5")
        trades = cursor.fetchall()
        
        print(f"\n📊 Sample trades (first 5): {len(trades)} found")
            
        # Count today's trades using different approach
        cursor.execute("SELECT COUNT(*) FROM paper_trades")
        print(f"\n📈 Total trades in database: {cursor.fetchone()[0]}")
        
        # Check for daily PnL calculation
        cursor.execute("""
            SELECT SUM(realized_pnl) 
            FROM paper_trades 
            WHERE DATE(exit_time) = DATE('now') 
            AND status = 'CLOSED'
        """)
        
        result = cursor.fetchone()
        
        print(f"💰 Daily PnL: ${result[0] if result[0] is not None else 0.0:.2f}")
        
        conn.close()
        
    except Exception:
        print("❌ Error checking schema")

if __name__ == "__main__":
    check_database_schema()