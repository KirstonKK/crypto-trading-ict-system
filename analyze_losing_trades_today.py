#!/usr/bin/env python3
"""
Analyze Today's Losing Trades - Performance Analysis and Lessons Learned
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, Counter

def analyze_trading_performance():
    """Comprehensive analysis of today's trading performance"""
    
    # Database paths to check
    db_paths = [
        '/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/trading_data.db',
        '/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/data/trading.db'
    ]
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"🔍 TRADING ANALYSIS FOR {today}")
    print("=" * 80)
    
    results = {}
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n📊 Analyzing database: {db_path}")
            try:
                results[db_path] = analyze_database(db_path, today)
            except Exception as e:
                print(f"❌ Error analyzing {db_path}: {e}")
        else:
            print(f"⚠️  Database not found: {db_path}")
    
    return results

def analyze_database(db_path, today):
    """Analyze specific database for trading performance"""
    
    conn = sqlite3.connect(db_path)
    
    # Check available tables
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    print(f"📋 Available tables: {list(tables['name'])}")
    
    analysis_results = {}
    
    # Look for trading-related tables
    trading_tables = ['signals', 'trades', 'trading_journal', 'live_signals', 'trade_history']
    
    for table in trading_tables:
        if table in list(tables['name']):
            print(f"\n🔎 Analyzing table: {table}")
            try:
                # Get table schema
                schema = pd.read_sql_query(f"PRAGMA table_info({table})", conn)
                print(f"Columns: {list(schema['name'])}")
                
                # Get today's data
                query = f"SELECT * FROM {table} WHERE date(timestamp) = '{today}' OR date(created_at) = '{today}' OR date(signal_time) = '{today}'"
                try:
                    data = pd.read_sql_query(query, conn)
                    if len(data) > 0:
                        analysis_results[table] = analyze_table_data(data, table)
                    else:
                        print(f"   No data found for today in {table}")
                except Exception as e:
                    # Try alternative date column names
                    for date_col in ['date', 'time', 'scan_time', 'entry_time']:
                        try:
                            query = f"SELECT * FROM {table} WHERE date({date_col}) = '{today}'"
                            data = pd.read_sql_query(query, conn)
                            if len(data) > 0:
                                analysis_results[table] = analyze_table_data(data, table)
                                break
                        except:
                            continue
                    else:
                        print(f"   Could not find date column for {table}: {e}")
                        
            except Exception as e:
                print(f"   ❌ Error analyzing {table}: {e}")
    
    conn.close()
    return analysis_results

def analyze_table_data(data, table_name):
    """Analyze specific table data for patterns"""
    
    print(f"   📈 Found {len(data)} records in {table_name}")
    
    analysis = {
        'total_records': len(data),
        'columns': list(data.columns),
        'sample_data': data.head(3).to_dict('records') if len(data) > 0 else []
    }
    
    # Look for PnL/performance indicators
    pnl_columns = ['pnl', 'profit_loss', 'result', 'outcome', 'status', 'direction', 'crypto']
    
    for col in pnl_columns:
        if col in data.columns:
            print(f"   📊 Analysis of {col}:")
            if col in ['pnl', 'profit_loss']:
                # Numeric PnL analysis
                try:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
                    total_pnl = data[col].sum()
                    winning_trades = len(data[data[col] > 0])
                    losing_trades = len(data[data[col] < 0])
                    
                    print(f"      Total PnL: ${total_pnl:.2f}")
                    print(f"      Winning Trades: {winning_trades}")
                    print(f"      Losing Trades: {losing_trades}")
                    
                    if losing_trades > 0:
                        avg_loss = data[data[col] < 0][col].mean()
                        max_loss = data[data[col] < 0][col].min()
                        print(f"      Average Loss: ${avg_loss:.2f}")
                        print(f"      Maximum Loss: ${max_loss:.2f}")
                    
                    analysis['pnl_summary'] = {
                        'total_pnl': total_pnl,
                        'winning_trades': winning_trades,
                        'losing_trades': losing_trades,
                        'avg_loss': avg_loss if losing_trades > 0 else 0,
                        'max_loss': max_loss if losing_trades > 0 else 0
                    }
                    
                except Exception as e:
                    print(f"      Error analyzing PnL: {e}")
            
            elif col in ['result', 'outcome', 'status']:
                # Categorical analysis
                value_counts = data[col].value_counts()
                print(f"      {col} distribution:")
                for value, count in value_counts.items():
                    print(f"        {value}: {count}")
                analysis[f'{col}_distribution'] = value_counts.to_dict()
            
            elif col in ['direction', 'crypto']:
                # Direction/crypto analysis
                value_counts = data[col].value_counts()
                print(f"      {col} distribution:")
                for value, count in value_counts.items():
                    print(f"        {value}: {count}")
                analysis[f'{col}_distribution'] = value_counts.to_dict()
    
    return analysis

