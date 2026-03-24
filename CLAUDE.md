# CipherPickle Research Platform — AI Session Context

This file is the single source of truth for bootstrapping any AI session on this project.
Read this before doing anything else.

---

## What This Project Is

CipherPickle (CP) is a systematic crypto trading research platform built on Freqtrade.
The goal is to develop, validate, and deploy trading strategies through a disciplined
hypothesis-driven process — never deploying a strategy live until it has proven itself
across three independent data windows.

The system starts with paper trading (dry_run), runs multiple strategy variants in parallel,
logs all performance, and promotes winners to live capital once consistency is proven.

Bot naming is a One Piece CP0 reference: CP-0, CP-1, CP-2, etc.

---

## Repository

**GitHub:** https://github.com/f1cklepickle/crypto-strategy-lab
**Branch strategy:** feature branches (`feat/issue-X-description`) → PR → squash merge → delete
**Git rule:** The assistant edits files. The user runs all git commands.

---

## Current Bot Roster

| Bot  | Strategy          | Status              | Port | Notes                          |
|------|-------------------|---------------------|------|--------------------------------|
| CP-0 | BaselineStrategy  | 🔵 Frozen milestone | 8080 | Never modify. Original control |
| CP-1 | VariantAStrategy  | 🟢 Paper trading    | 8081 | First validated challenger     |

Both bots run simultaneously. FreqUI at `localhost:8080` — add `localhost:8081` as second bot.

**Rule:** When a bot is deployed and running, its strategy file is frozen. New hypotheses
always create a new version file, never modify a deployed file in place.

---

## Exchange & Infrastructure

- **Exchange:** Kraken (US-compatible)
- **Timeframe:** 15m across all strategies
- **Pairs:** BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT, ADA/USDT, LINK/USDT
- **Mode:** dry_run (paper trading), 1500 USDT wallet per bot
- **Python:** 3.13 venv at `.\venv\` — always activate before running freqtrade
- **OS:** Windows — user runs all terminal commands

---

## Strategy Development Methodology

### Data Zones (never change these splits)
- **Training:** Sep 1 – Nov 30, 2025 (`--timerange 20250901-20251130`)
- **Validation:** Dec 1, 2025 – Feb 28, 2026 (`--timerange 20251201-20260228`)
- **Holdout:** Mar 1, 2026 – present (`--timerange 20260301-`)

### Rules
1. All new hypotheses are tested on **training data only** first
2. Only run validation if training shows improvement over baseline
3. Only run holdout if validation holds the improvement
4. A strategy must beat the current champion on **both validation and holdout** to be promoted
5. One hypothesis per version — never stack multiple changes at once
6. Trade count dropping is fine. Win rate and PnL% improvement is what matters.

### Backtest commands
```powershell
.\venv\Scripts\activate
freqtrade backtesting --config executor/config.json --strategy StrategyName --timerange 20250901-20251130
```

### Result reporting format (paste to AI for analysis)
```
A v4: [71] | [23.9%] | [-3.13%] | [3.50%] (training)
A v4: [73] | [19.2%] | [-3.53%] | [3.61%] (validation)
A v4: [25] | [24.0%] | [-1.15%] | [1.15%] (holdout)
```
Format: `[trades] | [win%] | [PnL%] | [DD%] (window)`

---

## Strategy Files

### BaselineStrategy.py — CP-0 (FROZEN)
- EMA 20/50 crossover, RSI 35-65
- Stop -3%, no trailing stop
- The permanent control. Never touch this file.

### VariantAStrategy.py — CP-1 (FROZEN)
- EMA 10/30 crossover, RSI 40-60
- Stop -2.5%, trailing stop (positive=1.5%, offset=2%)
- 200 EMA trend gate: only enter if close > EMA(200)
- Volume confirmation: only enter if volume > 20-period average
- `startup_candle_count = 210`

**Validated results:**
| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 71 | 23.9% | -3.13% | 3.50% |
| Validation | 73 | 19.2% | -3.53% | 3.61% |
| Holdout | 25 | 24.0% | -1.15% | 1.15% |

### VariantCStrategy.py — Deprioritized
- EMA 15/40, RSI 30-70, stop -3.5%, trailing stop
- 200 EMA trend gate added (Hypothesis 2)
- Did not consistently beat baseline on validation. Parked.

---

## Hypothesis History (full log in docs/hypothesis_results.md)

| Hypothesis | Change | Result |
|------------|--------|--------|
| H1 | Trailing stop on A and C | Minor improvement, not sufficient alone |
| H2 | 200 EMA trend gate | Halved losses vs baseline. Held on validation |
| H3 | Volume confirmation (A only) | Near-breakeven in bear market. Validated ✅ |

**Next candidate hypotheses (not yet tested):**
- H4: MACD confirmation — only enter if MACD > signal line
- H5: Minimum candles above EMA-200 before entry (avoid false breakouts)
- H6: Tighter RSI window (45-55) to reduce noise further

---

## File Structure

```
crypto-strategy-lab/
├── strategies/
│   ├── BaselineStrategy.py       # CP-0 — FROZEN
│   ├── VariantAStrategy.py       # CP-1 — FROZEN
│   └── VariantCStrategy.py       # Deprioritized
├── executor/
│   ├── config.json               # CP-0 live config — GITIGNORED
│   ├── config.example.json       # CP-0 safe template
│   ├── config_cp1.json           # CP-1 live config — GITIGNORED
│   └── config_cp1.example.json   # CP-1 safe template
├── schemas/
│   ├── trade_log_schema.py       # Pydantic v2 TradeRecord model
│   └── adapter.py                # SQLite reader + Kraken OHLCV fetcher
├── metrics/
│   └── report.py                 # Layer 0 validation report
├── variants/
│   ├── variant_a.json
│   ├── variant_b.json
│   └── variant_c.json
├── docs/
│   ├── setup.md                  # Environment setup guide
│   └── hypothesis_results.md     # Full backtest results log
├── .gitignore                    # Excludes all config.json files
├── .gitattributes                # LF line endings enforced
└── CLAUDE.md                     # This file
```

---

## Config Credentials (gitignored — never commit)

Both config.json files are gitignored. Credentials:
- **Username:** f1cklepickle
- **Password:** poiuPOIU0809!
- **CP-0 JWT:** b0ff581f34d3888472bf32fa3336b56540eab6a4b719292bd6241f946dd3a9ff
- **CP-0 ws_token:** 80d9a15cf26d9587f226e904c95f58c4c06ad5ecae478ab31d05c219e218e522
- **CP-1 JWT:** 2edee52ab1ec78eac2a4cdafe074b8e5c7dc8d072d56c7d15991d162a06e8960
- **CP-1 ws_token:** a07ec6dba0b853d4fc6c0de3b555d597b844996f2cf9b4030b911918b1d03ae3

---

## Starting the Bots

```powershell
# Terminal 1 — CP-0
cd C:\Users\Harrison Bruhl\dev\crypto-strategy-lab
.\venv\Scripts\activate
freqtrade trade --config executor/config.json --strategy BaselineStrategy

