"""
validate_schema.py

Loads the sample trade record and validates it against the schema.
Run this after any schema change to confirm nothing is broken.

Usage:
    python schemas/validate_schema.py
"""

import json
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.trade_log_schema import TradeRecord


def main():
    sample_path = Path(__file__).parent / "examples" / "sample_trade.json"

    print(f"Loading sample record from {sample_path}...")
    with open(sample_path) as f:
        raw = json.load(f)

    # Strip comment key if present
    raw.pop("_comment", None)

    print("Validating against TradeRecord schema...")
    try:
        record = TradeRecord(**raw)
        print("\n✓ Validation passed.\n")
        print("Parsed record summary:")
        print(f"  trade_id         : {record.trade_id}")
        print(f"  pair             : {record.pair}")
        print(f"  variant_id       : {record.variant_id}")
        print(f"  trading_mode     : {record.trading_mode}")
        print(f"  entry_price      : {record.entry_price}")
        print(f"  pnl_net          : {record.pnl_net}")
        print(f"  duration_minutes : {record.duration_minutes}")
        print(f"  tp_hit_first     : {record.tp_hit_first}")
        print(f"  champion_status  : {record.champion_status}")
    except Exception as e:
        print(f"\n✗ Validation failed:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
