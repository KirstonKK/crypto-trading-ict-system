#!/usr/bin/env python3
"""Enable WAL mode permanently on the database"""
import sqlite3

db_path = 'data/trading.db'

print(f"🔧 Enabling WAL mode on {db_path}...")

conn = sqlite3.connect(db_path, timeout=30.0)
cursor = conn.cursor()

# Enable WAL mode (persists across connections)
cursor.execute('PRAGMA journal_mode=WAL')
result = cursor.fetchone()[0]
print(f"✅ Journal mode set to: {result}")

# Set busy timeout
cursor.execute('PRAGMA busy_timeout=30000')
print("✅ Busy timeout set to 30 seconds")

# Set synchronous mode
cursor.execute('PRAGMA synchronous=NORMAL')
print("✅ Synchronous mode set to NORMAL")

# Verify settings
cursor.execute('PRAGMA journal_mode')
print(f"📊 Current journal_mode: {cursor.fetchone()[0]}")

cursor.execute('PRAGMA busy_timeout')
print(f"📊 Current busy_timeout: {cursor.fetchone()[0]}ms")

cursor.execute('PRAGMA synchronous')
print(f"📊 Current synchronous: {cursor.fetchone()[0]}")

conn.close()
print("✅ WAL mode enabled successfully!")
