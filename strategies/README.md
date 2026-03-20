# strategies

Freqtrade strategy definitions.

## Layer 0 — Baseline
- `BaselineStrategy.py` — EMA 20/50 crossover with RSI 14 filter. Simple, explainable, fully logged.

## Notes
- Strategies define logic only. Parameter values live in `/variants`.
- Every strategy must log trade decisions in a format compatible with `/schemas`.
