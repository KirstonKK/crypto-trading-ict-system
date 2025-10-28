#!/usr/bin/env python3
"""
Usage Example: System Diagnostic and SOL Trade Analysis
=======================================================

This script demonstrates how to use the new diagnostic and SOL analysis features.
Run this after starting the ICT Enhanced Monitor server.
"""

import requests
import json


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_diagnostic_endpoint(base_url="http://localhost:5001"):
    """Test the system diagnostic endpoint."""
    print_section("🔍 System Diagnostic Check")
    
    try:
        response = requests.get(f"{base_url}/api/diagnostic", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Overall Status: {data['overall_status']}")
            print(f"📅 Timestamp: {data['timestamp']}")
            print(f"⚠️  Issues: {data['issue_count']}")
            
            print("\n📋 Health Checks:")
            for check_name, check_result in data['checks'].items():
                status_emoji = {
                    'OK': '✅',
                    'WARNING': '⚠️',
                    'ERROR': '❌'
                }.get(check_result['status'], '❓')
                
                print(f"\n  {status_emoji} {check_name.upper()}")
                print(f"     Status: {check_result['status']}")
                print(f"     Message: {check_result['message']}")
            
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_sol_analysis_endpoint(base_url="http://localhost:5001"):
    """Test the SOL trade analysis endpoint."""
    print_section("🌟 SOL Trade Analysis")
    
    try:
        response = requests.get(f"{base_url}/api/analysis/sol", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n💹 Symbol: {data['symbol']}")
            print(f"💰 Current Price: ${data['current_price']:.2f}")
            print(f"✅ Status: {data['status']}")
            
            # Show liquidity zones
            if 'detailed_analysis' in data and 'liquidity_zones' in data['detailed_analysis']:
                zones = data['detailed_analysis']['liquidity_zones']
                
                print("\n🎯 LIQUIDITY ZONES:")
                print(f"  Buy-Side: {len(zones.get('buy_side', []))} zones")
                print(f"  Sell-Side: {len(zones.get('sell_side', []))} zones")
            
            # Show trade recommendations
            if 'recommendations' in data:
                recs = data['recommendations']
                print(f"\n💡 Trading Bias: {recs['bias']}")
                
                if recs.get('suggested_trades'):
                    print(f"📈 Found {len(recs['suggested_trades'])} trade setup(s)")
                    for i, trade in enumerate(recs['suggested_trades'], 1):
                        print(f"\n  Trade #{i}: {trade['direction']}")
                        print(f"    Entry: ${trade['entry_zone']['low']:.2f} - ${trade['entry_zone']['high']:.2f}")
                        print(f"    Stop Loss: ${trade['stop_loss']:.2f}")
                        print(f"    R:R = {trade['risk_reward']}:1")
                else:
                    print("  ℹ️  No high-probability setups at current price")
            
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    """Run usage examples."""
    print("\n" + "="*70)
    print("  🧪 System Diagnostic & SOL Analysis - Usage Examples")
    print("="*70)
    print("\n📝 Note: Make sure the ICT Enhanced Monitor is running on port 5001")
    
    base_url = "http://localhost:5001"
    
    diag_result = test_diagnostic_endpoint(base_url)
    sol_result = test_sol_analysis_endpoint(base_url)
    
    print_section("📊 Summary")
    print(f"\n  Diagnostic: {'✅ PASSED' if diag_result else '❌ FAILED'}")
    print(f"  SOL Analysis: {'✅ PASSED' if sol_result else '❌ FAILED'}")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
