# 🚀 KIRSTON'S CRYPTO TRADING SYSTEM - COMMAND REFERENCE GUIDE

## 🚀 **ONE-COMMAND OPERATIONS** (NEW!)

### 🎯 Start All Systems

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./scripts/setup/start_all_systems.sh    # Starts ICT Monitor only by default (single-flow). To include demo/fundamental, run:
# START_EXTRAS=true ./scripts/setup/start_all_systems.sh  OR
# ./scripts/setup/start_all_systems.sh --include-extras
# OR use new professional launcher:
python3 systems/trade_system.py --start-all
```

### 🛑 Stop All Systems

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./scripts/setup/stop_all_systems.sh     # Stops all three systems gracefully
# OR use new professional launcher:
python3 systems/trade_system.py --stop-all
```

### 🔍 Check All Systems

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./scripts/setup/check_all_systems.sh    # Shows status of all systems + web interfaces
# OR use new professional launcher:
python3 systems/trade_system.py --status
```

---

## � **VS CODE INTEGRATED TERMINAL USAGE**

### 🎯 **Running Commands in VS Code Terminal** (Recommended)

Instead of opening separate terminal windows, use VS Code's integrated terminal:

1. **Open VS Code Terminal**: `Ctrl+` `(backtick) or`View > Terminal`
2. **Run all commands directly in VS Code terminal**
3. **Split terminals if needed**: Click the split terminal icon or `Cmd+Shift+5`

```bash
# All commands should be run in VS Code terminal:
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Start systems
./scripts/setup/start_all_systems.sh --include-extras

# Check status
./scripts/setup/check_all_systems.sh

# Stop systems
./scripts/setup/stop_all_systems.sh
```

### 📊 **Monitor Logs in VS Code Terminal**

```bash
# View real-time logs in VS Code terminal
tail -f logs/ict_monitor.log

# Or monitor multiple logs (split terminals)
# Terminal 1: ICT Monitor logs
tail -f logs/ict_monitor.log

# Terminal 2: Demo Trading logs
tail -f logs/demo_trading.log
```

---

## 📋 QUICK SYSTEM STATUS

```bash
# Check all running systems (run in VS Code terminal)
ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis|python)" | grep -v grep

# Check specific ports in use
lsof -i :5001  # ICT Enhanced Monitor
lsof -i :5002  # Fundamental Analysis System
lsof -i :8000  # Demo Trading System (if applicable)
```

```bash
# Check all running systems
ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis|python)" | grep -v grep

# Check specific ports in use
lsof -i :5001  # ICT Enhanced Monitor
lsof -i :5002  # Fundamental Analysis System
lsof -i :8000  # Demo Trading System (if applicable)
```

## 🟢 START ALL SYSTEMS

### Method 1: Quick Start (Recommended)

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Start ICT Enhanced Monitor (with 1% strict risk + dynamic RR)
python3 core/monitors/ict_enhanced_monitor.py &

# Start Demo Trading System with auto-trading
python3 systems/demo_trading/demo_trading_system.py --auto-trading &

# Start Fundamental Analysis System (long-term investment analysis)
./scripts/setup/launch_fundamental_analysis.sh &

# Verify all systems are running
ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis)" | grep -v grep
```

### Method 2: Individual System Startup

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# 1. Start ICT Enhanced Monitor
python3 core/monitors/ict_enhanced_monitor.py

# 2. In new terminal - Start Demo Trading System
python3 systems/demo_trading/demo_trading_system.py --auto-trading

# 3. In new terminal - Start Fundamental Analysis System
./scripts/setup/launch_fundamental_analysis.sh

# 4. Optional: Start simple launcher
python3 systems/simple_ict_launch.py
```

### Method 3: Background Process Startup

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Start ICT Monitor in background
nohup python3 core/monitors/ict_enhanced_monitor.py > logs/ict_monitor.log 2>&1 &

# Start Demo Trading in background
nohup python3 systems/demo_trading/demo_trading_system.py --auto-trading > logs/demo_trading.log 2>&1 &

# Start Fundamental Analysis in background
nohup ./scripts/setup/launch_fundamental_analysis.sh > logs/fundamental_analysis.log 2>&1 &

# Check background processes
jobs
```

### 🚀 Method 4: **ONE-COMMAND STARTUP** (NEW!)

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Start all three systems with one command
./scripts/setup/start_all_systems.sh

# Check all systems are running
./scripts/setup/check_all_systems.sh
```

