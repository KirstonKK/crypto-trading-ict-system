#!/usr/bin/env python3
"""
Web-based TradingView Alert Dashboard
Real-time web interface to monitor webhook alerts
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
from collections import deque
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-monitor-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global alert storage
alerts = deque(maxlen=100)
stats = {
    'total_alerts': 0,
    'buy_signals': 0,
    'sell_signals': 0,
    'last_alert': None,
    'start_time': datetime.now()
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get current alerts"""
    return jsonify({
        'alerts': list(alerts),
        'stats': {
            **stats,
            'last_alert': stats['last_alert'].isoformat() if stats['last_alert'] else None,
            'start_time': stats['start_time'].isoformat(),
            'uptime_seconds': (datetime.now() - stats['start_time']).total_seconds()
        }
    })

@app.route('/api/simulate', methods=['POST'])
def simulate_alert():
    """Simulate a TradingView alert"""
    data = request.json
    symbol = data.get('symbol', 'BTCUSDT')
    action = data.get('action', 'BUY')
    
    import random
    price_ranges = {
        "BTCUSDT": (60000, 70000),
        "ETHUSDT": (2500, 3500),
        "BNBUSDT": (500, 700),
        "ADAUSDT": (0.3, 0.6)
    }
    
    price_min, price_max = price_ranges.get(symbol, (100, 1000))
    
    alert = {
        "symbol": symbol,
        "action": action,
        "price": round(random.uniform(price_min, price_max), 2),
        "timestamp": datetime.now().isoformat() + "Z",
        "confidence": round(random.uniform(0.6, 0.9), 2),
        "timeframe": random.choice(["1h", "4h", "1d"]),
        "rsi": round(random.uniform(30, 70), 1),
        "source": "SIMULATION"
    }
    
    # Send to actual webhook
    try:
        webhook_url = "http://localhost:8080/webhook/tradingview"
        response = requests.post(webhook_url, json=alert, timeout=5)
        status = "SUCCESS" if response.status_code == 200 else f"FAILED ({response.status_code})"
    except Exception as e:
        status = f"ERROR: {str(e)[:50]}"
    
    # Add to our monitoring
    add_alert(alert, status)
    
    return jsonify({"status": "sent", "alert": alert})

@app.route('/api/clear', methods=['POST'])
def clear_alerts():
    """Clear all alerts"""
    alerts.clear()
    stats['total_alerts'] = 0
    stats['buy_signals'] = 0
    stats['sell_signals'] = 0
    stats['last_alert'] = None
    
    # Broadcast clear event
    socketio.emit('alerts_cleared')
    
    return jsonify({"status": "cleared"})

def add_alert(alert_data, status="RECEIVED"):
    """Add alert to monitoring"""
    alert = {
        'id': len(alerts) + 1,
        'data': alert_data,
        'status': status,
        'received_at': datetime.now().isoformat(),
        'source': alert_data.get('source', 'TRADINGVIEW')
    }
    
    alerts.appendleft(alert)
    update_stats(alert_data)
    
    # Broadcast to connected clients
    socketio.emit('new_alert', alert)

def update_stats(alert_data):
    """Update statistics"""
    stats['total_alerts'] += 1
    stats['last_alert'] = datetime.now()
    
    action = alert_data.get('action', '').upper()
    if action in ['BUY', 'LONG']:
        stats['buy_signals'] += 1
    elif action in ['SELL', 'SHORT']:
        stats['sell_signals'] += 1

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print("Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to TradingView Monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected: {request.sid}")

