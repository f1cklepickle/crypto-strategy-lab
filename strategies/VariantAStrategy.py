"""
VariantAStrategy.py

Layer 1 — Variant A: Fast EMA crossover with tight RSI filter + 200 EMA trend gate
                     + volume confirmation.

Logic:
    Entry:  EMA10 crosses above EMA30 AND RSI(14) is between 40 and 60
            AND close is above EMA200 (uptrend gate)
            AND volume > 20-period average volume (conviction filter)
    Exit:   EMA10 crosses below EMA30 OR stop-loss hit

Compared to Baseline (EMA 20/50, RSI 35-65):
    - Faster EMAs (10/30) react quicker to price changes
    - Tighter RSI range (40-60) reduces false signals in choppy markets
    - Tighter stop (-2.5%) reduces per-trade risk

Hypothesis 1: trailing stop reduces exit_signal dependency.
Hypothesis 2: 200 EMA gate blocks entries during bear market conditions,
reducing losing trades in sustained downtrends.
Hypothesis 3: volume confirmation filters out weak, low-conviction crossovers,
keeping only entries where real buying pressure exists.
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class VariantAStrategy(IStrategy):
    """
    Variant A — EMA 10/30, RSI 40-60, stop -2.5%, 200 EMA trend gate, volume confirmation
    """

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {
        "0": 0.10,
    }

    stoploss = -0.025

    # Hypothesis 1: trailing stop replaces EMA cross-down exit
    # Once trade reaches +2%, trail 1.5% below the peak
    # Hard -2.5% stop still active until offset is reached
    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe["ema_short"] = ta.EMA(dataframe, timeperiod=10)
        dataframe["ema_long"] = ta.EMA(dataframe, timeperiod=30)
        dataframe["ema_200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["volume_mean_20"] = dataframe["volume"].rolling(20).mean()

        dataframe["ema_cross_up"] = (
            (dataframe["ema_short"] > dataframe["ema_long"]) &
            (dataframe["ema_short"].shift(1) <= dataframe["ema_long"].shift(1))
        )
        dataframe["ema_cross_down"] = (
            (dataframe["ema_short"] < dataframe["ema_long"]) &
            (dataframe["ema_short"].shift(1) >= dataframe["ema_long"].shift(1))
        )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                dataframe["ema_cross_up"] &
                (dataframe["rsi"] >= 40) &
                (dataframe["rsi"] <= 60) &
                (dataframe["close"] > dataframe["ema_200"]) &
                (dataframe["volume"] > dataframe["volume_mean_20"]) &
                (dataframe["volume"] > 0)
            ),
            "enter_long"
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                dataframe["ema_cross_down"] &
                (dataframe["volume"] > 0)
            ),
            "exit_long"
        ] = 1

        return dataframe