## 🔴 SHUTDOWN ALL SYSTEMS

### 🛑 Method 1: **ONE-COMMAND SHUTDOWN** (NEW!)

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Stop all three systems with one command
./scripts/setup/stop_all_systems.sh

# Verify all systems stopped
./scripts/setup/check_all_systems.sh
```

### Method 2: Graceful Shutdown (Individual)

```bash
# Stop ICT Enhanced Monitor
pkill -f "ict_enhanced_monitor.py"

# Stop Demo Trading System
pkill -f "demo_trading_system.py"

# Stop Fundamental Analysis System
pkill -f "fundamental_analysis_server.py"

# Kill any remaining Python processes (if needed)
pkill -f "python.*trading"

# Force kill specific ports if needed
lsof -ti:5001 | xargs kill -9  # ICT Monitor
lsof -ti:5002 | xargs kill -9  # Fundamental Analysis
lsof -ti:8000 | xargs kill -9  # Demo Trading (if applicable)
```

### Method 2: Process ID Shutdown

```bash
# Find process IDs
ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis)" | grep -v grep

# Kill by PID (replace XXXX with actual PID)
kill XXXX YYYY ZZZZ

# Or force kill
kill -9 XXXX YYYY ZZZZ
```

### Method 3: Complete System Reset

```bash
# Kill all Python trading processes
pkill -f python

# Kill specific ports
lsof -ti:5001 | xargs kill -9  # ICT Monitor
lsof -ti:5002 | xargs kill -9  # Fundamental Analysis
lsof -ti:8000 | xargs kill -9  # Demo Trading

# Verify everything stopped
ps aux | grep -E "(python|trading|fundamental)" | grep -v grep
```

## 🌐 CHECK ENDPOINTS & WEB INTERFACES

### ICT Enhanced Monitor Endpoints

```bash
# Main Dashboard
open http://localhost:5001
# or
curl http://localhost:5001

# Health Check
curl http://localhost:5001/health

# API Data Endpoint
curl http://localhost:5001/api/data

# Latest Signals
curl http://localhost:5001/api/signals/latest

# Trading Stats
curl http://localhost:5001/api/stats

# WebSocket Connection Test
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:5001/socket.io/
```

### 🚀 Fundamental Analysis System Endpoints (NEW!)

```bash
# Main Dashboard
open http://localhost:5002
# or
curl http://localhost:5002

# Health Check
curl http://localhost:5002/api/health

# All Analysis Data
curl http://localhost:5002/api/analysis

# Specific Crypto Analysis (e.g., BTC)
curl http://localhost:5002/api/analysis/BTC

# Investment Recommendations
curl http://localhost:5002/api/recommendations

# News Analysis
curl http://localhost:5002/api/news

# Test Bridge Connection
python3 -c "from core.analysis.fundamental_bridge import get_crypto_fundamental_bias; print(get_crypto_fundamental_bias('BTC'))"
```

### Demo Trading System Endpoints

```bash
# Check if demo system is responding (if it has web interface)
curl http://localhost:8000 || echo "No web interface available"

# Check process status
ps aux | grep demo_trading_system
```

### Database Health Check

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Quick database status
python3 -c "
import sqlite3
from datetime import date
conn = sqlite3.connect('databases/trading_data.db')
cursor = conn.cursor()
today = date.today().isoformat()

cursor.execute('SELECT COUNT(*) FROM scan_history WHERE date(timestamp) = ?', (today,))
scans = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?', (today,))
signals = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) = ?', (today,))
trades = cursor.fetchone()[0]

print(f'📊 Today: {scans} scans, {signals} signals, {trades} trades')
conn.close()
"
```

## 🔧 MAINTENANCE COMMANDS

### Database Operations

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Check database state
python3 scripts/maintenance/check_database_state.py

# Check real database status
python3 scripts/maintenance/check_real_database.py

# Populate test data (if needed)
python3 scripts/maintenance/populate_test_data.py

# Database analysis
python3 scripts/maintenance/ml_database_analysis.py
```

### Log Management

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# View latest ICT Monitor logs
tail -f logs/*.log | grep -E "(INFO|ERROR|WARNING)"

# View demo trading logs
tail -f logs/demo_trading.log

# Archive old logs
mkdir -p logs/archive/$(date +%Y%m%d)
mv logs/*.log logs/archive/$(date +%Y%m%d)/ 2>/dev/null || true
```