def create_template():
    """Create the HTML template"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView Alert Monitor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e, #2d2d44);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #4CAF50;
        }
        .header h1 {
            color: #4CAF50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .buy-signal { color: #4CAF50; }
        .sell-signal { color: #f44336; }
        .controls {
            text-align: center;
            padding: 20px;
        }
        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 10px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        .btn.sell { background: linear-gradient(45deg, #f44336, #d32f2f); }
        .btn.clear { background: linear-gradient(45deg, #ff9800, #f57c00); }
        .alerts-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .alerts-table {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .table-header {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            display: grid;
            grid-template-columns: 80px 100px 80px 120px 80px 80px 100px;
            gap: 15px;
            font-weight: bold;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .alert-row {
            padding: 15px;
            display: grid;
            grid-template-columns: 80px 100px 80px 120px 80px 80px 100px;
            gap: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            transition: background 0.3s;
        }
        .alert-row:hover {
            background: rgba(255,255,255,0.05);
        }
        .alert-row.new {
            animation: slideIn 0.5s ease-out;
            background: rgba(76, 175, 80, 0.2);
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .status {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            text-align: center;
        }
        .status.success { background: rgba(76, 175, 80, 0.3); }
        .status.error { background: rgba(244, 67, 54, 0.3); }
        .no-alerts {
            text-align: center;
            padding: 40px;
            color: #888;
            font-size: 1.2em;
        }
        .webhook-url {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            margin: 20px;
            border-radius: 10px;
            font-family: monospace;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 TradingView Alert Monitor</h1>
        <div id="connection-status">Connecting...</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="total-alerts">0</div>
            <div>Total Alerts</div>
        </div>
        <div class="stat-card">
            <div class="stat-value buy-signal" id="buy-signals">0</div>
            <div>Buy Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-value sell-signal" id="sell-signals">0</div>
            <div>Sell Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="uptime">0s</div>
            <div>Uptime</div>
        </div>
    </div>

    <div class="controls">
        <button class="btn" onclick="simulateAlert('BTCUSDT', 'BUY')">📈 Simulate BUY</button>
        <button class="btn sell" onclick="simulateAlert('ETHUSDT', 'SELL')">📉 Simulate SELL</button>
        <button class="btn clear" onclick="clearAlerts()">🧹 Clear Alerts</button>
    </div>

    <div class="webhook-url">
        <strong>Webhook URL:</strong> http://localhost:8080/webhook/tradingview
    </div>

    <div class="alerts-container">
        <div class="alerts-table">
            <div class="table-header">
                <div>Time</div>
                <div>Symbol</div>
                <div>Action</div>
                <div>Price</div>
                <div>RSI</div>
                <div>Source</div>
                <div>Status</div>
            </div>
            <div id="alerts-list">
                <div class="no-alerts">No alerts received yet. Test with the buttons above!</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let alerts = [];
        let stats = { total_alerts: 0, buy_signals: 0, sell_signals: 0, start_time: new Date() };

        socket.on('connect', function() {
            document.getElementById('connection-status').textContent = '🟢 Connected';
            document.getElementById('connection-status').style.color = '#4CAF50';
            loadInitialData();
        });

        socket.on('disconnect', function() {
            document.getElementById('connection-status').textContent = '🔴 Disconnected';
            document.getElementById('connection-status').style.color = '#f44336';
        });

        socket.on('new_alert', function(alert) {
            alerts.unshift(alert);
            if (alerts.length > 50) alerts.pop();
            
            // Update stats
            stats.total_alerts++;
            if (alert.data.action.toUpperCase() === 'BUY' || alert.data.action.toUpperCase() === 'LONG') {
                stats.buy_signals++;
            } else if (alert.data.action.toUpperCase() === 'SELL' || alert.data.action.toUpperCase() === 'SHORT') {
                stats.sell_signals++;
            }
            
            updateDisplay();
        });

        socket.on('alerts_cleared', function() {
            alerts = [];
            stats = { total_alerts: 0, buy_signals: 0, sell_signals: 0, start_time: new Date() };
            updateDisplay();
        });

        function loadInitialData() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    alerts = data.alerts;
                    stats = data.stats;
                    stats.start_time = new Date(stats.start_time);
                    updateDisplay();
                });
        }

        function updateDisplay() {
            // Update stats
            document.getElementById('total-alerts').textContent = stats.total_alerts;
            document.getElementById('buy-signals').textContent = stats.buy_signals;
            document.getElementById('sell-signals').textContent = stats.sell_signals;
            
            // Update uptime
            const uptime = Math.floor((new Date() - stats.start_time) / 1000);
            const minutes = Math.floor(uptime / 60);
            const seconds = uptime % 60;
            document.getElementById('uptime').textContent = `${minutes}m ${seconds}s`;

            // Update alerts table
            const alertsList = document.getElementById('alerts-list');
            if (alerts.length === 0) {
                alertsList.innerHTML = '<div class="no-alerts">No alerts received yet. Test with the buttons above!</div>';
                return;
            }

            alertsList.innerHTML = alerts.map(alert => {
                const time = new Date(alert.received_at).toLocaleTimeString();
                const data = alert.data;
                const actionClass = data.action.toLowerCase() === 'buy' || data.action.toLowerCase() === 'long' ? 'buy-signal' : 'sell-signal';
                const statusClass = alert.status.includes('SUCCESS') ? 'success' : 'error';
                
                return `
                    <div class="alert-row">
                        <div>${time}</div>
                        <div>${data.symbol}</div>
                        <div class="${actionClass}">${data.action}</div>
                        <div>$${data.price ? data.price.toLocaleString() : 'N/A'}</div>
                        <div>${data.rsi || 'N/A'}</div>
                        <div>${alert.source}</div>
                        <div class="status ${statusClass}">${alert.status}</div>
                    </div>
                `;
            }).join('');
        }

        function simulateAlert(symbol, action) {
            fetch('/api/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ symbol, action })
            });
        }

        function clearAlerts() {
            fetch('/api/clear', { method: 'POST' });
        }

        // Auto-update uptime
        setInterval(() => {
            const uptime = Math.floor((new Date() - stats.start_time) / 1000);
            const minutes = Math.floor(uptime / 60);
            const seconds = uptime % 60;
            document.getElementById('uptime').textContent = `${minutes}m ${seconds}s`;
        }, 1000);
    </script>
</body>
</html>"""
    
    with open(os.path.join(template_dir, 'dashboard.html'), 'w') as f:
        f.write(html_content)

def main():
    """Main function"""
    print("🚀 Starting TradingView Web Monitor...")
    create_template()
    
    # Start the webhook monitor
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🎯 Webhook endpoint: http://localhost:8080/webhook/tradingview")
    print("⚡ Real-time updates via WebSocket")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()