#!/usr/bin/env python3
"""
ICT Trading Dashboard System
===========================

Advanced web-based trading dashboard displaying complete ICT analysis
replacing traditional retail indicators with institutional concepts.

Dashboard Components:
- Order Block Analysis: Live detection and quality scoring
- Fair Value Gap Tracking: Real-time gap states and fills
- Market Structure Display: BoS/ChoCH patterns and trend analysis
- Liquidity Mapping: Equal highs/lows and sweep detection
- Fibonacci Confluence: 79% levels and OTE zone analysis
- ICT Signal Generation: Live institutional signals
- Timeframe Hierarchy: 4H bias → 5M setup → 1M execution

Features:
- Real-time institutional analysis
- Interactive ICT level plotting
- Signal alerts and notifications
- Performance tracking and statistics
- Mobile-responsive design
- Professional trading interface

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
import asyncio
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.utils
from threading import Thread
import time

# Import ICT components
from trading.ict_analyzer import ICTAnalyzer, TrendDirection, ICTSignal
from trading.ict_hierarchy import ICTTimeframeHierarchy, HierarchyAnalysis
from trading.order_block_detector import EnhancedOrderBlockDetector, OrderBlockZone, OrderBlockState
from trading.fvg_detector import FVGDetector, FVGZone, FVGState, FVGType
from trading.liquidity_detector import LiquidityDetector, LiquidityZone, LiquidityState
from trading.fibonacci_analyzer import ICTFibonacciAnalyzer, FibonacciZone
from integrations.tradingview.ict_signal_processor import ICTSignalProcessor, ICTProcessedSignal

# Traditional components for data
from src.utils.data_fetcher import DataFetcher
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

@dataclass
class DashboardData:
    """Complete dashboard data structure."""
    timestamp: datetime
    symbol: str
    timeframe: str
    current_price: float
    
    # ICT Analysis Components
    hierarchy_analysis: Optional[Dict] = None
    order_blocks: List[Dict] = None
    fair_value_gaps: List[Dict] = None
    liquidity_zones: List[Dict] = None
    fibonacci_zones: List[Dict] = None
    
    # Signals and alerts
    active_signals: List[Dict] = None
    recent_alerts: List[Dict] = None
    
    # Market context
    market_structure: Dict = None
    session_info: Dict = None
    
    # Performance metrics
    statistics: Dict = None
    
    def __post_init__(self):
        if self.order_blocks is None:
            self.order_blocks = []
        if self.fair_value_gaps is None:
            self.fair_value_gaps = []
        if self.liquidity_zones is None:
            self.liquidity_zones = []
        if self.fibonacci_zones is None:
            self.fibonacci_zones = []
        if self.active_signals is None:
            self.active_signals = []
        if self.recent_alerts is None:
            self.recent_alerts = []
        if self.market_structure is None:
            self.market_structure = {}
        if self.session_info is None:
            self.session_info = {}
        if self.statistics is None:
            self.statistics = {}

class ICTTradingDashboard:
    """
    Advanced ICT Trading Dashboard for institutional analysis display.
    
    Provides real-time visualization of all ICT components including
    Order Blocks, Fair Value Gaps, Market Structure, Liquidity Zones,
    and Fibonacci analysis in a professional trading interface.
    """
    
    def __init__(self, config_path: str = "project/configuration/"):
        """Initialize ICT Trading Dashboard."""
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_path)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='templates', 
                        static_folder='static')
        self.app.config['SECRET_KEY'] = 'ict_dashboard_secret_key_2025'
        
        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize ICT components
        self.ict_analyzer = ICTAnalyzer()
        self.ict_hierarchy = ICTTimeframeHierarchy(config_path)
        self.enhanced_order_block_detector = EnhancedOrderBlockDetector()
        self.fvg_detector = FVGDetector()
        self.liquidity_detector = LiquidityDetector()
        self.fibonacci_analyzer = ICTFibonacciAnalyzer()
        self.signal_processor = ICTSignalProcessor(config_path)
        
        # Data fetcher
        self.data_fetcher = DataFetcher()
        
        # Dashboard configuration
        self.dashboard_config = self._load_dashboard_config()
        
        # Data storage
        self.current_data: Dict[str, DashboardData] = {}
        self.chart_data: Dict[str, pd.DataFrame] = {}
        
        # Real-time update control
        self.update_interval = self.dashboard_config.get('update_interval', 30)  # 30 seconds
        self.is_running = False
        
        # Setup routes
        self._setup_routes()
        self._setup_socket_events()
        
        logger.info("ICT Trading Dashboard initialized")
    
    def _load_dashboard_config(self) -> Dict:
        """Load dashboard configuration."""
        try:
            config = self.config_loader.get_config("ict_dashboard")
        except Exception as e:
            logger.warning(f"Failed to load dashboard config: {e}")
            config = {}
        
        defaults = {
            'default_symbols': ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'],
            'default_timeframes': ['1m', '5m', '1h', '4h'],
            'update_interval': 30,
            'max_order_blocks': 10,
            'max_fvgs': 15,
            'max_liquidity_zones': 8,
            'max_fibonacci_zones': 12,
            'chart_candles': 200,
            'enable_alerts': True,
            'enable_sound': True,
            'theme': 'dark',
            'layout': 'professional'
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template('ict_dashboard.html', 
                                 config=self.dashboard_config)
        
        @self.app.route('/api/dashboard-data/<symbol>/<timeframe>')
        def get_dashboard_data(symbol, timeframe):
            """Get complete dashboard data for symbol/timeframe."""
            try:
                key = f"{symbol}_{timeframe}"
                
                if key in self.current_data:
                    data = self.current_data[key]
                    return jsonify(asdict(data))
                else:
                    # Generate fresh data
                    data = self._generate_dashboard_data(symbol, timeframe)
                    return jsonify(asdict(data)) if data else jsonify({'error': 'No data available'})
                
            except Exception as e:
                logger.error(f"Dashboard data API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/chart-data/<symbol>/<timeframe>')
        def get_chart_data(symbol, timeframe):
            """Get chart data with ICT overlays."""
            try:
                chart_data = self._generate_chart_data(symbol, timeframe)
                return jsonify(chart_data)
                
            except Exception as e:
                logger.error(f"Chart data API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/signals/<symbol>')
        def get_signals(symbol):
            """Get active signals for symbol."""
            try:
                signals = self._get_active_signals(symbol)
                return jsonify(signals)
                
            except Exception as e:
                logger.error(f"Signals API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """Get overall dashboard statistics."""
            try:
                stats = self._generate_statistics()
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"Statistics API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def dashboard_config():
            """Get or update dashboard configuration."""
            if request.method == 'GET':
                return jsonify(self.dashboard_config)
            else:
                try:
                    new_config = request.get_json()
                    self.dashboard_config.update(new_config)
                    return jsonify({'status': 'success'})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files."""
            return send_from_directory('static', filename)
    
    def _setup_socket_events(self):
        """Setup SocketIO events for real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info("Client connected to ICT dashboard")
            emit('status', {'message': 'Connected to ICT Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Client disconnected from ICT dashboard")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle symbol/timeframe subscription."""
            symbol = data.get('symbol')
            timeframe = data.get('timeframe')
            
            if symbol and timeframe:
                logger.info(f"Client subscribed to {symbol} {timeframe}")
                # Send initial data
                dashboard_data = self._generate_dashboard_data(symbol, timeframe)
                if dashboard_data:
                    emit('dashboard_update', asdict(dashboard_data))
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Handle unsubscription."""
            symbol = data.get('symbol')
            timeframe = data.get('timeframe')
            logger.info(f"Client unsubscribed from {symbol} {timeframe}")
    
    def _generate_dashboard_data(self, symbol: str, timeframe: str) -> Optional[DashboardData]:
        """Generate complete dashboard data for symbol/timeframe."""
        try:
            logger.debug(f"Generating dashboard data for {symbol} {timeframe}")
            
            # Fetch market data
            market_data = asyncio.run(self._fetch_market_data_async(symbol, timeframe))
            if not market_data or market_data.empty:
                logger.warning(f"No market data for {symbol} {timeframe}")
                return None
            
            current_price = market_data['close'].iloc[-1]
            
            # Generate ICT analysis
            hierarchy_analysis = asyncio.run(self.ict_hierarchy.analyze_symbol_hierarchy(symbol))
            enhanced_order_blocks = self.enhanced_order_block_detector.detect_enhanced_order_blocks(market_data, symbol, timeframe)
            fair_value_gaps = self.fvg_detector.detect_fair_value_gaps(market_data, symbol, timeframe)
            liquidity_map = self.liquidity_detector.detect_liquidity_zones(market_data, symbol, timeframe)
            fibonacci_zones = self.fibonacci_analyzer.analyze_fibonacci_confluence(
                market_data, symbol, timeframe, order_blocks, fair_value_gaps, liquidity_map.buy_side_liquidity + liquidity_map.sell_side_liquidity
            )
            
            # Get active signals
            active_signals = self._get_active_signals(symbol)
            
            # Create dashboard data
            dashboard_data = DashboardData(
                timestamp=datetime.now(),
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                hierarchy_analysis=self._serialize_hierarchy_analysis(hierarchy_analysis),
                order_blocks=self._serialize_order_blocks(order_blocks),
                fair_value_gaps=self._serialize_fvgs(fair_value_gaps),
                liquidity_zones=self._serialize_liquidity_zones(liquidity_map),
                fibonacci_zones=self._serialize_fibonacci_zones(fibonacci_zones),
                active_signals=active_signals,
                market_structure=self._generate_market_structure_data(market_data, hierarchy_analysis),
                session_info=self._generate_session_info(),
                statistics=self._generate_symbol_statistics(symbol, timeframe)
            )
            
            # Cache the data
            key = f"{symbol}_{timeframe}"
            self.current_data[key] = dashboard_data
            self.chart_data[key] = market_data
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed for {symbol} {timeframe}: {e}")
            return None
    
    async def _fetch_market_data_async(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Fetch market data asynchronously."""
        try:
            # Remove slash for API compatibility
            api_symbol = symbol.replace('/', '')
            
            # Fetch OHLCV data
            data = await self.data_fetcher.fetch_ohlcv_async(
                symbol=api_symbol,
                timeframe=timeframe,
                limit=self.dashboard_config['chart_candles']
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Market data fetch failed for {symbol}: {e}")
            return None
    
    def _serialize_hierarchy_analysis(self, hierarchy: HierarchyAnalysis) -> Dict:
        """Serialize hierarchy analysis for JSON."""
        if not hierarchy:
            return {}
        
        return {
            'trading_bias': hierarchy.trading_bias.value if hierarchy.trading_bias else 'CONSOLIDATION',
            'overall_confidence': hierarchy.overall_confidence,
            'timeframe_alignment': hierarchy.timeframe_alignment,
            'confluence_score': hierarchy.confluence_score,
            'bias_timeframe': hierarchy.bias_timeframe,
            'setup_timeframe': hierarchy.setup_timeframe,
            'execution_timeframe': hierarchy.execution_timeframe,
            'analysis_timestamp': hierarchy.analysis_timestamp.isoformat() if hierarchy.analysis_timestamp else None
        }
    
    def _serialize_order_blocks(self, order_blocks: List[OrderBlockZone]) -> List[Dict]:
        """Serialize Order Blocks for JSON."""
        serialized = []
        
        for ob in order_blocks[:self.dashboard_config['max_order_blocks']]:
            serialized.append({
                'id': ob.zone_id,
                'type': ob.ob_type,
                'high': ob.zone_high,
                'low': ob.zone_low,
                'mid': ob.zone_mid,
                'optimal_entry': ob.optimal_entry,
                'quality': ob.quality.value,
                'state': ob.state.value,
                'strength_score': ob.strength_score,
                'formation_timestamp': ob.formation_timestamp.isoformat(),
                'timeframe': ob.timeframe,
                'times_tested': ob.times_tested,
                'is_fresh': ob.state == OrderBlockState.FRESH
            })
        
        return serialized
    
    def _serialize_fvgs(self, fvgs: List[FVGZone]) -> List[Dict]:
        """Serialize Fair Value Gaps for JSON."""
        serialized = []
        
        for fvg in fvgs[:self.dashboard_config['max_fvgs']]:
            serialized.append({
                'id': fvg.zone_id,
                'type': fvg.fvg_type.value,
                'high': fvg.gap_high,
                'low': fvg.gap_low,
                'mid': fvg.gap_mid,
                'quality': fvg.quality.value,
                'state': fvg.state.value,
                'strength_score': fvg.strength_score,
                'formation_timestamp': fvg.formation_timestamp.isoformat(),
                'timeframe': fvg.timeframe,
                'fill_percentage': fvg.fill_percentage,
                'is_fresh': fvg.state == FVGState.FRESH
            })
        
        return serialized
    
    def _serialize_liquidity_zones(self, liquidity_map) -> List[Dict]:
        """Serialize liquidity zones for JSON."""
        serialized = []
        
        # Combine all liquidity zones
        all_zones = (liquidity_map.buy_side_liquidity + 
                    liquidity_map.sell_side_liquidity + 
                    liquidity_map.psychological_levels + 
                    liquidity_map.session_extremes)
        
        for zone in all_zones[:self.dashboard_config['max_liquidity_zones']]:
            serialized.append({
                'id': zone.zone_id,
                'type': zone.zone_type.value,
                'level': zone.exact_level,
                'high': zone.zone_high,
                'low': zone.zone_low,
                'quality': zone.quality.value,
                'state': zone.state.value,
                'strength_score': zone.strength_score,
                'formation_timestamp': zone.formation_timestamp.isoformat(),
                'times_tested': zone.times_tested,
                'is_swept': zone.is_swept,
                'estimated_stops': zone.estimated_stops
            })
        
        return serialized
    
    def _serialize_fibonacci_zones(self, fib_zones: List[FibonacciZone]) -> List[Dict]:
        """Serialize Fibonacci zones for JSON."""
        serialized = []
        
        for zone in fib_zones[:self.dashboard_config['max_fibonacci_zones']]:
            serialized.append({
                'id': zone.zone_id,
                'type': zone.zone_type.value,
                'level': zone.fibonacci_level,
                'level_name': f"{zone.fibonacci_level*100:.1f}%",
                'price': zone.zone_mid,
                'high': zone.zone_high,
                'low': zone.zone_low,
                'quality': zone.quality.value,
                'confluence_score': zone.confluence_score,
                'institutional_interest': zone.institutional_interest,
                'order_block_alignment': zone.order_block_alignment,
                'fvg_alignment': zone.fvg_alignment,
                'liquidity_alignment': zone.liquidity_alignment,
                'is_ote': zone.fibonacci_level in [0.618, 0.705, 0.79] if zone.retracement else False
            })
        
        return serialized
    
    def _generate_chart_data(self, symbol: str, timeframe: str) -> Dict:
        """Generate chart data with ICT overlays."""
        try:
            key = f"{symbol}_{timeframe}"
            
            if key not in self.chart_data:
                # Generate fresh data if not cached
                self._generate_dashboard_data(symbol, timeframe)
            
            if key not in self.chart_data:
                return {'error': 'No chart data available'}
            
            df = self.chart_data[key]
            dashboard_data = self.current_data.get(key)
            
            # Create candlestick chart
            candlestick = {
                'x': df.index.tolist(),
                'open': df['open'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'close': df['close'].tolist(),
                'type': 'candlestick',
                'name': symbol
            }
            
            # Create ICT overlays
            overlays = []
            
            if dashboard_data:
                # Order Block overlays
                for ob in dashboard_data.order_blocks:
                    color = 'rgba(0, 255, 0, 0.3)' if ob['type'] == 'BULLISH_OB' else 'rgba(255, 0, 0, 0.3)'
                    overlays.append({
                        'type': 'rect',
                        'x0': df.index[0],
                        'x1': df.index[-1],
                        'y0': ob['low'],
                        'y1': ob['high'],
                        'fillcolor': color,
                        'line': {'width': 0},
                        'name': f"Order Block {ob['quality']}"
                    })
                
                # Fair Value Gap overlays
                for fvg in dashboard_data.fair_value_gaps:
                    color = 'rgba(255, 255, 0, 0.2)' if fvg['type'] == 'BULLISH_FVG' else 'rgba(255, 165, 0, 0.2)'
                    overlays.append({
                        'type': 'rect',
                        'x0': df.index[0],
                        'x1': df.index[-1],
                        'y0': fvg['low'],
                        'y1': fvg['high'],
                        'fillcolor': color,
                        'line': {'width': 0},
                        'name': f"FVG {fvg['quality']}"
                    })
                
                # Liquidity level lines
                for liq in dashboard_data.liquidity_zones:
                    color = 'blue' if 'HIGH' in liq['type'] else 'purple'
                    overlays.append({
                        'type': 'line',
                        'x0': df.index[0],
                        'x1': df.index[-1],
                        'y0': liq['level'],
                        'y1': liq['level'],
                        'line': {'color': color, 'width': 2, 'dash': 'dash'},
                        'name': f"Liquidity {liq['type']}"
                    })
                
                # Fibonacci levels
                for fib in dashboard_data.fibonacci_zones:
                    color = 'gold' if fib['level'] == 0.79 else 'silver'
                    overlays.append({
                        'type': 'line',
                        'x0': df.index[0],
                        'x1': df.index[-1],
                        'y0': fib['price'],
                        'y1': fib['price'],
                        'line': {'color': color, 'width': 1},
                        'name': f"Fib {fib['level_name']}"
                    })
            
            return {
                'candlestick': candlestick,
                'overlays': overlays,
                'current_price': df['close'].iloc[-1],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chart data generation failed: {e}")
            return {'error': str(e)}
    
    def _get_active_signals(self, symbol: str) -> List[Dict]:
        """Get active ICT signals for symbol."""
        try:
            # In a real implementation, this would query the signal processor
            # For now, return mock signals
            return [
                {
                    'id': 'signal_1',
                    'symbol': symbol,
                    'type': 'ICT_ORDER_BLOCK_LONG',
                    'direction': 'LONG',
                    'entry_price': 50000.0,
                    'stop_loss': 49500.0,
                    'take_profit': 51000.0,
                    'confluence_score': 0.85,
                    'status': 'ACTIVE',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
        except Exception as e:
            logger.error(f"Active signals retrieval failed: {e}")
            return []
    
    def _generate_market_structure_data(self, df: pd.DataFrame, hierarchy: HierarchyAnalysis) -> Dict:
        """Generate market structure data."""
        try:
            return {
                'trend': hierarchy.trading_bias.value if hierarchy and hierarchy.trading_bias else 'CONSOLIDATION',
                'trend_strength': hierarchy.overall_confidence if hierarchy else 0.0,
                'session': self._get_current_session(),
                'volatility': self._calculate_volatility(df),
                'volume_profile': 'NORMAL',  # Placeholder
                'market_phase': 'CONSOLIDATION'  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Market structure data generation failed: {e}")
            return {}
    
    def _generate_session_info(self) -> Dict:
        """Generate trading session information."""
        current_hour = datetime.now().hour
        
        if 8 <= current_hour <= 16:
            session = 'LONDON'
        elif 13 <= current_hour <= 21:
            session = 'NEW_YORK'
        elif 22 <= current_hour or current_hour <= 7:
            session = 'ASIA'
        else:
            session = 'TRANSITION'
        
        return {
            'current_session': session,
            'session_start': f"{current_hour:02d}:00",
            'session_bias': 'BULLISH',  # Placeholder
            'high_impact_news': False,  # Placeholder
            'session_volume': 'NORMAL'  # Placeholder
        }
    
    def _get_current_session(self) -> str:
        """Get current trading session."""
        current_hour = datetime.now().hour
        
        if 8 <= current_hour <= 16:
            return 'LONDON'
        elif 13 <= current_hour <= 21:
            return 'NEW_YORK'
        else:
            return 'ASIA'
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate recent volatility."""
        if len(df) < 20:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        return returns.std() * np.sqrt(24)  # 24-hour volatility
    
    def _generate_symbol_statistics(self, symbol: str, timeframe: str) -> Dict:
        """Generate statistics for symbol/timeframe."""
        try:
            key = f"{symbol}_{timeframe}"
            dashboard_data = self.current_data.get(key)
            
            if not dashboard_data:
                return {}
            
            return {
                'total_order_blocks': len(dashboard_data.order_blocks),
                'fresh_order_blocks': len([ob for ob in dashboard_data.order_blocks if ob['is_fresh']]),
                'total_fvgs': len(dashboard_data.fair_value_gaps),
                'fresh_fvgs': len([fvg for fvg in dashboard_data.fair_value_gaps if fvg['is_fresh']]),
                'liquidity_zones': len(dashboard_data.liquidity_zones),
                'fibonacci_zones': len(dashboard_data.fibonacci_zones),
                'active_signals': len(dashboard_data.active_signals),
                'last_update': dashboard_data.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Symbol statistics generation failed: {e}")
            return {}
    
    def _generate_statistics(self) -> Dict:
        """Generate overall dashboard statistics."""
        try:
            total_symbols = len(set(data.symbol for data in self.current_data.values()))
            total_signals = sum(len(data.active_signals) for data in self.current_data.values())
            
            return {
                'symbols_tracked': total_symbols,
                'total_active_signals': total_signals,
                'dashboard_uptime': self._get_uptime(),
                'last_update': datetime.now().isoformat(),
                'system_status': 'OPERATIONAL'
            }
            
        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            return {}
    
    def _get_uptime(self) -> str:
        """Get dashboard uptime."""
        # Placeholder - in real implementation, track start time
        return "2h 34m"
    
    def start_real_time_updates(self):
        """Start real-time dashboard updates."""
        def update_loop():
            while self.is_running:
                try:
                    # Update all tracked symbols
                    for symbol in self.dashboard_config['default_symbols']:
                        for timeframe in self.dashboard_config['default_timeframes']:
                            # Generate fresh data
                            dashboard_data = self._generate_dashboard_data(symbol, timeframe)
                            
                            if dashboard_data:
                                # Emit update to connected clients
                                self.socketio.emit('dashboard_update', asdict(dashboard_data))
                    
                    # Wait for next update
                    time.sleep(self.update_interval)
                    
                except Exception as e:
                    logger.error(f"Real-time update error: {e}")
                    time.sleep(5)  # Short pause on error
        
        self.is_running = True
        update_thread = Thread(target=update_loop)
        update_thread.daemon = True
        update_thread.start()
        
        logger.info("Real-time dashboard updates started")
    
    def stop_real_time_updates(self):
        """Stop real-time updates."""
        self.is_running = False
        logger.info("Real-time dashboard updates stopped")
    
    async def run_dashboard(self, host='0.0.0.0', port=5001, debug=False):
        """Run the ICT Trading Dashboard asynchronously."""
        logger.info(f"Starting ICT Trading Dashboard on {host}:{port}")
        
        # Start real-time updates
        self.start_real_time_updates()
        
        # Run the Flask-SocketIO application in a separate thread
        import threading
        
        def run_socketio():
            self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        
        dashboard_thread = threading.Thread(target=run_socketio)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        logger.info(f"ICT Trading Dashboard started at http://{host}:{port}")
        
        # Keep the async method running
        while self.is_running:
            await asyncio.sleep(1)
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the ICT Trading Dashboard."""
        logger.info(f"Starting ICT Trading Dashboard on {host}:{port}")
        
        # Start real-time updates
        self.start_real_time_updates()
        
        # Run the Flask-SocketIO application
        self.socketio.run(self.app, host=host, port=port, debug=debug)


# Dashboard HTML Template (would be in templates/ict_dashboard.html)
DASHBOARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICT Trading Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {
            background-color: #1a1a1a;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
        }
        
        .header {
            background-color: #2d2d2d;
            padding: 15px;
            border-bottom: 2px solid #444;
        }
        
        .header h1 {
            margin: 0;
            color: #00ff88;
            font-size: 24px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 15px;
            padding: 15px;
            height: calc(100vh - 80px);
        }
        
        .chart-container {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 15px;
        }
        
        .sidebar {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 15px;
            overflow-y: auto;
        }
        
        .widget {
            background-color: #3d3d3d;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 15px;
        }
        
        .widget h3 {
            margin: 0 0 10px 0;
            color: #00ff88;
            font-size: 16px;
        }
        
        .signal-item {
            background-color: #4d4d4d;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 8px;
            border-left: 4px solid #00ff88;
        }
        
        .signal-long {
            border-left-color: #00ff88;
        }
        
        .signal-short {
            border-left-color: #ff4444;
        }
        
        .level-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid #555;
        }
        
        .status-online {
            color: #00ff88;
        }
        
        .status-offline {
            color: #ff4444;
        }
        
        .quality-premium {
            color: #ffd700;
        }
        
        .quality-high {
            color: #00ff88;
        }
        
        .quality-medium {
            color: #ffaa00;
        }
        
        .quality-low {
            color: #888;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>ICT Trading Dashboard</h1>
        <div>
            Status: <span id="connection-status" class="status-offline">Offline</span> |
            Last Update: <span id="last-update">Never</span>
        </div>
    </div>
    
    <div class="dashboard-grid">
        <div class="chart-container">
            <div id="price-chart" style="width:100%;height:100%;"></div>
        </div>
        
        <div class="sidebar">
            <!-- Market Structure Widget -->
            <div class="widget">
                <h3>Market Structure</h3>
                <div class="level-item">
                    <span>Trend:</span>
                    <span id="market-trend">-</span>
                </div>
                <div class="level-item">
                    <span>Session:</span>
                    <span id="current-session">-</span>
                </div>
                <div class="level-item">
                    <span>HTF Bias:</span>
                    <span id="htf-bias">-</span>
                </div>
            </div>
            
            <!-- Active Signals Widget -->
            <div class="widget">
                <h3>Active ICT Signals</h3>
                <div id="active-signals">
                    <div class="signal-item signal-long">
                        <div><strong>BTC/USDT LONG</strong></div>
                        <div>Order Block @ $50,000</div>
                        <div>Confluence: 85%</div>
                    </div>
                </div>
            </div>
            
            <!-- Order Blocks Widget -->
            <div class="widget">
                <h3>Order Blocks</h3>
                <div id="order-blocks">
                    <div class="level-item">
                        <span>Bullish OB</span>
                        <span class="quality-premium">$49,800</span>
                    </div>
                </div>
            </div>
            
            <!-- Fair Value Gaps Widget -->
            <div class="widget">
                <h3>Fair Value Gaps</h3>
                <div id="fair-value-gaps">
                    <div class="level-item">
                        <span>Bullish FVG</span>
                        <span class="quality-high">$50,200</span>
                    </div>
                </div>
            </div>
            
            <!-- Liquidity Zones Widget -->
            <div class="widget">
                <h3>Liquidity Zones</h3>
                <div id="liquidity-zones">
                    <div class="level-item">
                        <span>Equal Highs</span>
                        <span>$51,000</span>
                    </div>
                </div>
            </div>
            
            <!-- Fibonacci Levels Widget -->
            <div class="widget">
                <h3>Fibonacci Levels</h3>
                <div id="fibonacci-levels">
                    <div class="level-item">
                        <span>79% Level</span>
                        <span class="quality-premium">$49,900</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Connection status handling
        socket.on('connect', function() {
            document.getElementById('connection-status').textContent = 'Online';
            document.getElementById('connection-status').className = 'status-online';
            
            // Subscribe to BTC/USDT 5m by default
            socket.emit('subscribe', {symbol: 'BTC/USDT', timeframe: '5m'});
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').textContent = 'Offline';
            document.getElementById('connection-status').className = 'status-offline';
        });
        
        // Dashboard data updates
        socket.on('dashboard_update', function(data) {
            updateDashboard(data);
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        });
        
        function updateDashboard(data) {
            // Update market structure
            if (data.market_structure) {
                document.getElementById('market-trend').textContent = data.market_structure.trend || '-';
            }
            
            if (data.session_info) {
                document.getElementById('current-session').textContent = data.session_info.current_session || '-';
            }
            
            if (data.hierarchy_analysis) {
                document.getElementById('htf-bias').textContent = data.hierarchy_analysis.trading_bias || '-';
            }
            
            // Update Order Blocks
            updateOrderBlocks(data.order_blocks || []);
            
            // Update Fair Value Gaps
            updateFairValueGaps(data.fair_value_gaps || []);
            
            // Update Liquidity Zones
            updateLiquidityZones(data.liquidity_zones || []);
            
            // Update Fibonacci Levels
            updateFibonacciLevels(data.fibonacci_zones || []);
            
            // Update Active Signals
            updateActiveSignals(data.active_signals || []);
            
            // Update chart if we have chart data
            if (data.symbol && data.timeframe) {
                fetchAndUpdateChart(data.symbol, data.timeframe);
            }
        }
        
        function updateOrderBlocks(orderBlocks) {
            const container = document.getElementById('order-blocks');
            container.innerHTML = '';
            
            orderBlocks.slice(0, 5).forEach(ob => {
                const item = document.createElement('div');
                item.className = 'level-item';
                item.innerHTML = `
                    <span>${ob.type} (${ob.quality})</span>
                    <span class="quality-${ob.quality.toLowerCase()}">$${ob.mid.toFixed(0)}</span>
                `;
                container.appendChild(item);
            });
        }
        
        function updateFairValueGaps(fvgs) {
            const container = document.getElementById('fair-value-gaps');
            container.innerHTML = '';
            
            fvgs.slice(0, 5).forEach(fvg => {
                const item = document.createElement('div');
                item.className = 'level-item';
                item.innerHTML = `
                    <span>${fvg.type} (${fvg.quality})</span>
                    <span class="quality-${fvg.quality.toLowerCase()}">$${fvg.mid.toFixed(0)}</span>
                `;
                container.appendChild(item);
            });
        }
        
        function updateLiquidityZones(zones) {
            const container = document.getElementById('liquidity-zones');
            container.innerHTML = '';
            
            zones.slice(0, 5).forEach(zone => {
                const item = document.createElement('div');
                item.className = 'level-item';
                item.innerHTML = `
                    <span>${zone.type}</span>
                    <span>$${zone.level.toFixed(0)}</span>
                `;
                container.appendChild(item);
            });
        }
        
        function updateFibonacciLevels(levels) {
            const container = document.getElementById('fibonacci-levels');
            container.innerHTML = '';
            
            levels.slice(0, 5).forEach(fib => {
                const item = document.createElement('div');
                item.className = 'level-item';
                item.innerHTML = `
                    <span>${fib.level_name} (${fib.quality})</span>
                    <span class="quality-${fib.quality.toLowerCase()}">$${fib.price.toFixed(0)}</span>
                `;
                container.appendChild(item);
            });
        }
        
        function updateActiveSignals(signals) {
            const container = document.getElementById('active-signals');
            container.innerHTML = '';
            
            if (signals.length === 0) {
                container.innerHTML = '<div style="color: #888;">No active signals</div>';
                return;
            }
            
            signals.forEach(signal => {
                const item = document.createElement('div');
                item.className = `signal-item signal-${signal.direction.toLowerCase()}`;
                item.innerHTML = `
                    <div><strong>${signal.symbol} ${signal.direction}</strong></div>
                    <div>${signal.type}</div>
                    <div>Entry: $${signal.entry_price.toFixed(0)}</div>
                    <div>Confluence: ${(signal.confluence_score * 100).toFixed(0)}%</div>
                `;
                container.appendChild(item);
            });
        }
        
        function fetchAndUpdateChart(symbol, timeframe) {
            fetch(`/api/chart-data/${symbol}/${timeframe}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Chart data error:', data.error);
                        return;
                    }
                    
                    updateChart(data);
                })
                .catch(error => {
                    console.error('Chart fetch error:', error);
                });
        }
        
        function updateChart(chartData) {
            const traces = [chartData.candlestick];
            
            const layout = {
                title: `${chartData.candlestick.name} - ICT Analysis`,
                xaxis: {
                    type: 'date',
                    gridcolor: '#444'
                },
                yaxis: {
                    title: 'Price',
                    gridcolor: '#444'
                },
                plot_bgcolor: '#1a1a1a',
                paper_bgcolor: '#2d2d2d',
                font: {
                    color: '#ffffff'
                },
                shapes: chartData.overlays || []
            };
            
            Plotly.newPlot('price-chart', traces, layout, {responsive: true});
        }
        
        // Initialize chart with empty data
        updateChart({
            candlestick: {
                x: [],
                open: [],
                high: [],
                low: [],
                close: [],
                type: 'candlestick',
                name: 'Loading...'
            },
            overlays: []
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create templates directory and file
    import os
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/ict_dashboard.html', 'w') as f:
        f.write(DASHBOARD_HTML_TEMPLATE)
    
    # Initialize and run dashboard
    dashboard = ICTTradingDashboard()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                   ICT TRADING DASHBOARD                         ║
╠══════════════════════════════════════════════════════════════════╣
║  🌐 Dashboard URL:    http://localhost:5000                     ║
║  📊 Real-time ICT Analysis with institutional methodology       ║
║  📈 Order Blocks, FVGs, Liquidity Zones, Fibonacci Levels      ║
║  🎯 Professional trading interface for ICT signals             ║
║  📱 Mobile responsive design                                    ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    try:
        dashboard.run(debug=True)
    except KeyboardInterrupt:
        print("\n👋 ICT Trading Dashboard stopped")
        dashboard.stop_real_time_updates()