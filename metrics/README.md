# metrics

Scoring and reporting logic. Consumes canonical trade logs and produces summaries.

## Layer 0
- `report.py` — baseline validation report (win rate, PnL, drawdown, duration)

## Later layers
- Leaderboard scoring (Layer 2)
- Regime-breakdown matrix (Layer 4)
- Confidence scoring (Layer 5)

## Notes
- All scripts take a log file as input — no hardcoded paths.
- Output goes to `/reports/`.
