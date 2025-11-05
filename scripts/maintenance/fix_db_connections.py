#!/usr/bin/env python3
"""
Quick script to replace all remaining sqlite3.connect(self.db_path) calls
with self._get_connection() in trading_database.py
"""

import re

file_path = 'src/database/trading_database.py'

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Replace all remaining occurrences
original_content = content
content = content.replace('sqlite3.connect(self.db_path)', 'self._get_connection()')

# Count replacements
count = original_content.count('sqlite3.connect(self.db_path)') - content.count('sqlite3.connect(self.db_path)')

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print(f"✅ Replaced {count} occurrences of sqlite3.connect(self.db_path) with self._get_connection()")
print(f"📝 File: {file_path}")
