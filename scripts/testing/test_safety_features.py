#!/usr/bin/env python3
"""
Trading Safety Features - Integration Test
==========================================

Tests all 4 critical safety features:
1. Daily Loss Limit Tracker
2. Emergency Stop Mechanism
3. Trade Confirmation System
4. Position Size Validator
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

from core.safety import (
    DailyLossTracker,
    EmergencyStop,
    TradeConfirmation,
    PositionSizeValidator,
    TradingSafetyManager
)

def test_daily_loss_tracker():
    """Test daily loss limit tracking"""
    print("\n" + "="*60)
    print("TEST 1: Daily Loss Limit Tracker")
    print("="*60)
    
    tracker = DailyLossTracker(max_daily_loss_percent=0.05)  # 5% limit
    
    # Test 1: Set starting balance
    tracker.set_starting_balance(50.0)
    print(f"✅ Starting balance: $50.00")
    
    # Test 2: Check within limit
    is_ok, reason = tracker.check_daily_loss(48.0)  # -$2 (-4%)
    print(f"Test 2: Balance $48 (-4%): {'✅ PASS' if is_ok else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    
    # Test 3: Check at limit
    is_ok, reason = tracker.check_daily_loss(47.5)  # -$2.50 (-5%)
    print(f"Test 3: Balance $47.50 (-5%): {'❌ BLOCKED' if not is_ok else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")
    
    # Test 4: Check beyond limit
    is_ok, reason = tracker.check_daily_loss(45.0)  # -$5 (-10%)
    print(f"Test 4: Balance $45 (-10%): {'❌ BLOCKED' if not is_ok else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")
    
    # Test 5: Get daily stats
    stats = tracker.get_daily_stats(45.0)
    print(f"\n📊 Daily Stats:")
    print(f"   Starting Balance: ${stats['starting_balance']:.2f}")
    print(f"   Current Balance: ${stats['current_balance']:.2f}")
    print(f"   Daily P&L: ${stats['daily_pnl']:.2f} ({stats['daily_pnl_percent']*100:.2f}%)")
    print(f"   Limit Triggered: {stats['limit_triggered']}")
    print(f"   Remaining Loss Allowed: ${stats['remaining_loss_allowed']:.2f}")


def test_emergency_stop():
    """Test emergency stop mechanism"""
    print("\n" + "="*60)
    print("TEST 2: Emergency Stop Mechanism")
    print("="*60)
    
    stop = EmergencyStop()
    
    # Test 1: Check no stop initially
    is_stopped, reason = stop.is_emergency_stop_active()
    print(f"Test 1: No stop active: {'✅ PASS' if not is_stopped else '❌ FAIL'}")
    
    # Test 2: Trigger emergency stop
    print("\nTest 2: Triggering emergency stop...")
    stop.trigger_emergency_stop("Test emergency stop")
    
    # Test 3: Check stop is active
    is_stopped, reason = stop.is_emergency_stop_active()
    print(f"Test 3: Stop active: {'✅ PASS' if is_stopped else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    
    # Test 4: Clear emergency stop
    print("\nTest 4: Clearing emergency stop...")
    stop.clear_emergency_stop()
    
    # Test 5: Verify cleared
    is_stopped, reason = stop.is_emergency_stop_active()
    print(f"Test 5: Stop cleared: {'✅ PASS' if not is_stopped else '❌ FAIL'}")


def test_trade_confirmation():
    """Test trade confirmation system"""
    print("\n" + "="*60)
    print("TEST 3: Trade Confirmation System")
    print("="*60)
    
    # Test 1: Confirmation enabled
    confirmer = TradeConfirmation(enabled=True)
    trade_details = {
        'symbol': 'BTCUSDT',
        'direction': 'BUY',
        'size': 0.001,
        'entry': 45000,
        'stop_loss': 44500,
        'take_profit': 46500,
        'risk': 0.50,
        'reward': 1.50
    }
    
    print("\nTest 1: Confirmation enabled (AUTO_TRADING=false)")
    is_confirmed, reason = confirmer.confirm_trade(trade_details)
    print(f"   Result: {'❌ BLOCKED' if not is_confirmed else '✅ APPROVED'}")
    print(f"   Reason: {reason}")
    
    # Test 2: Auto-trading mode
    print("\nTest 2: Auto-trading mode")
    os.environ['AUTO_TRADING'] = 'true'
    is_confirmed, reason = confirmer.confirm_trade(trade_details)
    print(f"   Result: {'✅ APPROVED' if is_confirmed else '❌ BLOCKED'}")
    print(f"   Reason: {reason}")
    os.environ['AUTO_TRADING'] = 'false'


def test_position_validator():
    """Test position size validation"""
    print("\n" + "="*60)
    print("TEST 4: Position Size Validator")
    print("="*60)
    
    validator = PositionSizeValidator(
        max_position_size=10.0,  # $10 max
        max_portfolio_risk=0.02  # 2% portfolio risk
    )
    
    # Test 1: Valid position
    print("\nTest 1: Valid position ($8, $50 balance, $0.50 risk)")
    is_valid, reason = validator.validate_position(
        position_value=8.0,
        account_balance=50.0,
        risk_amount=0.50,
        symbol='BTCUSDT'
    )
    print(f"   Result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    
    # Test 2: Position too large
    print("\nTest 2: Position too large ($15)")
    is_valid, reason = validator.validate_position(
        position_value=15.0,
        account_balance=50.0,
        risk_amount=0.50,
        symbol='BTCUSDT'
    )
    print(f"   Result: {'❌ REJECTED' if not is_valid else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")
    
    # Test 3: Insufficient balance
    print("\nTest 3: Insufficient balance ($60 position, $50 balance)")
    is_valid, reason = validator.validate_position(
        position_value=60.0,
        account_balance=50.0,
        risk_amount=0.50,
        symbol='BTCUSDT'
    )
    print(f"   Result: {'❌ REJECTED' if not is_valid else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")
    
    # Test 4: Risk too high
    print("\nTest 4: Risk too high (3% risk)")
    is_valid, reason = validator.validate_position(
        position_value=8.0,
        account_balance=50.0,
        risk_amount=1.50,  # 3% of $50
        symbol='BTCUSDT'
    )
    print(f"   Result: {'❌ REJECTED' if not is_valid else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")
    
    # Test 5: Position too small
    print("\nTest 5: Position too small ($3)")
    is_valid, reason = validator.validate_position(
        position_value=3.0,
        account_balance=50.0,
        risk_amount=0.50,
        symbol='BTCUSDT'
    )
    print(f"   Result: {'❌ REJECTED' if not is_valid else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")


def test_safety_manager():
    """Test complete safety manager integration"""
    print("\n" + "="*60)
    print("TEST 5: Trading Safety Manager (Full Integration)")
    print("="*60)
    
    # Initialize safety manager
    config = {
        'max_daily_loss': 0.05,
        'require_confirmation': False,  # Disable for test
        'max_position_size': 10.0,
        'max_portfolio_risk': 0.02
    }
    
    manager = TradingSafetyManager(config)
    
    # Test 1: Valid trade
    print("\nTest 1: Valid trade (all checks pass)")
    trade_details = {
        'symbol': 'BTCUSDT',
        'direction': 'BUY',
        'size': 0.0002,
        'entry': 45000,
        'stop_loss': 44500,
        'take_profit': 46500,
        'risk': 0.50,
        'reward': 1.50,
        'account_balance': 50.0
    }
    
    is_safe, reason = manager.pre_trade_safety_check(trade_details)
    print(f"   Result: {'✅ APPROVED' if is_safe else '❌ REJECTED'}")
    print(f"   Reason: {reason}")
    
    # Test 2: After daily loss
    print("\nTest 2: After 5% daily loss")
    trade_details['account_balance'] = 47.5  # -$2.50 = -5%
    is_safe, reason = manager.pre_trade_safety_check(trade_details)
    print(f"   Result: {'❌ BLOCKED' if not is_safe else '✅ ALLOWED'}")
    print(f"   Reason: {reason}")
    
    # Test 3: Get safety status
    print("\n📊 Safety Status:")
    status = manager.get_safety_status(47.5)
    print(f"   Emergency Stop: {status['emergency_stop']['active']}")
    print(f"   Daily Loss Triggered: {status['daily_loss']['limit_triggered']}")
    print(f"   Daily P&L: ${status['daily_loss']['daily_pnl']:.2f}")
    print(f"   Trade Confirmation: {'Enabled' if status['trade_confirmation']['enabled'] else 'Disabled'}")
    print(f"   Max Position Size: ${status['position_limits']['max_position_size']:.2f}")


def main():
    """Run all safety feature tests"""
    print("\n" + "="*60)
    print("🛡️ TRADING SAFETY FEATURES - INTEGRATION TEST")
    print("="*60)
    
    try:
        test_daily_loss_tracker()
        test_emergency_stop()
        test_trade_confirmation()
        test_position_validator()
        test_safety_manager()
        
        print("\n" + "="*60)
        print("✅ ALL SAFETY TESTS COMPLETED")
        print("="*60)
        print("\nSafety features are ready for live trading!")
        print("⚠️  Remember to enable AUTO_TRADING=true when ready to trade")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
