"""
Crypto Trading Algorithm Setup Configuration
A professional trading algorithm for cryptocurrency markets.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="crypto-trading-algorithm",
    version="1.0.0",
    author="Trading Algorithm Team",
    description="Professional cryptocurrency trading algorithm with market phase prediction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/crypto-trading-algorithm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "trading": [
            "ccxt>=2.0.0",
            "python-binance>=1.0.16",
            "websocket-client>=1.4.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
            "tensorflow>=2.8.0",
            "ta-lib>=0.4.25",
        ],
        "notifications": [
            "discord-webhook>=1.0.0",
            "telegram-send>=0.34",
            "twilio>=7.16.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "crypto-trading=src.main:main",
            "crypto-backtest=scripts.backtest_runner:main",
            "crypto-setup=scripts.deployment_setup:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.md", "*.txt"],
    },
    keywords=[
        "cryptocurrency",
        "trading",
        "algorithm",
        "bybit",
        "market prediction",
        "technical analysis",
        "backtesting",
        "risk management"
    ],
    project_urls={
        "Documentation": "https://github.com/yourusername/crypto-trading-algorithm/docs",
        "Bug Reports": "https://github.com/yourusername/crypto-trading-algorithm/issues",
        "Source": "https://github.com/yourusername/crypto-trading-algorithm",
    },
)
