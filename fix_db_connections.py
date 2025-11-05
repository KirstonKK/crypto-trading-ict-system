#!/usr/bin/env python3
"""
Quick script to replace all remaining sqlite3.connect(self.db_path) calls
with self._get_connection() in trading_database.py
"""

import re

file_path = 'src/database/trading_database.py'

# Constants
OLD_PATTERN = 'sqlite3.connect(self.db_path)'
NEW_PATTERN = 'self._get_connection()'

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Replace all remaining occurrences
original_content = content
content = content.replace(OLD_PATTERN, NEW_PATTERN)

# Count replacements
count = original_content.count(OLD_PATTERN) - content.count(OLD_PATTERN)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print(f"✅ Replaced {count} occurrences of {OLD_PATTERN} with {NEW_PATTERN}")
print(f"📝 File: {file_path}")
