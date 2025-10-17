"""
Simplified ICT Performance Tracker
=================================

Basic performance tracking for ICT paper trading validation.

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SimpleICTMetrics:
    """Simple ICT performance metrics."""
    total_signals: int = 0
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_confluence: float = 0.0
    premium_signals: int = 0
    high_signals: int = 0
    medium_signals: int = 0
    low_signals: int = 0

class SimpleICTPerformanceTracker:
    """Simple performance tracker for ICT paper trading."""
    
    def __init__(self):
        self.trades = []
        self.signals = []
        self.session_start = datetime.now()
        
    def track_signal(self, signal_data: Dict):
        """Track ICT signal received."""
        self.signals.append({
            'timestamp': datetime.now(),
            'symbol': signal_data.get('symbol'),
            'confluence': signal_data.get('confluence_score', 0),
            'quality': signal_data.get('institutional_quality', 'LOW'),
            'entry_type': signal_data.get('entry_type', 'UNKNOWN')
        })
        
    def track_trade(self, trade_data: Dict):
        """Track executed trade."""
        self.trades.append({
            'timestamp': datetime.now(),
            'symbol': trade_data.get('symbol'),
            'action': trade_data.get('action'),
            'pnl': trade_data.get('pnl', 0),
            'confluence': trade_data.get('confluence_score', 0),
            'quality': trade_data.get('institutional_quality', 'LOW')
        })
        
    def get_metrics(self) -> SimpleICTMetrics:
        """Get current performance metrics."""
        total_signals = len(self.signals)
        total_trades = len(self.trades)
        
        if not self.trades:
            return SimpleICTMetrics(total_signals=total_signals)
            
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        total_pnl = sum(t['pnl'] for t in self.trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Quality breakdown
        quality_counts = {'PREMIUM': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        confluences = []
        
        for signal in self.signals:
            quality = signal.get('quality', 'LOW')
            if quality in quality_counts:
                quality_counts[quality] += 1
            confluences.append(signal.get('confluence', 0))
            
        avg_confluence = sum(confluences) / len(confluences) if confluences else 0
        
        return SimpleICTMetrics(
            total_signals=total_signals,
            total_trades=total_trades,
            winning_trades=winning_trades,
            total_pnl=total_pnl,
            win_rate=win_rate,
            avg_confluence=avg_confluence,
            premium_signals=quality_counts['PREMIUM'],
            high_signals=quality_counts['HIGH'],
            medium_signals=quality_counts['MEDIUM'],
            low_signals=quality_counts['LOW']
        )
        
    def generate_report(self) -> str:
        """Generate simple performance report."""
        metrics = self.get_metrics()
        duration = datetime.now() - self.session_start
        
        return f"""
ICT Paper Trading Performance Report
===================================

Session Duration: {str(duration).split('.')[0]}
Total ICT Signals: {metrics.total_signals}
Trades Executed: {metrics.total_trades}
Win Rate: {metrics.win_rate:.1f}%
Total P&L: ${metrics.total_pnl:.2f}
Average Confluence: {metrics.avg_confluence:.1%}

Signal Quality Breakdown:
- PREMIUM: {metrics.premium_signals}
- HIGH: {metrics.high_signals}  
- MEDIUM: {metrics.medium_signals}
- LOW: {metrics.low_signals}

Signal → Trade Rate: {(metrics.total_trades/max(1, metrics.total_signals)*100):.1f}%
"""
        
    def export_data(self) -> str:
        """Export performance data to JSON file."""
        filename = f"ict_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'session_start': self.session_start.isoformat(),
            'session_end': datetime.now().isoformat(),
            'signals': self.signals,
            'trades': self.trades,
            'metrics': self.get_metrics().__dict__
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
        return filename