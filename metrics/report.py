"""
report.py

Layer 0 — Baseline validation report.
Consumes a canonical trade log JSON file and outputs a summary report.

This is the baseline report all future layers will extend.
Same log input always produces the same output — fully reproducible.

Usage:
    python metrics/report.py --trades reports/trades.json --out reports/layer0_report.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from schemas.trade_log_schema import TradeRecord


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(records: list[dict]) -> dict:
    """Compute all Layer 0 metrics from a list of trade records."""

    total = len(records)
    if total == 0:
        return {}

    wins = [r for r in records if r.get("pnl_net") is not None and r["pnl_net"] > 0]
    losses = [r for r in records if r.get("pnl_net") is not None and r["pnl_net"] <= 0]

    pnl_values = [r["pnl_net"] for r in records if r.get("pnl_net") is not None]
    total_pnl = sum(pnl_values)
    avg_pnl = total_pnl / len(pnl_values) if pnl_values else 0

    avg_win = sum(r["pnl_net"] for r in wins) / len(wins) if wins else 0
    avg_loss = sum(r["pnl_net"] for r in losses) / len(losses) if losses else 0
    reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else None

    durations = [r["duration_minutes"] for r in records if r.get("duration_minutes") is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Drawdown — peak-to-trough on cumulative PnL curve
    cumulative = 0
    peak = 0
    max_drawdown = 0
    for pnl in pnl_values:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Trades per day
    dates = []
    for r in records:
        if r.get("timestamp_entry"):
            try:
                dates.append(datetime.fromisoformat(str(r["timestamp_entry"])))
            except Exception:
                pass
    if len(dates) >= 2:
        span_days = (max(dates) - min(dates)).total_seconds() / 86400
        trades_per_day = total / span_days if span_days > 0 else total
    else:
        trades_per_day = None

    # Fee analysis
    fees = [r["fees_total"] for r in records if r.get("fees_total") is not None]
    total_fees = sum(fees)

    # TP/SL breakdown
    tp_count = sum(1 for r in records if r.get("tp_hit_first") is True)
    sl_count = sum(1 for r in records if r.get("sl_hit_first") is True)

    return {
        "total_trades": total,
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate_pct": round(len(wins) / total * 100, 1),
        "total_pnl_net": round(total_pnl, 4),
        "avg_pnl_per_trade": round(avg_pnl, 4),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "reward_risk_ratio": round(reward_risk, 2) if reward_risk is not None else "N/A",
        "total_fees": round(total_fees, 4),
        "avg_duration_minutes": round(avg_duration, 1),
        "max_drawdown": round(max_drawdown, 4),
        "trades_per_day": round(trades_per_day, 2) if trades_per_day is not None else "N/A",
        "tp_hit_count": tp_count,
        "sl_hit_count": sl_count,
    }


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_markdown(records: list[dict], metrics: dict, variant_id: str) -> str:
    """Render metrics and sample trades as a markdown report."""

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append(f"# Layer 0 Validation Report")
    lines.append(f"\n**Generated:** {now}  ")
    lines.append(f"**Variant:** `{variant_id}`  ")
    lines.append(f"**Total trades:** {metrics.get('total_trades', 0)}  ")
    lines.append(f"**Trading mode:** paper (dry-run)\n")

    lines.append("---\n")
    lines.append("## Summary metrics\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total trades | {metrics['total_trades']} |")
    lines.append(f"| Win rate | {metrics['win_rate_pct']}% |")
    lines.append(f"| Net PnL (after fees) | {metrics['total_pnl_net']} USDT |")
    lines.append(f"| Avg PnL per trade | {metrics['avg_pnl_per_trade']} USDT |")
    lines.append(f"| Avg win | {metrics['avg_win']} USDT |")
    lines.append(f"| Avg loss | {metrics['avg_loss']} USDT |")
    lines.append(f"| Reward:Risk ratio | {metrics['reward_risk_ratio']} |")
    lines.append(f"| Total fees paid | {metrics['total_fees']} USDT |")
    lines.append(f"| Avg trade duration | {metrics['avg_duration_minutes']} min |")
    lines.append(f"| Max drawdown | {metrics['max_drawdown']} USDT |")
    lines.append(f"| Trades per day | {metrics['trades_per_day']} |")
    lines.append(f"| TP hit first | {metrics['tp_hit_count']} trades |")
    lines.append(f"| SL hit first | {metrics['sl_hit_count']} trades |\n")

    lines.append("---\n")
    lines.append("## Interpretation\n")

    win_rate = metrics.get("win_rate_pct", 0)
    rr = metrics.get("reward_risk_ratio")
    pnl = metrics.get("total_pnl_net", 0)

    if pnl > 0:
        lines.append(f"✓ **Net PnL is positive** after fees — variant is generating value in paper mode.")
    else:
        lines.append(f"✗ **Net PnL is negative** after fees — variant is not clearing the fee hurdle yet.")

    if isinstance(rr, float) and rr >= 1.5:
        lines.append(f"✓ **Reward:Risk ratio ({rr})** is healthy — wins are meaningfully larger than losses.")
    elif isinstance(rr, float):
        lines.append(f"⚠ **Reward:Risk ratio ({rr})** is below 1.5 — losses are eating into wins.")

    if win_rate >= 50:
        lines.append(f"✓ **Win rate ({win_rate}%)** is above 50%.")
    else:
        lines.append(f"⚠ **Win rate ({win_rate}%)** is below 50% — needs strong R:R to remain profitable.")

    lines.append("")
    lines.append("> This report is the Layer 0 baseline. Do not optimize based on this data alone.")
    lines.append("> Layer 2 leaderboard scoring will compare multiple variants fairly before any selection.\n")

    lines.append("---\n")
    lines.append("## Sample trades (last 5)\n")
    lines.append("| Trade ID | Pair | Entry | Exit | PnL net | Duration | Variant |")
    lines.append("|----------|------|-------|------|---------|----------|---------|")

    for r in records[-5:]:
        tid = r.get("trade_id", "—")
        pair = r.get("pair", "—")
        entry = r.get("entry_price", "—")
        exit_p = r.get("exit_price", "—")
        pnl = r.get("pnl_net", "—")
        dur = r.get("duration_minutes", "—")
        vid = r.get("variant_id", "—")
        lines.append(f"| {tid} | {pair} | {entry} | {exit_p} | {pnl} | {dur} min | {vid} |")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Layer 0 validation report")
    parser.add_argument("--trades", required=True, help="Path to canonical trades JSON file")
    parser.add_argument("--out", required=True, help="Output markdown report path")
    args = parser.parse_args()

    trades_path = Path(args.trades)
    if not trades_path.exists():
        print(f"Error: trades file not found at {trades_path}")
        sys.exit(1)

    print(f"Loading trades from {trades_path}...")
    with open(trades_path) as f:
        raw = json.load(f)

    if not raw:
        print("No trades found in file.")
        sys.exit(0)

    # Validate each record against schema
    records = []
    for item in raw:
        try:
            TradeRecord(**item)
            records.append(item)
        except Exception as e:
            print(f"  Warning: skipping invalid record — {e}")

    print(f"Validated {len(records)}/{len(raw)} records.")

    variant_id = records[0].get("variant_id", "unknown") if records else "unknown"
    metrics = compute_metrics(records)
    report = render_markdown(records, metrics, variant_id)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(report)

    print(f"\n✓ Report written to {out_path}")


if __name__ == "__main__":
    main()
