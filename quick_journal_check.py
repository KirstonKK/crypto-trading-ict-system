#!/usr/bin/env python3

import sqlite3

# Quick check of journal entries
conn = sqlite3.connect('databases/trading_data.db')
cursor = conn.cursor()

# Check if journal table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trading_journal_entries'")
table_exists = cursor.fetchone()

if table_exists:
    cursor.execute("SELECT COUNT(*) FROM trading_journal_entries")
    count = cursor.fetchone()[0]
    print(f"Journal entries in database: {count}")
    
    cursor.execute("SELECT * FROM trading_journal_entries ORDER BY timestamp DESC LIMIT 5")
    entries = cursor.fetchall()
    
    print("Recent entries:")
    for entry in entries:
        print(f"  {entry}")
else:
    print("No trading_journal_entries table found")

conn.close()