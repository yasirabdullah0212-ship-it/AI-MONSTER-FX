from dataclasses import dataclass
import pandas as pd


@dataclass
class StrategySignal:
    action: str
    score: int
    max_score: int
    support: float
    resistance: float
    fibonacci_zone: str
    trend: str
    rsi: float
    fast_ema: float
    slow_ema: float
    reason: str


class MarketStrategy:

    def __init__(
        self,
        fast_ema=20,
        slow_ema=50,
        rsi_period=14,
        swing_lookback=100,
    ):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.swing_lookback = swing_lookback

    def calculate_indicators(self, df):

        df = df.copy()

        df["ema_fast"] = (
            df["close"]
            .ewm(
                span=self.fast_ema,
                adjust=False,
            )
            .mean()
        )

        df["ema_slow"] = (
            df["close"]
            .ewm(
                span=self.slow_ema,
                adjust=False,
            )
            .mean()
        )

        delta = df["close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        average_gain = (
            gain.ewm(
                alpha=1 / self.rsi_period,
                adjust=False,
            )
            .mean()
        )

        average_loss = (
            loss.ewm(
                alpha=1 / self.rsi_period,
                adjust=False,
            )
            .mean()
        )

        rs = average_gain / average_loss.replace(
            0,
            pd.NA,
        )

        df["rsi"] = (
            100
            - (
                100
                / (1 + rs)
            )
        )

        return df

    def find_support_resistance(self, df):

        recent = df.tail(
            self.swing_lookback
        )

        support = float(
            recent["low"].min()
        )

        resistance = float(
            recent["high"].max()
        )

        return support, resistance

    def fibonacci_zone(
        self,
        price,
        support,
        resistance,
    ):

        distance = resistance - support

        if distance <= 0:
            return "UNDEFINED"

        level_236 = (
            resistance
            - distance * 0.236
        )

        level_382 = (
            resistance
            - distance * 0.382
        )

        level_500 = (
            resistance
            - distance * 0.500
        )

        level_618 = (
            resistance
            - distance * 0.618
        )

        level_786 = (
            resistance
            - distance * 0.786
        )

        if price >= level_236:
            return "23.6%"

        if price >= level_382:
            return "38.2%"

        if price >= level_500:
            return "50.0%"

        if price >= level_618:
            return "61.8%"

        if price >= level_786:
            return "78.6%"

        return "BELOW 78.6%"

    def analyze(self, df):

        if df is None or len(df) < 60:
            raise ValueError(
                "Not enough candles for analysis."
            )

        df = self.calculate_indicators(df)

        latest = df.iloc[-1]

        price = float(
            latest["close"]
        )

        fast_ema = float(
            latest["ema_fast"]
        )

        slow_ema = float(
            latest["ema_slow"]
        )

        rsi = float(
            latest["rsi"]
        )

        support, resistance = (
            self.find_support_resistance(df)
        )

        fib_zone = self.fibonacci_zone(
            price,
            support,
            resistance,
        )

        score = 0
        reasons = []

        # =====================================
        # TREND
        # =====================================

        if fast_ema > slow_ema:

            score += 2

            trend = "BULLISH"

            reasons.append(
                "Fast EMA is above slow EMA."
            )

        elif fast_ema < slow_ema:

            score -= 2

            trend = "BEARISH"

            reasons.append(
                "Fast EMA is below slow EMA."
            )

        else:

            trend = "NEUTRAL"

        # =====================================
        # RSI
        # =====================================

        if rsi >= 55:

            score += 1

            reasons.append(
                "RSI confirms bullish momentum."
            )

        elif rsi <= 45:

            score -= 1

            reasons.append(
                "RSI confirms bearish momentum."
            )

        # =====================================
        # FIBONACCI
        # =====================================

        if fib_zone in [
            "50.0%",
            "61.8%",
            "78.6%",
        ]:

            if trend == "BULLISH":

                score += 1

                reasons.append(
                    "Price is in a useful Fibonacci "
                    "retracement area."
                )

            elif trend == "BEARISH":

                score -= 1

                reasons.append(
                    "Price is in a useful Fibonacci "
                    "retracement area."
                )

        # =====================================
        # SUPPORT / RESISTANCE
        # =====================================

        range_size = (
            resistance - support
        )

        if range_size > 0:

            support_distance = (
                abs(price - support)
                / range_size
            )

            resistance_distance = (
                abs(resistance - price)
                / range_size
            )

            if support_distance <= 0.15:

                score += 1

                reasons.append(
                    "Price is close to support."
                )

            if resistance_distance <= 0.15:

                score -= 1

                reasons.append(
                    "Price is close to resistance."
                )

        # =====================================
        # FINAL DECISION
        # =====================================

        if score >= 3:

            action = "BUY"

        elif score <= -3:

            action = "SELL"

        else:

            action = "HOLD"

        reason = (
            " ".join(reasons)
            if reasons
            else "No strong confirmation."
        )

        return StrategySignal(
            action=action,
            score=score,
            max_score=5,
            support=round(
                support,
                5,
            ),
            resistance=round(
                resistance,
                5,
            ),
            fibonacci_zone=fib_zone,
            trend=trend,
            rsi=round(
                rsi,
                2,
            ),
            fast_ema=round(
                fast_ema,
                5,
            ),
            slow_ema=round(
                slow_ema,
                5,
            ),
            reason=reason,
        )