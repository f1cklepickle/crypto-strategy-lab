# schemas

The shared data contract for all layers. Every trade, market snapshot, and outcome
gets written to this format. Never break the schema — extend it with nullable fields.

## Files
- `trade_log_schema.json` — canonical schema definition
- `examples/sample_trade.json` — synthetic example record for testing

## Field groups
1. Trade-level (entry, exit, size, fees, pnl)
2. Market-state at entry (RSI, EMAs, ATR, volume)
3. Decision metadata (which variant, which rule, champion/challenger)
4. Outcome labels (TP/SL hit, MFE, MAE, relative performance)
