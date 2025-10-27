# 🚨 CRITICAL FILES - NEVER DELETE OR MODIFY WITHOUT EXPLICIT PERMISSION

## ⚠️ ABSOLUTELY CRITICAL - CORE SYSTEM FILES

These files contain LIVE STATE, BALANCES, and TRADING DATA. **DELETION = DATA LOSS**

### 1. Database Files (MOST CRITICAL)

```
databases/trading_data.db           # ALL trading data, signals, balances, history
databases/*.db                      # Any database backup files
```

**Consequences of loss**: Complete loss of trading history, signals, balance records

### 2. Persistence Files (CRITICAL)

```
data/persistence/ict_monitor_state.json    # LIVE balance, scan count, active signals
data/persistence/trading_state.json         # Trading system state
data/persistence/daily_*.json               # Daily session backups
data/persistence/*.json                     # All persistence files
```

**Consequences of loss**: Balance reset, scan count reset, active trades lost

### 3. ICT Strategy Files (CRITICAL)

```
core/monitors/ict_enhanced_monitor.py      # Main ICT analysis engine
core/strategy/directional_bias_engine.py   # Core ICT strategy logic
core/strategy/ict_*.py                     # All ICT strategy modules
```

**Consequences of loss**: Trading strategy broken, signals stop generating

### 4. Configuration Files (IMPORTANT)

```
config/api_settings.json           # API keys and configuration
config/risk_parameters.json        # Risk management settings
config/environments/*.json         # Environment configurations
```

**Consequences of loss**: System cannot connect to exchanges, risk management broken

### 5. Machine Learning Models (IMPORTANT)

```
machine_learning/models/*.pkl      # Trained ML models
machine_learning/models/*.h5       # Neural network models
ml_learning_insights.json          # ML training insights
```

**Consequences of loss**: ML predictions lost, models need retraining

## 🛡️ BACKUP REQUIREMENTS

**Before ANY system modification**:

1. Create timestamped backup of `databases/trading_data.db`
2. Create timestamped backup of `data/persistence/` directory
3. Verify backups exist before proceeding

**Automatic backups run**:

- On system startup
- Before system shutdown
- Every hour during operation
- Before any database operation

## 🚫 NEVER DELETE THESE DIRECTORIES

```
databases/              # All trading data
data/persistence/       # Live system state
core/                   # Core system logic
config/                 # System configuration
machine_learning/models/ # Trained models
```

## ✅ SAFE TO DELETE (Temporary/Generated Files)

```
logs/*.log              # Log files (archived regularly)
__pycache__/            # Python cache
*.pyc                   # Compiled Python files
.pytest_cache/          # Test cache
node_modules/           # Node dependencies (if any)
```

## 🚨 WHAT TO DO IF CRITICAL FILE IS LOST

1. **STOP ALL SYSTEMS IMMEDIATELY**
2. Check `backups/` directory for most recent backup
3. Check `data/persistence/` for any remaining backup files
4. Check database for recoverable data
5. Restore from most recent valid backup
6. **NEVER** reinitialize without user approval

## 📝 FILE MODIFICATION RULES

**ALWAYS required before modifying critical files**:

1. Create timestamped backup
2. Get explicit user confirmation
3. Document why modification is needed
4. Test modification in isolation first

**NEVER**:

- Delete persistence files during "cleanup"
- Modify database without backup
- Reinitialize state without user approval
- Assume files are "temporary" or "old"
- Delete files to "fix" issues

---

**Last Updated**: October 24, 2025
**Reason**: Persistence file was lost during Flask troubleshooting, causing balance data loss
**Never Again**: All critical files now have automatic backup system
