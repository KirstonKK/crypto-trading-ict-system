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
