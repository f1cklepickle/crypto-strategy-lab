"""
BaselineStrategy.py

Layer 0 — Baseline paper trading strategy for crypto-strategy-lab.

Logic:
    Entry:  EMA20 crosses above EMA50 AND RSI(14) is between 35 and 65
            (avoids chasing overbought entries)
    Exit:   EMA20 crosses below EMA50 OR take-profit / stop-loss hit

This strategy is intentionally simple and explainable. The goal is not
profit — it is to prove the engine runs and logs are clean.

Parameter values here match Variant B from /variants/. Variants A and C
will be tested in Layer 1.
"""

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class BaselineStrategy(IStrategy):
    """
    EMA crossover strategy with RSI filter.
    Variant B parameter set (EMA 20/50, RSI 35-65, ATR stop 2.0x).
    """

    # --- Strategy metadata ------------------------------------------------

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    # Minimal ROI — let stop-loss and trailing stop do the work
    minimal_roi = {
        "0": 0.10,   # 10% take-profit as a safety ceiling
    }

    # Stop loss: -3% hard stop (ATR-based refinement comes in Layer 3)
    stoploss = -0.03

    # Trailing stop disabled for Layer 0 — keep it simple and measurable
    trailing_stop = False

    # Allow buying on the same candle as a sell signal
    process_only_new_candles = True

    # Startup candle count — need at least 50 candles for EMA50
    startup_candle_count = 60

    # --- Parameters (Variant B defaults) ----------------------------------
    # These are defined as parameters so later layers can vary them
    # without modifying this file.

    ema_short = IntParameter(10, 30, default=20, space="buy", optimize=False)
    ema_long = IntParameter(30, 60, default=50, space="buy", optimize=False)
    rsi_low = IntParameter(25, 45, default=35, space="buy", optimize=False)
    rsi_high = IntParameter(55, 75, default=65, space="buy", optimize=False)

    # --- Indicator calculation --------------------------------------------

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all indicators needed for entry/exit signals.
        All indicator values are logged by Freqtrade automatically.
        """

        # EMAs
        dataframe["ema_short"] = ta.EMA(dataframe, timeperiod=self.ema_short.value)
        dataframe["ema_long"] = ta.EMA(dataframe, timeperiod=self.ema_long.value)

        # RSI
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # ATR (for context logging — not used in stop yet, that's Layer 3)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # EMA crossover signals
        dataframe["ema_cross_up"] = (
            (dataframe["ema_short"] > dataframe["ema_long"]) &
            (dataframe["ema_short"].shift(1) <= dataframe["ema_long"].shift(1))
        )
        dataframe["ema_cross_down"] = (
            (dataframe["ema_short"] < dataframe["ema_long"]) &
            (dataframe["ema_short"].shift(1) >= dataframe["ema_long"].shift(1))
        )

        return dataframe

    # --- Entry signal -----------------------------------------------------

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry condition:
            EMA20 crosses above EMA50
            AND RSI is between 35 and 65 (not overbought, not oversold)
        """

        dataframe.loc[
            (
                dataframe["ema_cross_up"] &
                (dataframe["rsi"] >= self.rsi_low.value) &
                (dataframe["rsi"] <= self.rsi_high.value) &
                (dataframe["volume"] > 0)
            ),
            "enter_long"
        ] = 1

        return dataframe

    # --- Exit signal ------------------------------------------------------

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit condition:
            EMA20 crosses below EMA50 (trend reversal signal)
        Hard stop-loss and minimal_roi handle the rest.
        """

        dataframe.loc[
            (
                dataframe["ema_cross_down"] &
                (dataframe["volume"] > 0)
            ),
            "exit_long"
        ] = 1

        return dataframe
