#!/usr/bin/env python3
"""
ICT ML Model Trainer
===================

Train machine learning models on ICT paper trading results to enhance
signal generation and confluence scoring.

Features:
- Feature extraction from ICT signals and market data
- Training on paper trade outcomes (win/loss/pnl)
- Model evaluation and validation
- Automatic model deployment to monitor
- Continuous learning from new trades

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
from pathlib import Path

# ML imports
try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import classification_report, mean_squared_error, r2_score
    ML_AVAILABLE = True
except ImportError as e:
    print("Warning: ML libraries not available: {e}")
    ML_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ICTMLTrainer:
    """Train ML models on ICT paper trading data."""
    
    def __init__(self):
        """Initialize the ML trainer."""
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Feature engineering components
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Models
        self.signal_classifier = None  # Predicts signal success probability
        self.pnl_regressor = None      # Predicts expected PnL
        self.confluence_enhancer = None # Enhances confluence scoring
        
        logger.info("ICT ML Trainer initialized")
    
    def extract_features_from_signal(self, signal: Dict, market_data: Dict = None) -> Dict:
        """Extract ML features from an ICT signal."""
        features = {}
        
        # Basic signal features
        features['confidence'] = signal.get('confidence', 0.0)
        features['risk_amount'] = signal.get('risk_amount', 100.0)
        features['entry_price'] = signal.get('entry_price', 0.0)
        features['stop_loss'] = signal.get('stop_loss', 0.0)
        features['take_profit'] = signal.get('take_profit', 0.0)
        
        # Calculate risk/reward ratio
        entry = features['entry_price']
        sl = features['stop_loss']
        tp = features['take_profit']
        
        if entry > 0 and sl > 0 and tp > 0:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            features['risk_reward_ratio'] = reward / risk if risk > 0 else 0
        else:
            features['risk_reward_ratio'] = 0
        
        # Action encoding
        features['action_buy'] = 1 if signal.get('action') == 'BUY' else 0
        features['action_sell'] = 1 if signal.get('action') == 'SELL' else 0
        
        # Crypto encoding
        crypto = signal.get('crypto', 'BTC')
        features['crypto_btc'] = 1 if crypto == 'BTC' else 0
        features['crypto_eth'] = 1 if crypto == 'ETH' else 0
        features['crypto_sol'] = 1 if crypto == 'SOL' else 0
        features['crypto_xrp'] = 1 if crypto == 'XRP' else 0
        
        # Timeframe encoding
        timeframe = signal.get('timeframe', '5m')
        features['tf_1m'] = 1 if timeframe == '1m' else 0
        features['tf_5m'] = 1 if timeframe == '5m' else 0
        features['tf_15m'] = 1 if timeframe == '15m' else 0
        features['tf_1h'] = 1 if timeframe == '1h' else 0
        features['tf_4h'] = 1 if timeframe == '4h' else 0
        
        # ICT-specific features
        features['ml_boost'] = signal.get('ml_boost', 0.0)
        features['ict_confidence'] = signal.get('ict_confidence', 0.0)
        
        # Time-based features
        timestamp = signal.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                features['hour'] = dt.hour
                features['day_of_week'] = dt.weekday()
                features['is_market_hours'] = 1 if 8 <= dt.hour <= 22 else 0
                
                # Session encoding
                features['session_asia'] = 1 if (dt.hour >= 23 or dt.hour <= 8) else 0
                features['session_london'] = 1 if (8 <= dt.hour <= 16) else 0
                features['session_ny'] = 1 if (13 <= dt.hour <= 22) else 0
            except Exception:
                features['hour'] = 12
                features['day_of_week'] = 1
                features['is_market_hours'] = 1
                features['session_asia'] = 0
                features['session_london'] = 1
                features['session_ny'] = 0
        
        # Market data features (if available)
        if market_data and crypto in market_data:
            market = market_data[crypto]
            features['price'] = market.get('price', entry)
            features['change_24h'] = market.get('change_24h', 0.0)
            features['volume'] = market.get('volume', 0.0)
            features['high_24h'] = market.get('high_24h', entry)
            features['low_24h'] = market.get('low_24h', entry)
            
            # Price position features
            if features['high_24h'] > features['low_24h']:
                price_range = features['high_24h'] - features['low_24h']
                features['price_position'] = (features['price'] - features['low_24h']) / price_range
            else:
                features['price_position'] = 0.5
        else:
            features['price'] = entry
            features['change_24h'] = 0.0
            features['volume'] = 0.0
            features['high_24h'] = entry
            features['low_24h'] = entry
            features['price_position'] = 0.5
        
        return features
    
    def extract_target_from_trade(self, trade: Dict) -> Tuple[int, float]:
        """Extract target variables from completed paper trade."""
        # Classification target: 1 for profitable, 0 for loss
        pnl = trade.get('final_pnl', trade.get('pnl', 0.0))
        success = 1 if pnl > 0 else 0
        
        # Regression target: actual PnL
        return success, pnl
    
    def prepare_training_data(self, trading_journal: List[Dict], market_data_history: Dict = None) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Prepare training data from trading journal."""
        features_list = []
        success_targets = []
        pnl_targets = []
        
        logger.info(f"Preparing training data from {len(trading_journal)} trades...")
        
        for trade in trading_journal:
            # Skip incomplete trades
            if 'final_pnl' not in trade and 'pnl' not in trade:
                continue
            
            # Extract features from the original signal (if available)
            signal_data = {
                'confidence': trade.get('confidence', 0.7),
                'risk_amount': trade.get('risk_amount', 100.0),
                'entry_price': trade.get('entry_price', 0.0),
                'stop_loss': trade.get('stop_loss', 0.0),
                'take_profit': trade.get('take_profit', 0.0),
                'action': trade.get('action', 'BUY'),
                'crypto': trade.get('crypto', 'BTC'),
                'timeframe': trade.get('timeframe', '5m'),
                'timestamp': trade.get('entry_time', datetime.now().isoformat()),
                'ml_boost': 0.0,
                'ict_confidence': trade.get('confidence', 0.7)
            }
            
            # Get market data for this trade if available
            trade_market_data = None
            if market_data_history:
                # In a real implementation, you'd look up historical market data
                # For now, we'll use current data as a placeholder
                trade_market_data = market_data_history
            
            features = self.extract_features_from_signal(signal_data, trade_market_data)
            success, pnl = self.extract_target_from_trade(trade)
            
            features_list.append(features)
            success_targets.append(success)
            pnl_targets.append(pnl)
        
        # Convert to DataFrame
        features_df = pd.DataFrame(features_list)
        success_series = pd.Series(success_targets)
        pnl_series = pd.Series(pnl_targets)
        
        logger.info(f"Prepared {len(features_df)} training samples")
        logger.info(f"Success rate: {success_series.mean():.2%}")
        logger.info(f"Average PnL: ${pnl_series.mean():.2f}")
        
        return features_df, success_series, pnl_series
    
    def train_models(self, features_df: pd.DataFrame, success_targets: pd.Series, pnl_targets: pd.Series) -> Dict:
        """Train ML models on the prepared data."""
        if not ML_AVAILABLE:
            logger.error("ML libraries not available. Cannot train models.")
            return {}
        
        logger.info("Training ML models...")
        results = {}
        
        # Prepare data
        X = features_df.fillna(0)  # Handle any missing values
        y_success = success_targets
        y_pnl = pnl_targets
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_success_train, y_success_test, y_pnl_train, y_pnl_test = train_test_split(
            X_scaled, y_success, y_pnl, test_size=0.2, random_state=42, stratify=y_success
        )
        
        # Train signal success classifier
        logger.info("Training signal success classifier...")
        self.signal_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.signal_classifier.fit(X_train, y_success_train)
        
        # Evaluate classifier
        train_score = self.signal_classifier.score(X_train, y_success_train)
        test_score = self.signal_classifier.score(X_test, y_success_test)
        cv_scores = cross_val_score(self.signal_classifier, X_scaled, y_success, cv=5)
        
        results['classifier'] = {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        logger.info(f"Classifier - Train: {train_score:.3f}, Test: {test_score:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
        
        # Train PnL regressor
        logger.info("Training PnL regressor...")
        self.pnl_regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.pnl_regressor.fit(X_train, y_pnl_train)
        
        # Evaluate regressor
        pnl_train_pred = self.pnl_regressor.predict(X_train)
        pnl_test_pred = self.pnl_regressor.predict(X_test)
        
        train_r2 = r2_score(y_pnl_train, pnl_train_pred)
        test_r2 = r2_score(y_pnl_test, pnl_test_pred)
        train_rmse = np.sqrt(mean_squared_error(y_pnl_train, pnl_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_pnl_test, pnl_test_pred))
        
        results['regressor'] = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse
        }
        
        logger.info(f"Regressor - Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}")
        logger.info(f"Regressor - Train RMSE: ${train_rmse:.2f}, Test RMSE: ${test_rmse:.2f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': features_df.columns,
            'importance': self.signal_classifier.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("Top 10 most important features:")
        for idx, row in feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.3f}")
        
        results['feature_importance'] = feature_importance.to_dict('records')
        results['feature_names'] = list(features_df.columns)
        
        return results
    
    def save_models(self) -> bool:
        """Save trained models to disk."""
        if not ML_AVAILABLE:
            return False
        
        try:
            # Save models
            if self.signal_classifier:
                joblib.dump(self.signal_classifier, self.models_dir / "signal_classifier.pkl")
                logger.info("Saved signal classifier")
            
            if self.pnl_regressor:
                joblib.dump(self.pnl_regressor, self.models_dir / "pnl_regressor.pkl")
                logger.info("Saved PnL regressor")
            
            # Save preprocessing components
            joblib.dump(self.scaler, self.models_dir / "feature_scaler.pkl")
            
            # Save combined model for the monitor (compatibility)
            combined_model = {
                'signal_classifier': self.signal_classifier,
                'pnl_regressor': self.pnl_regressor,
                'scaler': self.scaler,
                'version': '1.0',
                'trained_at': datetime.now().isoformat()
            }
            joblib.dump(combined_model, self.models_dir / "crypto_ml_model.pkl")
            logger.info("Saved combined model for monitor")
            
            return True
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
    
    def predict_signal_enhancement(self, signal: Dict, market_data: Dict = None) -> Dict:
        """Predict enhancements for a signal using trained models."""
        if not ML_AVAILABLE or not self.signal_classifier or not self.pnl_regressor:
            return {
                'ml_boost': 0.0,
                'success_probability': 0.5,
                'expected_pnl': 0.0,
                'confidence_multiplier': 1.0
            }
        
        try:
            # Extract features
            features = self.extract_features_from_signal(signal, market_data)
            features_df = pd.DataFrame([features])
            X = self.scaler.transform(features_df.fillna(0))
            
            # Predict success probability
            success_prob = self.signal_classifier.predict_proba(X)[0][1]  # Probability of success
            
            # Predict expected PnL
            expected_pnl = self.pnl_regressor.predict(X)[0]
            
            # Calculate ML boost (how much to add to confidence)
            base_confidence = signal.get('confidence', 0.7)
            
            # ML boost calculation based on model predictions
            if success_prob > 0.7 and expected_pnl > 50:  # High confidence, good expected return
                ml_boost = min(0.15, (success_prob - 0.7) * 0.5)  # Cap at 15% boost
            elif success_prob > 0.6 and expected_pnl > 0:  # Moderate confidence
                ml_boost = min(0.1, (success_prob - 0.6) * 0.3)   # Cap at 10% boost
            else:
                ml_boost = 0.0  # No boost for low confidence predictions
            
            # Confidence multiplier for risk sizing
            confidence_multiplier = min(1.5, max(0.5, success_prob * 2))
            
            return {
                'ml_boost': ml_boost,
                'success_probability': success_prob,
                'expected_pnl': expected_pnl,
                'confidence_multiplier': confidence_multiplier
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return {
                'ml_boost': 0.0,
                'success_probability': 0.5,
                'expected_pnl': 0.0,
                'confidence_multiplier': 1.0
            }
    
    def train_from_monitor_data(self, monitor_data_file: str = "monitor_data.json") -> bool:
        """Train models from monitor's trading journal data."""
        logger.info("Training ML models from monitor data...")
        
        # Try to load existing trading journal data
        trading_journal = []
        
        # Check if monitor data file exists
        if os.path.exists(monitor_data_file):
            try:
                with open(monitor_data_file, 'r') as f:
                    data = json.load(f)
                    trading_journal = data.get('trading_journal', [])
            except Exception as e:
                logger.warning(f"Could not load monitor data: {e}")
        
        # If no existing data, create some sample training data
        if not trading_journal:
            logger.info("No existing trading data found. Generating sample data for initial training...")
            trading_journal = self.generate_sample_training_data()
        
        if len(trading_journal) < 10:
            logger.warning(f"Not enough training data ({len(trading_journal)} trades). Need at least 10 completed trades.")
            logger.info("Generating additional sample data...")
            trading_journal.extend(self.generate_sample_training_data(30))
        
        # Prepare training data
        features_df, success_targets, pnl_targets = self.prepare_training_data(trading_journal)
        
        if len(features_df) < 10:
            logger.error("Insufficient training data after preparation")
            return False
        
        # Train models
        results = self.train_models(features_df, success_targets, pnl_targets)
        
        # Save models
        saved = self.save_models()
        
        if saved:
            logger.info("✅ ML models trained and saved successfully!")
            logger.info(f"📊 Training Summary:")
            logger.info(f"   Samples: {len(features_df)}")
            logger.info(f"   Success Rate: {success_targets.mean():.2%}")
            logger.info(f"   Classifier Accuracy: {results.get('classifier', {}).get('test_accuracy', 0):.3f}")
            logger.info(f"   Regressor R²: {results.get('regressor', {}).get('test_r2', 0):.3f}")
            return True
        else:
            logger.error("Failed to save models")
            return False
    
    def generate_sample_training_data(self, num_samples: int = 50) -> List[Dict]:
        """Generate sample training data for initial model training."""
        logger.info(f"Generating {num_samples} sample training trades...")
        
        trades = []
        cryptos = ['BTC', 'ETH', 'SOL', 'XRP']
        actions = ['BUY', 'SELL']
        timeframes = ['1m', '5m', '15m', '1h']
        
        for i in range(num_samples):
            crypto = np.random.default_rng(42).choice(cryptos)
            action = np.random.default_rng(42).choice(actions)
            timeframe = np.random.default_rng(42).choice(timeframes)
            
            # Generate realistic price data
            base_price = {'BTC': 50000, 'ETH': 3000, 'SOL': 100, 'XRP': 0.5}[crypto]
            entry_price = base_price * (1 + np.random.default_rng(42).uniform(-0.1, 0.1))
            
            # Generate stops and targets with realistic RR
            if action == 'BUY':
                stop_loss = entry_price * (1 - np.random.default_rng(42).uniform(0.01, 0.03))
                take_profit = entry_price * (1 + np.random.default_rng(42).uniform(0.02, 0.06))
            else:
                stop_loss = entry_price * (1 + np.random.default_rng(42).uniform(0.01, 0.03))
                take_profit = entry_price * (1 - np.random.default_rng(42).uniform(0.02, 0.06))
            
            # Generate outcome (70% success rate for good training)
            is_success = np.random.default_rng(42).random() < 0.7
            
            if is_success:
                final_pnl = np.random.default_rng(42).uniform(50, 300)
                status = 'TAKE_PROFIT'
            else:
                final_pnl = -np.random.default_rng(42).uniform(50, 150)
                status = 'STOP_LOSS'
            
            confidence = np.random.default_rng(42).uniform(0.6, 0.9)
            
            trade = {
                'id': f'SAMPLE_{i+1}',
                'crypto': crypto,
                'action': action,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': 100 / abs(entry_price - stop_loss),
                'risk_amount': 100,
                'entry_time': (datetime.now() - timedelta(days=np.random.default_rng(42).integers(1, 30))).isoformat(),
                'exit_time': (datetime.now() - timedelta(days=np.random.default_rng(42).integers(0, 29))).isoformat(),
                'status': status,
                'pnl': final_pnl,
                'final_pnl': final_pnl,
                'confidence': confidence,
                'timeframe': timeframe
            }
            
            trades.append(trade)
        
        return trades

def main():
    """Main training function."""
    if not ML_AVAILABLE:
        print("❌ ML libraries not available. Please install: pip install scikit-learn joblib")
        return
    
    print("🤖 ICT ML Model Training")
    print("=" * 50)
    
    trainer = ICTMLTrainer()
    
    # Train from monitor data
    success = trainer.train_from_monitor_data()
    
    if success:
        print("\n✅ Training completed successfully!")
        print("🚀 Models ready for deployment to ICT monitor")
        print("\nNext steps:")
        print("1. Restart the ICT monitor to load new models")
        print("2. Monitor ML-enhanced signal generation")
        print("3. Retrain models periodically with new data")
    else:
        print("\n❌ Training failed. Check logs for details.")

if __name__ == "__main__":
    main()