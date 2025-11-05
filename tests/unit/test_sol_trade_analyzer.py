#!/usr/bin/env python3
"""
Unit tests for SOL Trade Analyzer Module
========================================

Tests the SOL trade analysis functionality.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from core.analysis.sol_trade_analyzer import SOLTradeAnalyzer, create_sol_analyzer


class TestSOLTradeAnalyzer:
    """Test cases for SOLTradeAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create SOL analyzer instance for testing."""
        return SOLTradeAnalyzer()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        dates = pd.date_range(start='2025-01-01', periods=100, freq='15min')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(145, 155, 100),
            'high': np.random.uniform(146, 156, 100),
            'low': np.random.uniform(144, 154, 100),
            'close': np.random.uniform(145, 155, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        })
        return data
    
    def test_analyzer_initialization(self, analyzer):
        """Test SOL analyzer initialization."""
        assert analyzer.symbol == 'SOLUSDT'
        assert analyzer.liquidity_detector is not None
        assert analyzer.fvg_detector is not None
    
    def test_factory_function(self):
        """Test factory function creates valid instance."""
        analyzer = create_sol_analyzer()
        assert isinstance(analyzer, SOLTradeAnalyzer)
        assert analyzer.symbol == 'SOLUSDT'
    
    def test_analyze_sol_opportunity_basic(self, analyzer):
        """Test basic SOL opportunity analysis without market data."""
        current_price = 150.0
        result = analyzer.analyze_sol_opportunity(current_price)
        
        assert result['symbol'] == 'SOL'
        assert result['current_price'] == current_price
        assert 'timestamp' in result
        assert 'analysis_type' in result
        assert result['analysis_type'] == 'liquidity_zones_and_fvg'
        assert 'detailed_analysis' in result
        assert 'recommendations' in result
    
    def test_analyze_sol_with_market_data(self, analyzer, sample_market_data):
        """Test SOL analysis with market data."""
        current_price = 150.0
        result = analyzer.analyze_sol_opportunity(current_price, sample_market_data)
        
        assert result['status'] == 'success'
        assert 'detailed_analysis' in result
        assert 'recommendations' in result
    
    def test_general_analysis(self, analyzer):
        """Test general analysis method."""
        current_price = 150.0
        analysis = analyzer._perform_general_analysis(current_price)
        
        assert 'liquidity_zones' in analysis
        assert 'fair_value_gaps' in analysis
        assert 'key_levels' in analysis
        
        # Check liquidity zones structure
        assert 'buy_side' in analysis['liquidity_zones']
        assert 'sell_side' in analysis['liquidity_zones']
        assert len(analysis['liquidity_zones']['buy_side']) > 0
        assert len(analysis['liquidity_zones']['sell_side']) > 0
        
        # Check FVG structure
        assert 'bullish' in analysis['fair_value_gaps']
        assert 'bearish' in analysis['fair_value_gaps']
        
        # Check key levels
        assert 'resistance_1' in analysis['key_levels']
        assert 'support_1' in analysis['key_levels']
    
    def test_liquidity_zones_calculation(self, analyzer):
        """Test liquidity zone calculations."""
        current_price = 150.0
        analysis = analyzer._perform_general_analysis(current_price)
        
        # Verify buy-side zones are above current price
        for zone in analysis['liquidity_zones']['buy_side']:
            assert zone['price'] > current_price
            assert zone['zone_high'] > zone['zone_low']
            assert zone['type'] == 'buy_side'
            assert zone['state'] == 'UNTESTED'
        
        # Verify sell-side zones are below current price
        for zone in analysis['liquidity_zones']['sell_side']:
            assert zone['price'] < current_price
            assert zone['zone_high'] > zone['zone_low']
            assert zone['type'] == 'sell_side'
            assert zone['state'] == 'UNTESTED'
    
    def test_fair_value_gaps_calculation(self, analyzer):
        """Test fair value gap calculations."""
        current_price = 150.0
        analysis = analyzer._perform_general_analysis(current_price)
        
        # Check bullish FVG (below current price)
        for fvg in analysis['fair_value_gaps']['bullish']:
            assert fvg['type'] == 'BULLISH_FVG'
            assert fvg['high'] > fvg['low']
            assert fvg['mid'] == (fvg['high'] + fvg['low']) / 2
            assert 'quality' in fvg
            assert 'timestamp' in fvg
        
        # Check bearish FVG (above current price)
        for fvg in analysis['fair_value_gaps']['bearish']:
            assert fvg['type'] == 'BEARISH_FVG'
            assert fvg['high'] > fvg['low']
            assert fvg['mid'] == (fvg['high'] + fvg['low']) / 2
    
    def test_recommendations_generation(self, analyzer):
        """Test trade recommendations generation."""
        current_price = 150.0
        detailed_analysis = analyzer._perform_general_analysis(current_price)
        recommendations = analyzer._generate_recommendations(current_price, detailed_analysis)
        
        assert 'bias' in recommendations
        assert recommendations['bias'] in ['NEUTRAL', 'BULLISH', 'BEARISH', 'MIXED']
        assert 'suggested_trades' in recommendations
        assert 'risk_notes' in recommendations
        assert isinstance(recommendations['risk_notes'], list)
        assert len(recommendations['risk_notes']) > 0
    
    def test_buy_recommendation_structure(self, analyzer):
        """Test structure of buy recommendations when generated."""
        current_price = 150.0
        
        # Create analysis with price near support
        analysis = analyzer._perform_general_analysis(current_price)
        
        # Manually adjust to trigger buy recommendation
        analysis['liquidity_zones']['sell_side'][0]['price'] = current_price * 0.998  # Very close
        
        recommendations = analyzer._generate_recommendations(current_price, analysis)
        
        # Check if any trades suggested
        if len(recommendations['suggested_trades']) > 0:
            trade = recommendations['suggested_trades'][0]
            
            if trade['direction'] == 'BUY':
                assert 'entry_zone' in trade
                assert 'stop_loss' in trade
                assert 'targets' in trade
                assert 'confluence' in trade
                assert 'risk_reward' in trade
                assert trade['stop_loss'] < trade['entry_zone']['low']
                assert len(trade['targets']) > 0
    
    def test_key_levels_calculation(self, analyzer, sample_market_data):
        """Test key support/resistance level calculation."""
        current_price = 150.0
        key_levels = analyzer._calculate_key_levels(sample_market_data, current_price)
        
        assert 'resistance_1' in key_levels
        assert 'resistance_2' in key_levels
        assert 'support_1' in key_levels
        assert 'support_2' in key_levels
        
        # Verify resistances are above current price
        assert key_levels['resistance_1'] >= current_price
        assert key_levels['resistance_2'] >= key_levels['resistance_1']
        
        # Verify supports are below current price
        assert key_levels['support_1'] <= current_price
        assert key_levels['support_2'] <= key_levels['support_1']
    
    def test_risk_management_notes(self, analyzer):
        """Test that risk management notes are included."""
        current_price = 150.0
        analysis = analyzer._perform_general_analysis(current_price)
        recommendations = analyzer._generate_recommendations(current_price, analysis)
        
        risk_notes = recommendations['risk_notes']
        
        # Verify key risk management concepts are present
        risk_note_text = ' '.join(risk_notes).lower()
        assert '1%' in risk_note_text or 'risk' in risk_note_text
        assert 'stop loss' in risk_note_text or 'stop' in risk_note_text
    
    def test_analysis_handles_errors_gracefully(self, analyzer):
        """Test that analysis handles errors gracefully."""
        # Test with invalid data
        result = analyzer.analyze_sol_opportunity(None)
        
        # Should still return a result structure, possibly with error
        assert 'symbol' in result
        assert 'timestamp' in result
    
    def test_price_calculations_accuracy(self, analyzer):
        """Test accuracy of price calculations."""
        current_price = 150.0
        analysis = analyzer._perform_general_analysis(current_price)
        
        # Check that calculated prices are reasonable percentages
        buy_side_zone = analysis['liquidity_zones']['buy_side'][0]
        price_diff_pct = (buy_side_zone['price'] - current_price) / current_price * 100
        
        # Should be within reasonable range (e.g., 1-10%)
        assert 1 <= price_diff_pct <= 10
        
        sell_side_zone = analysis['liquidity_zones']['sell_side'][0]
        price_diff_pct = abs((sell_side_zone['price'] - current_price) / current_price * 100)
        
        # Should be within reasonable range
        assert 1 <= price_diff_pct <= 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
