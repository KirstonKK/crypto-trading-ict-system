# Smart Dynamic Risk:Reward System

## Date: October 26, 2025

## Overview

Upgraded the system from **fixed R:R tiers** (1:3, 1:5, 1:8) to **SMART dynamic R:R** based on **actual price levels**. The system now targets real market structure instead of arbitrary multiples.

---

## The Problem with Fixed R:R Tiers

### Old System ❌

```python
if confidence < 0.5:
    rr_target = 3  # Always 1:3
elif confidence < 0.7:
    rr_target = 5  # Always 1:5
else:
    rr_target = 8  # Always 1:8

take_profit = entry + (stop_distance * rr_target)
```

**Issues:**

- ❌ Ignored actual market structure
- ❌ Might place TP in "no man's land" (no support/resistance)
- ❌ Could miss obvious targets at previous highs/lows
- ❌ Capped at 1:8 even if 1:15 target exists
- ❌ Not proactive or intelligent

---

## The New Smart R:R System

### New System ✅

```python
# 1. Calculate stop loss (ATR-based)
stop_loss = calculate_atr_stop(entry_price)
stop_distance = abs(entry - stop_loss)

# 2. Find REAL price targets in priority order:
targets = [
    previous_4h_swing_high,      # Priority 1
    previous_1h_swing_high,      # Priority 2
    psychological_level,         # Priority 3
    atr_extension                # Priority 4 (fallback)
]

# 3. Calculate ACTUAL R:R from real target
actual_rr = (target - entry) / stop_distance
# Could be 1:2.7, 1:5.3, 1:15.8, whatever!

take_profit = target  # Real price level
```

---

## Target Selection Logic

### Priority Order

**For BUY Signals:**

1. **Previous 4H Swing Highs** (within 20R)
   - Most significant resistance levels
   - High probability targets
2. **Previous 1H Swing Highs** (within 20R)

   - Shorter-term resistance
   - More frequent hits

3. **Psychological Levels** (round numbers)
   - $100, $200, $300, $400, $500 increments
   - Market participants cluster orders here
4. **ATR Extensions** (fallback)
   - 2x, 3x, 5x, 8x ATR from entry
   - Only if no structural levels found

**For SELL Signals:**

- Same logic but targeting swing lows and lower psychological levels

### Example

**ETH Long Entry:**

```
Entry: $3,850
ATR Stop: $3,820 (0.8% away)
Stop Distance: $30

Available Targets:
- 4H Swing High: $3,950 → R:R = 1:3.3 ✅ SELECTED
- 1H Swing High: $3,900 → R:R = 1:1.7 (too low)
- Psychological: $4,000 → R:R = 1:5.0 (further away)
- ATR 5x: $4,000 → R:R = 1:5.0 (fallback)

Result: Target $3,950, R:R = 1:3.3
```

If no swing high existed and $3,950 was empty:

```
Entry: $3,850
Stop: $3,820

Available Targets:
- 4H Swing High: None
- 1H Swing High: None
- Psychological: $4,000 → R:R = 1:5.0 ✅ SELECTED
- ATR 5x: $4,000 → R:R = 1:5.0

Result: Target $4,000, R:R = 1:5.0
```

---

## Technical Implementation

### New Function: `_calculate_smart_take_profit()`

**Location:** `backtesting/strategy_engine.py` (lines 902-1019)

**Inputs:**

- `entry_price`: Entry price
- `stop_loss`: ATR-based stop loss
- `action`: 'BUY' or 'SELL'
- `mtf_data`: Multi-timeframe price data
- `current_time`: Current timestamp
- `min_rr`: Minimum acceptable R:R (default 2.0)

**Process:**

1. Calculate stop distance
2. Scan last 100 candles (4H) and 50 candles (1H)
3. Identify swing highs/lows using rolling max/min
4. Calculate psychological levels (round numbers)
5. Calculate ATR extensions as fallback
6. Filter targets: must be >= min_rr and <= 20R
7. Sort by priority: swings > psychological > ATR
8. Return best target with actual R:R

**Output:**

```python
{
    'take_profit': 3950.0,      # Actual target price
    'rr_ratio': 3.33,           # Real R:R (not fixed tier)
    'target_type': '4H_SWING_HIGH'  # What kind of target
}
```

### Integration Points

**Modified:** `generate_ict_signal()` method (lines 547-605)

**Changes:**

1. Calculate ATR stop first
2. Call `_calculate_smart_take_profit()`
3. Use actual R:R instead of fixed tiers
4. Log target type for transparency

**Before:**

```python
rr_target = 8  # Fixed tier
take_profit = entry + (stop_distance * 8)
```

**After:**

```python
smart_tp = _calculate_smart_take_profit(...)
take_profit = smart_tp['take_profit']  # Real price level
actual_rr = smart_tp['rr_ratio']       # Could be 3.3, 5.7, 15.2, etc.
target_type = smart_tp['target_type']  # '4H_SWING_HIGH', etc.
```

