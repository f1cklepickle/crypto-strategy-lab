# refinement

Controlled parameter mutation. Generates new variant candidates from successful ones.

## Layer 3
- Takes top-performing variants as seeds
- Applies bounded mutations (e.g. ±10% on EMA length)
- Outputs new variant configs to `/variants`

## Notes
- Mutation bounds are defined per parameter to prevent wild swings.
- All generated candidates are versioned and traceable.
