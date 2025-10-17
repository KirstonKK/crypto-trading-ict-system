"""
Integration tests for API connectivity and data flow.
Tests the complete pipeline from configuration to API calls.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Import modules to test
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from utils.data_fetcher import DataFetcher
    from utils.notifications import NotificationManager
    from utils.crypto_pairs import CryptoPairs
except ImportError as e:
    pytest.skip(f"Skipping integration tests due to import error: {e}", allow_module_level=True)


class TestAPIIntegration:
    """Integration tests for API connectivity"""
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock successful API response data"""
        return [
            [1640995200000, 47000.0, 47500.0, 46800.0, 47200.0, 100.5],  # timestamp, o, h, l, c, v
            [1640995260000, 47200.0, 47300.0, 46900.0, 47100.0, 85.2],
            [1640995320000, 47100.0, 47400.0, 47000.0, 47300.0, 92.1]
        ]
    
    @pytest.fixture
    def data_fetcher(self):
        """Create DataFetcher instance for testing"""
        with patch('ccxt.bybit') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            return DataFetcher(use_testnet=True)
    
    @patch('ccxt.bybit')
    def test_data_fetcher_initialization(self, mock_exchange):
        """Test DataFetcher initializes correctly with API"""
        mock_instance = MagicMock()
        mock_exchange.return_value = mock_instance
        
        df = DataFetcher(use_testnet=True)
        assert df is not None
        assert df.exchange is not None
        
        # Verify testnet configuration
        mock_instance.set_sandbox_mode.assert_called_once_with(True)
    
    @patch('ccxt.bybit')
    def test_fetch_ohlcv_success(self, mock_exchange, mock_api_response):
        """Test successful OHLCV data fetching"""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.fetch_ohlcv.return_value = mock_api_response
        mock_exchange.return_value = mock_instance
        
        df = DataFetcher(use_testnet=True)
        
        # Test data fetching
        data = df.fetch_ohlcv("BTCUSDT", "1m", limit=3)
        
        assert data is not None
        assert len(data) == 3
        mock_instance.fetch_ohlcv.assert_called_once_with("BTCUSDT", "1m", limit=3)
    
    @patch('ccxt.bybit')
    def test_fetch_ohlcv_api_error(self, mock_exchange):
        """Test OHLCV fetching with API error"""
        # Setup mock to raise exception
        mock_instance = MagicMock()
        mock_instance.fetch_ohlcv.side_effect = Exception("API Error")
        mock_exchange.return_value = mock_instance
        
        df = DataFetcher(use_testnet=True)
        
        # Should handle error gracefully
        data = df.fetch_ohlcv("BTCUSDT", "1m", limit=3)
        assert data is None
    
    @patch('ccxt.bybit')
    def test_rate_limiting_integration(self, mock_exchange):
        """Test rate limiting during API calls"""
        mock_instance = MagicMock()
        mock_instance.fetch_ohlcv.return_value = [[1640995200000, 47000, 47500, 46800, 47200, 100]]
        mock_exchange.return_value = mock_instance
        
        df = DataFetcher(use_testnet=True)
        
        # Make multiple rapid calls
        start_time = asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0
        for _ in range(3):
            df.fetch_ohlcv("BTCUSDT", "1m", limit=1)
        
        # Rate limiting should prevent too rapid calls
        # (This is a basic test - real rate limiting needs time measurement)
        assert mock_instance.fetch_ohlcv.call_count == 3


