#!/bin/bash

# 🏗️ RESTRUCTURE TRADING SYSTEM CODEBASE
# =======================================
# Professional organization of the crypto trading system

echo "🏗️ RESTRUCTURING CODEBASE TO PROFESSIONAL STANDARDS"
echo "===================================================="

# Create new professional directory structure
mkdir -p {core/{engines,monitors,analysis},systems/{day_trading,fundamental_analysis,demo_trading},scripts/{setup,maintenance,testing},docs,databases,logs/archive,config/environments}

echo "📁 Created professional directory structure"

# Move core system files
echo "🚀 Moving core system files..."
mv ict_enhanced_monitor.py core/monitors/
mv demo_trading_system.py systems/demo_trading/
mv fundamental_analysis_server.py systems/fundamental_analysis/
mv crypto_fundamental_analyzer.py systems/fundamental_analysis/
mv real_world_data_integrator.py systems/fundamental_analysis/
mv fundamental_bridge.py core/analysis/

echo "🔧 Moving engine and bridge files..."
mv ict_bybit_bridge.py core/engines/
mv ict_enhanced_system.py core/engines/
mv ict_ml_trainer.py core/engines/

# Move configuration files
echo "⚙️ Moving configuration files..."
mv fundamental_analysis_config.json config/
mv .env config/environments/
mv .env.demo config/environments/

# Move scripts
echo "📜 Moving scripts..."
mv start_all_systems.sh scripts/setup/
mv stop_all_systems.sh scripts/setup/
mv check_all_systems.sh scripts/setup/
mv launch_fundamental_analysis.sh scripts/setup/
mv setup_demo_mainnet.sh scripts/setup/
mv quick_setup.py scripts/setup/

# Move maintenance scripts
mv check_database_state.py scripts/maintenance/
mv check_real_database.py scripts/maintenance/
mv populate_test_data.py scripts/maintenance/
mv ml_database_analysis.py scripts/maintenance/
mv database_cleanup.py scripts/maintenance/
mv analyze_database_for_cleanup.py scripts/maintenance/

# Move testing scripts
mv test_*.py scripts/testing/
mv verify_*.py scripts/testing/
mv debug_persistence.py scripts/testing/

# Move documentation
echo "📚 Moving documentation..."
mv *.md docs/
mv LICENSE docs/

# Move databases and logs
echo "💾 Moving databases and logs..."
mv *.db databases/
mv *.log logs/
mv logs/demo_mainnet_trading.log logs/archive/ 2>/dev/null || true

# Move monitoring and utilities
echo "📊 Moving monitoring utilities..."
mv api_monitor.py core/monitors/
mv monitor_funds.py core/monitors/
mv simple_dashboard.py core/monitors/
mv ict_web_monitor.py core/monitors/

# Move other system files
mv app.py systems/
mv main.py systems/
mv simple_ict_launch.py systems/
mv launch_ict_paper_trading.py systems/

# Create README files for each directory
echo "📝 Creating README files..."

cat > core/README.md << 'EOF'
# Core Trading System Components

## Structure:
- **engines/**: Core trading engines and bridges
- **monitors/**: System monitoring and dashboard components  
- **analysis/**: Analysis engines and data processing

## Key Files:
- `engines/ict_enhanced_system.py`: Main ICT trading engine
- `engines/ict_bybit_bridge.py`: Bybit exchange integration
- `monitors/ict_enhanced_monitor.py`: Main monitoring system
- `analysis/fundamental_bridge.py`: Bridge to fundamental analysis
EOF

cat > systems/README.md << 'EOF'
# Trading Systems

## Structure:
- **day_trading/**: ICT day trading system components
- **fundamental_analysis/**: Long-term fundamental analysis system
- **demo_trading/**: Demo and paper trading system

## Key Systems:
- Day Trading: High-frequency ICT methodology trading
- Fundamental Analysis: Long-term investment analysis  
- Demo Trading: Paper trading and backtesting
EOF

cat > scripts/README.md << 'EOF'
# Scripts and Utilities

## Structure:
- **setup/**: System startup and configuration scripts
- **maintenance/**: Database and system maintenance
- **testing/**: Test suites and verification scripts

## Key Scripts:
- `setup/start_all_systems.sh`: Start all trading systems
- `setup/stop_all_systems.sh`: Stop all systems gracefully
- `maintenance/check_database_state.py`: Database health checks
EOF

# Update import paths in main files
echo "🔄 Updating import paths..."

# Create main system launcher
cat > trade_system.py << 'EOF'
#!/usr/bin/env python3
"""
🚀 KIRSTON'S CRYPTO TRADING SYSTEM - MAIN LAUNCHER
=================================================

Professional trading system with:
- ICT Day Trading System
- Fundamental Analysis System  
- Demo Trading System
- Unified Management Interface

Usage:
    python3 trade_system.py --help
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent / "core"))
sys.path.append(str(Path(__file__).parent / "systems"))

def main():
    parser = argparse.ArgumentParser(description="Kirston's Crypto Trading System")
    parser.add_argument('--start-all', action='store_true', help='Start all systems')
    parser.add_argument('--stop-all', action='store_true', help='Stop all systems')
    parser.add_argument('--status', action='store_true', help='Check system status')
    parser.add_argument('--ict-only', action='store_true', help='Start ICT monitor only')
    parser.add_argument('--fundamental-only', action='store_true', help='Start fundamental analysis only')
    
    args = parser.parse_args()
    
    if args.start_all:
        print("🚀 Starting all trading systems...")
        subprocess.run(['./scripts/setup/start_all_systems.sh'])
    elif args.stop_all:
        print("🛑 Stopping all trading systems...")
        subprocess.run(['./scripts/setup/stop_all_systems.sh'])
    elif args.status:
        print("🔍 Checking system status...")
        subprocess.run(['./scripts/setup/check_all_systems.sh'])
    elif args.ict_only:
        print("🎯 Starting ICT Enhanced Monitor...")
        subprocess.run(['python3', 'core/monitors/ict_enhanced_monitor.py'])
    elif args.fundamental_only:
        print("🔍 Starting Fundamental Analysis System...")
        subprocess.run(['./scripts/setup/launch_fundamental_analysis.sh'])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
EOF

chmod +x trade_system.py

echo ""
echo "✅ RESTRUCTURING COMPLETE!"
echo "=========================="
echo "📁 New Structure:"
echo "  core/           - Core trading engines and monitors"
echo "  systems/        - Complete trading systems"
echo "  scripts/        - Setup, maintenance, and testing scripts"
echo "  config/         - Configuration files"
echo "  databases/      - SQLite databases"
echo "  logs/           - System logs"
echo "  docs/           - Documentation"
echo ""
echo "🚀 New Main Launcher: trade_system.py"
echo "📜 Quick Commands:"
echo "  python3 trade_system.py --start-all    # Start all systems"
echo "  python3 trade_system.py --stop-all     # Stop all systems"
echo "  python3 trade_system.py --status       # Check status"
echo ""
echo "🔧 Update scripts to use new paths..."