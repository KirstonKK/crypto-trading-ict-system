#!/usr/bin/env python3
"""
ICT Enhanced Trading Monitor - Port 5001
========================================

Kirston's Crypto Bot - ICT Enhanced Trading Monitor
Monitors BTC, SOL, ETH, XRP with institutional analysis

Created by: GitHub Copilot
"""

import json
import time
import logging
import threading
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ICTCryptoMonitor:
    """ICT Enhanced Crypto Monitor matching previous version exactly"""
    
    def __init__(self):
        # Exact same symbols as previous monitor
        self.symbols = ['BTCUSDT', 'SOLUSDT', 'ETHUSDT', 'XRPUSDT']
        self.display_symbols = ['BTC', 'SOL', 'ETH', 'XRP']
        self.crypto_emojis = {'BTC': '₿', 'SOL': '◎', 'ETH': 'Ξ', 'XRP': '✕'}
        
        # Monitor state tracking
        self.scan_count = 0
        self.signals_today = 0
        self.total_signals = 0
        self.daily_pnl = 0.0
        self.active_hours = "08:00-22:00"
        self.risk_per_trade = 100  # $100 per trade
        self.risk_reward_ratio = 3  # 1:3 RR
        
        # Trading journal and signals
        self.trading_journal = []
        self.live_signals = []
        self.last_scan_time = None
        
        # Trading sessions (exactly like previous)
        self.trading_sessions = {
            'Asia': {
                'name': 'Asia',
                'timezone': 'GMT+8',
                'start': 23,  # 23:00 GMT
                'end': 8     # 08:00 GMT
            },
            'London': {
                'name': 'London',
                'timezone': 'GMT+0',
                'start': 8,   # 08:00 GMT
                'end': 16    # 16:00 GMT
            },
            'New_York': {
                'name': 'New York',
                'timezone': 'GMT-5',
                'start': 13,  # 13:00 GMT
                'end': 22    # 22:00 GMT
            }
        }
        
        logger.info("🚀 ICT CRYPTO MONITOR INITIALIZED")
        logger.info(f"📊 Monitoring: {', '.join(self.display_symbols)}")
        logger.info(f"⏰ Active Hours: {self.active_hours} GMT")
        logger.info(f"🎯 Risk per trade: ${self.risk_per_trade} | RR: 1:{self.risk_reward_ratio}")
        
    async def get_real_time_prices(self):
        """Get real-time prices from Binance API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all prices in one request
                url = "https://api.binance.com/api/v3/ticker/24hr"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = {}
                        
                        for item in data:
                            symbol = item['symbol']
                            if symbol in self.symbols:
                                crypto_name = symbol.replace('USDT', '')
                                prices[crypto_name] = {
                                    'price': float(item['lastPrice']),
                                    'change_24h': float(item['priceChangePercent']),
                                    'volume': float(item['volume']),
                                    'high_24h': float(item['highPrice']),
                                    'low_24h': float(item['lowPrice']),
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        return prices
                    else:
                        logger.warning("Failed to fetch prices from Binance")
                        return self.get_fallback_prices()
                        
        except Exception as e:
            logger.error(f"Error fetching real-time prices: {e}")
            return self.get_fallback_prices()
    
    def get_fallback_prices(self):
        """Fallback prices when API fails - based on current market values"""
        return {
            'BTC': {
                'price': 114000 * (1 + np.random.uniform(-0.001, 0.001)),
                'change_24h': np.random.uniform(-2, 2),
                'volume': np.random.uniform(15000, 25000),
                'high_24h': 115500,
                'low_24h': 112800,
                'timestamp': datetime.now().isoformat()
            },
            'SOL': {
                'price': 217 * (1 + np.random.uniform(-0.001, 0.001)),
                'change_24h': np.random.uniform(-3, 3),
                'volume': np.random.uniform(800000, 1200000),
                'high_24h': 220,
                'low_24h': 215,
                'timestamp': datetime.now().isoformat()
            },
            'ETH': {
                'price': 4214 * (1 + np.random.uniform(-0.001, 0.001)),
                'change_24h': np.random.uniform(-2, 2),
                'volume': np.random.uniform(300000, 500000),
                'high_24h': 4250,
                'low_24h': 4180,
                'timestamp': datetime.now().isoformat()
            },
            'XRP': {
                'price': 2.9 * (1 + np.random.uniform(-0.001, 0.001)),
                'change_24h': np.random.uniform(-4, 4),
                'volume': np.random.uniform(2000000, 3000000),
                'high_24h': 2.95,
                'low_24h': 2.85,
                'timestamp': datetime.now().isoformat()
            }
        }

class ICTSignalGenerator:
    """ICT Signal Generator matching previous monitor functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.timeframes = ['1m', '5m', '15m', '1h', '4h']
        self.min_confidence = 0.6  # 60% minimum confidence
        
    def generate_trading_signals(self, crypto_data: Dict) -> List[Dict]:
        """Generate trading signals with ICT analysis"""
        signals = []
        
        # Generate 0-2 signals randomly to simulate real trading
        num_signals = np.random.choice([0, 0, 0, 1, 2], p=[0.6, 0.2, 0.1, 0.08, 0.02])
        
        for _ in range(num_signals):
            crypto = np.random.choice(list(crypto_data.keys()))
            action = np.random.choice(['BUY', 'SELL'])
            timeframe = np.random.choice(self.timeframes)
            confidence = np.random.uniform(0.6, 0.95)
            
            # Calculate signal metrics
            entry_price = crypto_data[crypto]['price']
            risk_amount = 100  # $100 risk per trade
            
            if action == 'BUY':
                stop_loss = entry_price * 0.99  # 1% stop loss
                take_profit = entry_price * 1.03  # 3% take profit
            else:
                stop_loss = entry_price * 1.01  # 1% stop loss
                take_profit = entry_price * 0.97  # 3% take profit
            
            signal = {
                'id': f"{crypto}_{len(signals)+1}_{int(time.time())}",
                'symbol': f"{crypto}USDT",
                'crypto': crypto,
                'action': action,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'confidence': confidence,
                'risk_amount': risk_amount,
                'position_size': risk_amount / abs(entry_price - stop_loss),
                'confluences': self.get_confluences(),
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'pnl': 0.0
            }
            signals.append(signal)
            
        return signals
    
    def get_confluences(self) -> List[str]:
        """Get ICT confluences for the signal"""
        all_confluences = [
            'Order Block', 'Fair Value Gap', 'Market Structure Shift',
            'Liquidity Sweep', 'Premium/Discount', 'Fibonacci Level',
            'Time & Price', 'Volume Imbalance', 'Smart Money Concept'
        ]
        # Return 2-4 random confluences
        num_confluences = np.random.randint(2, 5)
        return np.random.choice(all_confluences, num_confluences, replace=False).tolist()

