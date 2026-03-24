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

Freqtrade will connect to Kraken. No API key is required for paper trading (dry_run mode).

## Download historical data for backtesting

Kraken requires `--dl-trades` to build historical OHLCV data — there is no shortcut.
This downloads raw trades and converts them to candles. It is slow (~1 hour per 6 months)
but only needs to be done once. Run it overnight.

```powershell
# Full dataset back to Jan 2023 (run once overnight — ~4-5 hours)
freqtrade download-data --config executor/config.json --timerange 20230101- --timeframe 15m --dl-trades

# Refresh to latest candle (run anytime — appends only new data, much faster)
freqtrade download-data --config executor/config.json --timerange 20230101- --timeframe 15m --dl-trades
```

Freqtrade detects existing data and only downloads the missing gap — re-running will
not re-download candles you already have. Data is stored in `user_data/data/kraken/`.

## Run a backtest

Use `research.py` for all backtesting — it runs all three windows and applies
overfitting guardrails automatically:

```powershell
python research.py backtest VariantAStrategy   # single strategy, all 3 windows
python research.py roster                      # all active strategies, then leaderboard
python research.py compare                     # leaderboard only (no new backtests)
```

Direct freqtrade command (single window, no guardrails):

```powershell
freqtrade backtesting --config executor/config.json --strategy BaselineStrategy --timerange 20250901-20251130
```

## Security reminders

- Never add real API keys until Layer 6 is reached and justified
- If a key is ever added, it must be read-only with zero trading permissions
- Keys go in `.env` only — never in `config.json` or anywhere in the repo
- Run `git status` before every commit to confirm no secrets are staged
