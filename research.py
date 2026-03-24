"""
research.py

CipherPickle lab tool — hypothesis research pipeline.
Never run against live bots. Backtesting only.

Usage:
    python research.py backtest <StrategyName>   # run all 3 windows + guardrails
    python research.py compare                   # leaderboard of all saved results
    python research.py branch <StrategyName>     # scaffold next version file
"""

import argparse
import json
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────

CONFIG = "executor/config.json"
STRATEGY_PATH = Path("strategies")
REPORTS_DIR = Path("reports")
BACKTEST_RESULTS_DIR = Path("user_data/backtest_results")

WINDOWS = {
    "training":   "20250901-20251130",
    "validation": "20251201-20260228",
    "holdout":    "20260301-",
}

# Guardrail thresholds
MIN_TRADES = 40
MAX_WINRATE_SWING_PP = 15.0

# Current champion strategies (shown in compare leaderboard)
CHAMPIONS = {
    "BaselineStrategy": "CP-0",
    "VariantAStrategy": "CP-1",
}

# Known current version numbers for naming
KNOWN_VERSIONS = {
    "BaselineStrategy": 1,
    "VariantAStrategy": 4,
    "VariantCStrategy": 3,
}


# ─────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────

def short_label(strategy_name: str) -> str:
    """
    Convert a strategy class name to the compact display label.
    VariantAStrategy     → A v4
    VariantAStrategy_v5  → A v5
    BaselineStrategy     → B v1
    VariantCStrategy     → C v3
    """
    if "_v" in strategy_name:
        base, version = strategy_name.rsplit("_v", 1)
        letter = base.replace("VariantStrategy", "").replace("Variant", "").replace("Strategy", "")
        return f"{letter} v{version}"

    name = strategy_name.replace("Strategy", "")
    if name == "Baseline":
        return f"B v{KNOWN_VERSIONS.get(strategy_name, 1)}"
    if name.startswith("Variant"):
        letter = name.replace("Variant", "")
        v = KNOWN_VERSIONS.get(strategy_name, "?")
        return f"{letter} v{v}"
    return name


def format_line(strategy_name: str, metrics: dict, window: str) -> str:
    """Format one result line in the standard reporting format."""
    label = short_label(strategy_name)
    trades = metrics["total_trades"]
    winrate = round(metrics["winrate"] * 100, 1)
    pnl = round(metrics["profit_total"] * 100, 2)
    dd = round(metrics["max_drawdown_account"] * 100, 2)
    flag = "✓" if trades >= MIN_TRADES else "⚠"
    return f"{flag} {label}: [{trades}] | [{winrate}%] | [{pnl:+.2f}%] | [{dd:.2f}%] ({window})"


# ─────────────────────────────────────────────────────────────────
# Backtest result parsing
# ─────────────────────────────────────────────────────────────────

def parse_latest_zip(strategy_name: str, known_before: set) -> dict:
    """
    Find the zip file created after `known_before` and extract metrics.
    Raises RuntimeError if no new result is found.
    """
    all_zips = set(BACKTEST_RESULTS_DIR.glob("*.zip"))
    new_zips = all_zips - known_before

    if not new_zips:
        raise RuntimeError(f"No new backtest result file found for {strategy_name}")

    newest = max(new_zips, key=lambda p: p.stat().st_mtime)

    with zipfile.ZipFile(newest) as z:
        json_files = [f for f in z.namelist() if f.endswith(".json") and "_config" not in f]
        if not json_files:
            raise RuntimeError(f"No JSON found in {newest}")
        with z.open(json_files[0]) as f:
            data = json.load(f)

    strategy_data = data.get("strategy", {})
    if strategy_name not in strategy_data:
        raise RuntimeError(
            f"Strategy '{strategy_name}' not found in result. "
            f"Available: {list(strategy_data.keys())}"
        )

    return strategy_data[strategy_name]


# ─────────────────────────────────────────────────────────────────
# Guardrails
# ─────────────────────────────────────────────────────────────────

def run_guardrails(results: dict) -> list[str]:
    """
    Run all overfitting guardrail checks.
    Returns a list of warning strings (empty = all passed).
    """
    warnings = []

    # 1. Minimum trade count floor
    for window, m in results.items():
        if m["total_trades"] < MIN_TRADES:
            warnings.append(
                f"⚠  TRADE COUNT [{window}]: {m['total_trades']} trades "
                f"— below minimum of {MIN_TRADES}. Statistically unreliable."
            )

    # 2. Cross-window consistency (win rate swing)
    win_rates = {w: m["winrate"] * 100 for w, m in results.items()}
    if len(win_rates) >= 2:
        swing = max(win_rates.values()) - min(win_rates.values())
        if swing > MAX_WINRATE_SWING_PP:
            hi = max(win_rates, key=win_rates.get)
            lo = min(win_rates, key=win_rates.get)
            warnings.append(
                f"⚠  CONSISTENCY: Win rate swings {swing:.1f}pp "
                f"({lo} {win_rates[lo]:.1f}% → {hi} {win_rates[hi]:.1f}%). "
                f"Max allowed: {MAX_WINRATE_SWING_PP}pp."
            )

    return warnings


