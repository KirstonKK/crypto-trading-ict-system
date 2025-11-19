#!/bin/bash
# Trading Safety Features - Quick Reference
# =========================================

# Emergency Stop Commands
echo "🚨 EMERGENCY STOP COMMANDS"
echo "=========================="
echo ""
echo "1. Create emergency stop file:"
echo "   touch /tmp/trading_emergency_stop"
echo ""
echo "2. Set environment variable:"
echo "   export EMERGENCY_STOP=true"
echo ""
echo "3. Create workspace stop file:"
echo "   touch EMERGENCY_STOP.txt"
echo ""

# Clear Emergency Stop
echo "🔧 CLEAR EMERGENCY STOP"
echo "======================="
echo ""
echo "1. Remove temp file:"
echo "   rm /tmp/trading_emergency_stop"
echo ""
echo "2. Remove workspace file:"
echo "   rm EMERGENCY_STOP.txt"
echo ""
echo "3. Unset environment:"
echo "   unset EMERGENCY_STOP"
echo ""

# Test Safety Features
echo "✅ TEST SAFETY FEATURES"
echo "======================"
echo ""
echo "Run comprehensive test:"
echo "   python3 scripts/testing/test_safety_features.py"
echo ""

# Check Safety Status
echo "📊 CHECK SAFETY STATUS"
echo "====================="
echo ""
echo "View recent safety logs:"
echo "   tail -f logs/ict_monitor.log | grep 'Safety'"
echo ""
echo "Check for rejections:"
echo "   grep 'TRADE REJECTED' logs/ict_monitor.log"
echo ""
echo "View daily loss tracker:"
echo "   grep 'Daily Loss' logs/ict_monitor.log"
echo ""

# Trading Mode Configuration
echo "⚙️  TRADING MODE CONFIG"
echo "======================"
echo ""
echo "Enable auto-trading (USE WITH CAUTION):"
echo "   export AUTO_TRADING=true"
echo ""
echo "Enable manual confirmation (RECOMMENDED):"
echo "   export AUTO_TRADING=false"
echo ""

# Safety Limits ($50 Account)
echo "📈 SAFETY LIMITS ($50 Account)"
echo "==============================="
echo ""
echo "Risk per Trade:      $0.50 (1%)"
echo "Daily Loss Limit:    $2.50 (5%)"
echo "Max Position Size:   $10.00 (20%)"
echo "Portfolio Risk:      $1.00 (2%)"
echo "Min Position Size:   $5.00 (Bybit)"
echo "Blow Up Threshold:   $10.00"
echo ""

# Quick Status Check
echo "🔍 QUICK STATUS CHECK"
echo "===================="
echo ""
echo "Check if emergency stop is active:"
if [ -f "/tmp/trading_emergency_stop" ]; then
    echo "   ⚠️  EMERGENCY STOP ACTIVE: /tmp/trading_emergency_stop exists"
else
    echo "   ✅ No emergency stop file found"
fi
echo ""

if [ -f "EMERGENCY_STOP.txt" ]; then
    echo "   ⚠️  EMERGENCY STOP ACTIVE: EMERGENCY_STOP.txt exists"
else
    echo "   ✅ No workspace stop file found"
fi
echo ""

if [ "$EMERGENCY_STOP" = "true" ]; then
    echo "   ⚠️  EMERGENCY STOP ACTIVE: EMERGENCY_STOP environment variable set"
else
    echo "   ✅ No emergency stop environment variable"
fi
echo ""

# Current Configuration
echo "⚙️  CURRENT CONFIGURATION"
echo "========================"
echo ""
echo "AUTO_TRADING: ${AUTO_TRADING:-false}"
echo "BYBIT_TESTNET: ${BYBIT_TESTNET:-false}"
echo "EMERGENCY_STOP: ${EMERGENCY_STOP:-false}"
echo ""

# Help
echo "📚 DOCUMENTATION"
echo "==============="
echo ""
echo "Full documentation: docs/SAFETY_FEATURES.md"
echo "Test script: scripts/testing/test_safety_features.py"
echo "Safety module: core/safety/trading_safety.py"
echo ""
