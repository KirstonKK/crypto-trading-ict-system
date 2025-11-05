# 🚀 KIRSTON'S CRYPTO TRADING SYSTEM - COMMAND REFERENCE GUIDE# 🚀 KIRSTON'S CRYPTO TRADING SYSTEM - COMMAND REFERENCE GUIDE

## 🚀 **ONE-COMMAND OPERATIONS** (UNIFIED SYSTEM)## 🚀 **ONE-COMMAND OPERATIONS** (NEW!)

### 🎯 Start Unified System### 🎯 Start All Systems

`bash`bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/start_all_systems.sh # Starts unified ICT monitor with all features on port 5001./scripts/setup/start_all_systems.sh # Starts ICT Monitor only by default (single-flow). To include demo/fundamental, run:

````# START_EXTRAS=true ./scripts/setup/start_all_systems.sh  OR

# ./scripts/setup/start_all_systems.sh --include-extras

### 🛑 Stop Unified System# OR use new professional launcher:

python3 systems/trade_system.py --start-all

```bash```

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/stop_all_systems.sh     # Stops unified system gracefully### 🛑 Stop All Systems

````

````bash

### 🔍 Check System Statuscd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/stop_all_systems.sh     # Stops all three systems gracefully

```bash# OR use new professional launcher:

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"python3 systems/trade_system.py --stop-all

./scripts/setup/check_all_systems.sh    # Shows unified system status + web interfaces```

````

### 🔍 Check All Systems

---

````bash

## 💻 **VS CODE INTEGRATED TERMINAL USAGE**cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/check_all_systems.sh    # Shows status of all systems + web interfaces

### 🎯 **Running Commands in VS Code Terminal** (Recommended)# OR use new professional launcher:

python3 systems/trade_system.py --status

Instead of opening separate terminal windows, use VS Code's integrated terminal:```



1. **Open VS Code Terminal**: `Ctrl+` ` (backtick) or `View > Terminal`---

2. **Run all commands directly in VS Code terminal**

3. **Split terminals if needed**: Click the split terminal icon or `Cmd+Shift+5`## � **VS CODE INTEGRATED TERMINAL USAGE**



```bash### 🎯 **Running Commands in VS Code Terminal** (Recommended)

# All commands should be run in VS Code terminal:

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"Instead of opening separate terminal windows, use VS Code's integrated terminal:



# Start unified system1. **Open VS Code Terminal**: `Ctrl+` ` (backtick) or `View > Terminal`

./scripts/setup/start_all_systems.sh2. **Run all commands directly in VS Code terminal**

3. **Split terminals if needed**: Click the split terminal icon or `Cmd+Shift+5`

# Check status

./scripts/setup/check_all_systems.sh```bash

# All commands should be run in VS Code terminal:

# Stop systemcd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/stop_all_systems.sh

```# Start systems

./scripts/setup/start_all_systems.sh --include-extras

### 📊 **Monitor Logs in VS Code Terminal**

# Check status

```bash./scripts/setup/check_all_systems.sh

# View real-time logs in VS Code terminal

tail -f logs/ict_monitor.log# Stop systems

./scripts/setup/stop_all_systems.sh

# Monitor system activity```

