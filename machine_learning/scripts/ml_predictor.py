"""
ML-based price prediction system for crypto trading
Integrates with TradingView webhook data to predict future movements
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import requests
import ta
from datetime import datetime, timedelta
import json

class CryptoPricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.prediction_horizon = 15  # minutes
        
    def fetch_historical_data(self, symbol="BTCUSDT", interval="1m", limit=1000):
        """Fetch historical data from Binance API"""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to numeric
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def create_features(self, df):
        """Create technical indicator features for ML"""
        features = df.copy()
        
        # Price-based features
        features['price_change'] = df['close'].pct_change()
        features['high_low_ratio'] = df['high'] / df['low']
        features['close_open_ratio'] = df['close'] / df['open']
        
        # Technical indicators
        features['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        features['macd'] = ta.trend.MACD(df['close']).macd()
        features['macd_signal'] = ta.trend.MACD(df['close']).macd_signal()
        features['bb_upper'] = ta.volatility.BollingerBands(df['close']).bollinger_hband()
        features['bb_lower'] = ta.volatility.BollingerBands(df['close']).bollinger_lband()
        features['bb_middle'] = ta.volatility.BollingerBands(df['close']).bollinger_mavg()
        
        # Moving averages
        features['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
        features['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
        features['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
        
        # Volume indicators
        features['volume_sma'] = ta.trend.SMAIndicator(df['volume'], window=20).sma_indicator()
        features['volume_ratio'] = df['volume'] / features['volume_sma']
        
        # Volatility
        features['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        
        # Time-based features
        features['hour'] = features.index.hour
        features['day_of_week'] = features.index.dayofweek
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            features[f'close_lag_{lag}'] = df['close'].shift(lag)
            features[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            features[f'rsi_lag_{lag}'] = features['rsi'].shift(lag)
        
        return features
    
    def prepare_prediction_data(self, df):
        """Prepare features and targets for ML model"""
        features_df = self.create_features(df)
        
        # Target: future price change percentage
        target = df['close'].shift(-self.prediction_horizon).pct_change()
        
        # Remove rows with NaN values
        valid_indices = ~(features_df.isnull().any(axis=1) | target.isnull())
        features_clean = features_df[valid_indices]
        target_clean = target[valid_indices]
        
        # Select numerical features only
        numerical_features = features_clean.select_dtypes(include=[np.number])
        
        return numerical_features, target_clean
    
    def train_model(self, symbol="BTCUSDT"):
        """Train the ML model on historical data"""
        print(f"🤖 Training ML model for {symbol}...")
        
        # Fetch historical data
        df = self.fetch_historical_data(symbol, limit=5000)
        if df is None:
            return False
        
        # Prepare features and targets
        X, y = self.prepare_prediction_data(df)
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train ensemble model
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        print(f"✅ Model trained successfully!")
        print(f"📊 Training Score: {train_score:.4f}")
        print(f"🎯 Test Score: {test_score:.4f}")
        
        # Save model
        self.save_model()
        return True
    
    def predict_future_movement(self, current_data):
        """Predict future price movement based on current data"""
        if self.model is None:
            return None
        
        try:
            # Create features from current data
            features_df = self.create_features(current_data)
            latest_features = features_df.iloc[-1:][self.feature_names]
            
            # Scale features
            features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            
            # Calculate confidence based on recent model performance
            confidence = min(abs(prediction) * 10, 1.0)  # Simple confidence metric
            
            return {
                'predicted_change_pct': prediction * 100,  # Convert to percentage
                'direction': 'UP' if prediction > 0 else 'DOWN',
                'confidence': confidence,
                'prediction_horizon_minutes': self.prediction_horizon,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return None
    
    def save_model(self):
        """Save trained model and scaler"""
        joblib.dump(self.model, 'crypto_predictor_model.pkl')
        joblib.dump(self.scaler, 'crypto_predictor_scaler.pkl')
        joblib.dump(self.feature_names, 'crypto_predictor_features.pkl')
    
    def load_model(self):
        """Load pre-trained model and scaler"""
        try:
            self.model = joblib.load('crypto_predictor_model.pkl')
            self.scaler = joblib.load('crypto_predictor_scaler.pkl')
            self.feature_names = joblib.load('crypto_predictor_features.pkl')
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

# Enhanced webhook handler with ML predictions
def enhanced_webhook_handler(tradingview_data):
    """Enhanced webhook handler that includes ML predictions"""
    predictor = CryptoPricePredictor()
    
    # Load or train model
    if not predictor.load_model():
        print("🔄 No existing model found. Training new model...")
        if not predictor.train_model(tradingview_data.get('symbol', 'BTCUSDT')):
            print("❌ Failed to train model")
            return tradingview_data
    
    # Fetch recent data for prediction
    symbol = tradingview_data.get('symbol', 'BTCUSDT')
    recent_data = predictor.fetch_historical_data(symbol, limit=100)
    
    if recent_data is not None:
        # Get ML prediction
        prediction = predictor.predict_future_movement(recent_data)
        
        if prediction:
            # Add prediction to webhook data
            tradingview_data['ml_prediction'] = prediction
            
            print(f"🔮 ML Prediction for {symbol}:")
            print(f"   Direction: {prediction['direction']}")
            print(f"   Expected Change: {prediction['predicted_change_pct']:.2f}%")
            print(f"   Confidence: {prediction['confidence']:.2f}")
            print(f"   Time Horizon: {prediction['prediction_horizon_minutes']} minutes")
    
    return tradingview_data

if __name__ == "__main__":
    # Example usage - train model for BTCUSDT
    predictor = CryptoPricePredictor()
    predictor.train_model("BTCUSDT")
    
    # Test prediction
    test_data = predictor.fetch_historical_data("BTCUSDT", limit=100)
    if test_data is not None:
        prediction = predictor.predict_future_movement(test_data)
        print(f"🔮 Test Prediction: {prediction}")