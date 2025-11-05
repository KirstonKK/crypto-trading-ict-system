# 🧹 Signal Cleanup System

## Overview

This system ensures that the monitor's "Today's Signals Summary" only shows **truly active** signals and automatically removes:

1. ✅ Closed trades (STOP_LOSS, TAKE_PROFIT, TIME_LIMIT, etc.)
2. ✅ Cancelled signals
3. ✅ Un-executed "orphan" signals older than 2 hours

## Problem Solved

### Issue

The monitor was showing closed trades in the "Today's Signals Summary" section because:

1. Some signals had close statuses like `MAX_HOLD_TIME_EXCEEDED` or `TIME_LIMIT` that weren't being filtered
2. Un-executed signals (generated but never traded) remained in `ACTIVE` status indefinitely

### Example

```
📈 Today's Signals Summary
28/10/2025  09:07  ₿ BTC  SELL  $114440.5000  62.0%  5m
```

This signal was generated at 09:07 but never executed as a trade, yet remained visible all day.

## Solution Implemented

### 1. Enhanced Status Filtering

**File**: `src/monitors/ict_enhanced_monitor.py`

Added comprehensive filtering that excludes ALL closed/completed statuses:

```python
# Define all possible closed/completed statuses to exclude
CLOSED_STATUSES = {
    'CANCELLED', 'STOP_LOSS', 'TAKE_PROFIT', 'SESSION_CLOSE',
    'TIME_LIMIT', 'MAX_HOLD_TIME_EXCEEDED', 'MANUAL_CLOSE', 'EXPIRED'
}

# Only show ACTIVE or FILLED signals
if signal_status in CLOSED_STATUSES or signal_status not in ('ACTIVE', 'FILLED'):
    continue  # Skip this signal
```

This filtering is applied in TWO places:

- **serialized_signals**: Recent signals for the live feed (last 5)
- **todays_summary**: All of today's signals for the summary table

### 2. Automatic Orphan Signal Cleanup

**File**: `src/monitors/ict_enhanced_monitor.py`

Added automatic cleanup that runs every analysis cycle (3-5 minutes):

```python
# Find ACTIVE signals older than 2 hours that have no corresponding trade
two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
cursor.execute("""
    SELECT s.signal_id, s.symbol, s.direction, s.entry_time
    FROM signals s
    WHERE s.status = 'ACTIVE'
    AND s.entry_time < ?
    AND NOT EXISTS (
        SELECT 1 FROM paper_trades pt
        WHERE pt.signal_id = s.signal_id
    )
""", (two_hours_ago,))

# Expire each orphan signal
for signal in orphan_signals:
    self.crypto_monitor.db.close_signal(signal_id, 0, 'EXPIRED')
```

### 3. Time-Based Trade Management

**File**: `src/trading/intraday_trade_manager.py`

Automatically closes trades exceeding maximum hold time (4 hours):

- Calculates trade duration
- Compares against max_hold_hours (default: 4.0)
- Auto-closes with `MAX_HOLD_TIME_EXCEEDED` status
- Updates signal status to match

## Signal Lifecycle

### Normal Flow (Executed Trade)

```
1. Signal Generated     → status: ACTIVE
2. Trade Executed       → status: FILLED
3. Trade Running        → status: FILLED
4. Exit via TP/SL       → status: TAKE_PROFIT or STOP_LOSS
   ✅ Removed from display
```

### Time-Limited Flow

```
1. Signal Generated     → status: ACTIVE
2. Trade Executed       → status: FILLED
3. Exceeds 4 hours      → status: MAX_HOLD_TIME_EXCEEDED
   ✅ Removed from display
```

### Un-Executed Flow (Orphan)

```
1. Signal Generated     → status: ACTIVE
2. Not executed         → status: ACTIVE (no trade created)
3. After 2 hours        → status: EXPIRED (auto-cleanup)
   ✅ Removed from display
```

## Why Un-Executed Signals Happen

Signals may not get executed for valid reasons:

1. **Confidence threshold**: Signal generated but below minimum confidence for trading
2. **Price movement**: Price moved away before trade could be placed
3. **Risk management**: Already at position limit
4. **Market conditions**: Volatility too high, spread too wide, etc.