tail -f logs/*.log

```### 📊 **Monitor Logs in VS Code Terminal**



---```bash

# View real-time logs in VS Code terminal

## 📋 QUICK SYSTEM STATUStail -f logs/ict_monitor.log



```bash# Or monitor multiple logs (split terminals)

# Check if unified system is running (run in VS Code terminal)# Terminal 1: ICT Monitor logs

ps aux | grep -E "(ict_enhanced_monitor|python)" | grep -v greptail -f logs/ict_monitor.log



# Check port in use# Terminal 2: Demo Trading logs

lsof -i :5001  # Unified ICT Monitortail -f logs/demo_trading.log

````

## 🟢 START UNIFIED SYSTEM---

### Method 1: Quick Start (Recommended)## 📋 QUICK SYSTEM STATUS

`bash`bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"# Check all running systems (run in VS Code terminal)

ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis|python)" | grep -v grep

# Start unified ICT Enhanced Monitor (all features integrated)

./scripts/setup/start_all_systems.sh# Check specific ports in use

lsof -i :5001 # ICT Enhanced Monitor

# Verify system is runninglsof -i :5002 # Fundamental Analysis System

ps aux | grep "ict_enhanced_monitor" | grep -v greplsof -i :8000 # Demo Trading System (if applicable)

````



### Method 2: Direct Python Launch```bash

# Check all running systems

```bashps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis|python)" | grep -v grep

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Check specific ports in use

# Start unified system directlylsof -i :5001  # ICT Enhanced Monitor

python3 core/monitors/ict_enhanced_monitor.pylsof -i :5002  # Fundamental Analysis System

```lsof -i :8000  # Demo Trading System (if applicable)

```

### Method 3: Background Process Startup

## 🟢 START ALL SYSTEMS

```bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"### Method 1: Quick Start (Recommended)



# Start in background with logging```bash

nohup python3 core/monitors/ict_enhanced_monitor.py > logs/ict_monitor.log 2>&1 &cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"



# Check background process# Start ICT Enhanced Monitor (with 1% strict risk + dynamic RR)

jobspython3 core/monitors/ict_enhanced_monitor.py &

```

# Start Demo Trading System with auto-trading

## 🔴 SHUTDOWN UNIFIED SYSTEMpython3 systems/demo_trading/demo_trading_system.py --auto-trading &



### 🛑 Method 1: **ONE-COMMAND SHUTDOWN** (Recommended)# Start Fundamental Analysis System (long-term investment analysis)

./scripts/setup/launch_fundamental_analysis.sh &

```bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"# Verify all systems are running

ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis)" | grep -v grep

# Stop unified system with one command```

./scripts/setup/stop_all_systems.sh

### Method 2: Individual System Startup

# Verify system stopped

./scripts/setup/check_all_systems.sh```bash

```cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"



### Method 2: Graceful Shutdown# 1. Start ICT Enhanced Monitor

python3 core/monitors/ict_enhanced_monitor.py

```bash

# Stop unified ICT Monitor# 2. In new terminal - Start Demo Trading System

pkill -f "ict_enhanced_monitor.py"python3 systems/demo_trading/demo_trading_system.py --auto-trading



# Verify stopped# 3. In new terminal - Start Fundamental Analysis System

ps aux | grep "ict_enhanced_monitor" | grep -v grep./scripts/setup/launch_fundamental_analysis.sh

```

# 4. Optional: Start simple launcher

### Method 3: Force Killpython3 systems/simple_ict_launch.py

```

```bash

# Force kill unified system### Method 3: Background Process Startup

pkill -9 -f "ict_enhanced_monitor.py"

```bash

# Kill port if still occupiedcd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

lsof -ti:5001 | xargs kill -9

```# Start ICT Monitor in background

nohup python3 core/monitors/ict_enhanced_monitor.py > logs/ict_monitor.log 2>&1 &

## 🌐 CHECK ENDPOINTS & WEB INTERFACES

# Start Demo Trading in background

### Unified System Endpoints (Port 5001)nohup python3 systems/demo_trading/demo_trading_system.py --auto-trading > logs/demo_trading.log 2>&1 &



```bash# Start Fundamental Analysis in background

# Main Dashboardnohup ./scripts/setup/launch_fundamental_analysis.sh > logs/fundamental_analysis.log 2>&1 &

open http://localhost:5001

# or# Check background processes

curl http://localhost:5001jobs

```

# Fundamental Analysis Dashboard

open http://localhost:5001/fundamental### 🚀 Method 4: **ONE-COMMAND STARTUP** (NEW!)

# or

curl http://localhost:5001/fundamental```bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Health Check

curl http://localhost:5001/health# Start all three systems with one command

./scripts/setup/start_all_systems.sh

# API Data Endpoint

curl http://localhost:5001/api/data# Check all systems are running

./scripts/setup/check_all_systems.sh

# Fundamental Analysis API```

curl http://localhost:5001/api/fundamental

## 🔴 SHUTDOWN ALL SYSTEMS

# Specific Crypto Fundamental Analysis (e.g., BTC)

curl http://localhost:5001/api/fundamental/BTC### 🛑 Method 1: **ONE-COMMAND SHUTDOWN** (NEW!)



# Latest Signals```bash

curl http://localhost:5001/api/signals/latestcd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"



# Trading Stats# Stop all three systems with one command

curl http://localhost:5001/api/stats./scripts/setup/stop_all_systems.sh



# WebSocket Connection Test# Verify all systems stopped

curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:5001/socket.io/./scripts/setup/check_all_systems.sh

````

### Database Health Check### Method 2: Graceful Shutdown (Individual)

`bash`bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"# Stop ICT Enhanced Monitor

pkill -f "ict_enhanced_monitor.py"

# Quick database status

python3 -c "# Stop Demo Trading System

import sqlite3pkill -f "demo_trading_system.py"

from datetime import date

conn = sqlite3.connect('databases/trading_data.db')# Stop Fundamental Analysis System

cursor = conn.cursor()pkill -f "fundamental_analysis_server.py"

today = date.today().isoformat()

# Kill any remaining Python processes (if needed)

cursor.execute('SELECT COUNT(*) FROM scan_history WHERE date(timestamp) = ?', (today,))pkill -f "python.*trading"

scans = cursor.fetchone()[0]

# Force kill specific ports if needed

cursor.execute('SELECT COUNT(\*) FROM signals WHERE date(entry_time) = ?', (today,))lsof -ti:5001 | xargs kill -9 # ICT Monitor

signals = cursor.fetchone()[0]lsof -ti:5002 | xargs kill -9 # Fundamental Analysis

lsof -ti:8000 | xargs kill -9 # Demo Trading (if applicable)

cursor.execute('SELECT COUNT(\*) FROM paper_trades WHERE date(entry_time) = ?', (today,))```

trades = cursor.fetchone()[0]

### Method 2: Process ID Shutdown

print(f'📊 Today: {scans} scans, {signals} signals, {trades} trades')

conn.close()```bash

"# Find process IDs

````ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis)" | grep -v grep



## 🔧 MAINTENANCE COMMANDS# Kill by PID (replace XXXX with actual PID)

kill XXXX YYYY ZZZZ

### Database Operations

# Or force kill

```bashkill -9 XXXX YYYY ZZZZ

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"```



# Check database state### Method 3: Complete System Reset

python3 scripts/maintenance/check_database_state.py

```bash

# Check real database status# Kill all Python trading processes

python3 scripts/maintenance/check_real_database.pypkill -f python



# Populate test data (if needed)# Kill specific ports

python3 scripts/maintenance/populate_test_data.pylsof -ti:5001 | xargs kill -9  # ICT Monitor

lsof -ti:5002 | xargs kill -9  # Fundamental Analysis

# Database analysislsof -ti:8000 | xargs kill -9  # Demo Trading

python3 scripts/maintenance/ml_database_analysis.py

```# Verify everything stopped

ps aux | grep -E "(python|trading|fundamental)" | grep -v grep

### Log Management```



```bash## 🌐 CHECK ENDPOINTS & WEB INTERFACES

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

### ICT Enhanced Monitor Endpoints

# View latest ICT Monitor logs

tail -f logs/*.log | grep -E "(INFO|ERROR|WARNING)"```bash

# Main Dashboard

# Archive old logsopen http://localhost:5001

mkdir -p logs/archive/$(date +%Y%m%d)# or

mv logs/*.log logs/archive/$(date +%Y%m%d)/ 2>/dev/null || truecurl http://localhost:5001

````

# Health Check

### System Monitoringcurl http://localhost:5001/health

````bash# API Data Endpoint

# Monitor system resourcescurl http://localhost:5001/api/data

top -pid $(pgrep -f "ict_enhanced_monitor")

# Latest Signals

# Check memory usagecurl http://localhost:5001/api/signals/latest

ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f "ict_enhanced_monitor")

# Trading Stats

# Monitor network connectionscurl http://localhost:5001/api/stats

netstat -an | grep ":5001"

```# WebSocket Connection Test

curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:5001/socket.io/

## 🧪 TESTING & DEBUGGING```



### Quick System Test### 🚀 Fundamental Analysis System Endpoints (NEW!)



```bash```bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"# Main Dashboard

open http://localhost:5002

# Test persistence system# or

python3 scripts/testing/debug_persistence.pycurl http://localhost:5002



# Test real balance verification# Health Check

python3 scripts/testing/test_real_balance.pycurl http://localhost:5002/api/health



# Test daily reset functionality# All Analysis Data

python3 scripts/testing/test_daily_reset.pycurl http://localhost:5002/api/analysis

````

# Specific Crypto Analysis (e.g., BTC)

### Connection Testscurl http://localhost:5002/api/analysis/BTC

````bash# Investment Recommendations

# Test unified system APIcurl http://localhost:5002/api/recommendations

curl -s http://localhost:5001/api/data | python3 -m json.tool

# News Analysis

# Test fundamental analysis APIcurl http://localhost:5002/api/news

curl -s http://localhost:5001/api/fundamental | python3 -m json.tool

# Test Bridge Connection

# Test health endpointpython3 -c "from core.analysis.fundamental_bridge import get_crypto_fundamental_bias; print(get_crypto_fundamental_bias('BTC'))"

curl -s http://localhost:5001/health | python3 -m json.tool```

````

### Demo Trading System Endpoints

## 📊 CURRENT SYSTEM STATUS (Updated January 2025)

````bash

### ✅ **UNIFIED SYSTEM ARCHITECTURE**:# Check if demo system is responding (if it has web interface)

curl http://localhost:8000 || echo "No web interface available"

- **ICT Enhanced Monitor**: ✅ **UNIFIED SYSTEM** (Port 5001)

  - **Day Trading**: ✅ Real-time ICT signal monitoring# Check process status

  - **Fundamental Analysis**: ✅ Integrated (accessible at /fundamental)ps aux | grep demo_trading_system

  - **Auto Trading**: ✅ Integrated with Bybit```

  - Scan Count: Live monitoring active

  - DirectionalBiasEngine: ✅ Running### Database Health Check

  - Real-time Analysis: ✅ Active

  - Web Interfaces:```bash

    - Main Dashboard: ✅ http://localhost:5001cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

    - Fundamental Analysis: ✅ http://localhost:5001/fundamental

  - **✅ Journal Cleanup**: Only shows TODAY's trades# Quick database status

  - **✅ Directory Structure**: Organized under `/core/monitors/`python3 -c "

import sqlite3

### 🎯 Integrated Features:from datetime import date

conn = sqlite3.connect('databases/trading_data.db')

- ✅ Advanced ICT Directional Bias Methodology (Conservative Thresholds ≥0.6/≥0.7)cursor = conn.cursor()

- ✅ NY Open Bias Detection with Enhanced Quality Controlstoday = date.today().isoformat()

- ✅ Change of Character (ChoCH) Analysis

- ✅ Fibonacci + Elliott Wave Confluencecursor.execute('SELECT COUNT(*) FROM scan_history WHERE date(timestamp) = ?', (today,))

- ✅ **STRICT 1% RISK MANAGEMENT** - Maximum 1% loss per tradescans = cursor.fetchone()[0]

- ✅ **DYNAMIC RISK-REWARD RATIOS** - 1:2 to 1:5 based on signal quality

- ✅ Price Separation Enforcement (2% BTC, 3% ETH, 5% SOL, 4% XRP)cursor.execute('SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?', (today,))

- ✅ Complete Data Persistencesignals = cursor.fetchone()[0]

- ✅ Paper Trading with Real Balance Tracking

- ✅ Real-time Price Updates via WebSocketcursor.execute('SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) = ?', (today,))

- ✅ **Trading Journal & Session Management**trades = cursor.fetchone()[0]

- ✅ ML Training Data Preservation

- ✅ **FUNDAMENTAL ANALYSIS** (Integrated)print(f'📊 Today: {scans} scans, {signals} signals, {trades} trades')

  - ✅ Long-term Investment Analysis (4-year horizon)conn.close()

  - ✅ Supply/Demand Fundamentals"

  - ✅ Sentiment Analysis```

  - ✅ Real-time Price Monitoring

  - ✅ Integrated Dashboard (Port 5001/fundamental)## 🔧 MAINTENANCE COMMANDS



### 🚀 **ONE-COMMAND STARTUP**: ✅ **UNIFIED SYSTEM**### Database Operations



```bash```bash

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/start_all_systems.sh    # ✅ STARTS UNIFIED SYSTEM!

```# Check database state

python3 scripts/maintenance/check_database_state.py

**Access Points:**

- Main Dashboard: http://localhost:5001# Check real database status

- Fundamental Analysis: http://localhost:5001/fundamentalpython3 scripts/maintenance/check_real_database.py

- API Endpoints: http://localhost:5001/api/*

# Populate test data (if needed)

## 🚨 EMERGENCY COMMANDSpython3 scripts/maintenance/populate_test_data.py



### If System Becomes Unresponsive:# Database analysis

python3 scripts/maintenance/ml_database_analysis.py

```bash```

# Force kill everything

sudo pkill -f "ict_enhanced_monitor"### Log Management

sudo lsof -ti:5001 | xargs kill -9

```bash

# Restart with clean slatecd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

./scripts/setup/start_all_systems.sh# View latest ICT Monitor logs

```tail -f logs/*.log | grep -E "(INFO|ERROR|WARNING)"



### If Database Issues:# View demo trading logs

tail -f logs/demo_trading.log

```bash

# Backup database# Archive old logs

cp databases/trading_data.db databases/trading_data_backup_$(date +%Y%m%d_%H%M%S).dbmkdir -p logs/archive/$(date +%Y%m%d)

mv logs/*.log logs/archive/$(date +%Y%m%d)/ 2>/dev/null || true

# Check database integrity```

sqlite3 databases/trading_data.db "PRAGMA integrity_check;"

### System Monitoring

# Restore from backup if needed

# cp databases/trading_data_backup_YYYYMMDD_HHMMSS.db databases/trading_data.db```bash

```# Monitor system resources

top -pid $(pgrep -f "ict_enhanced_monitor|demo_trading_system")

## 📝 NOTES:

# Check memory usage

- **UNIFIED SYSTEM**: All features integrated into single process on port 5001ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f "ict_enhanced_monitor|demo_trading_system")

- Always use `python3` (not `python`) for compatibility

- **Data persistence**: Only TODAY's data is shown and persisted# Monitor network connections

  - Scan counts reset to #1 each day at midnightnetstat -an | grep -E ":5001|:8000"

  - Signal history shows only today's signals```

  - Balance carries over (never resets)

  - Journal entries show only today's activity## 🧪 TESTING & DEBUGGING

- System supports graceful shutdown with Ctrl+C

- Logs are saved in the logs/ folder### Quick System Test

- Database is automatically backed up during critical operations

```bash

## 📁 DIRECTORY STRUCTURE:cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"



- **`/core/`** - Core trading systems and engines# Test persistence system

  - `monitors/` - ICT Enhanced Monitor (unified system)python3 scripts/testing/debug_persistence.py

  - `engines/` - Trading engines and algorithms

  - `analysis/` - Core analysis modules# Test real balance verification

- **`/systems/`** - Legacy standalone systems (archived)python3 scripts/testing/test_real_balance.py

- **`/scripts/`** - All scripts organized by purpose

  - `setup/` - System setup and management scripts# Test daily reset functionality

  - `analysis/` - Trading analysis and reporting scriptspython3 scripts/testing/test_daily_reset.py

  - `testing/` - Test scripts and validation tools```

  - `maintenance/` - Database and system maintenance scripts

- **`/docs/`** - All documentation and guides### Connection Tests

- **`/config/`** - Configuration files and credentials

- **`/databases/`** - All database files```bash

- **`/logs/`** - System logs and output files# Test ICT Monitor API

- **`/archive/`** - Archived standalone servers and old codecurl -s http://localhost:5001/api/data | python3 -m json.tool


# Test health endpoint
curl -s http://localhost:5001/health | python3 -m json.tool

# Test WebSocket (requires wscat: npm install -g wscat)
# wscat -c ws://localhost:5001/socket.io/?EIO=4&transport=websocket
````

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