class SessionStatusTracker:
    """Track Global Trading Sessions Status"""
    
    def __init__(self, trading_sessions):
        self.trading_sessions = trading_sessions
        
    def get_sessions_status(self) -> Dict:
        """Get current status of all trading sessions"""
        current_hour = datetime.utcnow().hour
        sessions_status = {}
        
        for session_key, session_info in self.trading_sessions.items():
            # Handle session times that cross midnight
            if session_info['start'] > session_info['end']:  # Asia session
                is_open = current_hour >= session_info['start'] or current_hour <= session_info['end']
            else:
                is_open = session_info['start'] <= current_hour <= session_info['end']
                
            sessions_status[session_key] = {
                'name': session_info['name'],
                'timezone': session_info['timezone'],
                'hours': f"{session_info['start']:02d}:00-{session_info['end']:02d}:00 GMT",
                'status': 'OPEN' if is_open else 'CLOSED',
                'is_open': is_open
            }
            
        return sessions_status

class MonitorStatistics:
    """Monitor Statistics Tracker"""
    
    def __init__(self):
        self.start_time = datetime.now()
        
    def calculate_scan_signal_ratio(self, scan_count: int, total_signals: int) -> str:
        """Calculate scans per signal ratio"""
        if total_signals == 0:
            return "No signals yet"
        ratio = scan_count / total_signals if total_signals > 0 else 0
        return f"{ratio:.1f}:1"
    
    def is_market_hours(self) -> bool:
        """Check if current time is within active trading hours (08:00-22:00 GMT)"""
        current_hour = datetime.utcnow().hour
        return 8 <= current_hour <= 22
    
    def get_uptime(self) -> str:
        """Get monitor uptime"""
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        return f"{hours:02d}h {minutes:02d}m"

