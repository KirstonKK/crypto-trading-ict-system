# Monitoring System

This directory contains all monitoring and dashboard components.

## Dashboards (`dashboards/`)

- `proactive_web_dashboard.py` - **MAIN DASHBOARD** - Smart Crypto Trading Monitor (Port 5001)
  - Monitors BTC, SOL, ETH, XRP during market hours (08:00-22:00 UTC)
  - Ghana time tracking table
  - Risk management ($100 per trade, 1:3 RR)
  - Trading journal with confluences
- `web_monitor.py` - Alternative web monitoring interface
- `webhook_monitor.py` - Webhook monitoring utilities
- `proactive_monitor.py` - Background proactive monitoring engine

## Scripts (`scripts/`)

- `enhanced_main_predictive.py` - Enhanced main script with predictive features

## Usage

Run the main dashboard: `python monitoring/dashboards/proactive_web_dashboard.py`
Access at: http://localhost:5001
