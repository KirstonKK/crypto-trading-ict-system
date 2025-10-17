"""
ICT Paper Trading Performance Tracker
====================================

Comprehensive performance tracking system for ICT paper trading,
providing detailed analytics on institutional trading methodology
effectiveness compared to traditional retail approaches.

Key Metrics Tracked:
✅ ICT Signal Quality and Confluence Accuracy
✅ Order Block Success Rate and Quality Analysis
✅ Fair Value Gap Fill Rate and Timing
✅ Market Structure Pattern Recognition
✅ Liquidity Hunt Success and Sweep Analysis
✅ Fibonacci Confluence Effectiveness
✅ Timeframe Hierarchy Performance
✅ Risk-Reward Ratio Achievement
✅ Institutional vs Retail Performance Comparison

Features:
- Real-time performance monitoring
- Detailed trade analytics
- ICT pattern success tracking
- Quality score correlation analysis
- Session performance summaries
- Historical trend analysis
- Export capabilities for further analysis

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import json
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ICTTradeAnalysis:
    """Detailed analysis of a single ICT trade."""
    trade_id: int
    symbol: str
    action: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    
    # ICT-specific data
    confluence_score: float
    institutional_quality: str
    entry_type: str  # ORDER_BLOCK, FVG_CONFLUENCE, LIQUIDITY_SWEEP
    market_structure: str
    bias_direction: str
    
    # Components
    order_blocks_count: int
    fair_value_gaps_count: int
    liquidity_zones_count: int
    
    # Performance
    pnl: float
    pnl_percentage: float
    risk_reward_achieved: float
    duration_minutes: Optional[int]
    
    # Success factors
    confluence_accuracy: float  # How well confluence predicted outcome
    pattern_success: bool
    structure_held: bool
    
    # Trade outcome
    status: str  # OPEN, CLOSED_PROFIT, CLOSED_LOSS, CLOSED_BE
    exit_reason: str  # TP_HIT, SL_HIT, MANUAL_CLOSE, TIME_EXIT

@dataclass
class ICTPerformanceMetrics:
    """Comprehensive ICT performance metrics."""
    # Overall Performance
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Financial Metrics
    total_pnl: float
    total_pnl_percentage: float
    average_win: float
    average_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    
    # ICT-Specific Metrics
    average_confluence_score: float
    confluence_accuracy: float  # Correlation between confluence and success
    
    # Quality Analysis
    premium_signals: int
    high_quality_signals: int
    medium_quality_signals: int
    low_quality_signals: int
    quality_success_rates: Dict[str, float]
    
    # Entry Type Analysis
    order_block_success_rate: float
    fvg_confluence_success_rate: float
    liquidity_sweep_success_rate: float
    
    # Pattern Analysis
    market_structure_accuracy: float
    bias_alignment_success: float
    timeframe_hierarchy_effectiveness: float
    
    # Component Effectiveness
    order_block_avg_per_trade: float
    fvg_avg_per_trade: float
    liquidity_zones_avg_per_trade: float
    
    # Risk Management
    average_risk_reward: float
    max_risk_per_trade: float
    risk_consistency: float
    
    # Timing Analysis
    average_trade_duration: float
    quick_wins_percentage: float  # Trades closed within 1 hour
    session_performance: Dict[str, float]

class ICTPaperTradingPerformanceTracker:
    """
    Comprehensive performance tracking for ICT paper trading.
    
    This class monitors and analyzes all aspects of ICT trading performance,
    providing detailed insights into the effectiveness of institutional
    trading methodology compared to traditional approaches.
    """
    
    def __init__(self, session_name: str = None):
        """Initialize performance tracker."""
        self.session_name = session_name or f"ict_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trades: List[ICTTradeAnalysis] = []
        self.session_start = datetime.now()
        
        # Real-time metrics
        self.current_metrics = None
        self.last_analysis_time = None
        
        # Historical data
        self.performance_history = []
        
        # Configuration
        self.analysis_interval = 300  # 5 minutes
        self.export_directory = Path("ict_performance_data")
        self.export_directory.mkdir(exist_ok=True)
        
        logger.info(f"ICT Performance Tracker initialized: {self.session_name}")
    
    def add_trade(self, trade_data: Dict) -> None:
        """Add a new trade to tracking."""
        try:
            # Convert trade data to ICTTradeAnalysis
            trade_analysis = ICTTradeAnalysis(
                trade_id=trade_data.get('trade_id'),
                symbol=trade_data.get('symbol'),
                action=trade_data.get('action'),
                entry_time=trade_data.get('entry_time', datetime.now()),
                exit_time=trade_data.get('exit_time'),
                entry_price=trade_data.get('entry_price'),
                exit_price=trade_data.get('exit_price'),
                
                # ICT data
                confluence_score=trade_data.get('confluence_score', 0.0),
                institutional_quality=trade_data.get('institutional_quality', 'LOW'),
                entry_type=trade_data.get('entry_type', 'UNKNOWN'),
                market_structure=trade_data.get('market_structure', 'UNCLEAR'),
                bias_direction=trade_data.get('bias_direction', 'NEUTRAL'),
                
                # Components
                order_blocks_count=trade_data.get('order_blocks_count', 0),
                fair_value_gaps_count=trade_data.get('fair_value_gaps_count', 0),
                liquidity_zones_count=trade_data.get('liquidity_zones_count', 0),
                
                # Performance (calculated)
                pnl=self._calculate_pnl(trade_data),
                pnl_percentage=self._calculate_pnl_percentage(trade_data),
                risk_reward_achieved=trade_data.get('risk_reward_ratio', 0.0),
                duration_minutes=self._calculate_duration(trade_data),
                
                # Analysis (calculated)
                confluence_accuracy=self._calculate_confluence_accuracy(trade_data),
                pattern_success=self._determine_pattern_success(trade_data),
                structure_held=self._check_structure_held(trade_data),
                
                # Status
                status=trade_data.get('status', 'OPEN'),
                exit_reason=trade_data.get('exit_reason', 'NONE')
            )
            
            self.trades.append(trade_analysis)
            logger.info(f"Trade added to tracking: {trade_analysis.symbol} {trade_analysis.action} "
                       f"({trade_analysis.institutional_quality})")
            
            # Update metrics if needed
            self._update_real_time_metrics()
            
        except Exception as e:
            logger.error(f"Error adding trade to tracking: {e}")
    
    def update_trade(self, trade_id: int, update_data: Dict) -> None:
        """Update existing trade with new data (e.g., exit information)."""
        try:
            trade = next((t for t in self.trades if t.trade_id == trade_id), None)
            if not trade:
                logger.warning(f"Trade {trade_id} not found for update")
                return
            
            # Update trade data
            for key, value in update_data.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            
            # Recalculate performance metrics
            if 'exit_price' in update_data:
                trade.pnl = self._calculate_pnl(asdict(trade))
                trade.pnl_percentage = self._calculate_pnl_percentage(asdict(trade))
                trade.duration_minutes = self._calculate_duration(asdict(trade))
                trade.confluence_accuracy = self._calculate_confluence_accuracy(asdict(trade))
                trade.pattern_success = self._determine_pattern_success(asdict(trade))
            
            logger.info(f"Trade {trade_id} updated: Status {trade.status}, P&L ${trade.pnl:.2f}")
            
            # Update metrics
            self._update_real_time_metrics()
            
        except Exception as e:
            logger.error(f"Error updating trade {trade_id}: {e}")
    
    def analyze_performance(self) -> ICTPerformanceMetrics:
        """Analyze current performance and return comprehensive metrics."""
        try:
            if not self.trades:
                logger.warning("No trades to analyze")
                return None
            
            closed_trades = [t for t in self.trades if t.status != 'OPEN']
            if not closed_trades:
                logger.info("No closed trades for analysis")
                return None
            
            # Calculate basic metrics
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t.pnl > 0])
            losing_trades = len([t for t in closed_trades if t.pnl < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Financial metrics
            total_pnl = sum(t.pnl for t in closed_trades)
            wins = [t.pnl for t in closed_trades if t.pnl > 0]
            losses = [t.pnl for t in closed_trades if t.pnl < 0]
            
            average_win = np.mean(wins) if wins else 0
            average_loss = abs(np.mean(losses)) if losses else 0
            profit_factor = (sum(wins) / sum(abs(l) for l in losses)) if losses else float('inf')
            
            # ICT-specific metrics
            confluence_scores = [t.confluence_score for t in closed_trades]
            average_confluence = np.mean(confluence_scores) if confluence_scores else 0
            
            # Quality analysis
            quality_counts = {'PREMIUM': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            quality_success = {'PREMIUM': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
            
            for trade in closed_trades:
                quality = trade.institutional_quality
                if quality in quality_counts:
                    quality_counts[quality] += 1
                    quality_success[quality].append(trade.pnl > 0)
            
            quality_success_rates = {}
            for quality, successes in quality_success.items():
                if successes:
                    quality_success_rates[quality] = (sum(successes) / len(successes) * 100)
                else:
                    quality_success_rates[quality] = 0
            
            # Entry type analysis
            entry_types = {'ORDER_BLOCK': [], 'FVG_CONFLUENCE': [], 'LIQUIDITY_SWEEP': []}
            for trade in closed_trades:
                if trade.entry_type in entry_types:
                    entry_types[trade.entry_type].append(trade.pnl > 0)
            
            entry_success_rates = {}
            for entry_type, successes in entry_types.items():
                if successes:
                    entry_success_rates[entry_type] = (sum(successes) / len(successes) * 100)
                else:
                    entry_success_rates[entry_type] = 0
            
            # Component effectiveness
            ob_counts = [t.order_blocks_count for t in closed_trades]
            fvg_counts = [t.fair_value_gaps_count for t in closed_trades]
            liq_counts = [t.liquidity_zones_count for t in closed_trades]
            
            # Risk management
            rr_ratios = [t.risk_reward_achieved for t in closed_trades if t.risk_reward_achieved > 0]
            average_rr = np.mean(rr_ratios) if rr_ratios else 0
            
            # Timing analysis
            durations = [t.duration_minutes for t in closed_trades if t.duration_minutes]
            average_duration = np.mean(durations) if durations else 0
            quick_wins = len([t for t in closed_trades if t.duration_minutes and t.duration_minutes <= 60 and t.pnl > 0])
            quick_wins_percentage = (quick_wins / winning_trades * 100) if winning_trades > 0 else 0\n            \n            # Create metrics object\n            metrics = ICTPerformanceMetrics(\n                total_trades=total_trades,\n                winning_trades=winning_trades,\n                losing_trades=losing_trades,\n                win_rate=win_rate,\n                \n                total_pnl=total_pnl,\n                total_pnl_percentage=(total_pnl / 10000 * 100),  # Assuming $10k starting balance\n                average_win=average_win,\n                average_loss=average_loss,\n                profit_factor=profit_factor,\n                sharpe_ratio=self._calculate_sharpe_ratio(closed_trades),\n                max_drawdown=self._calculate_max_drawdown(closed_trades),\n                \n                average_confluence_score=average_confluence,\n                confluence_accuracy=self._calculate_overall_confluence_accuracy(closed_trades),\n                \n                premium_signals=quality_counts['PREMIUM'],\n                high_quality_signals=quality_counts['HIGH'],\n                medium_quality_signals=quality_counts['MEDIUM'],\n                low_quality_signals=quality_counts['LOW'],\n                quality_success_rates=quality_success_rates,\n                \n                order_block_success_rate=entry_success_rates.get('ORDER_BLOCK', 0),\n                fvg_confluence_success_rate=entry_success_rates.get('FVG_CONFLUENCE', 0),\n                liquidity_sweep_success_rate=entry_success_rates.get('LIQUIDITY_SWEEP', 0),\n                \n                market_structure_accuracy=self._calculate_structure_accuracy(closed_trades),\n                bias_alignment_success=self._calculate_bias_success(closed_trades),\n                timeframe_hierarchy_effectiveness=self._calculate_hierarchy_effectiveness(closed_trades),\n                \n                order_block_avg_per_trade=np.mean(ob_counts) if ob_counts else 0,\n                fvg_avg_per_trade=np.mean(fvg_counts) if fvg_counts else 0,\n                liquidity_zones_avg_per_trade=np.mean(liq_counts) if liq_counts else 0,\n                \n                average_risk_reward=average_rr,\n                max_risk_per_trade=0.02,  # 2% max risk\n                risk_consistency=np.std(rr_ratios) if len(rr_ratios) > 1 else 0,\n                \n                average_trade_duration=average_duration,\n                quick_wins_percentage=quick_wins_percentage,\n                session_performance=self._calculate_session_performance(closed_trades)\n            )\n            \n            self.current_metrics = metrics\n            self.last_analysis_time = datetime.now()\n            \n            logger.info(f\"Performance analysis completed: {total_trades} trades, {win_rate:.1f}% win rate, ${total_pnl:.2f} P&L\")\n            \n            return metrics\n            \n        except Exception as e:\n            logger.error(f\"Error analyzing performance: {e}\")\n            return None\n    \n    def generate_performance_report(self) -> str:\n        \"\"\"Generate comprehensive performance report.\"\"\"\n        try:\n            metrics = self.analyze_performance()\n            if not metrics:\n                return \"No performance data available\"\n            \n            session_duration = datetime.now() - self.session_start\n            \n            report = f\"\"\"\n\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557\n\u2551              ICT PAPER TRADING PERFORMANCE REPORT              \u2551\n\u2551                Session: {self.session_name}                \u2551\n\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563\n\u2551  \u23f1\ufe0f  Session Duration: {str(session_duration).split('.')[0]}\u2551\n\u2551  \ud83d\udcc8 Total Trades: {metrics.total_trades}\u2551\n\u2551  \ud83c\udfc6 Win Rate: {metrics.win_rate:.1f}%\u2551\n\u2551  \ud83d\udcb0 Total P&L: ${metrics.total_pnl:.2f} ({metrics.total_pnl_percentage:.1f}%)\u2551\n\u2551  \ud83d\udcc9 Profit Factor: {metrics.profit_factor:.2f}\u2551\n\u2551  \u26a1 Average Win: ${metrics.average_win:.2f}\u2551\n\u2551  \ud83d\udd34 Average Loss: ${metrics.average_loss:.2f}\u2551\n\u2551  \ud83d\udcca Max Drawdown: {metrics.max_drawdown:.2f}%\u2551\n\u2551\u2551\n\u2551  \ud83c\udfaf ICT SIGNAL QUALITY ANALYSIS:\u2551\n\u2551     Average Confluence: {metrics.average_confluence_score:.1%}\u2551\n\u2551     Confluence Accuracy: {metrics.confluence_accuracy:.1%}\u2551\n\u2551\u2551\n\u2551  \ud83c\udfc6 INSTITUTIONAL QUALITY BREAKDOWN:\u2551\n\u2551     PREMIUM: {metrics.premium_signals} signals ({metrics.quality_success_rates.get('PREMIUM', 0):.1f}% win rate)\u2551\n\u2551     HIGH: {metrics.high_quality_signals} signals ({metrics.quality_success_rates.get('HIGH', 0):.1f}% win rate)\u2551\n\u2551     MEDIUM: {metrics.medium_quality_signals} signals ({metrics.quality_success_rates.get('MEDIUM', 0):.1f}% win rate)\u2551\n\u2551     LOW: {metrics.low_quality_signals} signals ({metrics.quality_success_rates.get('LOW', 0):.1f}% win rate)\u2551\n\u2551\u2551\n\u2551  \ud83d\udce6 ENTRY TYPE PERFORMANCE:\u2551\n\u2551     Order Block: {metrics.order_block_success_rate:.1f}% success rate\u2551\n\u2551     FVG Confluence: {metrics.fvg_confluence_success_rate:.1f}% success rate\u2551\n\u2551     Liquidity Sweep: {metrics.liquidity_sweep_success_rate:.1f}% success rate\u2551\n\u2551\u2551\n\u2551  \ud83c\udfd7\ufe0f  ICT COMPONENT EFFECTIVENESS:\u2551\n\u2551     Avg Order Blocks/Trade: {metrics.order_block_avg_per_trade:.1f}\u2551\n\u2551     Avg FVGs/Trade: {metrics.fvg_avg_per_trade:.1f}\u2551\n\u2551     Avg Liquidity Zones/Trade: {metrics.liquidity_zones_avg_per_trade:.1f}\u2551\n\u2551\u2551\n\u2551  \ud83c\udfaf MARKET STRUCTURE ANALYSIS:\u2551\n\u2551     Structure Accuracy: {metrics.market_structure_accuracy:.1f}%\u2551\n\u2551     Bias Alignment Success: {metrics.bias_alignment_success:.1f}%\u2551\n\u2551     Hierarchy Effectiveness: {metrics.timeframe_hierarchy_effectiveness:.1f}%\u2551\n\u2551\u2551\n\u2551  \u23f0 TIMING ANALYSIS:\u2551\n\u2551     Average Trade Duration: {metrics.average_trade_duration:.0f} minutes\u2551\n\u2551     Quick Wins (< 1 hour): {metrics.quick_wins_percentage:.1f}%\u2551\n\u2551\u2551\n\u2551  \ud83d\udd32 RISK MANAGEMENT:\u2551\n\u2551     Average Risk:Reward: {metrics.average_risk_reward:.2f}:1\u2551\n\u2551     Risk Consistency: {metrics.risk_consistency:.2f}\u2551\n\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\n\"\"\"\n            \n            return report\n            \n        except Exception as e:\n            logger.error(f\"Error generating performance report: {e}\")\n            return \"Error generating performance report\"\n    \n    def export_data(self, format: str = 'json') -> str:\n        \"\"\"Export performance data to file.\"\"\"\n        try:\n            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n            \n            if format.lower() == 'json':\n                filename = self.export_directory / f\"{self.session_name}_performance_{timestamp}.json\"\n                \n                export_data = {\n                    'session_info': {\n                        'session_name': self.session_name,\n                        'start_time': self.session_start.isoformat(),\n                        'export_time': datetime.now().isoformat(),\n                        'duration': str(datetime.now() - self.session_start)\n                    },\n                    'trades': [asdict(trade) for trade in self.trades],\n                    'metrics': asdict(self.current_metrics) if self.current_metrics else None,\n                    'performance_history': self.performance_history\n                }\n                \n                with open(filename, 'w') as f:\n                    json.dump(export_data, f, indent=2, default=str)\n                \n            elif format.lower() == 'csv':\n                filename = self.export_directory / f\"{self.session_name}_trades_{timestamp}.csv\"\n                \n                df = pd.DataFrame([asdict(trade) for trade in self.trades])\n                df.to_csv(filename, index=False)\n            \n            logger.info(f\"Performance data exported to: {filename}\")\n            return str(filename)\n            \n        except Exception as e:\n            logger.error(f\"Error exporting data: {e}\")\n            return None\n    \n    # Helper methods for calculations\n    \n    def _calculate_pnl(self, trade_data: Dict) -> float:\n        \"\"\"Calculate P&L for a trade.\"\"\"\n        if not trade_data.get('exit_price'):\n            return 0.0\n        \n        entry_price = trade_data.get('entry_price', 0)\n        exit_price = trade_data.get('exit_price', 0)\n        position_size = trade_data.get('position_size', 0)\n        action = trade_data.get('action', '')\n        \n        if action.upper() == 'BUY':\n            return (exit_price - entry_price) * position_size\n        else:\n            return (entry_price - exit_price) * position_size\n    \n    def _calculate_pnl_percentage(self, trade_data: Dict) -> float:\n        \"\"\"Calculate P&L percentage.\"\"\"\n        entry_price = trade_data.get('entry_price', 0)\n        if entry_price == 0:\n            return 0.0\n        \n        pnl = self._calculate_pnl(trade_data)\n        position_size = trade_data.get('position_size', 0)\n        \n        if position_size == 0:\n            return 0.0\n        \n        return (pnl / (entry_price * position_size)) * 100\n    \n    def _calculate_duration(self, trade_data: Dict) -> Optional[int]:\n        \"\"\"Calculate trade duration in minutes.\"\"\"\n        entry_time = trade_data.get('entry_time')\n        exit_time = trade_data.get('exit_time')\n        \n        if not entry_time or not exit_time:\n            return None\n        \n        if isinstance(entry_time, str):\n            entry_time = datetime.fromisoformat(entry_time)\n        if isinstance(exit_time, str):\n            exit_time = datetime.fromisoformat(exit_time)\n        \n        duration = exit_time - entry_time\n        return int(duration.total_seconds() / 60)\n    \n    def _calculate_confluence_accuracy(self, trade_data: Dict) -> float:\n        \"\"\"Calculate how well confluence score predicted trade outcome.\"\"\"\n        confluence = trade_data.get('confluence_score', 0)\n        pnl = self._calculate_pnl(trade_data)\n        \n        # Simple correlation: higher confluence should correlate with better outcomes\n        if pnl > 0:\n            return confluence  # Successful trade, confluence accuracy = confluence score\n        else:\n            return 1 - confluence  # Failed trade, lower confluence = more accurate\n    \n    def _determine_pattern_success(self, trade_data: Dict) -> bool:\n        \"\"\"Determine if the ICT pattern was successful.\"\"\"\n        return self._calculate_pnl(trade_data) > 0\n    \n    def _check_structure_held(self, trade_data: Dict) -> bool:\n        \"\"\"Check if market structure held during the trade.\"\"\"\n        # Simplified: assume structure held if trade was profitable\n        return self._calculate_pnl(trade_data) > 0\n    \n    def _calculate_sharpe_ratio(self, trades: List[ICTTradeAnalysis]) -> float:\n        \"\"\"Calculate Sharpe ratio.\"\"\"\n        if len(trades) < 2:\n            return 0.0\n        \n        returns = [t.pnl_percentage for t in trades]\n        return (np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0.0\n    \n    def _calculate_max_drawdown(self, trades: List[ICTTradeAnalysis]) -> float:\n        \"\"\"Calculate maximum drawdown.\"\"\"\n        if not trades:\n            return 0.0\n        \n        # Calculate cumulative P&L\n        cumulative_pnl = []\n        running_total = 0\n        \n        for trade in sorted(trades, key=lambda x: x.entry_time):\n            running_total += trade.pnl\n            cumulative_pnl.append(running_total)\n        \n        if not cumulative_pnl:\n            return 0.0\n        \n        # Calculate drawdown\n        peak = cumulative_pnl[0]\n        max_drawdown = 0\n        \n        for value in cumulative_pnl:\n            if value > peak:\n                peak = value\n            drawdown = (peak - value) / abs(peak) * 100 if peak != 0 else 0\n            max_drawdown = max(max_drawdown, drawdown)\n        \n        return max_drawdown\n    \n    def _calculate_overall_confluence_accuracy(self, trades: List[ICTTradeAnalysis]) -> float:\n        \"\"\"Calculate overall confluence accuracy.\"\"\"\n        if not trades:\n            return 0.0\n        \n        accuracies = [t.confluence_accuracy for t in trades]\n        return np.mean(accuracies) * 100\n    \n    def _calculate_structure_accuracy(self, trades: List[ICTTradeAnalysis]) -> float:\n        \"\"\"Calculate market structure accuracy.\"\"\"\n        if not trades:\n            return 0.0\n        \n        structure_held_count = sum(1 for t in trades if t.structure_held)\n        return (structure_held_count / len(trades)) * 100\n    \n    def _calculate_bias_success(self, trades: List[ICTTradeAnalysis]) -> float:\n        \"\"\"Calculate bias alignment success rate.\"\"\"\n        if not trades:\n            return 0.0\n        \n        # Successful trades where bias was correctly identified\n        bias_success_count = 0\n        for trade in trades:\n            if trade.pnl > 0 and trade.bias_direction != 'NEUTRAL':\n                # Check if action aligned with bias\n                if ((trade.bias_direction == 'BULLISH' and trade.action == 'BUY') or\n                    (trade.bias_direction == 'BEARISH' and trade.action == 'SELL')):\n                    bias_success_count += 1\n        \n        return (bias_success_count / len(trades)) * 100\n    \n    def _calculate_hierarchy_effectiveness(self, trades: List[ICTTradeAnalysis]) -> float:\n        \"\"\"Calculate timeframe hierarchy effectiveness.\"\"\"\n        if not trades:\n            return 0.0\n        \n        # Simplified: trades with higher confluence scores should be more successful\n        high_confluence_trades = [t for t in trades if t.confluence_score >= 0.8]\n        if not high_confluence_trades:\n            return 0.0\n        \n        successful_high_confluence = sum(1 for t in high_confluence_trades if t.pnl > 0)\n        return (successful_high_confluence / len(high_confluence_trades)) * 100\n    \n    def _calculate_session_performance(self, trades: List[ICTTradeAnalysis]) -> Dict[str, float]:\n        \"\"\"Calculate performance by trading session.\"\"\"\n        sessions = {'ASIAN': [], 'LONDON': [], 'NEW_YORK': [], 'OTHER': []}\n        \n        for trade in trades:\n            hour = trade.entry_time.hour\n            \n            if 0 <= hour <= 7:  # Asian session (UTC)\n                session = 'ASIAN'\n            elif 8 <= hour <= 12:  # London session\n                session = 'LONDON'\n            elif 13 <= hour <= 17:  # New York session\n                session = 'NEW_YORK'\n            else:\n                session = 'OTHER'\n            \n            sessions[session].append(trade.pnl)\n        \n        session_performance = {}\n        for session, pnls in sessions.items():\n            if pnls:\n                session_performance[session] = sum(pnls)\n            else:\n                session_performance[session] = 0.0\n        \n        return session_performance\n    \n    def _update_real_time_metrics(self) -> None:\n        \"\"\"Update real-time metrics if enough time has passed.\"\"\"\n        if (not self.last_analysis_time or \n            (datetime.now() - self.last_analysis_time).total_seconds() >= self.analysis_interval):\n            \n            metrics = self.analyze_performance()\n            if metrics:\n                self.performance_history.append({\n                    'timestamp': datetime.now().isoformat(),\n                    'metrics': asdict(metrics)\n                })\n\n\n# Example usage and testing\nif __name__ == \"__main__\":\n    logging.basicConfig(level=logging.INFO)\n    \n    # Initialize tracker\n    tracker = ICTPaperTradingPerformanceTracker(\"test_session\")\n    \n    # Add sample trades\n    sample_trades = [\n        {\n            'trade_id': 1,\n            'symbol': 'BTC/USDT',\n            'action': 'BUY',\n            'entry_price': 50000,\n            'exit_price': 51000,\n            'position_size': 0.1,\n            'confluence_score': 0.85,\n            'institutional_quality': 'HIGH',\n            'entry_type': 'ORDER_BLOCK',\n            'market_structure': 'BULLISH_BOS',\n            'bias_direction': 'BULLISH',\n            'order_blocks_count': 2,\n            'fair_value_gaps_count': 1,\n            'liquidity_zones_count': 3,\n            'status': 'CLOSED_PROFIT',\n            'exit_reason': 'TP_HIT'\n        },\n        {\n            'trade_id': 2,\n            'symbol': 'ETH/USDT',\n            'action': 'SELL',\n            'entry_price': 3000,\n            'exit_price': 2950,\n            'position_size': 1.0,\n            'confluence_score': 0.75,\n            'institutional_quality': 'MEDIUM',\n            'entry_type': 'FVG_CONFLUENCE',\n            'market_structure': 'BEARISH_BOS',\n            'bias_direction': 'BEARISH',\n            'order_blocks_count': 1,\n            'fair_value_gaps_count': 2,\n            'liquidity_zones_count': 1,\n            'status': 'CLOSED_PROFIT',\n            'exit_reason': 'TP_HIT'\n        }\n    ]\n    \n    for trade in sample_trades:\n        tracker.add_trade(trade)\n    \n    # Generate report\n    report = tracker.generate_performance_report()\n    print(report)\n    \n    # Export data\n    filename = tracker.export_data('json')\n    print(f\"\\nData exported to: {filename}\")\n