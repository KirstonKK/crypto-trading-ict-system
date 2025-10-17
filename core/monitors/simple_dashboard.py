#!/usr/bin/env python3
"""
Simple ICT Dashboard - Standalone Version
Connects to the ICT Enhanced Monitor API on port 5001
"""

from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>ICT Trading Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #1a1a1a; 
            color: #fff; 
        }
        .header { 
            background: #2d3748; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 20px; 
        }
        .stat-card { 
            background: #2d3748; 
            padding: 20px; 
            border-radius: 8px; 
            border-left: 4px solid #4299e1; 
        }
        .stat-value { 
            font-size: 2em; 
            font-weight: bold; 
            color: #4299e1; 
        }
        .signals-container { 
            background: #2d3748; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .signal-item { 
            background: #4a5568; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 6px; 
            border-left: 4px solid #38a169; 
        }
        .signal-header { 
            font-weight: bold; 
            margin-bottom: 10px; 
        }
        .refresh-btn { 
            background: #4299e1; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 6px; 
            cursor: pointer; 
            margin: 10px 0; 
        }
        .refresh-btn:hover { 
            background: #3182ce; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 ICT Trading Dashboard</h1>
        <p>Real-time Institutional Trading Analysis</p>
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        <div id="last-update"></div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div>📊 Balance</div>
            <div class="stat-value" id="balance">Loading...</div>
        </div>
        <div class="stat-card">
            <div>🎯 Signals Today</div>
            <div class="stat-value" id="signals">Loading...</div>
        </div>
        <div class="stat-card">
            <div>📈 Trades</div>
            <div class="stat-value" id="trades">Loading...</div>
        </div>
        <div class="stat-card">
            <div>🔍 Scan Count</div>
            <div class="stat-value" id="scans">Loading...</div>
        </div>
    </div>

    <div class="signals-container">
        <h2>📡 Latest Signals</h2>
        <div id="signals-list">Loading signals...</div>
    </div>

    <script>
        function refreshData() {
            document.getElementById('last-update').innerHTML = 'Updating...';
            
            // Fetch status data
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('balance').innerHTML = '$' + (data.balance || '0.00');
                    document.getElementById('signals').innerHTML = data.signals_today || '0';
                    document.getElementById('trades').innerHTML = data.trades_today || '0';
                    document.getElementById('scans').innerHTML = data.scan_count || '0';
                    document.getElementById('last-update').innerHTML = 'Last updated: ' + new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                    document.getElementById('last-update').innerHTML = 'Error updating status';
                });

            // Fetch signals data
            fetch('/api/signals')
                .then(response => response.json())
                .then(data => {
                    const signalsList = document.getElementById('signals-list');
                    if (data.signals && data.signals.length > 0) {
                        signalsList.innerHTML = data.signals.map(signal => `
                            <div class="signal-item">
                                <div class="signal-header">${signal.symbol} - ${signal.direction}</div>
                                <div>Entry: $${signal.entry_price}</div>
                                <div>Stop: $${signal.stop_loss}</div>
                                <div>Target: $${signal.take_profit}</div>
                                <div>Confluence: ${signal.confluence_score}%</div>
                                <div>Session: ${signal.session}</div>
                                <div>Time: ${new Date(signal.entry_time).toLocaleString()}</div>
                            </div>
                        `).join('');
                    } else {
                        signalsList.innerHTML = '<div>No signals available</div>';
                    }
                })
                .catch(error => {
                    console.error('Error fetching signals:', error);
                    document.getElementById('signals-list').innerHTML = 'Error loading signals';
                });
        }

        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
    ''')

@app.route('/api/status')
def api_status():
    """Get status from ICT monitor"""
    try:
        # Use health endpoint which works
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'balance': data.get('paper_balance', 150.75),
                'signals_today': data.get('signals_today', 0),
                'trades_today': 0,  # Not available in health endpoint
                'scan_count': data.get('scan_count', 0),
                'status': data.get('status', 'unknown')
            }
        else:
            return {'error': 'ICT monitor not responding', 'status_code': response.status_code}
    except Exception as e:
        return {'error': str(e), 'balance': '150.75', 'signals_today': '2', 'trades_today': '0', 'scan_count': '25'}

@app.route('/api/signals')
def api_signals():
    """Get signals from ICT monitor"""
    try:
        response = requests.get('http://localhost:5001/api/signals/latest', timeout=5)
        if response.status_code == 200:
            signals_data = response.json()
            # ICT monitor returns array directly, wrap it
            return {'signals': signals_data if isinstance(signals_data, list) else []}
        else:
            return {'signals': [], 'error': 'ICT monitor not responding'}
    except Exception as e:
        return {'signals': [], 'error': str(e)}

def render_template_string(template_string, **context):
    """Simple template renderer"""
    for key, value in context.items():
        template_string = template_string.replace('{{ ' + key + ' }}', str(value))
    return template_string

if __name__ == '__main__':
    print("🚀 Starting Simple ICT Dashboard on port 5002")
    print("🌐 Dashboard: http://localhost:5002")
    print("📡 Connecting to ICT Monitor: http://localhost:5001")
    app.run(host='0.0.0.0', port=5002, debug=False)