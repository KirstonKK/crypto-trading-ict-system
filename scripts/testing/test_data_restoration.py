#!/usr/bin/env python3
"""
Database Restoration Verification Test
====================================

This script tests that all fields correctly display previous data after a restart.
"""

from src.database.trading_database import TradingDatabase
from datetime import datetime
import json

def test_data_restoration():
    """Test that all data is correctly restored from database after restart"""
    
    print("🔄 TESTING DATABASE RESTORATION AFTER RESTART")
    print("=" * 60)
    
    db = TradingDatabase()
    
    # Test 1: Check signals restoration
    print("\n1️⃣ SIGNALS RESTORATION TEST:")
    signals = db.get_signals_today()
    print("   📊 Total signals in database: {len(signals)}")
    
    for i, signal in enumerate(signals, 1):
        print("   📈 Signal {i}: {signal.get('symbol', 'N/A')} {signal.get('direction', 'N/A')} "
              f"- Confidence: {signal.get('confluence_score', 0):.2f}")
    
    # Test 2: Check trades restoration
    print("\n2️⃣ TRADES RESTORATION TEST:")
    trades = db.get_trades_today()
    print("   💰 Total trades in database: {len(trades)}")
    
    executed_trades = [t for t in trades if t.get('status') == 'CLOSED']
    active_trades = [t for t in trades if t.get('status') in ['ACTIVE', 'OPEN']]
    lost_trades = [t for t in trades if t.get('status') == 'LOST_IN_RESTART']
    
    print("   ✅ Executed trades: {len(executed_trades)}")
    print("   🔄 Active trades: {len(active_trades)}")
    print("   ⚠️  Lost in restart: {len(lost_trades)}")
    
    # Show executed trade details
    for i, trade in enumerate(executed_trades, 1):
        pnl = trade.get('pnl', 0)
        outcome = 'WIN' if pnl > 0 else 'LOSS'
        print("   💸 Trade {i}: {trade.get('symbol', 'N/A')} - PnL: ${pnl:.2f} ({outcome})")
    
    # Test 3: Check daily stats restoration
    print("\n3️⃣ DAILY STATS RESTORATION TEST:")
    daily_stats = db.get_daily_stats()
    
    print("   📊 Signals generated: {daily_stats.get('signals_generated', 0)}")
    print("   💰 Paper balance: ${daily_stats.get('paper_balance', 100):.2f}")
    print("   📈 Total PnL: ${daily_stats.get('total_pnl', 0):.2f}")
    print("   🔢 Scan count: {daily_stats.get('scan_count', 0)}")
    print("   💸 Trades executed: {daily_stats.get('trades_executed', 0)}")
    
    # Test 4: Verify user's specific data
    print("\n4️⃣ USER DATA VERIFICATION TEST:")
    expected_signals = 7
    expected_executed = 3
    expected_lost = 4
    
    actual_signals = len(signals)
    actual_executed = len(executed_trades)
    actual_lost = len(lost_trades)
    
    print("   Expected: {expected_signals} signals, {expected_executed} executed, {expected_lost} lost")
    print("   Actual:   {actual_signals} signals, {actual_executed} executed, {actual_lost} lost")
    
    verification_passed = (
        actual_signals == expected_signals and
        actual_executed == expected_executed and
        actual_lost == expected_lost
    )
    
    if verification_passed:
        print("   ✅ USER DATA VERIFICATION: PASSED")
    else:
        print("   ❌ USER DATA VERIFICATION: FAILED")
    
    # Test 5: Check that all losses are properly recorded
    print("\n5️⃣ LOSS VERIFICATION TEST:")
    all_losses = all(trade.get('pnl', 0) < 0 for trade in executed_trades)
    
    if executed_trades:
        print("   📉 All executed trades are losses: {'✅ YES' if all_losses else '❌ NO'}")
        total_loss = sum(trade.get('pnl', 0) for trade in executed_trades)
        print("   💸 Total loss amount: ${total_loss:.2f}")
    else:
        print("   📉 No executed trades to verify")
    
    # Test 6: Web interface data simulation
    print("\n6️⃣ WEB INTERFACE DATA SIMULATION:")
    
    # Simulate what the web interface will display
    web_data = {
        'signals_today': daily_stats.get('signals_generated', 0),
        'paper_balance': daily_stats.get('paper_balance', 100),
        'daily_pnl': daily_stats.get('total_pnl', 0),
        'scan_count': daily_stats.get('scan_count', 0),
        'account_blown': daily_stats.get('paper_balance', 100) <= 10,
        'live_signals': signals,
        'active_trades_count': len(active_trades),
        'executed_trades': executed_trades,
        'lost_trades': lost_trades
    }
    
    print("   🌐 Web interface will display:")
    print("     📊 Signals Today: {web_data['signals_today']}")
    print("     💰 Paper Balance: ${web_data['paper_balance']:.2f}")
    print("     📈 Daily PnL: ${web_data['daily_pnl']:.2f}")
    print("     🔢 Scan Count: {web_data['scan_count']}")
    print("     💥 Account Blown: {web_data['account_blown']}")
    print("     📈 Live Signals: {len(web_data['live_signals'])}")
    print("     🔄 Active Trades: {web_data['active_trades_count']}")
    print("     ✅ Executed Trades: {len(web_data['executed_trades'])}")
    print("     ⚠️  Lost Trades: {len(web_data['lost_trades'])}")
    
    return {
        'verification_passed': verification_passed,
        'web_data': web_data,
        'signals': signals,
        'trades': trades,
        'daily_stats': daily_stats
    }

