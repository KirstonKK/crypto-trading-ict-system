#!/usr/bin/env python3

import sqlite3

def check_database_schema():
    """Check the database schema and current data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(paper_trades)")
        columns = cursor.fetchall()
        
        print("📋 Paper trades table schema:")
        for col in columns:
            print("  {col[1]} ({col[2]})")
        
        # Get all trades today using correct column names
        cursor.execute("SELECT * FROM paper_trades LIMIT 5")
        trades = cursor.fetchall()
        
        print("\n📊 Sample trades (first 5):")
        for i, trade in enumerate(trades):
            print("  Trade {i+1}: {trade}")
            
        # Count today's trades using different approach
        cursor.execute("SELECT COUNT(*) FROM paper_trades")
        total_count = cursor.fetchone()[0]
        print("\n📈 Total trades in database: {total_count}")
        
        # Check for daily PnL calculation
        cursor.execute("""
            SELECT SUM(realized_pnl) 
            FROM paper_trades 
            WHERE DATE(exit_time) = DATE('now') 
            AND status = 'CLOSED'
        """)
        
        result = cursor.fetchone()
        daily_pnl = result[0] if result[0] is not None else 0.0
        
        print("💰 Daily PnL: ${daily_pnl:.2f}")
        
        conn.close()
        
    except Exception as e:
        print("❌ Error: {e}")

if __name__ == "__main__":
    check_database_schema()