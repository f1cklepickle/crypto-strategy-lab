# variants

Parameter sets for each strategy variant. These are not different strategies — they are
the same logic with different values, designed to be tested side by side.

## Layer 1 — Initial Variants

| Variant | EMA Short | EMA Long | RSI Filter | ATR Stop Multiplier |
|---------|-----------|----------|------------|---------------------|
| A       | 10        | 30       | 40–60      | 1.5x                |
| B       | 20        | 50       | 35–65      | 2.0x                |
| C       | 15        | 40       | 30–70      | 1.75x               |

## Notes
- Each variant has a unique `variant_id` that maps to the trade log schema.
- Variant configs are plain JSON — no code, no secrets.
