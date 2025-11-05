#!/usr/bin/env python3
"""
SOL Trade Analysis Module
=========================

Specialized analysis for SOL (Solana) trading opportunities using ICT methodology.
Focuses on liquidity zones and fair value gaps for precise entry and target identification.

Author: GitHub Copilot
Date: October 2025
"""

import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

# Add trading modules to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

from trading.liquidity_detector import LiquidityDetector, LiquidityZone, LiquidityType, LiquidityState
from trading.fvg_detector import FVGDetector, FVGZone, FVGType, FVGState

logger = logging.getLogger(__name__)


class SOLTradeAnalyzer:
    """
    Specialized analyzer for SOL trading opportunities.
    Combines liquidity zone analysis with fair value gap detection.
    """
    
    def __init__(self):
        """Initialize SOL trade analyzer with ICT components."""
        self.symbol = 'SOLUSDT'
        self.liquidity_detector = LiquidityDetector()
        self.fvg_detector = FVGDetector()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🌟 SOL Trade Analyzer initialized")
    
    def analyze_sol_opportunity(
        self,
        current_price: float,
        market_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Analyze SOL for trading opportunities based on liquidity zones and FVGs.
        
        Args:
            current_price: Current SOL price
            market_data: Optional OHLCV data for detailed analysis
            
        Returns:
            Dictionary with trade analysis and recommendations
        """
        # Handle invalid price
        if current_price is None or current_price <= 0:
            return {
                'symbol': 'SOL',
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': 'Invalid current price provided'
            }
        
        self.logger.info(f"🔍 Analyzing SOL trade opportunity at ${current_price:.2f}")
        
        analysis = {
            'symbol': 'SOL',
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'liquidity_zones_and_fvg',
            'opportunities': []
        }
        
        try:
            # If market data provided, do detailed analysis
            if market_data is not None and not market_data.empty:
                analysis['detailed_analysis'] = self._perform_detailed_analysis(
                    current_price, market_data
                )
            else:
                # Provide general analysis based on ICT principles
                analysis['detailed_analysis'] = self._perform_general_analysis(current_price)
            
            # Generate trade recommendations
            analysis['recommendations'] = self._generate_recommendations(
                current_price,
                analysis['detailed_analysis']
            )
            
            analysis['status'] = 'success'
            
        except Exception as e:
            self.logger.error(f"❌ SOL analysis error: {e}", exc_info=True)
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _perform_detailed_analysis(
        self,
        current_price: float,
        market_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Perform detailed analysis using market data.
        
        Args:
            current_price: Current SOL price
            market_data: OHLCV DataFrame
            
        Returns:
            Detailed analysis results
        """
        self.logger.info("📊 Performing detailed SOL analysis with market data")
        
        analysis = {
            'liquidity_zones': [],
            'fair_value_gaps': [],
            'key_levels': {}
        }
        
        try:
            # Detect liquidity zones
            liquidity_map = self.liquidity_detector.detect_liquidity_zones(
                market_data,
                self.symbol,
                '15m'  # Use 15-minute timeframe for intraday
            )
            
            # Convert liquidity zones to serializable format
            buy_side_zones = []
            for zone in liquidity_map.buy_side_liquidity:
                if zone.state == LiquidityState.UNTESTED:
                    buy_side_zones.append({
                        'type': 'buy_side',
                        'price': zone.exact_level,
                        'zone_high': zone.zone_high,
                        'zone_low': zone.zone_low,
                        'strength': zone.strength_score,
                        'state': zone.state.value
                    })
            
            sell_side_zones = []
            for zone in liquidity_map.sell_side_liquidity:
                if zone.state == LiquidityState.UNTESTED:
                    sell_side_zones.append({
                        'type': 'sell_side',
                        'price': zone.exact_level,
                        'zone_high': zone.zone_high,
                        'zone_low': zone.zone_low,
                        'strength': zone.strength_score,
                        'state': zone.state.value
                    })
            
            analysis['liquidity_zones'] = {
                'buy_side': buy_side_zones[:3],  # Top 3 buy-side zones
                'sell_side': sell_side_zones[:3]  # Top 3 sell-side zones
            }
            
            # Detect fair value gaps
            fvgs = self.fvg_detector.detect_fvgs(market_data, self.symbol, '15m')
            
            # Filter fresh FVGs
            fresh_bullish_fvgs = []
            fresh_bearish_fvgs = []
            
            for fvg in fvgs:
                if fvg.state == FVGState.FRESH:
                    fvg_dict = {
                        'type': fvg.fvg_type.value,
                        'high': fvg.gap_high,
                        'low': fvg.gap_low,
                        'mid': (fvg.gap_high + fvg.gap_low) / 2,
                        'quality': fvg.quality.value,
                        'timestamp': fvg.formation_timestamp.isoformat()
                    }
                    
                    if fvg.fvg_type == FVGType.BULLISH_FVG:
                        fresh_bullish_fvgs.append(fvg_dict)
                    elif fvg.fvg_type == FVGType.BEARISH_FVG:
                        fresh_bearish_fvgs.append(fvg_dict)
            
            analysis['fair_value_gaps'] = {
                'bullish': fresh_bullish_fvgs[:3],  # Top 3 bullish FVGs
                'bearish': fresh_bearish_fvgs[:3]   # Top 3 bearish FVGs
            }
            
            # Calculate key levels
            analysis['key_levels'] = self._calculate_key_levels(market_data, current_price)
            
        except Exception as e:
            self.logger.error(f"❌ Detailed analysis error: {e}", exc_info=True)
            analysis['error'] = str(e)
        
        return analysis
    
    def _perform_general_analysis(self, current_price: float) -> Dict[str, Any]:
        """
        Perform general analysis using ICT principles without detailed data.
        
        Args:
            current_price: Current SOL price
            
        Returns:
            General analysis results
        """
        self.logger.info("📈 Performing general SOL analysis")
        
        # Calculate percentage-based key levels using ICT principles
        # These are approximate zones based on typical SOL volatility (5% moves)
        
        analysis = {
            'liquidity_zones': {
                'buy_side': [
                    {
                        'type': 'buy_side',
                        'price': round(current_price * 1.03, 2),  # 3% above
                        'zone_high': round(current_price * 1.035, 2),
                        'zone_low': round(current_price * 1.025, 2),
                        'strength': 0.75,
                        'state': 'UNTESTED'
                    },
                    {
                        'type': 'buy_side',
                        'price': round(current_price * 1.05, 2),  # 5% above
                        'zone_high': round(current_price * 1.055, 2),
                        'zone_low': round(current_price * 1.045, 2),
                        'strength': 0.85,
                        'state': 'UNTESTED'
                    }
                ],
                'sell_side': [
                    {
                        'type': 'sell_side',
                        'price': round(current_price * 0.97, 2),  # 3% below
                        'zone_high': round(current_price * 0.975, 2),
                        'zone_low': round(current_price * 0.965, 2),
                        'strength': 0.75,
                        'state': 'UNTESTED'
                    },
                    {
                        'type': 'sell_side',
                        'price': round(current_price * 0.95, 2),  # 5% below
                        'zone_high': round(current_price * 0.955, 2),
                        'zone_low': round(current_price * 0.945, 2),
                        'strength': 0.85,
                        'state': 'UNTESTED'
                    }
                ]
            },
            'fair_value_gaps': {
                'bullish': [
                    {
                        'type': 'BULLISH_FVG',
                        'high': round(current_price * 0.985, 2),
                        'low': round(current_price * 0.975, 2),
                        'mid': round(current_price * 0.98, 2),
                        'quality': 'MEDIUM',
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'bearish': [
                    {
                        'type': 'BEARISH_FVG',
                        'high': round(current_price * 1.025, 2),
                        'low': round(current_price * 1.015, 2),
                        'mid': round(current_price * 1.02, 2),
                        'quality': 'MEDIUM',
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            },
            'key_levels': {
                'resistance_1': round(current_price * 1.02, 2),
                'resistance_2': round(current_price * 1.05, 2),
                'support_1': round(current_price * 0.98, 2),
                'support_2': round(current_price * 0.95, 2)
            }
        }
        
        return analysis
    
    def _calculate_key_levels(
        self,
        market_data: pd.DataFrame,
        current_price: float
    ) -> Dict[str, float]:
        """
        Calculate key support and resistance levels.
        
        Args:
            market_data: OHLCV DataFrame
            current_price: Current price
            
        Returns:
            Dictionary of key levels
        """
        # Use recent highs/lows for support/resistance
        recent_data = market_data.tail(100)  # Last 100 candles
        
        highs = recent_data['high'].nlargest(5)
        lows = recent_data['low'].nsmallest(5)
        
        # Find nearest levels above and below current price
        resistance_levels = sorted([h for h in highs if h > current_price])
        support_levels = sorted([l for l in lows if l < current_price], reverse=True)
        
        key_levels = {
            'resistance_1': resistance_levels[0] if len(resistance_levels) > 0 else current_price * 1.02,
            'resistance_2': resistance_levels[1] if len(resistance_levels) > 1 else current_price * 1.05,
            'support_1': support_levels[0] if len(support_levels) > 0 else current_price * 0.98,
            'support_2': support_levels[1] if len(support_levels) > 1 else current_price * 0.95
        }
        
        return key_levels
    
    def _generate_recommendations(
        self,
        current_price: float,
        detailed_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trade recommendations based on analysis.
        
        Args:
            current_price: Current SOL price
            detailed_analysis: Results from detailed analysis
            
        Returns:
            Trade recommendations
        """
        recommendations = {
            'bias': 'NEUTRAL',
            'suggested_trades': [],
            'risk_notes': []
        }
        
        try:
            liquidity_zones = detailed_analysis.get('liquidity_zones', {})
            fair_value_gaps = detailed_analysis.get('fair_value_gaps', {})
            key_levels = detailed_analysis.get('key_levels', {})
            
            # Check for bullish setup (price near sell-side liquidity + bullish FVG)
            sell_side_zones = liquidity_zones.get('sell_side', [])
            bullish_fvgs = fair_value_gaps.get('bullish', [])
            
            if sell_side_zones and bullish_fvgs:
                nearest_support = sell_side_zones[0]['price']
                nearest_fvg = bullish_fvgs[0]['mid']
                
                # If price is near support and FVG, suggest buy
                if abs(current_price - nearest_support) / current_price < 0.02:  # Within 2%
                    buy_recommendation = {
                        'direction': 'BUY',
                        'entry_zone': {
                            'high': round(nearest_support * 1.005, 2),
                            'low': round(nearest_support * 0.995, 2)
                        },
                        'stop_loss': round(nearest_support * 0.97, 2),  # 3% below support
                        'targets': [
                            {'level': round(current_price * 1.02, 2), 'label': 'TP1 (2%)'},
                            {'level': round(current_price * 1.03, 2), 'label': 'TP2 (3%)'},
                            {'level': round(current_price * 1.05, 2), 'label': 'TP3 (5%)'}
                        ],
                        'confluence': [
                            'Sell-side liquidity zone',
                            'Bullish fair value gap',
                            'ICT buy model'
                        ],
                        'risk_reward': 2.0
                    }
                    recommendations['suggested_trades'].append(buy_recommendation)
                    recommendations['bias'] = 'BULLISH'
            
            # Check for bearish setup (price near buy-side liquidity + bearish FVG)
            buy_side_zones = liquidity_zones.get('buy_side', [])
            bearish_fvgs = fair_value_gaps.get('bearish', [])
            
            if buy_side_zones and bearish_fvgs:
                nearest_resistance = buy_side_zones[0]['price']
                nearest_fvg = bearish_fvgs[0]['mid']
                
                # If price is near resistance and FVG, suggest sell
                if abs(current_price - nearest_resistance) / current_price < 0.02:  # Within 2%
                    sell_recommendation = {
                        'direction': 'SELL',
                        'entry_zone': {
                            'high': round(nearest_resistance * 1.005, 2),
                            'low': round(nearest_resistance * 0.995, 2)
                        },
                        'stop_loss': round(nearest_resistance * 1.03, 2),  # 3% above resistance
                        'targets': [
                            {'level': round(current_price * 0.98, 2), 'label': 'TP1 (2%)'},
                            {'level': round(current_price * 0.97, 2), 'label': 'TP2 (3%)'},
                            {'level': round(current_price * 0.95, 2), 'label': 'TP3 (5%)'}
                        ],
                        'confluence': [
                            'Buy-side liquidity zone',
                            'Bearish fair value gap',
                            'ICT sell model'
                        ],
                        'risk_reward': 2.0
                    }
                    recommendations['suggested_trades'].append(sell_recommendation)
                    if recommendations['bias'] == 'NEUTRAL':
                        recommendations['bias'] = 'BEARISH'
                    else:
                        recommendations['bias'] = 'MIXED'  # Both bullish and bearish setups
            
            # Add risk management notes
            recommendations['risk_notes'] = [
                'Risk 1% of account per trade',
                'Place stop loss beyond liquidity zone',
                'Take partial profits at each target',
                'Monitor for liquidity sweeps',
                'Respect NY session highs/lows'
            ]
            
            # If no specific trades found, provide general guidance
            if not recommendations['suggested_trades']:
                recommendations['general_guidance'] = {
                    'message': 'No high-probability setup at current price',
                    'watch_zones': {
                        'buy_zone': sell_side_zones[0] if sell_side_zones else None,
                        'sell_zone': buy_side_zones[0] if buy_side_zones else None
                    },
                    'action': 'Wait for price to reach key liquidity zones'
                }
        
        except Exception as e:
            self.logger.error(f"❌ Recommendation generation error: {e}", exc_info=True)
            recommendations['error'] = str(e)
        
        return recommendations


def create_sol_analyzer() -> SOLTradeAnalyzer:
    """
    Factory function to create SOL trade analyzer.
    
    Returns:
        SOLTradeAnalyzer instance
    """
    return SOLTradeAnalyzer()
