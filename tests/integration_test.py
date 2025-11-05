#!/usr/bin/env python3
"""
Integration Test for Diagnostic and SOL Analysis Endpoints
==========================================================

Quick verification that the new endpoints work correctly.
"""

import sys
import os
import tempfile
import sqlite3
from datetime import date

# Add paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

from diagnostics.system_diagnostic import create_diagnostic_checker
from analysis.sol_trade_analyzer import create_sol_analyzer

# Constants
EXPECTED_DIAGNOSTIC_CHECKS = 6  # Number of diagnostic checks to expect


def setup_test_database():
    """Create a temporary test database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create required tables
    cursor.execute('''
        CREATE TABLE signals (
            id INTEGER PRIMARY KEY,
            signal_id TEXT,
            symbol TEXT,
            direction TEXT,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            confluence_score REAL,
            timeframes TEXT,
            ict_concepts TEXT,
            session TEXT,
            market_regime TEXT,
            directional_bias TEXT,
            signal_strength TEXT,
            status TEXT,
            entry_time TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE paper_trades (
            id INTEGER PRIMARY KEY,
            signal_id TEXT,
            symbol TEXT,
            direction TEXT,
            entry_price REAL,
            position_size REAL,
            stop_loss REAL,
            take_profit REAL,
            status TEXT,
            risk_amount REAL,
            entry_time TIMESTAMP,
            current_price REAL,
            unrealized_pnl REAL,
            realized_pnl REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE daily_stats (
            id INTEGER PRIMARY KEY,
            date DATE,
            scan_count INTEGER,
            signals_generated INTEGER,
            paper_balance REAL
        )
    ''')
    
    # Insert sample data
    today = date.today().isoformat()
    
    cursor.execute('''
        INSERT INTO daily_stats (date, scan_count, signals_generated, paper_balance)
        VALUES (?, ?, ?, ?)
    ''', (today, 50, 10, 100.0))
    
    cursor.execute('''
        INSERT INTO signals 
        (signal_id, symbol, direction, entry_price, stop_loss, take_profit,
         confluence_score, timeframes, ict_concepts, session, market_regime,
         directional_bias, signal_strength, status, entry_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('SIG_TEST_001', 'SOLUSDT', 'BUY', 150.0, 145.0, 158.0, 0.85,
          '["5m","15m"]', '["FVG","Liquidity"]', 'NY', 'TRENDING',
          'BULLISH', 'HIGH', 'ACTIVE', today))
    
    conn.commit()
    conn.close()
    
    return path


def test_diagnostic_endpoint():
    """Test the diagnostic system."""
    print("\n" + "="*60)
    print("🔍 Testing Diagnostic System")
    print("="*60)
    
    db_path = setup_test_database()
    
    try:
        diagnostic = create_diagnostic_checker(db_path=db_path)
        results = diagnostic.run_full_diagnostic()
        
        print(f"\n✅ Diagnostic Status: {results['overall_status']}")
        print(f"📊 Timestamp: {results['timestamp']}")
        print(f"⚠️  Issues Found: {results['issue_count']}")
        
        print("\n📋 Check Results:")
        for check_name, check_result in results['checks'].items():
            status_emoji = "✅" if check_result['status'] == 'OK' else "⚠️" if check_result['status'] == 'WARNING' else "❌"
            print(f"  {status_emoji} {check_name}: {check_result['status']} - {check_result['message']}")
        
        if results['issues']:
            print("\n⚠️  Issues:")
            for issue in results['issues']:
                print(f"  - {issue}")
        
        assert results['overall_status'] in ['HEALTHY', 'WARNING', 'ERROR']
        assert 'checks' in results
        assert len(results['checks']) == EXPECTED_DIAGNOSTIC_CHECKS
        
        print("\n✅ Diagnostic test PASSED")
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_sol_analysis_endpoint():
    """Test the SOL analysis system."""
    print("\n" + "="*60)
    print("🌟 Testing SOL Trade Analyzer")
    print("="*60)
    
    try:
        analyzer = create_sol_analyzer()
        current_price = 150.0
        
        print(f"\n📈 Analyzing SOL at ${current_price:.2f}")
        
        results = analyzer.analyze_sol_opportunity(current_price)
        
        print(f"\n✅ Analysis Status: {results['status']}")
        print(f"💹 Symbol: {results['symbol']}")
        print(f"💰 Current Price: ${results['current_price']:.2f}")
        
        if 'detailed_analysis' in results:
            analysis = results['detailed_analysis']
            
            if 'liquidity_zones' in analysis:
                print("\n🎯 Liquidity Zones:")
                buy_zones = analysis['liquidity_zones'].get('buy_side', [])
                sell_zones = analysis['liquidity_zones'].get('sell_side', [])
                
                print(f"  Buy-side (resistance): {len(buy_zones)} zones")
                for zone in buy_zones[:2]:
                    print(f"    - ${zone['price']:.2f} (strength: {zone['strength']:.2f})")
                
                print(f"  Sell-side (support): {len(sell_zones)} zones")
                for zone in sell_zones[:2]:
                    print(f"    - ${zone['price']:.2f} (strength: {zone['strength']:.2f})")
            
            if 'fair_value_gaps' in analysis:
                fvgs = analysis['fair_value_gaps']
                print(f"\n📊 Fair Value Gaps:")
                print(f"  Bullish: {len(fvgs.get('bullish', []))} gaps")
                print(f"  Bearish: {len(fvgs.get('bearish', []))} gaps")
        
        if 'recommendations' in results:
            recs = results['recommendations']
            print(f"\n💡 Trading Bias: {recs['bias']}")
            
            if recs['suggested_trades']:
                print(f"📈 Suggested Trades: {len(recs['suggested_trades'])}")
                for i, trade in enumerate(recs['suggested_trades'], 1):
                    print(f"\n  Trade #{i}:")
                    print(f"    Direction: {trade['direction']}")
                    print(f"    Entry: ${trade['entry_zone']['low']:.2f} - ${trade['entry_zone']['high']:.2f}")
                    print(f"    Stop Loss: ${trade['stop_loss']:.2f}")
                    print(f"    Targets: {len(trade['targets'])} levels")
                    print(f"    Risk/Reward: {trade['risk_reward']}:1")
            else:
                print("  No high-probability setups at current price")
        
        assert results['status'] == 'success'
        assert results['symbol'] == 'SOL'
        assert 'recommendations' in results
        
        print("\n✅ SOL analysis test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ SOL analysis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("🧪 Integration Tests for Diagnostic & SOL Analysis")
    print("="*60)
    
    results = []
    
    # Test diagnostic system
    try:
        result = test_diagnostic_endpoint()
        results.append(("Diagnostic System", result))
    except Exception as e:
        print(f"\n❌ Diagnostic test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Diagnostic System", False))
    
    # Test SOL analysis
    try:
        result = test_sol_analysis_endpoint()
        results.append(("SOL Trade Analyzer", result))
    except Exception as e:
        print(f"\n❌ SOL analysis test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SOL Trade Analyzer", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All integration tests PASSED!")
    else:
        print("⚠️  Some integration tests FAILED")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