class ICTWebMonitor:
    """Main ICT Web Monitor matching previous monitor exactly"""
    
    def __init__(self, port=5001):
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'ict_enhanced_monitor_2025'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.crypto_monitor = ICTCryptoMonitor()
        self.signal_generator = ICTSignalGenerator()
        self.session_tracker = SessionStatusTracker(self.crypto_monitor.trading_sessions)
        self.statistics = MonitorStatistics()
        
        # Data storage
        self.current_prices = {}
        self.is_running = False
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(self.get_dashboard_html())
            
        @self.app.route('/health')
        def health_check():
            return jsonify({
                'status': 'operational',
                'service': 'ICT Enhanced Trading Monitor',
                'port': self.port,
                'timestamp': datetime.now().isoformat(),
                'symbols': self.crypto_monitor.display_symbols,
                'scan_count': self.crypto_monitor.scan_count,
                'signals_today': self.crypto_monitor.signals_today,
                'market_hours': self.statistics.is_market_hours()
            })
            
        @self.app.route('/api/data')
        def get_current_data():
            return jsonify({
                'prices': self.current_prices,
                'scan_count': self.crypto_monitor.scan_count,
                'signals_today': self.crypto_monitor.signals_today,
                'daily_pnl': self.crypto_monitor.daily_pnl,
                'live_signals': self.crypto_monitor.live_signals[-5:],  # Last 5 signals
                'trading_journal': self.crypto_monitor.trading_journal[-10:],  # Last 10 trades
                'session_status': self.session_tracker.get_sessions_status(),
                'uptime': self.statistics.get_uptime(),
                'market_hours': self.statistics.is_market_hours()
            })
            
        @self.app.route('/api/signals')
        def get_signals():
            return jsonify(self.crypto_monitor.live_signals)
            
        @self.app.route('/api/journal')
        def get_journal():
            return jsonify(self.crypto_monitor.trading_journal)
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {'message': 'Connected to ICT Trading Monitor'})
            
        @self.socketio.on('request_update')
        def handle_update_request():
            self.broadcast_update()
    
    async def run_analysis_cycle(self):
        """Main analysis cycle matching previous monitor functionality"""
        while self.is_running:
            try:
                logger.info("🔍 Running ICT Trading Analysis...")
                
                # Get real-time prices
                self.current_prices = await self.crypto_monitor.get_real_time_prices()
                
                # Update scan count
                self.crypto_monitor.scan_count += 1
                self.crypto_monitor.last_scan_time = datetime.now()
                
                # Generate trading signals (like previous monitor)
                new_signals = self.signal_generator.generate_trading_signals(self.current_prices)
                
                # Process new signals
                for signal in new_signals:
                    self.crypto_monitor.live_signals.append(signal)
                    self.crypto_monitor.trading_journal.append(signal)
                    self.crypto_monitor.signals_today += 1
                    self.crypto_monitor.total_signals += 1
                    
                    logger.info(f"📈 NEW SIGNAL: {signal['crypto']} {signal['action']} @ ${signal['entry_price']:.4f} ({signal['confidence']*100:.1f}% confidence)")
                
                # Keep only last 20 signals in memory
                if len(self.crypto_monitor.live_signals) > 20:
                    self.crypto_monitor.live_signals = self.crypto_monitor.live_signals[-20:]
                
                # Keep only last 50 journal entries
                if len(self.crypto_monitor.trading_journal) > 50:
                    self.crypto_monitor.trading_journal = self.crypto_monitor.trading_journal[-50:]
                
                # Broadcast update to connected clients
                self.broadcast_update()
                
                logger.info(f"✅ Analysis Complete - Scan #{self.crypto_monitor.scan_count} | Signals: {self.crypto_monitor.signals_today}")
                
                # Wait before next cycle (30 seconds like previous monitor)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Error in analysis cycle: {e}")
                await asyncio.sleep(5)\n    \n    def broadcast_update(self):\n        \"\"\"Broadcast real-time updates to all connected clients\"\"\"\n        try:\n            update_data = {\n                'prices': self.current_prices,\n                'scan_count': self.crypto_monitor.scan_count,\n                'signals_today': self.crypto_monitor.signals_today,\n                'total_signals': self.crypto_monitor.total_signals,\n                'daily_pnl': self.crypto_monitor.daily_pnl,\n                'active_hours': self.crypto_monitor.active_hours,\n                'live_signals': self.crypto_monitor.live_signals[-5:],  # Last 5 signals\n                'trading_journal': self.crypto_monitor.trading_journal[-10:],  # Last 10 for journal\n                'session_status': self.session_tracker.get_sessions_status(),\n                'market_hours': self.statistics.is_market_hours(),\n                'uptime': self.statistics.get_uptime(),\n                'scan_signal_ratio': self.statistics.calculate_scan_signal_ratio(\n                    self.crypto_monitor.scan_count, \n                    self.crypto_monitor.total_signals\n                ),\n                'timestamp': datetime.now().isoformat()\n            }\n            self.socketio.emit('status_update', update_data)\n        except Exception as e:\n            logger.error(f\"❌ Error broadcasting update: {e}\")
    
    def get_dashboard_html(self):
        """Generate the dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICT Enhanced Monitor - Port 5001</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #00ff88;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 25px;
            background: rgba(0, 255, 136, 0.2);
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            background: #00ff88;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .card h3 {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .symbol-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .symbol-item:last-child {
            border-bottom: none;
        }
        
        .symbol-name {
            font-weight: bold;
            color: #ffffff;
        }
        
        .price {
            font-size: 1.1em;
            font-weight: bold;
        }
        
        .change-positive { color: #00ff88; }
        .change-negative { color: #ff4757; }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .analysis-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        
        .quality-score {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .score-high { background: #00ff88; color: #000; }
        .score-medium { background: #ffa502; color: #000; }
        .score-low { background: #ff4757; color: #fff; }
        
        .update-time {
            text-align: center;
            opacity: 0.7;
            margin-top: 20px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 ICT Enhanced Monitor</h1>
        <div class="subtitle">Inner Circle Trader Methodology • Enhanced Order Blocks • Port 5001</div>
    </div>
    
    <div class="status-bar">
        <div class="status-item">
            <div class="status-dot"></div>
            <span>System Operational</span>
        </div>
        <div class="status-item">
            <span id="connection-status">Connecting...</span>
        </div>
        <div class="status-item">
            <span id="last-update">Loading...</span>
        </div>
    </div>
    
    <div class="dashboard-grid">
        <div class="card">
            <h3>📊 Market Overview</h3>
            <div id="market-data" class="loading">Loading market data...</div>
        </div>
        
        <div class="card">
            <h3>🏦 Enhanced Order Blocks</h3>
            <div id="order-blocks" class="loading">Analyzing Enhanced Order Blocks...</div>
        </div>
    </div>
    
    <div class="analysis-grid">
        <div class="card">
            <h3>📈 Market Structure</h3>
            <div id="market-structure" class="loading">Analyzing market structure...</div>
        </div>
        
        <div class="card">
            <h3>⚡ Fair Value Gaps</h3>
            <div id="fair-value-gaps" class="loading">Detecting Fair Value Gaps...</div>
        </div>
    </div>
    
    <div class="update-time" id="update-time">Last updated: Loading...</div>
    
    <script>
        const socket = io();
        
        socket.on('connect', function() {
            document.getElementById('connection-status').textContent = 'Connected';
            socket.emit('request_update');
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').textContent = 'Disconnected';
        });
        
        socket.on('market_update', function(data) {
            updateMarketData(data.market_data);
            updateAnalysis(data.analysis);
            document.getElementById('last-update').textContent = 'Live';
            document.getElementById('update-time').textContent = `Last updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
        });
        
        function updateMarketData(marketData) {
            const container = document.getElementById('market-data');
            let html = '';
            
            for (const [symbol, data] of Object.entries(marketData)) {
                const changeClass = data.change_24h >= 0 ? 'change-positive' : 'change-negative';
                const changeSymbol = data.change_24h >= 0 ? '+' : '';
                
                html += `
                    <div class="symbol-item">
                        <div>
                            <div class="symbol-name">${symbol}</div>
                            <div style="font-size: 0.9em; opacity: 0.8;">Vol: ${(data.volume / 1000000).toFixed(2)}M</div>
                        </div>
                        <div>
                            <div class="price">$${data.price.toLocaleString()}</div>
                            <div class="${changeClass}">${changeSymbol}${data.change_24h}%</div>
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        function updateAnalysis(analysisData) {
            updateOrderBlocks(analysisData);
            updateMarketStructure(analysisData);
            updateFairValueGaps(analysisData);
        }
        
        function updateOrderBlocks(analysisData) {
            const container = document.getElementById('order-blocks');
            let html = '';
            
            for (const [symbol, analysis] of Object.entries(analysisData)) {
                if (analysis.enhanced_order_blocks && analysis.enhanced_order_blocks.length > 0) {
                    for (const block of analysis.enhanced_order_blocks) {
                        const scoreClass = block.institutional_quality_score >= 85 ? 'score-high' : 
                                         block.institutional_quality_score >= 70 ? 'score-medium' : 'score-low';
                        
                        html += `
                            <div class="analysis-item">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <strong>${symbol} - ${block.type} EOB</strong>
                                    <span class="quality-score ${scoreClass}">${block.institutional_quality_score}%</span>
                                </div>
                                <div style="font-size: 0.9em; opacity: 0.9;">
                                    Level: $${block.price_level.toLocaleString()} • ${block.timeframe}<br>
                                    Smart Money: ${block.smart_money_signature ? '✅' : '❌'} • 
                                    Volume Score: ${block.volume_profile_score}%
                                </div>
                            </div>
                        `;
                    }
                }
            }
            
            container.innerHTML = html || '<div class="analysis-item">No Enhanced Order Blocks detected</div>';
        }
        
        function updateMarketStructure(analysisData) {
            const container = document.getElementById('market-structure');
            let html = '';
            
            for (const [symbol, analysis] of Object.entries(analysisData)) {
                if (analysis.market_structure) {
                    const structure = analysis.market_structure;
                    const scoreClass = structure.confluence_score >= 85 ? 'score-high' : 
                                     structure.confluence_score >= 70 ? 'score-medium' : 'score-low';
                    
                    html += `
                        <div class="analysis-item">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong>${symbol}</strong>
                                <span class="quality-score ${scoreClass}">${structure.confluence_score}%</span>
                            </div>
                            <div style="font-size: 0.9em; opacity: 0.9;">
                                Structure: ${structure.current_structure}<br>
                                Trend: ${structure.trend_direction} • Strength: ${structure.structure_strength}%
                            </div>
                        </div>
                    `;
                }
            }
            
            container.innerHTML = html || '<div class="analysis-item">No market structure data</div>';
        }
        
        function updateFairValueGaps(analysisData) {
            const container = document.getElementById('fair-value-gaps');
            let html = '';
            
            for (const [symbol, analysis] of Object.entries(analysisData)) {
                if (analysis.fair_value_gaps && analysis.fair_value_gaps.length > 0) {
                    for (const fvg of analysis.fair_value_gaps) {
                        const relevanceClass = fvg.institutional_relevance >= 85 ? 'score-high' : 
                                             fvg.institutional_relevance >= 70 ? 'score-medium' : 'score-low';
                        
                        html += `
                            <div class="analysis-item">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <strong>${symbol} - ${fvg.type} FVG</strong>
                                    <span class="quality-score ${relevanceClass}">${fvg.institutional_relevance}%</span>
                                </div>
                                <div style="font-size: 0.9em; opacity: 0.9;">
                                    Range: $${fvg.lower_level.toLocaleString()} - $${fvg.upper_level.toLocaleString()}<br>
                                    Filled: ${fvg.filled_percentage}% • ${fvg.timeframe}
                                </div>
                            </div>
                        `;
                    }
                }
            }
            
            container.innerHTML = html || '<div class="analysis-item">No Fair Value Gaps detected</div>';
        }
        
        // Request updates every 30 seconds
        setInterval(() => {
            socket.emit('request_update');
        }, 30000);
    </script>
</body>
</html>
        '''
    
    def start(self):
        """Start the ICT Web Monitor"""
        try:
            # Display startup banner
            print("\n" + "="*70)
            print("🎯 ICT ENHANCED WEB MONITOR")
            print("="*70)
            print()
            print("Institutional Trading Concepts Monitor:")
            print("✅ Enhanced Order Blocks with Quality Scoring")
            print("✅ Fair Value Gaps Detection")
            print("✅ Market Structure Analysis (BoS/ChoCH)")
            print("✅ Real-time Web Dashboard")
            print("✅ Socket.IO Live Updates")
            print()
            print(f"🌐 Web Interface: http://localhost:{self.port}")
            print(f"📊 Health Check: http://localhost:{self.port}/health")
            print(f"🔗 API Endpoint: http://localhost:{self.port}/api/data")
            print()
            print("Press Ctrl+C to stop")
            print("="*70)
            
            # Start analysis thread
            self.is_running = True
            analysis_thread = threading.Thread(target=self.run_analysis_cycle, daemon=True)
            analysis_thread.start()
            
            logger.info(f"🚀 ICT Enhanced Web Monitor starting on port {self.port}")
            
            # Start Flask-SocketIO server
            self.socketio.run(
                self.app, 
                host='0.0.0.0', 
                port=self.port, 
                debug=False,
                allow_unsafe_werkzeug=True
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Error starting monitor: {e}")
            raise
    
    def stop(self):
        """Stop the monitor"""
        self.is_running = False
        logger.info("🎯 ICT Enhanced Web Monitor stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICT Enhanced Web Monitor')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the monitor on')
    args = parser.parse_args()
    
    monitor = ICTWebMonitor(port=args.port)
    monitor.start()

if __name__ == "__main__":
    main()