# Terminal 2 — CP-1
cd C:\Users\Harrison Bruhl\dev\crypto-strategy-lab
.\venv\Scripts\activate
freqtrade trade --config executor/config_cp1.json --strategy VariantAStrategy
```

FreqUI: `http://localhost:8080` — add CP-1 via bot selector at `http://localhost:8081`

---

## Planned Features (not yet built)

### research.py — Batch Backtest Runner (HIGH PRIORITY)
Single command runs all three windows and prints formatted output:
```powershell
python research.py backtest VariantAStrategy    # runs train + val + holdout
python research.py compare                      # leaderboard of all strategies
python research.py branch VariantAStrategy      # scaffolds next version file
```

### Strategy Leaderboard Dashboard
Local HTML file reading result JSONs — shows all strategy versions ranked by
validation PnL with live bot status pulled from FreqUI API.

### Docker Compose Multi-Bot
One command starts all active bots. Adding a new CP just means adding a config entry.

### Hypothesis Template Generator
`python research.py branch VariantAStrategy` creates `VariantAStrategy_v5.py` with
parent rules pre-loaded and docstring slot for next hypothesis.

---

## Promotion Rules (how a new bot earns a CP number)

1. Run on training data — must beat current champion
2. Run on validation — improvement must hold
3. Run on holdout — improvement must hold
4. Win rate consistent across all three windows (not just lucky on one)
5. Drawdown controlled (not just better PnL with worse DD)
6. If all pass → assign next CP number, create config, deploy paper trading
7. Previous champion becomes frozen milestone, stays running for comparison

---

## Open GitHub Issues (check repo for current state)

- Issue #24 — research.py batch backtest runner (HIGH PRIORITY)
- Issue #25 — Overfitting guardrails for backtest runner
- Issue #26 — Historical data download + extended backtest windows
- Issue #27 — Pre-wire sentiment fields in TradeRecord schema
- Issue #16 — Live bot leaderboard dashboard
- Issues #18-21 — Security hardening (pre-live-capital, not urgent)

---

## Key Decisions Made

- **Long-only** strategies only (no shorts) — Kraken spot trading
- **15m timeframe** across all bots for fair comparison
- **Fixed pairs** — same 6 pairs across all strategies
- **1500 USDT** dry wallet per bot
- **Hypothesis-one-at-a-time** — no stacking changes, clean signal isolation
- **User runs all git commands** — assistant edits files only
- **config.json always gitignored** — credentials never reach GitHub

---

## GitHub Templates

### Issue template
Use this format for all new issues. Title format: `type(scope): short description`
Types: `feat`, `fix`, `chore`, `docs`. Scope examples: `research`, `schema`, `data`, `dashboard`, `security`.

```markdown
## Summary
[One paragraph: what this is and why it matters.]

## [Context heading — e.g. Implementation / Architecture / Why this matters]
[Technical details, tables, code examples, rationale. Add more sections if needed.]

## Acceptance Criteria
- [ ] Specific, testable criterion
- [ ] Specific, testable criterion
- [ ] Specific, testable criterion
```

### PR template
Use this format for all pull requests. Title format matches the issue it closes.

```markdown
## Summary
- What was changed or added (bullet)
- What was changed or added (bullet)

## Test plan
- [ ] Thing verified manually or via script
- [ ] Thing verified manually or via script

🤖 Generated with Claude
```