def simulate_monitor_restart():
    """Simulate what happens when the monitor restarts"""
    
    print("\n🔄 SIMULATING MONITOR RESTART")
    print("=" * 60)
    
    db = TradingDatabase()
    
    # This is what the monitor does on startup
    daily_stats = db.get_daily_stats()
    todays_signals = db.get_signals_today()
    todays_trades = db.get_trades_today()
    
    # Restore state variables
    scan_count = daily_stats.get('scan_count', 0)
    signals_today = daily_stats.get('signals_generated', 0)
    paper_balance = daily_stats.get('paper_balance', 100.0)
    total_paper_pnl = daily_stats.get('total_pnl', 0.0)
    account_blown = paper_balance <= 10.0
    
    # Restore signals and trades
    live_signals = todays_signals.copy()
    active_paper_trades = [
        trade for trade in todays_trades 
        if trade.get('status') in ['ACTIVE', 'OPEN', 'LOST_IN_RESTART']
    ]
    
    completed_trades = [
        trade for trade in todays_trades 
        if trade.get('status') == 'CLOSED'
    ]
    
    print("📊 MONITOR STATE AFTER RESTART:")
    print("   🔢 Scan Count: {scan_count}")
    print("   📈 Signals Today: {signals_today}")
    print("   💰 Paper Balance: ${paper_balance:.2f}")
    print("   📊 Total PnL: ${total_paper_pnl:.2f}")
    print("   💥 Account Blown: {account_blown}")
    print("   🎯 Live Signals Count: {len(live_signals)}")
    print("   🔄 Active Trades: {len(active_paper_trades)}")
    print("   ✅ Completed Trades: {len(completed_trades)}")
    
    # Verify the exact user data
    losses = len([t for t in completed_trades if t.get('pnl', 0) < 0])
    lost_in_restart = len([t for t in todays_trades if t.get('status') == 'LOST_IN_RESTART'])
    
    print("\n✅ USER VERIFICATION:")
    print("   📊 Total signals: {len(live_signals)} (Expected: 7)")
    print("   💸 Executed trades: {len(completed_trades)} (Expected: 3)")
    print("   📉 All losses: {losses == len(completed_trades)} (Expected: True)")
    print("   ⚠️  Lost in restart: {lost_in_restart} (Expected: 4)")
    
    user_data_correct = (
        len(live_signals) == 7 and
        len(completed_trades) == 3 and
        losses == len(completed_trades) and
        lost_in_restart == 4
    )
    
    if user_data_correct:
        print("   🎉 ALL USER DATA RESTORED CORRECTLY!")
    else:
        print("   ⚠️  Some user data may not match expectations")
    
    return user_data_correct

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           DATABASE RESTORATION VERIFICATION TEST                ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Run tests
    test_results = test_data_restoration()
    restart_success = simulate_monitor_restart()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                         TEST RESULTS                            ║
╠══════════════════════════════════════════════════════════════════╣
║  📊 Data Restoration: {'✅ PASSED' if test_results['verification_passed'] else '❌ FAILED'}                        ║
║  🔄 Monitor Restart: {'✅ SUCCESS' if restart_success else '❌ ISSUES'}                         ║
║                                                                  ║
║  🎯 After restart, all fields will show:                        ║
║     • 7 signals generated today                                 ║
║     • 3 executed trades (all losses)                            ║
║     • 4 active trades lost in restart                           ║
║     • Correct PnL and balance                                   ║
║     • Complete trading journal                                  ║
║                                                                  ║
║  {'🚀 READY FOR PRODUCTION!' if test_results['verification_passed'] and restart_success else '⚠️  NEEDS ATTENTION'}                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")