### System Monitoring

```bash
# Monitor system resources
top -pid $(pgrep -f "ict_enhanced_monitor|demo_trading_system")

# Check memory usage
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f "ict_enhanced_monitor|demo_trading_system")

# Monitor network connections
netstat -an | grep -E ":5001|:8000"
```

## 🧪 TESTING & DEBUGGING

### Quick System Test

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Test persistence system
python3 scripts/testing/debug_persistence.py

# Test real balance verification
python3 scripts/testing/test_real_balance.py

# Test daily reset functionality
python3 scripts/testing/test_daily_reset.py
```

### Connection Tests

```bash
# Test ICT Monitor API
curl -s http://localhost:5001/api/data | python3 -m json.tool

# Test health endpoint
curl -s http://localhost:5001/health | python3 -m json.tool

# Test WebSocket (requires wscat: npm install -g wscat)
# wscat -c ws://localhost:5001/socket.io/?EIO=4&transport=websocket
```

## 📊 CURRENT SYSTEM STATUS (Updated October 29, 2025)

### ✅ **ALL SYSTEMS CURRENTLY RUNNING**:

- **ICT Enhanced Monitor**: ✅ **ACTIVE** (Port 5001)

  - Scan Count: Live monitoring active
  - DirectionalBiasEngine: ✅ Running
  - Real-time Analysis: ✅ Active
  - Web Interface: ✅ http://localhost:5001
  - **✅ Journal Cleanup**: Only shows TODAY's trades (fixed!)
  - **✅ Directory Structure**: Organized under `/core/monitors/`

- **Demo Trading System**: ✅ **ACTIVE** (Dry-run mode)

  - Auto-trading: ✅ Running in dry-run mode
  - Bybit Integration: ✅ Connected with real-time prices
  - Runtime: ✅ Live monitoring ICT signals
  - **✅ WebSocket Callbacks**: Fixed NoneType await errors
  - **✅ Directory Structure**: Organized under `/systems/demo_trading/`

- **🚀 Enhanced Fundamental Analysis System**: ✅ **ACTIVE** (Port 5002) **WORKING!**
  - **News Sources**: ✅ FIXED (all external API failures resolved with fallbacks)
  - **Real-time Prices**: ✅ Active (Live BTC pricing via Bybit)
  - **Supply/Demand Analysis**: ✅ Active
  - **News Sentiment**: ✅ Processing (demo data when APIs fail)
  - **Web Dashboard**: ✅ http://localhost:5002
  - **Background Updates**: ✅ Hourly
  - **🔔 Bitcoin Alert System**: ✅ Ready (WatcherGuru Telegram integration)
  - **✅ Directory Structure**: Organized under `/systems/fundamental_analysis/`

### 🚨 **BITCOIN ALERT STATUS** (Live Monitoring):

- **Current Status**: 🟢 Real-time monitoring active
- **Alert Detection**: ✅ System actively monitoring Bitcoin price movements
- **WatcherGuru Integration**: ✅ Built and functional (requires TELEGRAM_BOT_TOKEN)
- **Live Price Feed**: ✅ Connected via Bybit WebSocket
- **Future Alerts**: ✅ WILL be caught (system monitoring 24/7)

### 🎯 Key Features Active:

- ✅ Advanced ICT Directional Bias Methodology (Conservative Thresholds ≥0.6/≥0.7)
- ✅ NY Open Bias Detection with Enhanced Quality Controls
- ✅ Change of Character (ChoCH) Analysis
- ✅ Fibonacci + Elliott Wave Confluence
- ✅ **STRICT 1% RISK MANAGEMENT** - Maximum 1% loss per trade
- ✅ **DYNAMIC RISK-REWARD RATIOS** - 1:2 to 1:5 based on signal quality
- ✅ Price Separation Enforcement (2% BTC, 3% ETH, 5% SOL, 4% XRP)
- ✅ Complete Data Persistence (Fixed!)
- ✅ Paper Trading with Real Balance Tracking
- ✅ Real-time Price Updates via WebSocket
- ✅ **Trading Journal & Session Management** (Fixed - Only Today's Activity!)
- ✅ ML Training Data Preservation
- 🚀 **FUNDAMENTAL ANALYSIS SYSTEM** (NEW!)
  - ✅ Long-term Investment Analysis (4-year horizon)
  - ✅ Supply/Demand Fundamentals
  - ✅ News Sentiment Analysis
  - ✅ Real-world Data Integration
  - ✅ Independent System Operation (Port 5002)
  - ✅ Bridge to Day Trading System

### 🚀 **ONE-COMMAND STARTUP**: ✅ **CURRENTLY ACTIVE & TESTED!**

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./scripts/setup/start_all_systems.sh --include-extras    # ✅ ALL SYSTEMS RUNNING!
```

