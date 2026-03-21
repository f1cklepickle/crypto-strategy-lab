"""
adapter.py

Transforms Freqtrade dry-run trade history into the canonical trade log schema.
This is the bridge between the executor and all future layers.

Usage:
    python schemas/adapter.py --db tradesv3.dryrun.sqlite --variant variant_b --out reports/trades.json

Requirements:
    pip install pydantic ccxt pandas ta-lib  (ta-lib optional, falls back to pandas-ta)
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from schemas.trade_log_schema import TradeRecord, TradeDirection, ChampionStatus, TradingMode


# ---------------------------------------------------------------------------
# OHLCV context fetcher
# ---------------------------------------------------------------------------

def fetch_ohlcv_context(pair: str, timestamp_ms: int, timeframe: str = "1h") -> dict:
    """
    Fetch OHLCV candle data around the entry timestamp from Kraken public API.
    Returns a dict of market-state fields, or all-None if fetch fails.
    """
    try:
        import ccxt
        exchange = ccxt.kraken()
        # Fetch candles ending just after entry time
        since = timestamp_ms - (20 * 3600 * 1000)  # 20 candles before entry
        ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe, since=since, limit=60)
        if not ohlcv:
            return _empty_context()

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        # Find the candle at or just before entry
        entry_dt = pd.Timestamp(timestamp_ms, unit="ms", tz="UTC")
        candle = df[df["timestamp"] <= entry_dt].tail(1)
        if candle.empty:
            return _empty_context()

        idx = candle.index[0]
        close = df["close"]

        # EMA calculation
        ema_short = close.ewm(span=20, adjust=False).mean().iloc[idx]
        ema_long = close.ewm(span=50, adjust=False).mean().iloc[idx]

        # RSI calculation
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[idx]

        # ATR calculation
        high = df["high"]
        low = df["low"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[idx]
        atr_normalized = atr / close.iloc[idx] if close.iloc[idx] > 0 else None

        # Volume ratio
        vol_avg = df["volume"].rolling(20).mean().iloc[idx]
        vol_ratio = df["volume"].iloc[idx] / vol_avg if vol_avg > 0 else None

        # Recent returns
        if idx >= 4:
            ret_1h = (close.iloc[idx] - close.iloc[idx - 1]) / close.iloc[idx - 1]
            ret_4h = (close.iloc[idx] - close.iloc[idx - 4]) / close.iloc[idx - 4]
        else:
            ret_1h = None
            ret_4h = None

        return {
            "recent_return_1h": round(float(ret_1h), 6) if ret_1h is not None else None,
            "recent_return_4h": round(float(ret_4h), 6) if ret_4h is not None else None,
            "atr_normalized": round(float(atr_normalized), 6) if atr_normalized is not None else None,
            "rsi_14": round(float(rsi), 2) if rsi is not None else None,
            "ema_short": round(float(ema_short), 4),
            "ema_long": round(float(ema_long), 4),
            "ema_relationship": "above" if ema_short > ema_long else "below",
            "volume_ratio": round(float(vol_ratio), 4) if vol_ratio is not None else None,
            "spread": None,
        }

    except Exception as e:
        print(f"  Warning: could not fetch OHLCV context for {pair} at {timestamp_ms}: {e}")
        return _empty_context()


def _empty_context() -> dict:
    return {
        "recent_return_1h": None,
        "recent_return_4h": None,
        "atr_normalized": None,
        "rsi_14": None,
        "ema_short": None,
        "ema_long": None,
        "ema_relationship": None,
        "volume_ratio": None,
        "spread": None,
    }


# ---------------------------------------------------------------------------
# Freqtrade DB reader
# ---------------------------------------------------------------------------

def read_freqtrade_trades(db_path: str) -> list[dict]:
    """Read closed trades from Freqtrade's SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id, pair, open_date, close_date,
            open_rate, close_rate, stake_amount,
            fee_open, fee_close, calc_profit_ratio,
            close_profit_abs, is_open, sell_reason
        FROM trades
        WHERE is_open = 0
        ORDER BY close_date ASC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform(row: dict, variant_id: str, timeframe: str = "1h") -> Optional[TradeRecord]:
    """Transform a single Freqtrade trade row into a canonical TradeRecord."""

    try:
        entry_dt = datetime.fromisoformat(row["open_date"]).replace(tzinfo=timezone.utc)
        exit_dt = datetime.fromisoformat(row["close_date"]).replace(tzinfo=timezone.utc)
        duration_mins = (exit_dt - entry_dt).total_seconds() / 60

        entry_ts_ms = int(entry_dt.timestamp() * 1000)
        context = fetch_ohlcv_context(row["pair"], entry_ts_ms, timeframe)

        fees = (row["fee_open"] + row["fee_close"]) * row["stake_amount"]
        pnl_net = float(row["close_profit_abs"]) if row["close_profit_abs"] is not None else None
        pnl_gross = pnl_net + fees if pnl_net is not None else None

        entry_price = float(row["open_rate"])
        exit_price = float(row["close_rate"])
        stop_price = round(entry_price * 0.97, 8)    # -3% default, refine in Layer 3
        target_price = round(entry_price * 1.10, 8)  # 10% ROI ceiling

        record = TradeRecord(
            trade_id=f"ft-{row['id']}",
            timestamp_entry=entry_dt,
            timestamp_exit=exit_dt,
            pair=row["pair"],
            variant_id=variant_id,
            trade_direction=TradeDirection.LONG,
            trading_mode=TradingMode.PAPER,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_price=stop_price,
            target_price=target_price,
            position_size=float(row["stake_amount"]) / entry_price,
            fees_total=round(fees, 6),
            pnl_gross=round(pnl_gross, 6) if pnl_gross is not None else None,
            pnl_net=round(pnl_net, 6) if pnl_net is not None else None,
            duration_minutes=round(duration_mins, 1),
            candle_timeframe=timeframe,
            rule_triggered="ema_crossover_rsi_filter",
            parameter_set_id=f"{variant_id}_v1",
            champion_status=ChampionStatus.CHALLENGER,
            selection_round=0,
            **context
        )
        return record

    except Exception as e:
        print(f"  Error transforming trade id={row.get('id')}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Transform Freqtrade trades to canonical schema")
    parser.add_argument("--db", required=True, help="Path to Freqtrade SQLite DB (tradesv3.dryrun.sqlite)")
    parser.add_argument("--variant", required=True, help="Variant ID (e.g. variant_b)")
    parser.add_argument("--out", required=True, help="Output JSON file path (e.g. reports/trades.json)")
    parser.add_argument("--timeframe", default="1h", help="Candle timeframe (default: 1h)")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: database not found at {db_path}")
        sys.exit(1)

    print(f"Reading trades from {db_path}...")
    rows = read_freqtrade_trades(str(db_path))
    print(f"Found {len(rows)} closed trades.")

    if not rows:
        print("No closed trades yet — run the bot longer to accumulate paper trades.")
        sys.exit(0)

    records = []
    for i, row in enumerate(rows):
        print(f"  Processing trade {i + 1}/{len(rows)} — {row['pair']}...")
        record = transform(row, args.variant, args.timeframe)
        if record:
            records.append(record.model_dump(mode="json"))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2, default=str)

    print(f"\n✓ Wrote {len(records)} records to {out_path}")
    print("  Run schemas/validate_schema.py to verify the output.")


if __name__ == "__main__":
    main()
