# Trading Algorithm - Clean Project Structure

## 📁 Root Directory Files
- `README.md` - Main project documentation
- `SYSTEM_COMMANDS.md` - Command reference guide
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (gitignored)
- `.env.example` - Environment template

## 📂 Core Directories

### `/core/` - Core Trading System
- `engines/` - Trading engines and algorithms
- `monitors/` - **ict_enhanced_monitor.py** (main system)
- `analysis/` - Analysis modules

### `/systems/` - Complete Trading Systems
- `demo_trading/` - Demo trading system with Bybit integration
- `fundamental_analysis/` - Long-term fundamental analysis
- `trade_system.py` - Main system launcher

### `/trading/` - ICT Analysis Modules
- `ict_analyzer.py` - Main ICT analyzer
- `directional_bias_engine.py` - Bias detection
- `order_block_detector.py` - Order block detection
- `fvg_detector.py` - Fair Value Gap detection
- `liquidity_detector.py` - Liquidity analysis
- `fibonacci_analyzer.py` - Fibonacci analysis
- `ict_hierarchy.py` - Timeframe hierarchy

### `/scripts/` - Organized Scripts
- `setup/` - System setup and management
  - `start_all_systems.sh`
  - `stop_all_systems.sh`
  - `check_all_systems.sh`
- `analysis/` - Trading analysis scripts
- `testing/` - Test and validation scripts
- `maintenance/` - Database and system maintenance

### `/config/` - Configuration Files
- `api_settings.json` - API configuration
- `crypto_pairs.json` - Trading pairs
- `risk_parameters.json` - Risk management settings
- `fundamental_analysis_config.json` - Fundamental analysis config
- `credentials/` - API credentials (gitignored)
- `environments/` - Environment-specific configs

### `/bybit_integration/` - Bybit Exchange Integration
- `bybit_client.py` - API client
- `websocket_client.py` - WebSocket connection
- `trading_executor.py` - Trade execution
- `integration_manager.py` - Integration orchestration

### `/databases/` - Database Files
- `trading_data.db` - Main SQLite database
- Other database files

### `/data/` - Data Storage
- `persistence/` - Trading state persistence
- `cache/` - Cached data
- `trading_sessions/` - Session data
- `trading.db` - Additional database

### `/logs/` - System Logs
- Log files from all systems

### `/results/` - Backtest Results
- Backtest output files (JSON format)

### `/docs/` - Documentation
- All project documentation
- Implementation summaries
- System status reports
- Trading analysis reports
- API guides and integration docs

### `/docker/` - Docker Deployment
- `Dockerfile` - Multi-stage build
- `docker-compose.yml` - Orchestration
- `docker-entrypoint.sh` - Container initialization
- `docker-setup.sh` - Automated setup
- `DOCKER_README.md` - Complete deployment guide

### `/tests/` - Test Suite
- Unit and integration tests

### `/utils/` - Utility Modules
- Helper functions and utilities

### `/dashboard/` - Web Dashboard
- `ict_dashboard.py` - Main dashboard

### `/integrations/` - External Integrations
- `tradingview/` - TradingView integration

### `/backtesting/` - Backtesting Framework
- Backtesting modules and tools

### `/deployment/` - Deployment Scripts
- Production and staging deployment

### `/frontend/` - Frontend Application
- React/Vue frontend (if used)

### `/tradingview/` - TradingView Resources
- Pine scripts
- Integration guides

### `/media/` - Media Files
- Transcripts and other media

### `/services/` - Service Modules
- Notification and other services

### `/machine_learning/` - ML Components
- Machine learning models and scripts

## 🗄️ Archived Directories

### `/archive/` - Archived/Legacy Code
- `old_src/` - Legacy src/ directory
- `old_project/` - Legacy project/ configurations
- `old_monitoring/` - Old monitoring scripts
- `old_files/` - Archived tasks, templates, models, examples
- `standalone_servers/` - Old standalone servers

## 🚫 Removed/Cleaned
- ✅ Duplicate configuration files
- ✅ Old backup directories
- ✅ Temporary files (.DS_Store, screenshots)
- ✅ Old log files (>7 days)
- ✅ Duplicate scripts (api_server.py, fix_db_connections.py)

## 📝 Key Changes Made
1. **Consolidated monitor location**: `ict_enhanced_monitor.py` now in `core/monitors/`
2. **Organized documentation**: All docs in `/docs/` directory
3. **Archived duplicates**: Legacy code moved to `/archive/`
4. **Clean root**: Only essential config files remain in root
5. **Updated .gitignore**: Excludes archives and backups

## 🎯 Active System Entry Points
- `core/monitors/ict_enhanced_monitor.py` - Main ICT monitor
- `systems/demo_trading/demo_trading_system.py` - Demo trading
- `systems/trade_system.py` - System launcher
- `scripts/setup/start_all_systems.sh` - One-command startup