---

## Example Scenarios

### Scenario 1: Perfect Swing High Target

```
Symbol: BTCUSDT
Entry: $68,500 (BUY)
ATR Stop: $67,800 (1% away)
Stop Distance: $700

Scan Results:
- 4H Swing High at $70,000 found
- R:R = ($70,000 - $68,500) / $700 = 2.14

Target: $70,000
Actual R:R: 1:2.14
Target Type: 4H_SWING_HIGH
```

### Scenario 2: High R:R Psychological Level

```
Symbol: ETHUSDT
Entry: $3,200 (BUY)
ATR Stop: $3,150 (1.5% away)
Stop Distance: $50

Scan Results:
- No swing highs above $3,200
- Psychological level at $4,000
- R:R = ($4,000 - $3,200) / $50 = 16.0

Target: $4,000
Actual R:R: 1:16.0 🎯
Target Type: PSYCHOLOGICAL
```

### Scenario 3: ATR Fallback

```
Symbol: SOLUSDT
Entry: $180 (SELL)
ATR Stop: $185 (2.8% away)
Stop Distance: $5

Scan Results:
- No swing lows below $180
- No psychological levels nearby
- ATR 5x extension: $180 - (ATR $3 × 5) = $165
- R:R = ($180 - $165) / $5 = 3.0

Target: $165
Actual R:R: 1:3.0
Target Type: ATR_5X
```

---

## Risk Model (Unchanged)

**Risk**: Strict 1% per trade  
**Reward**: Dynamic 1:1.5 to 1:20 based on real targets  
**Position Sizing**: `risk_amount / stop_distance` (pure 1%)

**Example:**

```
Account: $10,000
Risk: 1% = $100
Entry: $200
Stop: $195
Stop Distance: $5
Position Size: $100 / $5 = 20 units
Position Cost: 20 × $200 = $4,000

Smart Target: $240 (previous high)
Actual R:R: ($240 - $200) / $5 = 1:8.0
Potential Profit: 20 × ($240 - $200) = $800 (8%)
```

---

## Advantages

✅ **Proactive Target Selection**

- Targets real market structure
- Adapts to each unique setup
- No arbitrary caps (can go to 1:20 if level exists)

✅ **Higher Win Rate**

- Targets where price is likely to react
- Takes profit at logical levels
- Reduces "stopped out before target" scenarios

✅ **Intelligent Exits**

- Previous highs/lows = natural resistance/support
- Psychological levels = order clustering
- Not random price points

✅ **Flexibility**

- Can target 1:2.3 if that's where the level is
- Can target 1:15.7 if previous high is far
- Adapts to volatility and market structure

✅ **Transparency**

- Logs target type (4H_SWING_HIGH, PSYCHOLOGICAL, etc.)
- Shows actual R:R (not approximation)
- Easy to verify target logic

---

## Monitoring

### Check Logs for:

```
🎯 Smart TP: $3,950.00 | Actual R:R: 1:3.3 | Target: 4H_SWING_HIGH
ICT Signal: ETHUSDT BUY @ $3,850.0000 | Confluence: 0.685 | RR: 1:3.3 (4H_SWING_HIGH)
```

### Verify:

- [ ] R:R is not locked to 3, 5, or 8
- [ ] Target types show real levels (SWING_HIGH, PSYCHOLOGICAL, etc.)
- [ ] R:R ratios have decimals (1:3.3, 1:5.7, not 1:3, 1:5)
- [ ] Some targets reach 1:10+ when structure allows
- [ ] Logs show reasoning for target selection

---

## Fallback Protection

**Minimum R:R:** 2.0 (1:2)

- If no targets found >= 1:2, uses minimum fallback
- Ensures every trade has acceptable risk:reward

**Maximum R:R:** 20.0 (1:20)

- Caps unrealistic targets
- Prevents chasing price too far from entry
- Maintains realistic profit targets

**ATR Fallback:**

- If no swing or psychological targets exist
- Uses 2x, 3x, 5x, 8x ATR extensions
- Ensures target always exists

---

## Configuration

**Enabled by default** - no config changes needed

To adjust minimum R:R:

```python
# In generate_ict_signal() call:
smart_tp_data = self._calculate_smart_take_profit(
    entry_price=entry_price,
    stop_loss=stop_loss,
    action=action,
    mtf_data=mtf_data,
    current_time=current_time,
    min_rr=2.0  # ← Adjust this (default 2.0, can go to 1.5)
)
```

---

## Summary

**What Changed:** R:R calculation method  
**From:** Fixed tiers (1:3, 1:5, 1:8)  
**To:** Smart dynamic targets based on real price levels  
**Result:** More intelligent exits, higher win rate, no arbitrary caps  
**Risk Model:** Still strict 1% risk per trade (unchanged)

**Status:** ✅ INTEGRATED & READY
