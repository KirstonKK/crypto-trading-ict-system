# Diagnostic System and SOL Trade Analysis - Documentation

## Overview

This implementation adds two major features to the crypto trading system:

1. **System Diagnostic Checker** - Comprehensive health monitoring and performance analysis
2. **SOL Trade Analyzer** - Specialized analysis for Solana trading opportunities using ICT methodology

---

## 1. System Diagnostic Checker

### Purpose
Monitors the overall health of the trading system, checking database integrity, trading performance, signal quality, risk management compliance, and active trades.

### Location
- Module: `core/diagnostics/system_diagnostic.py`
- API Endpoint: `/api/diagnostic`

### Features

#### Database Health Check
- Verifies database connectivity and integrity
- Checks table counts and database size
- Validates data persistence

#### Trading Performance Analysis
- Analyzes today's trading metrics
- Calculates win rate and P&L
- Identifies performance issues
- Monitors open and closed trades

#### Signal Quality Monitoring
- Tracks signal generation frequency
- Measures average confluence scores
- Monitors symbols traded
- Flags low-quality signals

#### Risk Management Compliance
- Verifies 1% risk per trade rule
- Monitors position sizing
- Checks balance consistency
- Flags excessive risk exposure

#### Active Trades Monitor
- Lists currently open trades
- Identifies stale trades (>24 hours)
- Tracks unrealized P&L
- Monitors trade duration

#### System Metrics
- Scan count tracking
- Signal generation statistics
- Uptime monitoring
- Last update timestamps

### API Usage

#### Request
```bash
GET /api/diagnostic
```

#### Response Example
```json
{
  "timestamp": "2025-10-28T16:01:09.450474",
  "overall_status": "HEALTHY",
  "issue_count": 0,
  "issues": [],
  "checks": {
    "database": {
      "status": "OK",
      "message": "Database is healthy",
      "details": {
        "integrity": "ok",
        "size_mb": 0.05,
        "tables": {
          "signals": 1,
          "paper_trades": 0,
          "daily_stats": 1
        }
      }
    },
    "trading_performance": {
      "status": "OK",
      "message": "Trading performance is normal",
      "details": {
        "total_trades_today": 0,
        "open_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "win_rate": 0.0,
        "total_pnl": 0.0,
        "avg_pnl": 0.0
      }
    },
    "signal_quality": {
      "status": "OK",
      "message": "Signal quality is acceptable",
      "details": {
        "signals_today": 1,
        "avg_confluence_score": 0.85,
        "symbols_traded": 1
      }
    },
    "risk_management": {
      "status": "OK",
      "message": "Risk management is compliant",
      "details": {
        "current_balance": 100.0,
        "avg_risk_per_trade": 0.0,
        "max_risk_per_trade": 0.0,
        "expected_risk_1pct": 1.0
      }
    },
    "active_trades": {
      "status": "OK",
      "message": "0 active trade(s)",
      "details": {
        "active_trades_count": 0,
        "stale_trades_count": 0,
        "trades": []
      }
    },
    "system_metrics": {
      "status": "OK",
      "message": "System metrics collected",
      "details": {
        "scan_count_today": 50,
        "signals_generated_today": 10,
        "last_stats_update": "2025-10-28",
        "uptime_status": "operational"
      }
    }
  }
}
```

#### Status Levels
- `HEALTHY` - All systems operational
- `WARNING` - Minor issues detected (low win rate, stale trades, etc.)
- `ERROR` - Critical issues (database failure, corruption, etc.)

### Usage in Code

```python
from core.diagnostics.system_diagnostic import create_diagnostic_checker

# Create diagnostic checker
diagnostic = create_diagnostic_checker(db_path="data/trading.db")

# Run full diagnostic
results = diagnostic.run_full_diagnostic()

# Check status
if results['overall_status'] == 'ERROR':
    print("Critical issues detected!")
    for issue in results['issues']:
        print(f"  - {issue}")
```

---

## 2. SOL Trade Analyzer

