# Setup Guide

## Prerequisites

- Python 3.10+
- Git

## First-time setup

```powershell
# Clone the repo
git clone https://github.com/f1cklepickle/crypto-strategy-lab.git
cd crypto-strategy-lab

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install freqtrade pydantic

# Copy env file — never commit .env
copy .env.example .env
```

## Initialize Freqtrade user data directory

This creates the `user_data/` folder Freqtrade needs at runtime.
It is gitignored — run this once after cloning.

```powershell
freqtrade create-userdir --userdir user_data
```

## Validate the schema

```powershell
python schemas/validate_schema.py
```

## Run the bot in dry-run (paper) mode

```powershell
freqtrade trade --config executor/config.json --strategy BaselineStrategy
```

Freqtrade will connect to Binance public market data.
No API key is required for paper trading.

## Download historical data for backtesting

```powershell
freqtrade download-data --config executor/config.json --days 90 --timeframe 1h
```

## Run a backtest

```powershell
freqtrade backtesting --config executor/config.json --strategy BaselineStrategy --timerange 20250101-20260101
```

## Security reminders

- Never add real API keys until Layer 6 is reached and justified
- If a key is ever added, it must be read-only with zero trading permissions
- Keys go in `.env` only — never in `config.json` or anywhere in the repo
- Run `git status` before every commit to confirm no secrets are staged