def format_guardrail_footer(results: dict, warnings: list[str]) -> str:
    """Format the summary lines printed after results."""
    lines = []

    if not warnings:
        win_rates = [m["winrate"] * 100 for m in results.values()]
        swing = round(max(win_rates) - min(win_rates), 1) if len(win_rates) >= 2 else 0.0
        lines.append(f"Consistency: ✓ win rate stable (±{swing}pp across windows)")
        lines.append("Jitter:      → test manually: nudge EMA ±1, RSI ±2 and compare")
    else:
        for w in warnings:
            lines.append(w)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Subcommand: backtest
# ─────────────────────────────────────────────────────────────────

def cmd_backtest(strategy_name: str):
    """Run all three windows and print formatted results with guardrail checks."""

    print(f"\n{'─' * 62}")
    print(f"  research.py backtest — {strategy_name}")
    print(f"  Lab tool only. Never run on live bots.")
    print(f"{'─' * 62}\n")

    collected = {}

    for window_name, timerange in WINDOWS.items():
        print(f"  [{window_name}]  {timerange} ...", flush=True)

        # Snapshot existing results before running
        before = set(BACKTEST_RESULTS_DIR.glob("*.zip"))

        proc = subprocess.run(
            [
                "freqtrade", "backtesting",
                "--config", CONFIG,
                "--strategy", strategy_name,
                "--timerange", timerange,
            ],
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            print(f"\n  ERROR running {window_name} backtest:")
            print(proc.stderr[-800:])
            sys.exit(1)

        try:
            metrics = parse_latest_zip(strategy_name, before)
        except RuntimeError as e:
            print(f"\n  ERROR parsing result: {e}")
            sys.exit(1)

        collected[window_name] = metrics
        print(f"  {format_line(strategy_name, metrics, window_name)}")

    # Guardrails
    warnings = run_guardrails(collected)
    print()
    print(format_guardrail_footer(collected, warnings))
    print()

    if warnings:
        print("❌  Guardrail(s) failed — review before advancing this hypothesis.\n")
        passed = False
    else:
        print("✓  All guardrails passed.\n")
        passed = True

    # Save to reports/
    REPORTS_DIR.mkdir(exist_ok=True)
    label = short_label(strategy_name).replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = REPORTS_DIR / f"{label}_{ts}.json"

    with open(out_path, "w") as f:
        json.dump(
            {
                "strategy": strategy_name,
                "label": short_label(strategy_name),
                "timestamp": ts,
                "guardrails_passed": passed,
                "results": {
                    w: {
                        "trades":      m["total_trades"],
                        "winrate_pct": round(m["winrate"] * 100, 1),
                        "pnl_pct":     round(m["profit_total"] * 100, 2),
                        "dd_pct":      round(m["max_drawdown_account"] * 100, 2),
                    }
                    for w, m in collected.items()
                },
            },
            f,
            indent=2,
        )

    print(f"  Results saved → {out_path}")


# ─────────────────────────────────────────────────────────────────
# Subcommand: compare
# ─────────────────────────────────────────────────────────────────

def cmd_compare():
    """Print a ranked leaderboard of all saved backtest results."""

    report_files = sorted(REPORTS_DIR.glob("*.json"))
    if not report_files:
        print(
            "\nNo reports found in reports/.\n"
            "Run: python research.py backtest <StrategyName>\n"
        )
        return

    rows = []
    for path in report_files:
        with open(path) as f:
            data = json.load(f)
        val = data["results"].get("validation")
        if not val:
            continue
        rows.append(
            {
                "label":    data["label"],
                "strategy": data["strategy"],
                "ts":       data["timestamp"],
                "passed":   data.get("guardrails_passed", "?"),
                "t_trades": data["results"].get("training", {}).get("trades", "—"),
                "v_trades": val["trades"],
                "v_win":    val["winrate_pct"],
                "v_pnl":    val["pnl_pct"],
                "v_dd":     val["dd_pct"],
                "h_pnl":    data["results"].get("holdout", {}).get("pnl_pct", "—"),
            }
        )

    rows.sort(key=lambda r: r["v_pnl"], reverse=True)

    W = 78
    print(f"\n{'─' * W}")
    print(
        f"  {'Label':<9} {'Strategy':<26} {'Tr Tr':>5} {'Vl Tr':>5} "
        f"{'Vl Win%':>7} {'Vl PnL%':>8} {'Vl DD%':>7} {'Ho PnL%':>8}"
    )
    print(f"{'─' * W}")

    for r in rows:
        cp_tag = f"  ◄ {CHAMPIONS[r['strategy']]}" if r["strategy"] in CHAMPIONS else ""
        guard = "✓" if r["passed"] is True else ("⚠" if r["passed"] is False else "?")
        h_pnl = f"{r['h_pnl']:+.2f}%" if isinstance(r["h_pnl"], float) else str(r["h_pnl"])
        print(
            f"  {r['label']:<9} {r['strategy']:<26} {str(r['t_trades']):>5} "
            f"{r['v_trades']:>5} {r['v_win']:>6.1f}% {r['v_pnl']:>+7.2f}% "
            f"{r['v_dd']:>6.2f}% {h_pnl:>8}  {guard}{cp_tag}"
        )

    print(f"{'─' * W}")
    print(f"  Ranked by validation PnL. Champions marked ◄. Guardrail: ✓ pass  ⚠ fail\n")


# ─────────────────────────────────────────────────────────────────
# Subcommand: branch
# ─────────────────────────────────────────────────────────────────

def cmd_branch(strategy_name: str):
    """Scaffold the next version file, inheriting from the parent strategy."""

    src = STRATEGY_PATH / f"{strategy_name}.py"
    if not src.exists():
        print(f"\nERROR: {src} not found.")
        sys.exit(1)

    # Determine next version number
    existing_versions = []
    for p in STRATEGY_PATH.glob(f"{strategy_name}_v*.py"):
        try:
            existing_versions.append(int(p.stem.split("_v")[-1]))
        except ValueError:
            pass

    if existing_versions:
        next_v = max(existing_versions) + 1
    else:
        next_v = KNOWN_VERSIONS.get(strategy_name, 1) + 1

    new_name = f"{strategy_name}_v{next_v}"
    dest = STRATEGY_PATH / f"{new_name}.py"

    if dest.exists():
        print(f"\nERROR: {dest} already exists.")
        sys.exit(1)

    parent_lines = src.read_text().splitlines()
    parent_as_comments = "\n".join(f"# {line}" for line in parent_lines)

    template = f'''\
"""
{new_name}.py

Parent:     {strategy_name} (frozen — do not modify the parent file)
Hypothesis: [FILL IN: one sentence describing the change and expected effect]
Change:     [FILL IN: one line — exactly what is different from the parent]
Expected:   [FILL IN: what metric should improve and why]

Run after editing:
    python research.py backtest {new_name}
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta

# ── Import parent so this class can inherit cleanly ──────────────
from strategies.{strategy_name} import {strategy_name}


class {new_name}({strategy_name}):
    """
    {new_name}
    Inherits all rules from {strategy_name}.
    Single change: [FILL IN]
    """

    # ── Hypothesis change ─────────────────────────────────────────
    # Add or override ONLY what changes from the parent.
    # Delete this comment block when done.
    #
    # Examples:
    #   stoploss = -0.02                          # tighter stop
    #   trailing_stop_positive = 0.01             # tighter trail
    #   # override populate_entry_trend to add a filter
    # ─────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════
# PARENT SOURCE — frozen reference (do not edit below this line)
# ══════════════════════════════════════════════════════════════════
{parent_as_comments}
'''

    dest.write_text(template)

    print(f"\n✓  Created {dest}")
    print(f"\n   Next steps:")
    print(f"   1. Edit {dest}")
    print(f"   2. Fill in the hypothesis docstring at the top")
    print(f"   3. Add your one change below the '── Hypothesis change ──' line")
    print(f"   4. Run: python research.py backtest {new_name}\n")


# ─────────────────────────────────────────────────────────────────
# Subcommand: roster
# ─────────────────────────────────────────────────────────────────

# Strategy files to skip in roster runs (deprioritized / not competitive)
ROSTER_SKIP = {"VariantCStrategy"}


def cmd_roster():
    """Run backtest on every active strategy file, then print the leaderboard."""

    strategy_files = sorted(STRATEGY_PATH.glob("*.py"))
    names = [f.stem for f in strategy_files if f.stem not in ROSTER_SKIP]

    if not names:
        print("\nNo strategy files found in strategies/.\n")
        return

    W = 62
    print(f"\n{'─' * W}")
    print(f"  research.py roster — running {len(names)} strategies")
    print(f"  Lab tool only. Never run on live bots.")
    print(f"{'─' * W}\n")

    for name in names:
        print(f"  ── {name}")
        cmd_backtest(name)
        print()

    cmd_compare()


# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="research.py",
        description=(
            "CipherPickle research tool — lab use only, never run on live bots.\n"
            "Runs backtests, compares results, and scaffolds new hypothesis files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_bt = sub.add_parser("backtest", help="Run all 3 windows for a strategy + guardrails")
    p_bt.add_argument("strategy", help="Strategy class name (e.g. VariantAStrategy_v5)")

    sub.add_parser("compare", help="Print leaderboard of all saved results")

    p_br = sub.add_parser("branch", help="Scaffold the next version of a strategy")
    p_br.add_argument("strategy", help="Parent strategy class name (e.g. VariantAStrategy)")

    sub.add_parser("roster", help="Backtest all active strategies, then compare")

    args = parser.parse_args()

    if args.command == "backtest":
        cmd_backtest(args.strategy)
    elif args.command == "compare":
        cmd_compare()
    elif args.command == "branch":
        cmd_branch(args.strategy)
    elif args.command == "roster":
        cmd_roster()


if __name__ == "__main__":
    main()