### Purpose
Provides specialized trading analysis for Solana (SOL) using ICT methodology, focusing on liquidity zones and fair value gaps to identify high-probability trade setups.

### Location
- Module: `core/analysis/sol_trade_analyzer.py`
- API Endpoint: `/api/analysis/sol`

### Features

#### Liquidity Zone Detection
- **Buy-side Liquidity** - Identifies resistance zones above price where institutional traders may sell
- **Sell-side Liquidity** - Identifies support zones below price where institutions may buy
- Calculates zone strength and priority
- Tracks zone state (UNTESTED, SWEPT, DEFENDED)

#### Fair Value Gap (FVG) Analysis
- **Bullish FVGs** - Unfilled gaps below price acting as support
- **Bearish FVGs** - Unfilled gaps above price acting as resistance
- Quality assessment (PREMIUM, HIGH, MEDIUM, LOW)
- Fresh gap prioritization

#### Trade Recommendations
- Entry zone identification
- Stop loss placement beyond liquidity zones
- Multiple take-profit targets (2%, 3%, 5%)
- Risk/reward ratio calculation
- Confluence scoring

#### ICT Methodology Integration
- Respects institutional order flow
- Considers liquidity sweeps
- Analyzes market structure
- Incorporates NY session levels

### API Usage

#### Request
```bash
GET /api/analysis/sol
```

#### Response Example
```json
{
  "symbol": "SOL",
  "current_price": 150.0,
  "timestamp": "2025-10-28T16:01:09.534876",
  "analysis_type": "liquidity_zones_and_fvg",
  "status": "success",
  "detailed_analysis": {
    "liquidity_zones": {
      "buy_side": [
        {
          "type": "buy_side",
          "price": 154.5,
          "zone_high": 155.25,
          "zone_low": 153.75,
          "strength": 0.75,
          "state": "UNTESTED"
        },
        {
          "type": "buy_side",
          "price": 157.5,
          "zone_high": 158.25,
          "zone_low": 156.75,
          "strength": 0.85,
          "state": "UNTESTED"
        }
      ],
      "sell_side": [
        {
          "type": "sell_side",
          "price": 145.5,
          "zone_high": 146.25,
          "zone_low": 144.75,
          "strength": 0.75,
          "state": "UNTESTED"
        },
        {
          "type": "sell_side",
          "price": 142.5,
          "zone_high": 143.25,
          "zone_low": 141.75,
          "strength": 0.85,
          "state": "UNTESTED"
        }
      ]
    },
    "fair_value_gaps": {
      "bullish": [
        {
          "type": "BULLISH_FVG",
          "high": 147.75,
          "low": 146.25,
          "mid": 147.0,
          "quality": "MEDIUM",
          "timestamp": "2025-10-28T16:01:09.534876"
        }
      ],
      "bearish": [
        {
          "type": "BEARISH_FVG",
          "high": 153.75,
          "low": 152.25,
          "mid": 153.0,
          "quality": "MEDIUM",
          "timestamp": "2025-10-28T16:01:09.534876"
        }
      ]
    },
    "key_levels": {
      "resistance_1": 153.0,
      "resistance_2": 157.5,
      "support_1": 147.0,
      "support_2": 142.5
    }
  },
  "recommendations": {
    "bias": "NEUTRAL",
    "suggested_trades": [],
    "risk_notes": [
      "Risk 1% of account per trade",
      "Place stop loss beyond liquidity zone",
      "Take partial profits at each target",
      "Monitor for liquidity sweeps",
      "Respect NY session highs/lows"
    ],
    "general_guidance": {
      "message": "No high-probability setup at current price",
      "watch_zones": {
        "buy_zone": {
          "type": "sell_side",
          "price": 145.5,
          "zone_high": 146.25,
          "zone_low": 144.75,
          "strength": 0.75,
          "state": "UNTESTED"
        },
        "sell_zone": {
          "type": "buy_side",
          "price": 154.5,
          "zone_high": 155.25,
          "zone_low": 153.75,
          "strength": 0.75,
          "state": "UNTESTED"
        }
      },
      "action": "Wait for price to reach key liquidity zones"
    }
  }
}
```