def identify_patterns_and_lessons(analysis_results):
    """Identify patterns in losing trades and extract lessons"""
    
    print("\n" + "=" * 80)
    print("🎯 PATTERNS & LESSONS LEARNED")
    print("=" * 80)
    
    lessons = []
    
    # Aggregate data across all tables
    total_losses = 0
    total_trades = 0
    crypto_performance = defaultdict(list)
    direction_performance = defaultdict(list)
    
    for db_path, db_results in analysis_results.items():
        print(f"\n📊 Analysis from {os.path.basename(db_path)}:")
        
        for table, table_data in db_results.items():
            if 'pnl_summary' in table_data:
                pnl = table_data['pnl_summary']
                losing_trades = pnl['losing_trades']
                total_losses += losing_trades
                total_trades += pnl['winning_trades'] + losing_trades
                
                print(f"   {table}: {losing_trades} losing trades")
                
                if losing_trades >= 8:
                    lessons.append(f"⚠️  High loss rate in {table}: {losing_trades} losses")
            
            # Analyze crypto performance
            if 'crypto_distribution' in table_data:
                crypto_dist = table_data['crypto_distribution']
                for crypto, count in crypto_dist.items():
                    crypto_performance[crypto].append(count)
            
            # Analyze direction performance
            if 'direction_distribution' in table_data:
                dir_dist = table_data['direction_distribution']
                for direction, count in dir_dist.items():
                    direction_performance[direction].append(count)
    
    print(f"\n📈 OVERALL PERFORMANCE:")
    print(f"   Total Trades Today: {total_trades}")
    print(f"   Total Losses: {total_losses}")
    if total_trades > 0:
        win_rate = ((total_trades - total_losses) / total_trades) * 100
        print(f"   Win Rate: {win_rate:.1f}%")
    
    # Pattern Analysis
    print(f"\n🔍 PATTERN ANALYSIS:")
    
    # Crypto performance patterns
    if crypto_performance:
        print(f"   Crypto Activity:")
        for crypto, counts in crypto_performance.items():
            total_count = sum(counts)
            print(f"     {crypto}: {total_count} signals")
            if total_count >= 3:
                lessons.append(f"🔄 High activity in {crypto}: {total_count} signals - may indicate over-trading")
    
    # Direction bias patterns
    if direction_performance:
        print(f"   Direction Bias:")
        total_buys = sum(direction_performance.get('BUY', []))
        total_sells = sum(direction_performance.get('SELL', []))
        print(f"     BUY signals: {total_buys}")
        print(f"     SELL signals: {total_sells}")
        
        if total_buys > total_sells * 2:
            lessons.append("📈 Strong BUY bias detected - may need better bearish signal detection")
        elif total_sells > total_buys * 2:
            lessons.append("📉 Strong SELL bias detected - may need better bullish signal detection")
        elif total_sells == 0:
            lessons.append("⚠️  NO SELL signals generated - bearish detection may be broken")
    
    # Loss pattern analysis
    if total_losses >= 8:
        lessons.append("🚨 CRITICAL: 8+ losing trades indicates systematic issues")
        lessons.append("💡 Recommendation: Review confluence requirements and risk management")
        lessons.append("🔧 Action: Consider increasing minimum confluence score threshold")
        lessons.append("⏸️  Action: Implement temporary trading pause for system review")
    
    return lessons

def main():
    """Main analysis function"""
    print("🚀 Starting Trading Performance Analysis...")
    
    # Analyze trading performance
    analysis_results = analyze_trading_performance()
    
    # Extract patterns and lessons
    lessons = identify_patterns_and_lessons(analysis_results)
    
    # Display lessons learned
    print("\n" + "=" * 80)
    print("📚 KEY LESSONS LEARNED")
    print("=" * 80)
    
    if lessons:
        for i, lesson in enumerate(lessons, 1):
            print(f"{i}. {lesson}")
    else:
        print("✅ No critical patterns detected in available data")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("🎯 IMMEDIATE RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = [
        "📊 Review confluence score thresholds - may be too low",
        "⚡ Check if comprehensive ICT methodology is generating quality signals",
        "🔍 Verify market conditions aren't affecting signal quality",
        "💰 Review risk management parameters (stop-loss, take-profit)",
        "📈 Analyze if specific cryptos are performing worse than others",
        "🕐 Check if specific time periods have higher loss rates",
        "🔄 Consider implementing signal filtering during high volatility",
        "⏳ Implement cooling-off periods after consecutive losses"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n✨ Analysis complete!")

if __name__ == "__main__":
    main()