**Latest Status (October 29, 2025 - 8:50 AM):**

- ✅ ICT Enhanced Monitor: ✅ **RUNNING** (Port 5001) - PID: 37472
- ✅ Demo Trading System: ✅ **RUNNING** (dry-run mode) - PID: 37494
- ✅ **Enhanced Fundamental Analysis**: ✅ **RUNNING** (Port 5002) - PID: 37503
  - **News Sources**: ✅ ACTIVE (using reliable demo data when APIs fail)
  - **Bitcoin Price Monitoring**: ✅ Live prices via Bybit WebSocket
  - **WatcherGuru Telegram Capability**: ✅ Ready (requires token to activate)
  - **Dashboard**: ✅ http://localhost:5002
  - **Background Analysis**: ✅ Hourly updates active
- ✅ **Directory Structure**: ✅ FULLY ORGANIZED AND CLEANED
- ✅ **WebSocket Callbacks**: ✅ FIXED (NoneType await errors resolved)
- ✅ **File Organization**: ✅ All scripts moved to proper directories
- ✅ **Database Management**: ✅ All database files in `/databases/` directory

**🎯 Enhanced Features Currently Active:**

- ✅ **Bitcoin Alert Detection System**: ✅ LIVE MONITORING
- ✅ **Multi-source News Integration**: ✅ ACTIVE with fallbacks
- ✅ **Real-time Price Monitoring**: ✅ Live Bybit WebSocket feed
- ✅ **WatcherGuru Telegram Bridge**: ✅ Built and ready (needs token)
- ✅ **Demo News Generation**: ✅ Active when external APIs fail
- ✅ **Directory Structure**: ✅ COMPLETELY REORGANIZED
- ✅ **WebSocket Error Fixes**: ✅ NoneType await errors resolved
- ✅ **File Organization**: ✅ All scripts in proper directories

## 🚨 EMERGENCY COMMANDS

### If Systems Become Unresponsive:

```bash
# Force kill everything
sudo pkill -f python
sudo lsof -ti:5001,5002,8000 | xargs kill -9

# Restart with clean slate using one command
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./scripts/setup/start_all_systems.sh
```

### If Database Issues:

```bash
# Backup database
cp databases/trading_data.db databases/trading_data_backup_$(date +%Y%m%d_%H%M%S).db

# Check database integrity
sqlite3 databases/trading_data.db "PRAGMA integrity_check;"

# Restore from backup if needed
# cp databases/trading_data_backup_YYYYMMDD_HHMMSS.db databases/trading_data.db
```

## 📝 NOTES:

- Always use `python3` (not `python`) for compatibility
- ICT Monitor runs on port 5001 with web interface
- Demo Trading System runs as background process with auto-trading
- **Data persistence**: Only TODAY's data is shown and persisted
  - Scan counts reset to #1 each day at midnight
  - Signal history shows only today's signals
  - Balance carries over (never resets)
  - Journal entries show only today's activity
- All systems support graceful shutdown with Ctrl+C
- Logs are saved in the main directory and logs/ folder
- Database is automatically backed up during critical operations

## 📁 DIRECTORY STRUCTURE:

- **`/core/`** - Core trading systems and engines
  - `monitors/` - ICT Enhanced Monitor and other monitoring systems
  - `engines/` - Trading engines and algorithms
  - `analysis/` - Core analysis modules
- **`/systems/`** - Complete trading systems
  - `demo_trading/` - Demo trading system with Bybit integration
  - `fundamental_analysis/` - Long-term fundamental analysis system
  - `trade_system.py` - Main system launcher
- **`/scripts/`** - All scripts organized by purpose
  - `setup/` - System setup and management scripts
  - `analysis/` - Trading analysis and reporting scripts
  - `testing/` - Test scripts and validation tools
  - `maintenance/` - Database and system maintenance scripts
- **`/docs/`** - All documentation and guides
- **`/config/`** - Configuration files and credentials
- **`/databases/`** - All database files
- **`/logs/`** - System logs and output files
