# 🚀 KIRSTON'S CRYPTO TRADING SYSTEM - COMMAND REFERENCE GUIDE

## 🚀 **ONE-COMMAND OPERATIONS** (NEW!)

### 🎯 Start All Systems

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./start_all_systems.sh    # Starts ICT Monitor + Demo Trading + Fundamental Analysis
```

### 🛑 Stop All Systems

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./stop_all_systems.sh     # Stops all three systems gracefully
```

### 🔍 Check All Systems

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./check_all_systems.sh    # Shows status of all systems + web interfaces
```

---

## 📋 QUICK SYSTEM STATUS

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
python3 ict_enhanced_monitor.py &

# Start Demo Trading System with auto-trading
python3 demo_trading_system.py --auto-trading &

# Start Fundamental Analysis System (long-term investment analysis)
./launch_fundamental_analysis.sh &

# Verify all systems are running
ps aux | grep -E "(ict_enhanced_monitor|demo_trading_system|fundamental_analysis)" | grep -v grep
```

### Method 2: Individual System Startup

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# 1. Start ICT Enhanced Monitor
python3 ict_enhanced_monitor.py

# 2. In new terminal - Start Demo Trading System
python3 demo_trading_system.py --auto-trading

# 3. In new terminal - Start Fundamental Analysis System
./launch_fundamental_analysis.sh

# 4. Optional: Start simple launcher
python3 simple_ict_launch.py
```

### Method 3: Background Process Startup

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Start ICT Monitor in background
nohup python3 ict_enhanced_monitor.py > ict_monitor.log 2>&1 &

# Start Demo Trading in background
nohup python3 demo_trading_system.py --auto-trading > demo_trading.log 2>&1 &

# Start Fundamental Analysis in background
nohup ./launch_fundamental_analysis.sh > fundamental_analysis.log 2>&1 &

# Check background processes
jobs
```

### 🚀 Method 4: **ONE-COMMAND STARTUP** (NEW!)

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Start all three systems with one command
./start_all_systems.sh

# Check all systems are running
./check_all_systems.sh
```

## 🔴 SHUTDOWN ALL SYSTEMS

### 🛑 Method 1: **ONE-COMMAND SHUTDOWN** (NEW!)

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Stop all three systems with one command
./stop_all_systems.sh

# Verify all systems stopped
./check_all_systems.sh
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
python3 -c "from fundamental_bridge import get_crypto_fundamental_bias; print(get_crypto_fundamental_bias('BTC'))"
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
conn = sqlite3.connect('trading_data.db')
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
python3 check_database_state.py

# Check real database status
python3 check_real_database.py

# Populate test data (if needed)
python3 populate_test_data.py

# Database analysis
python3 ml_database_analysis.py
```

### Log Management

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# View latest ICT Monitor logs
tail -f *.log | grep -E "(INFO|ERROR|WARNING)"

# View demo trading logs
tail -f logs/demo_mainnet_trading.log

# Archive old logs
mkdir -p logs/archive/$(date +%Y%m%d)
mv *.log logs/archive/$(date +%Y%m%d)/
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
python3 debug_persistence.py

# Test real balance verification
python3 test_real_balance.py

# Test daily reset functionality
python3 test_daily_reset.py
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

## 📊 CURRENT SYSTEM STATUS (as of last check)

### ✅ Currently Running:

- **ICT Enhanced Monitor**: ✅ ACTIVE (Port 5001)

  - Scan Count: 991+ (with persistence working)
  - DirectionalBiasEngine: ✅ Active
  - Real-time Analysis: ✅ Running
  - Web Interface: http://localhost:5001

- **Demo Trading System**: ✅ ACTIVE (Auto-trading enabled)

  - Auto-trading: ✅ Enabled
  - Bybit Integration: ✅ Connected
  - Runtime: Active

- **🚀 Fundamental Analysis System**: ✅ ACTIVE (Port 5002) **NEW!**
  - Long-term Analysis: ✅ Running
  - Supply/Demand Analysis: ✅ Active
  - News Sentiment: ✅ Processing
  - Web Dashboard: http://localhost:5002
  - Background Updates: ✅ Hourly

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
- ✅ Trading Journal & Session Management
- ✅ ML Training Data Preservation
- 🚀 **FUNDAMENTAL ANALYSIS SYSTEM** (NEW!)
  - ✅ Long-term Investment Analysis (4-year horizon)
  - ✅ Supply/Demand Fundamentals
  - ✅ News Sentiment Analysis
  - ✅ Real-world Data Integration
  - ✅ Independent System Operation (Port 5002)
  - ✅ Bridge to Day Trading System

## 🚨 EMERGENCY COMMANDS

### If Systems Become Unresponsive:

```bash
# Force kill everything
sudo pkill -f python
sudo lsof -ti:5001,5002,8000 | xargs kill -9

# Restart with clean slate using one command
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
./start_all_systems.sh
```

### If Database Issues:

```bash
# Backup database
cp trading_data.db trading_data_backup_$(date +%Y%m%d_%H%M%S).db

# Check database integrity
sqlite3 trading_data.db "PRAGMA integrity_check;"

# Restore from backup if needed
# cp trading_data_backup_YYYYMMDD_HHMMSS.db trading_data.db
```

## 📝 NOTES:

- Always use `python3` (not `python`) for compatibility
- ICT Monitor runs on port 5001 with web interface
- Demo Trading System runs as background process with auto-trading
- Data persistence is now working correctly
- All systems support graceful shutdown with Ctrl+C
- Logs are saved in the main directory and logs/ folder
- Database is automatically backed up during critical operations