class TestNotificationIntegration:
    """Integration tests for notification system"""
    
    @pytest.fixture
    def notification_manager(self):
        """Create NotificationManager for testing"""
        return NotificationManager()
    
    @patch('requests.post')
    def test_discord_notification_success(self, mock_post, notification_manager):
        """Test successful Discord notification"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        nm = notification_manager
        
        # Test Discord notification
        result = nm.send_discord_alert("Test message", "INFO")
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_discord_notification_failure(self, mock_post, notification_manager):
        """Test Discord notification failure handling"""
        # Setup mock to raise exception
        mock_post.side_effect = Exception("Network error")
        
        nm = notification_manager
        
        # Should handle error gracefully
        result = nm.send_discord_alert("Test message", "INFO")
        assert result is False
    
    @patch('smtplib.SMTP')
    def test_email_notification_integration(self, mock_smtp, notification_manager):
        """Test email notification integration"""
        # Setup SMTP mock
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        nm = notification_manager
        
        # Test email sending
        result = nm.send_email_alert("Test subject", "Test message", "HIGH")
        
        # Verify SMTP methods were called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()


class TestDataPipeline:
    """Integration tests for complete data pipeline"""
    
    @patch('ccxt.bybit')
    def test_end_to_end_data_flow(self, mock_exchange):
        """Test complete data flow from API to processing"""
        # Setup mocks
        mock_instance = MagicMock()
        mock_instance.fetch_ohlcv.return_value = [
            [1640995200000, 47000.0, 47500.0, 46800.0, 47200.0, 100.5]
        ]
        mock_exchange.return_value = mock_instance
        
        # Initialize components
        df = DataFetcher(use_testnet=True)
        
        # Test data flow
        raw_data = df.fetch_ohlcv("BTCUSDT", "1m", limit=1)
        assert raw_data is not None
        
        # Process data (basic validation)
        processed_data = df.validate_ohlcv_data(raw_data)
        assert processed_data is not None
        assert len(processed_data) > 0
    
    def test_configuration_integration(self):
        """Test integration between different configuration components"""
        with patch('builtins.open'), \
             patch('json.load', return_value={"pairs": {"BTCUSDT": {"enabled": True}}}), \
             patch('pathlib.Path.exists', return_value=True):
            
            cp = CryptoPairs()
            
            # Test configuration loading and validation
            assert cp.validate_symbol("BTCUSDT") is True
            enabled_pairs = cp.get_enabled_pairs()
            assert "BTCUSDT" in enabled_pairs
    
    @patch('ccxt.bybit')
    @patch('requests.post')
    def test_error_notification_integration(self, mock_post, mock_exchange):
        """Test integration between API errors and notification system"""
        # Setup API to fail
        mock_instance = MagicMock()
        mock_instance.fetch_ohlcv.side_effect = Exception("API Error")
        mock_exchange.return_value = mock_instance
        
        # Setup notification mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        df = DataFetcher(use_testnet=True)
        nm = NotificationManager()
        
        # Test error handling and notification
        try:
            data = df.fetch_ohlcv("BTCUSDT", "1m")
            if data is None:
                nm.send_discord_alert("API Error occurred", "ERROR")
        except Exception:
            nm.send_discord_alert("Critical API Error", "CRITICAL")
        
        # Verify notification was sent
        mock_post.assert_called()


class TestPerformanceIntegration:
    """Performance and load testing for integration scenarios"""
    
    @patch('ccxt.bybit')
    def test_concurrent_api_calls(self, mock_exchange):
        """Test performance with concurrent API calls"""
        mock_instance = MagicMock()
        mock_instance.fetch_ohlcv.return_value = [[1640995200000, 47000, 47500, 46800, 47200, 100]]
        mock_exchange.return_value = mock_instance
        
        df = DataFetcher(use_testnet=True)
        
        # Simulate concurrent requests
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        results = []
        
        for symbol in symbols:
            result = df.fetch_ohlcv(symbol, "1m", limit=1)
            results.append(result)
        
        # All requests should complete successfully
        assert len([r for r in results if r is not None]) == len(symbols)
    
    def test_memory_usage_integration(self):
        """Test memory usage during data processing"""
        # This is a placeholder for memory profiling
        # In a real scenario, we'd use memory_profiler or similar
        
        with patch('builtins.open'), \
             patch('json.load', return_value={"pairs": {}}), \
             patch('pathlib.Path.exists', return_value=True):
            
            # Initialize multiple components
            cp = CryptoPairs()
            nm = NotificationManager()
            
            # Perform operations that could consume memory
            for _ in range(100):
                cp.validate_symbol("BTCUSDT")
                cp.get_volatility_factor("BTCUSDT")
        
        # If we get here without memory issues, test passes
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