#### Response When Trade Setup Available
When price is near a key liquidity zone with confluence, the response includes suggested trades:

```json
{
  "recommendations": {
    "bias": "BULLISH",
    "suggested_trades": [
      {
        "direction": "BUY",
        "entry_zone": {
          "high": 146.23,
          "low": 145.23
        },
        "stop_loss": 141.17,
        "targets": [
          {"level": 147.45, "label": "TP1 (2%)"},
          {"level": 148.68, "label": "TP2 (3%)"},
          {"level": 151.13, "label": "TP3 (5%)"}
        ],
        "confluence": [
          "Sell-side liquidity zone",
          "Bullish fair value gap",
          "ICT buy model"
        ],
        "risk_reward": 2.0
      }
    ],
    "risk_notes": [
      "Risk 1% of account per trade",
      "Place stop loss beyond liquidity zone",
      "Take partial profits at each target",
      "Monitor for liquidity sweeps",
      "Respect NY session highs/lows"
    ]
  }
}
```

### Usage in Code

```python
from core.analysis.sol_trade_analyzer import create_sol_analyzer

# Create analyzer
analyzer = create_sol_analyzer()

# Analyze current opportunity
current_price = 150.0
analysis = analyzer.analyze_sol_opportunity(current_price)

# Check for trade setups
if analysis['recommendations']['bias'] != 'NEUTRAL':
    print(f"Trading bias: {analysis['recommendations']['bias']}")
    
    for trade in analysis['recommendations']['suggested_trades']:
        print(f"\n{trade['direction']} Setup:")
        print(f"  Entry: ${trade['entry_zone']['low']:.2f} - ${trade['entry_zone']['high']:.2f}")
        print(f"  Stop Loss: ${trade['stop_loss']:.2f}")
        print(f"  Targets: {len(trade['targets'])} levels")
        print(f"  R:R = {trade['risk_reward']}:1")
```

---

## Testing

### Unit Tests
- 22 comprehensive unit tests included
- 9 tests for diagnostic system
- 13 tests for SOL analyzer
- All tests passing

Run unit tests:
```bash
# Test diagnostic system
python3 -m pytest tests/unit/test_system_diagnostic.py -v

# Test SOL analyzer
python3 -m pytest tests/unit/test_sol_trade_analyzer.py -v

# Run all tests
python3 -m pytest tests/unit/ -v
```

### Integration Tests
Run the integration test suite:
```bash
python3 tests/integration_test.py
```

---

## Key Design Decisions

### 1. Minimal Database Changes
- No database schema modifications required
- Works with existing trading database structure
- Read-only operations for diagnostic checks

### 2. ICT Methodology Compliance
- SOL analyzer follows ICT principles
- Respects liquidity zones and FVGs
- Considers institutional order flow
- Implements proper risk management (1% rule)

### 3. Error Handling
- Graceful degradation on data unavailability
- Comprehensive error messages
- Fallback to general analysis when detailed data missing

### 4. Extensibility
- Easy to add support for other cryptocurrencies
- Diagnostic checks can be extended
- Modular design for future enhancements

---

## Future Enhancements

### Potential Improvements
1. Real-time price integration for SOL analyzer
2. Historical backtesting of recommendations
3. Email/SMS alerts for diagnostic issues
4. Multi-symbol analysis (ETH, BTC, XRP)
5. Advanced machine learning for pattern recognition
6. Integration with TradingView webhooks

### Monitoring Recommendations
- Run diagnostics hourly during trading hours
- Set up alerts for WARNING and ERROR statuses
- Review SOL analysis before each trading session
- Track recommendation accuracy over time

---

## Contact & Support

For issues or questions about this implementation:
1. Check the test files for usage examples
2. Review the API endpoint responses
3. Consult the inline code documentation
4. Run integration tests to verify functionality
