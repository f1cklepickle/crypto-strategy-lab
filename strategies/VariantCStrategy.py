"""
VariantCStrategy.py

Layer 1 — Variant C: Medium EMA crossover with wide RSI filter + 200 EMA trend gate.

Logic:
    Entry:  EMA15 crosses above EMA40 AND RSI(14) is between 30 and 70
            AND close is above EMA200 (uptrend gate)
    Exit:   EMA15 crosses below EMA40 OR stop-loss hit

Compared to Baseline (EMA 20/50, RSI 35-65):
    - Slightly faster EMAs (15/40) vs baseline
    - Wider RSI range (30-70) allows entries in more market conditions
    - Wider stop (-3.5%) gives trades more room to breathe

Hypothesis 1: trailing stop reduces exit_signal dependency.
Hypothesis 2: 200 EMA gate blocks entries during bear market conditions,
reducing losing trades in sustained downtrends.
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class VariantCStrategy(IStrategy):
    """
    Variant C — EMA 15/40, RSI 30-70, stop -3.5%, 200 EMA trend gate
    """

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {
        "0": 0.10,
    }

    stoploss = -0.035

    # Hypothesis 1: trailing stop replaces EMA cross-down exit
    # Once trade reaches +3%, trail 2% below the peak
    # Hard -3.5% stop still active until offset is reached
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe["ema_short"] = ta.EMA(dataframe, timeperiod=15)
        dataframe["ema_long"] = ta.EMA(dataframe, timeperiod=40)
        dataframe["ema_200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

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
                (dataframe["rsi"] >= 30) &
                (dataframe["rsi"] <= 70) &
                (dataframe["close"] > dataframe["ema_200"]) &
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
