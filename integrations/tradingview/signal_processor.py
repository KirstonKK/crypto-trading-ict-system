"""
TradingView Signal Processing Engine
===================================

Converts TradingView webhook alerts into validated trading signals
with comprehensive risk management and filtering.

Features:
- Alert validation and sanitization
- Risk-based signal filtering
- Position size calculation
- Market condition validation
- Signal confidence scoring
- Real-time processing pipeline

Signal Flow:
1. Alert Reception → 2. Validation → 3. Risk Assessment → 
4. Signal Generation → 5. Position Sizing → 6. Execution Ready

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import asyncio

from utils.config_loader import ConfigLoader
from utils.crypto_pairs import CryptoPairs
from utils.risk_management import RiskManager
from .webhook_server import WebhookAlert

logger = logging.getLogger(__name__)

@dataclass
class ProcessedSignal:
    """Container for processed trading signal ready for execution."""
    # Original alert data
    original_alert: WebhookAlert
    
    # Processed signal data
    symbol: str
    action: str  # 'BUY', 'SELL', 'CLOSE_LONG', 'CLOSE_SHORT'
    validated_price: float
    position_size: float
    
    # Risk management
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    
    # Signal quality metrics
    confidence_score: float
    validation_status: str  # 'APPROVED', 'REJECTED', 'PENDING'
    
    # Market context
    market_phase: str
    volatility_regime: str
    
    # Timing
    processing_timestamp: datetime
    execution_deadline: datetime
    
    # Optional fields with defaults
    rejection_reason: Optional[str] = None
    metadata: Optional[Dict] = None


class SignalProcessor:
    """
    Advanced signal processing engine for TradingView alerts.
    
    This class validates, filters, and processes TradingView webhook alerts
    into executable trading signals with comprehensive risk management.
    """
    
    def __init__(self, config_path: str = "project/configuration/"):
        """Initialize signal processor with risk management."""
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_path)
        self.crypto_pairs = CryptoPairs(config_path)
        self.risk_manager = RiskManager(config_path)
        
        # Load signal processing configuration
        self.signal_config = self._load_signal_config()
        
        # Signal handlers
        self.signal_handlers: List[Callable[[ProcessedSignal], None]] = []
        
        # Processing statistics
        self.stats = {
            'total_alerts': 0,
            'approved_signals': 0,
            'rejected_signals': 0,
            'processing_errors': 0,
            'last_reset': datetime.now()
        }
        
        # Alert cache for deduplication
        self.alert_cache = {}
        self.cache_expiry = timedelta(minutes=5)
        
        logger.info("Signal processor initialized with risk management")
    
    def _load_signal_config(self) -> Dict:
        """Load signal processing configuration."""
        try:
            config = self.config_loader.get_config("signal_processing")
        except Exception as e:
            logger.warning(f"Failed to load signal config: {e}")
            config = {}
        
        # Default configuration
        defaults = {
            'min_confidence': 0.6,
            'max_position_risk': 0.02,  # 2% max risk per position
            'price_tolerance': 0.005,   # 0.5% price tolerance
            'signal_timeout_minutes': 10,
            'duplicate_window_minutes': 5,
            'require_market_hours': False,
            'enable_signal_filtering': True,
            'max_concurrent_positions': 3,
            'min_risk_reward_ratio': 1.5,
            'volatility_filters': {
                'max_extreme_volatility_trades': 1,
                'skip_low_volatility_pairs': True
            },
            'market_phase_filters': {
                'allowed_phases': ['ACCUMULATION', 'MARKUP', 'DISTRIBUTION'],
                'block_markdown_longs': True
            }
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
    
    def add_signal_handler(self, handler: Callable[[ProcessedSignal], None]) -> None:
        """Add handler for processed signals."""
        self.signal_handlers.append(handler)
        logger.info(f"Added signal handler: {handler.__name__}")
    
    async def process_alert(self, alert: WebhookAlert) -> Optional[ProcessedSignal]:
        """
        Process TradingView alert into executable trading signal.
        
        Args:
            alert: Raw webhook alert from TradingView
            
        Returns:
            ProcessedSignal if valid, None if rejected
        """
        self.stats['total_alerts'] += 1
        
        try:
            logger.info(f"Processing alert: {alert.action} {alert.symbol}")
            
            # Step 1: Basic validation
            validation_result = self._validate_alert(alert)
            if not validation_result['valid']:
                logger.warning(f"Alert validation failed: {validation_result['reason']}")
                self._record_rejection(validation_result['reason'])
                return None
            
            # Step 2: Duplicate detection
            if self._is_duplicate_alert(alert):
                logger.info(f"Duplicate alert detected for {alert.symbol}")
                self._record_rejection("Duplicate alert")
                return None
            
            # Step 3: Market conditions validation
            market_validation = await self._validate_market_conditions(alert)
            if not market_validation['valid']:
                logger.warning(f"Market validation failed: {market_validation['reason']}")
                self._record_rejection(market_validation['reason'])
                return None
            
            # Step 4: Risk assessment
            risk_assessment = await self._assess_risk(alert)
            if not risk_assessment['approved']:
                logger.warning(f"Risk assessment failed: {risk_assessment['reason']}")
                self._record_rejection(risk_assessment['reason'])
                return None
            
            # Step 5: Position sizing
            position_data = await self._calculate_position_sizing(alert, risk_assessment)
            if not position_data:
                logger.warning(f"Position sizing failed for {alert.symbol}")
                self._record_rejection("Position sizing failed")
                return None
            
            # Step 6: Signal confidence scoring
            confidence_score = self._calculate_confidence_score(alert, market_validation, risk_assessment)
            
            # Step 7: Final validation
            if confidence_score < self.signal_config['min_confidence']:
                logger.warning(f"Confidence score too low: {confidence_score:.2f}")
                self._record_rejection(f"Low confidence: {confidence_score:.2f}")
                return None
            
            # Step 8: Create processed signal
            processed_signal = ProcessedSignal(
                original_alert=alert,
                symbol=alert.symbol,
                action=self._normalize_action(alert.action),
                validated_price=alert.price,
                position_size=position_data['size'],
                stop_loss=position_data['stop_loss'],
                take_profit=position_data['take_profit'],
                risk_amount=position_data['risk_amount'],
                reward_amount=position_data['reward_amount'],
                risk_reward_ratio=position_data['risk_reward_ratio'],
                confidence_score=confidence_score,
                validation_status='APPROVED',
                market_phase=alert.market_phase,
                volatility_regime=market_validation['volatility_regime'],
                processing_timestamp=datetime.now(),
                execution_deadline=datetime.now() + timedelta(minutes=self.signal_config['signal_timeout_minutes']),
                metadata={
                    'source_ip': alert.source_ip,
                    'signature_valid': alert.signature_valid,
                    'strategy_name': alert.strategy_name
                }
            )
            
            # Cache alert to prevent duplicates
            self._cache_alert(alert)
            
            # Record success
            self.stats['approved_signals'] += 1
            logger.info(f"Signal approved: {alert.symbol} {alert.action} with {confidence_score:.2f} confidence")
            
            # Process with handlers
            await self._dispatch_signal(processed_signal)
            
            return processed_signal
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            logger.error(f"Error processing alert: {e}")
            return None
    
    def _validate_alert(self, alert: WebhookAlert) -> Dict[str, any]:
        """Validate basic alert structure and content."""
        try:
            # Check required fields
            if not alert.symbol or not alert.action or not alert.price:
                return {'valid': False, 'reason': 'Missing required fields'}
            
            # Validate symbol
            if not self.crypto_pairs.is_pair_supported(alert.symbol):
                return {'valid': False, 'reason': f'Unsupported symbol: {alert.symbol}'}
            
            # Validate action
            valid_actions = ['BUY', 'SELL', 'CLOSE', 'CLOSE_LONG', 'CLOSE_SHORT']
            if alert.action.upper() not in valid_actions:
                return {'valid': False, 'reason': f'Invalid action: {alert.action}'}
            
            # Validate price
            if alert.price <= 0:
                return {'valid': False, 'reason': 'Invalid price'}
            
            # Validate confidence
            if alert.confidence < 0 or alert.confidence > 1:
                return {'valid': False, 'reason': 'Invalid confidence score'}
            
            # Validate stop loss and take profit if provided
            if alert.stop_loss and alert.stop_loss <= 0:
                return {'valid': False, 'reason': 'Invalid stop loss'}
            
            if alert.take_profit and alert.take_profit <= 0:
                return {'valid': False, 'reason': 'Invalid take profit'}
            
            return {'valid': True, 'reason': 'Valid alert'}
            
        except Exception as e:
            return {'valid': False, 'reason': f'Validation error: {e}'}
    
    def _is_duplicate_alert(self, alert: WebhookAlert) -> bool:
        """Check if alert is a duplicate within the cache window."""
        alert_key = f"{alert.symbol}_{alert.action}_{alert.price:.2f}_{alert.market_phase}"
        current_time = datetime.now()
        
        # Clean expired cache entries
        expired_keys = []
        for key, timestamp in self.alert_cache.items():
            if current_time - timestamp > self.cache_expiry:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.alert_cache[key]
        
        # Check for duplicate
        return alert_key in self.alert_cache
    
    def _cache_alert(self, alert: WebhookAlert) -> None:
        """Cache alert to prevent duplicates."""
        alert_key = f"{alert.symbol}_{alert.action}_{alert.price:.2f}_{alert.market_phase}"
        self.alert_cache[alert_key] = datetime.now()
    
    async def _validate_market_conditions(self, alert: WebhookAlert) -> Dict[str, any]:
        """Validate current market conditions for signal execution."""
        try:
            # Get volatility regime for the symbol
            volatility_regime = self.crypto_pairs.get_volatility_factor(alert.symbol)
            
            # Market phase validation
            phase_filters = self.signal_config.get('market_phase_filters', {})
            allowed_phases = phase_filters.get('allowed_phases', [])
            
            if allowed_phases and alert.market_phase not in allowed_phases:
                return {
                    'valid': False,
                    'reason': f'Market phase {alert.market_phase} not allowed',
                    'volatility_regime': volatility_regime
                }
            
            # Block long positions in markdown phase
            if (phase_filters.get('block_markdown_longs', True) and 
                alert.market_phase == 'MARKDOWN' and 
                alert.action == 'BUY'):
                return {
                    'valid': False,
                    'reason': 'Long positions blocked in markdown phase',
                    'volatility_regime': volatility_regime
                }
            
            # Volatility-based filtering
            volatility_filters = self.signal_config.get('volatility_filters', {})
            
            if volatility_regime == 'EXTREME':
                max_extreme_trades = volatility_filters.get('max_extreme_volatility_trades', 1)
                # Here you would check current extreme volatility positions
                # For now, we'll allow it but with higher confidence requirement
                pass
            
            if (volatility_regime == 'LOW' and 
                volatility_filters.get('skip_low_volatility_pairs', True)):
                return {
                    'valid': False,
                    'reason': 'Low volatility pairs filtered',
                    'volatility_regime': volatility_regime
                }
            
            return {
                'valid': True,
                'reason': 'Market conditions acceptable',
                'volatility_regime': volatility_regime
            }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Market validation error: {e}',
                'volatility_regime': 'UNKNOWN'
            }
    
    async def _assess_risk(self, alert: WebhookAlert) -> Dict[str, any]:
        """Assess risk for the proposed trade."""
        try:
            # Check maximum position risk
            max_risk = self.signal_config['max_position_risk']
            
            # Calculate potential risk (simplified)
            if alert.stop_loss:
                risk_per_unit = abs(alert.price - alert.stop_loss)
                risk_percentage = risk_per_unit / alert.price
                
                if risk_percentage > max_risk:
                    return {
                        'approved': False,
                        'reason': f'Risk too high: {risk_percentage:.2%} > {max_risk:.2%}',
                        'risk_percentage': risk_percentage
                    }
            
            # Check risk-reward ratio if take profit provided
            if alert.stop_loss and alert.take_profit:
                risk = abs(alert.price - alert.stop_loss)
                reward = abs(alert.take_profit - alert.price)
                risk_reward_ratio = reward / risk if risk > 0 else 0
                
                min_ratio = self.signal_config['min_risk_reward_ratio']
                if risk_reward_ratio < min_ratio:
                    return {
                        'approved': False,
                        'reason': f'Poor risk/reward: {risk_reward_ratio:.2f} < {min_ratio}',
                        'risk_reward_ratio': risk_reward_ratio
                    }
            
            return {
                'approved': True,
                'reason': 'Risk acceptable',
                'risk_percentage': risk_percentage if 'risk_percentage' in locals() else 0.01,
                'risk_reward_ratio': risk_reward_ratio if 'risk_reward_ratio' in locals() else 2.0
            }
            
        except Exception as e:
            return {
                'approved': False,
                'reason': f'Risk assessment error: {e}',
                'risk_percentage': 0,
                'risk_reward_ratio': 0
            }
    
    async def _calculate_position_sizing(self, alert: WebhookAlert, risk_data: Dict) -> Optional[Dict]:
        """Calculate appropriate position size based on risk management."""
        try:
            # Use risk manager for position sizing
            position_size = self.risk_manager.calculate_position_size(
                symbol=alert.symbol,
                side=alert.action.lower(),
                entry_price=alert.price
            )
            
            # Calculate stop loss if not provided
            stop_loss = alert.stop_loss
            if not stop_loss:
                stop_loss = self.risk_manager.calculate_stop_loss(
                    symbol=alert.symbol,
                    side=alert.action.lower(),
                    entry_price=alert.price
                )
            
            # Calculate take profit if not provided
            take_profit = alert.take_profit
            if not take_profit:
                risk_amount = abs(alert.price - stop_loss)
                if alert.action == 'BUY':
                    take_profit = alert.price + (risk_amount * 2)  # 2:1 ratio
                else:
                    take_profit = alert.price - (risk_amount * 2)
            
            # Calculate amounts
            risk_amount = abs(alert.price - stop_loss) * position_size
            reward_amount = abs(take_profit - alert.price) * position_size
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            return {
                'size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': risk_amount,
                'reward_amount': reward_amount,
                'risk_reward_ratio': risk_reward_ratio
            }
            
        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            return None
    
    def _calculate_confidence_score(self, alert: WebhookAlert, 
                                  market_data: Dict, risk_data: Dict) -> float:
        """Calculate overall confidence score for the signal."""
        try:
            base_confidence = alert.confidence
            
            # Market phase bonus/penalty
            phase_multipliers = {
                'ACCUMULATION': 1.1,
                'MARKUP': 1.0,
                'DISTRIBUTION': 0.9,
                'MARKDOWN': 0.8,
                'TRANSITION': 0.7
            }
            phase_multiplier = phase_multipliers.get(alert.market_phase, 0.8)
            
            # Volatility adjustment
            volatility_regime = market_data.get('volatility_regime', 'MEDIUM')
            volatility_multipliers = {
                'LOW': 0.9,
                'MEDIUM': 1.0,
                'HIGH': 1.05,
                'EXTREME': 0.8  # Higher risk, lower confidence
            }
            volatility_multiplier = volatility_multipliers.get(volatility_regime, 1.0)
            
            # Risk-reward bonus
            risk_reward_ratio = risk_data.get('risk_reward_ratio', 1.0)
            rr_bonus = min(0.1, (risk_reward_ratio - 1.5) * 0.05) if risk_reward_ratio > 1.5 else 0
            
            # Signature validation bonus
            signature_bonus = 0.05 if alert.signature_valid else 0
            
            # Calculate final score
            confidence_score = (
                base_confidence * 
                phase_multiplier * 
                volatility_multiplier + 
                rr_bonus + 
                signature_bonus
            )
            
            return min(1.0, max(0.0, confidence_score))
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return alert.confidence
    
    def _normalize_action(self, action: str) -> str:
        """Normalize action to standard format."""
        action = action.upper().strip()
        
        # Map variations to standard actions
        action_map = {
            'BUY': 'BUY',
            'LONG': 'BUY',
            'SELL': 'SELL',
            'SHORT': 'SELL',
            'CLOSE': 'CLOSE',
            'CLOSE_LONG': 'CLOSE_LONG',
            'CLOSE_SHORT': 'CLOSE_SHORT',
            'EXIT': 'CLOSE'
        }
        
        return action_map.get(action, action)
    
    def _record_rejection(self, reason: str) -> None:
        """Record signal rejection for statistics."""
        self.stats['rejected_signals'] += 1
        logger.debug(f"Signal rejected: {reason}")
    
    async def _dispatch_signal(self, signal: ProcessedSignal) -> None:
        """Dispatch processed signal to handlers."""
        for handler in self.signal_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(signal)
                else:
                    handler(signal)
            except Exception as e:
                logger.error(f"Error in signal handler {handler.__name__}: {e}")
    
    def get_statistics(self) -> Dict[str, any]:
        """Get processing statistics."""
        uptime = datetime.now() - self.stats['last_reset']
        
        return {
            'total_alerts': self.stats['total_alerts'],
            'approved_signals': self.stats['approved_signals'],
            'rejected_signals': self.stats['rejected_signals'],
            'processing_errors': self.stats['processing_errors'],
            'approval_rate': (
                self.stats['approved_signals'] / max(1, self.stats['total_alerts']) * 100
            ),
            'error_rate': (
                self.stats['processing_errors'] / max(1, self.stats['total_alerts']) * 100
            ),
            'uptime_hours': uptime.total_seconds() / 3600,
            'cached_alerts': len(self.alert_cache)
        }
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'total_alerts': 0,
            'approved_signals': 0,
            'rejected_signals': 0,
            'processing_errors': 0,
            'last_reset': datetime.now()
        }
        logger.info("Processing statistics reset")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    async def test_signal_handler(signal: ProcessedSignal):
        """Test signal handler."""
        print("Processed signal: {signal.action} {signal.symbol} at {signal.validated_price}")
        print("Confidence: {signal.confidence_score:.2f}, R/R: {signal.risk_reward_ratio:.2f}")
    
    async def main():
        # Initialize signal processor
        processor = SignalProcessor()
        processor.add_signal_handler(test_signal_handler)
        
        # Create test alert
        test_alert = WebhookAlert(
            timestamp=datetime.now(),
            symbol="BTC/USDT",
            action="BUY",
            price=50000.0,
            market_phase="ACCUMULATION",
            confidence=0.8,
            stop_loss=49000.0,
            take_profit=52000.0,
            source_ip="127.0.0.1",
            signature_valid=True
        )
        
        # Process alert
        result = await processor.process_alert(test_alert)
        
        if result:
            print("Signal processing successful: {result.validation_status}")
        else:
            print("Signal processing failed")
        
        # Print statistics
        stats = processor.get_statistics()
        print("Processing stats: {stats}")
    
    # Run test
    asyncio.run(main())
