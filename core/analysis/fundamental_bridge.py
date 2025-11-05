#!/usr/bin/env python3
"""
🔗 FUNDAMENTAL ANALYSIS INTEGRATION BRIDGE
==========================================

Optional bridge for day trading system to access fundamental analysis insights.
Provides long-term context for short-term trading decisions.

Usage:
- from fundamental_bridge import FundamentalBridge
- bridge = FundamentalBridge()
- insights = bridge.get_insights('BTC')
"""

import requests
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FundamentalBridge:
    """Bridge to connect day trading system with fundamental analysis"""
    
    def __init__(self, fundamental_port: int = 5002, timeout: int = 5):
        self.base_url = f"http://localhost:{fundamental_port}"
        self.timeout = timeout
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def is_fundamental_system_available(self) -> bool:
        """Check if fundamental analysis system is running"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_insights(self, symbol: str) -> Optional[Dict]:
        """Get fundamental insights for a specific crypto symbol"""
        try:
            # Check cache first
            cache_key = f"insights_{symbol.upper()}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Fetch from fundamental analysis system
            response = requests.get(
                f"{self.base_url}/api/analysis/{symbol.upper()}", 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now()
                }
                
                return data
            else:
                logger.warning(f"Failed to get insights for {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting fundamental insights for {symbol}: {e}")
            return None
    
    def get_investment_signals(self, symbol: str) -> Dict:
        """Get investment signals that can inform day trading decisions"""
        insights = self.get_insights(symbol)
        if not insights:
            return {'available': False}
        
        # Extract actionable signals for day trading
        signals = {
            'available': True,
            'symbol': symbol.upper(),
            'overall_score': insights.get('overall_score', 0),
            'recommendation': insights.get('recommendation', 'UNKNOWN'),
            'confidence': insights.get('confidence', 0),
            'long_term_bias': self._get_long_term_bias(insights),
            'supply_pressure': self._assess_supply_pressure(insights),
            'demand_strength': self._assess_demand_strength(insights),
            'news_sentiment': insights.get('news_sentiment', 'NEUTRAL'),
            'risk_level': self._assess_risk_level(insights),
            'timeframe_alignment': self._check_timeframe_alignment(insights),
            'summary': self._generate_trading_summary(insights)
        }
        
        return signals
    
    def get_market_overview(self) -> Optional[Dict]:
        """Get overall market fundamental overview"""
        try:
            response = requests.get(f"{self.base_url}/api/analysis", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return self._process_market_overview(data)
            return None
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return None
    
    def get_recommendations(self) -> List[Dict]:
        """Get top fundamental recommendations"""
        try:
            response = requests.get(f"{self.base_url}/api/recommendations", timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get('recommendations', [])
            return []
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        age = datetime.now() - self.cache[cache_key]['timestamp']
        return age.total_seconds() < self.cache_ttl
    
    def _get_long_term_bias(self, insights: Dict) -> str:
        """Determine long-term bias for day trading context"""
        score = insights.get('overall_score', 0)
        recommendation = insights.get('recommendation', 'UNKNOWN')
        
        if recommendation == 'BUY' and score >= 80:
            return 'STRONG_BULLISH'
        elif recommendation == 'BUY' and score >= 70:
            return 'BULLISH'
        elif recommendation == 'HOLD':
            return 'NEUTRAL'
        elif recommendation == 'SELL':
            return 'BEARISH'
        else:
            return 'UNKNOWN'
    
    def _assess_supply_pressure(self, insights: Dict) -> str:
        """Assess supply pressure from fundamental data"""
        inflation_rate = insights.get('inflation_rate', 0)
        supply_score = insights.get('supply_score', 'UNKNOWN')
        
        if supply_score == 'EXCELLENT' and inflation_rate < 2:
            return 'LOW'
        elif supply_score == 'GOOD' and inflation_rate < 5:
            return 'MODERATE'
        else:
            return 'HIGH'
    
    def _assess_demand_strength(self, insights: Dict) -> str:
        """Assess demand strength from fundamental data"""
        demand_score = insights.get('demand_score', 'UNKNOWN')
        dau = insights.get('daily_active_users', 0)
        tvl = insights.get('total_value_locked', 0)
        
        if demand_score == 'EXCELLENT' and dau > 1000000:
            return 'STRONG'
        elif demand_score == 'GOOD' and tvl > 1000000000:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _assess_risk_level(self, insights: Dict) -> str:
        """Assess overall risk level"""
        confidence = insights.get('confidence', 0)
        score = insights.get('overall_score', 0)
        
        if confidence > 0.85 and score > 80:
            return 'LOW'
        elif confidence > 0.70 and score > 65:
            return 'MODERATE'
        else:
            return 'HIGH'
    
    def _check_timeframe_alignment(self, insights: Dict) -> Dict:
        """Check how fundamental timeframe aligns with day trading"""
        timeframe = insights.get('target_timeframe', 'UNKNOWN')
        recommendation = insights.get('recommendation', 'UNKNOWN')
        
        alignment = {
            'fundamental_timeframe': timeframe,
            'day_trading_alignment': 'NEUTRAL',
            'advice': 'No specific alignment guidance'
        }
        
        if timeframe == '4-YEAR' and recommendation == 'BUY':
            alignment.update({
                'day_trading_alignment': 'SUPPORTIVE',
                'advice': 'Long-term bullish bias supports buying dips'
            })
        elif timeframe == '2-YEAR' and recommendation == 'HOLD':
            alignment.update({
                'day_trading_alignment': 'NEUTRAL',
                'advice': 'Focus on technical levels, no fundamental bias'
            })
        
        return alignment
    
    def _generate_trading_summary(self, insights: Dict) -> str:
        """Generate summary for day traders"""
        symbol = insights.get('symbol', 'UNKNOWN')
        recommendation = insights.get('recommendation', 'UNKNOWN')
        score = insights.get('overall_score', 0)
        sentiment = insights.get('news_sentiment', 'NEUTRAL')
        
        summary = f"{symbol} fundamental analysis: {recommendation} ({score}/100). "
        summary += f"News sentiment: {sentiment}. "
        
        if recommendation == 'BUY' and score >= 80:
            summary += "Strong fundamental support for long positions."
        elif recommendation == 'BUY' and score >= 70:
            summary += "Moderate fundamental support, favor buying dips."
        elif recommendation == 'HOLD':
            summary += "Neutral fundamentals, rely on technical analysis."
        else:
            summary += "Weak fundamentals, consider defensive approach."
        
        return summary
    
    def _process_market_overview(self, data: Dict) -> Dict:
        """Process market overview data for trading context"""
        analysis_data = data.get('analysis_data', {})
        
        overview = {
            'last_update': data.get('last_update'),
            'total_symbols': len(analysis_data),
            'strong_buy_count': 0,
            'buy_count': 0,
            'hold_count': 0,
            'sell_count': 0,
            'average_score': 0,
            'market_sentiment': 'NEUTRAL',
            'top_performers': [],
            'market_summary': ''
        }
        
        scores = []
        for symbol, info in analysis_data.items():
            score = info.get('overall_score', 0)
            scores.append(score)
            rec = info.get('recommendation', 'UNKNOWN')
            
            if rec == 'BUY' and score >= 85:
                overview['strong_buy_count'] += 1
                overview['top_performers'].append({
                    'symbol': symbol,
                    'score': score,
                    'name': info.get('name', symbol)
                })
            elif rec == 'BUY':
                overview['buy_count'] += 1
            elif rec == 'HOLD':
                overview['hold_count'] += 1
            elif rec == 'SELL':
                overview['sell_count'] += 1
        
        if scores:
            overview['average_score'] = sum(scores) / len(scores)
            
            if overview['average_score'] >= 80:
                overview['market_sentiment'] = 'BULLISH'
            elif overview['average_score'] >= 65:
                overview['market_sentiment'] = 'NEUTRAL'
            else:
                overview['market_sentiment'] = 'BEARISH'
        
        # Sort top performers by score
        overview['top_performers'].sort(key=lambda x: x['score'], reverse=True)
        overview['top_performers'] = overview['top_performers'][:3]  # Top 3
        
        # Generate market summary
        total = overview['total_symbols']
        strong_buy = overview['strong_buy_count']
        buy = overview['buy_count']
        
        overview['market_summary'] = f"Market analysis: {strong_buy}/{total} strong buys, "
        overview['market_summary'] += f"{buy}/{total} buys. "
        overview['market_summary'] += f"Average score: {overview['average_score']:.1f}. "
        overview['market_summary'] += f"Sentiment: {overview['market_sentiment']}."
        
        return overview

# Example usage functions for day trading system integration
def get_crypto_fundamental_bias(symbol: str) -> str:
    """Quick function to get fundamental bias for a crypto symbol"""
    bridge = FundamentalBridge()
    if not bridge.is_fundamental_system_available():
        return 'UNAVAILABLE'
    
    signals = bridge.get_investment_signals(symbol)
    if signals.get('available'):
        return signals.get('long_term_bias', 'UNKNOWN')
    return 'UNKNOWN'

def should_favor_longs(symbol: str) -> bool:
    """Check if fundamentals support favoring long positions"""
    bias = get_crypto_fundamental_bias(symbol)
    return bias in ['STRONG_BULLISH', 'BULLISH']

def get_fundamental_summary(symbol: str) -> str:
    """Get a quick fundamental summary for trading decisions"""
    bridge = FundamentalBridge()
    if not bridge.is_fundamental_system_available():
        return f"{symbol}: Fundamental analysis unavailable"
    
    signals = bridge.get_investment_signals(symbol)
    if signals.get('available'):
        return signals.get('summary', f"{symbol}: No summary available")
    return f"{symbol}: Analysis not available"

# Example integration with existing trading system
def enhance_signal_with_fundamentals(signal_data: Dict) -> Dict:
    """Enhance trading signal with fundamental analysis context"""
    symbol = signal_data.get('symbol', '')
    if not symbol:
        return signal_data
    
    bridge = FundamentalBridge()
    if not bridge.is_fundamental_system_available():
        signal_data['fundamental_context'] = 'Unavailable'
        return signal_data
    
    fundamental_signals = bridge.get_investment_signals(symbol)
    if fundamental_signals.get('available'):
        signal_data['fundamental_context'] = {
            'bias': fundamental_signals.get('long_term_bias', 'UNKNOWN'),
            'score': fundamental_signals.get('overall_score', 0),
            'confidence': fundamental_signals.get('confidence', 0),
            'summary': fundamental_signals.get('summary', ''),
            'risk_level': fundamental_signals.get('risk_level', 'UNKNOWN')
        }
    else:
        signal_data['fundamental_context'] = 'Not available'
    
    return signal_data

if __name__ == "__main__":
    # Test the bridge
    bridge = FundamentalBridge()
    
    print("🔗 FUNDAMENTAL ANALYSIS BRIDGE TEST")
    print("=" * 40)
    
    # Check if system is available
    if bridge.is_fundamental_system_available():
        print("✅ Fundamental analysis system is available")
        
        # Test getting insights for BTC
        insights = bridge.get_insights('BTC')
        if insights:
            print("📊 BTC Insights: Score {insights.get('overall_score')}/100")
            print("📈 Recommendation: {insights.get('recommendation')}")
        
        # Test getting trading signals
        signals = bridge.get_investment_signals('BTC')
        if signals.get('available'):
            print("🎯 BTC Trading Bias: {signals.get('long_term_bias')}")
            print("📝 Summary: {signals.get('summary')}")
        
        # Test market overview
        overview = bridge.get_market_overview()
        if overview:
            print("🌍 Market Sentiment: {overview.get('market_sentiment')}")
            print("📈 Average Score: {overview.get('average_score', 0):.1f}")
    else:
        print("❌ Fundamental analysis system is not available")
        print("💡 Start it with: ./launch_fundamental_analysis.sh")
    
    print("=" * 40)