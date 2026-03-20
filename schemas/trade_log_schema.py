"""
trade_log_schema.py

Canonical trade log schema for crypto-strategy-lab.
This is the shared data contract all layers read from and write to.

Never remove fields. Add new fields as Optional with a default of None
so older log files remain valid.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TradeDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


class ChampionStatus(str, Enum):
    CHAMPION = "champion"
    CHALLENGER = "challenger"
    ARCHIVED = "archived"


class TradingMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


# ---------------------------------------------------------------------------
# Trade Log Record
# ---------------------------------------------------------------------------

class TradeRecord(BaseModel):
    """
    One complete record per closed trade.
    All four field groups must be present for a record to be valid.
    Outcome labels are filled at trade close.
    """

    # --- 1. Trade-level fields -------------------------------------------

    trade_id: str = Field(
        ...,
        description="Unique identifier for this trade (e.g. freqtrade trade ID or UUID)"
    )
    timestamp_entry: datetime = Field(
        ...,
        description="UTC timestamp when the trade was entered"
    )
    timestamp_exit: Optional[datetime] = Field(
        None,
        description="UTC timestamp when the trade was closed (None if still open)"
    )
    pair: str = Field(
        ...,
        description="Trading pair symbol (e.g. BTC/USDT)"
    )
    variant_id: str = Field(
        ...,
        description="ID of the parameter set / variant that took this trade (e.g. variant_a)"
    )
    trade_direction: TradeDirection = Field(
        ...,
        description="Direction of the trade: long or short"
    )
    trading_mode: TradingMode = Field(
        TradingMode.PAPER,
        description="Whether this was a paper or live trade"
    )
    entry_price: float = Field(
        ...,
        description="Execution price at entry"
    )
    exit_price: Optional[float] = Field(
        None,
        description="Execution price at exit"
    )
    stop_price: float = Field(
        ...,
        description="Stop-loss price at entry"
    )
    target_price: float = Field(
        ...,
        description="Take-profit target price at entry"
    )
    position_size: float = Field(
        ...,
        description="Position size in base currency (e.g. amount of BTC)"
    )
    fees_total: float = Field(
        ...,
        description="Total fees paid in quote currency (entry + exit combined)"
    )
    pnl_gross: Optional[float] = Field(
        None,
        description="Gross PnL before fees in quote currency"
    )
    pnl_net: Optional[float] = Field(
        None,
        description="Net PnL after fees in quote currency"
    )
    duration_minutes: Optional[float] = Field(
        None,
        description="Trade duration in minutes from entry to exit"
    )

    # --- 2. Market-state fields (snapshot at entry) ----------------------

    candle_timeframe: str = Field(
        ...,
        description="Candle timeframe used for this trade (e.g. 5m, 1h, 4h)"
    )
    recent_return_1h: Optional[float] = Field(
        None,
        description="Price return over the past 1 hour at entry time (fractional, e.g. 0.012)"
    )
    recent_return_4h: Optional[float] = Field(
        None,
        description="Price return over the past 4 hours at entry time (fractional)"
    )
    atr_normalized: Optional[float] = Field(
        None,
        description="ATR(14) divided by price at entry — normalized volatility measure"
    )
    rsi_14: Optional[float] = Field(
        None,
        description="RSI(14) value at entry (0–100)"
    )
    ema_short: Optional[float] = Field(
        None,
        description="Short EMA value at entry"
    )
    ema_long: Optional[float] = Field(
        None,
        description="Long EMA value at entry"
    )
    ema_relationship: Optional[str] = Field(
        None,
        description="Relationship between EMAs at entry: 'above' (short > long) or 'below'"
    )
    volume_ratio: Optional[float] = Field(
        None,
        description="Current candle volume divided by 20-period average volume"
    )
    spread: Optional[float] = Field(
        None,
        description="Bid-ask spread at entry if available (fractional)"
    )

    # --- 3. Decision metadata --------------------------------------------

    rule_triggered: Optional[str] = Field(
        None,
        description="Name or ID of the rule/signal that triggered this trade"
    )
    parameter_set_id: Optional[str] = Field(
        None,
        description="Specific parameter set version (may differ from variant_id in later layers)"
    )
    champion_status: Optional[ChampionStatus] = Field(
        None,
        description="Whether this variant was champion, challenger, or archived at time of trade"
    )
    selection_round: Optional[int] = Field(
        None,
        description="Which selection/evaluation round was active when this trade was taken"
    )

    # --- 4. Outcome labels (filled at close) -----------------------------

    tp_hit_first: Optional[bool] = Field(
        None,
        description="True if take-profit was hit before stop-loss"
    )
    sl_hit_first: Optional[bool] = Field(
        None,
        description="True if stop-loss was hit before take-profit"
    )
    max_favorable_excursion: Optional[float] = Field(
        None,
        description="Maximum unrealised gain during the trade (fractional, e.g. 0.03 = 3%)"
    )
    max_adverse_excursion: Optional[float] = Field(
        None,
        description="Maximum unrealised loss during the trade (fractional, e.g. -0.015 = -1.5%)"
    )
    outperformed_median_variant: Optional[bool] = Field(
        None,
        description="True if this trade's PnL exceeded the median PnL of all variants at that time"
    )

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
