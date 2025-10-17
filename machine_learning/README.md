# Machine Learning Components

This directory contains all ML-related files for crypto price prediction.

## Scripts (`scripts/`)

- `ml_predictor.py` - Main ML predictor with 15-minute price forecasting

## Models (`models/`)

- `crypto_predictor_features.pkl` - Trained feature transformer
- `crypto_predictor_model.pkl` - Gradient boosting model
- `crypto_predictor_scaler.pkl` - Data scaler for normalization

## Features

- 15-minute price prediction horizon
- Technical indicator features (RSI, MACD, EMA, Bollinger Bands)
- Gradient boosting algorithm
- Real-time prediction capabilities

## Usage

The ML predictor is integrated into the main trading system for enhanced signal confidence.
