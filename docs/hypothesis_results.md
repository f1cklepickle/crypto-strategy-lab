# CipherPickle — Hypothesis Results Log

Data zones:
- **Training**: Sep 1 – Nov 30, 2025 (`20250901-20251130`)
- **Validation**: Dec 1, 2025 – Feb 28, 2026 (`20251201-20260228`)
- **Holdout**: Mar 1, 2026 – present (`20260301-`)

All tests use 15m timeframe, 6 pairs (BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT, ADA/USDT, LINK/USDT), 1500 USDT dry wallet.

---

## Baseline (B v1) — EMA 20/50, RSI 35-65, stop -3%

| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 324 | 19.8% | -19.22% | 19.29% |
| Validation | 347 | 13.5% | -20.12% | 22.43% |

---

## Variant A Hypothesis Chain

### A v2 — Hypothesis 1: Trailing Stop
Added trailing stop (positive=1.5%, offset=2%) to replace exit_signal exits.

| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 568 | 18.7% | -32.76% | 32.76% |

Result: More trades, worse PnL. Trailing stop alone insufficient — root cause is long-only entries in a bear market.

---

### A v3 — Hypothesis 2: 200 EMA Trend Gate
Added rule: only enter if close > EMA(200). Blocks entries in sustained downtrends.

| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 245 | 19.2% | -12.8% | 12.80% |
| Validation | 271 | 12.9% | -17.09% | 17.09% |

Result: Beats baseline on both windows. PnL cut by ~37% vs baseline. Improvement held on validation.

---

### A v4 — Hypothesis 3: Volume Confirmation ✅ VALIDATED
Added rule: only enter if volume > 20-period average volume. Filters weak/low-conviction crossovers.

| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 71 | 23.9% | -3.13% | 3.50% |
| Validation | 73 | 19.2% | -3.53% | 3.61% |
| Holdout | 25 | 24.0% | -1.15% | 1.15% |

Result: **Validated across all three independent data splits.** Win rate consistent (~19-24%), drawdown below 4% in all windows. 82% reduction in losses vs baseline on validation. Deployed as **CP-1** paper trading on port 8081.

Strategy rules (entry):
1. EMA(10) crosses above EMA(30)
2. RSI(14) between 40 and 60
3. Close > EMA(200)
4. Volume > 20-period average volume

---

## Variant C Hypothesis Chain

### C v2 — Hypothesis 1: Trailing Stop

| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 532 | 17.9% | -32.87% | 32.87% |

### C v3 — Hypothesis 2: 200 EMA Trend Gate

| Window | Trades | Win% | PnL% | DD% |
|--------|--------|------|------|-----|
| Training | 263 | 20.5% | -12.76% | 12.76% |
| Validation | 266 | 13.2% | -20.68% | 20.68% |

Result: Beats baseline in training, ties/slightly underperforms on validation. Deprioritized in favor of A v4.

---

## Summary

| Strategy | Val PnL% | Val DD% | Status |
|----------|----------|---------|--------|
| B v1 baseline | -20.12% | 22.43% | CP-0 (running) |
| A v4 | -3.53% | 3.61% | **CP-1 (paper trading)** |
| C v3 | -20.68% | 20.68% | Deprioritized |