These signals are informational and should be cleared after 2 hours since they're no longer relevant.

## Configuration

### Orphan Signal Expiry Time

**Location**: `src/monitors/ict_enhanced_monitor.py` line ~1356

```python
# Default: 2 hours
two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()

# To change to 1 hour:
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

# To change to 3 hours:
three_hours_ago = (datetime.now() - timedelta(hours=3)).isoformat()
```

### Trade Time Limits

**Location**: `src/monitors/ict_enhanced_monitor.py` line 127

```python
# Default: 4 hours maximum
self.trade_manager = create_trade_manager(max_hold_hours=4.0)

# To change to 3 hours:
self.trade_manager = create_trade_manager(max_hold_hours=3.0)
```

## Monitoring

### Check Signal Statuses

```bash
python3 << 'EOF'
import sqlite3
db = sqlite3.connect('data/trading.db')
cursor = db.execute("""
    SELECT status, COUNT(*) as count
    FROM signals
    WHERE date(created_date) = date('now')
    GROUP BY status
""")
print("Today's Signal Statuses:")
for row in cursor:
    print(f"  {row[0]}: {row[1]} signals")
db.close()
EOF
```

### Check for Orphan Signals

```bash
python3 << 'EOF'
import sqlite3
from datetime import datetime, timedelta
db = sqlite3.connect('data/trading.db')
two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
cursor = db.execute("""
    SELECT s.signal_id, s.symbol, s.direction, s.entry_time
    FROM signals s
    WHERE s.status = 'ACTIVE'
    AND s.entry_time < ?
    AND NOT EXISTS (
        SELECT 1 FROM paper_trades pt
        WHERE pt.signal_id = s.signal_id
    )
""", (two_hours_ago,))
orphans = cursor.fetchall()
print(f"Orphan signals (>2hrs old): {len(orphans)}")
for sig in orphans:
    print(f"  {sig[0]}: {sig[1]} {sig[2]} from {sig[3]}")
db.close()
EOF
```

### View Monitor Logs

```bash
# See cleanup activity
grep "🧹" logs/ict_monitor.log

# See time-based closures
grep "⏰" logs/ict_monitor.log
```

## Benefits

1. **Clean Display**: Only shows truly active signals
2. **Automatic Maintenance**: No manual cleanup required
3. **Database Integrity**: Signals properly closed with appropriate statuses
4. **Clear History**: Closed trades don't clutter the summary
5. **Performance**: Orphan signals don't accumulate over time

## Status Types Reference

| Status                   | Meaning                          | Display   |
| ------------------------ | -------------------------------- | --------- |
| `ACTIVE`                 | Signal generated, not yet traded | ✅ Shows  |
| `FILLED`                 | Signal executed as trade         | ✅ Shows  |
| `TAKE_PROFIT`            | Trade closed at target           | ❌ Hidden |
| `STOP_LOSS`              | Trade closed at stop             | ❌ Hidden |
| `TIME_LIMIT`             | Trade closed by time limit       | ❌ Hidden |
| `MAX_HOLD_TIME_EXCEEDED` | Trade held too long (>4hrs)      | ❌ Hidden |
| `SESSION_CLOSE`          | Trade closed at session end      | ❌ Hidden |
| `EXPIRED`                | Un-executed signal auto-expired  | ❌ Hidden |
| `CANCELLED`              | Signal cancelled manually        | ❌ Hidden |
| `MANUAL_CLOSE`           | Trade closed manually            | ❌ Hidden |

## Implementation Date

October 28, 2025

## Files Modified

1. `src/monitors/ict_enhanced_monitor.py`
   - Enhanced status filtering (lines ~1039-1085)
   - Automatic orphan cleanup (lines ~1354-1390)

## Testing

✅ Tested with BTC SELL signal from 09:07 (28/10/2025)
✅ Signal properly filtered after manual expiry
✅ Monitor restart confirmed clean display
✅ Automatic cleanup logic integrated

## Notes

- Cleanup runs every analysis cycle (3-5 minutes)
- Only affects signals, not the database scan history
- Balance is never affected by signal cleanup
- Closed trades remain in database for historical analysis
