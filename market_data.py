import MetaTrader5 as mt5
import pandas as pd


TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}


def find_symbol(requested_symbol):
    """
    Find the broker's actual MT5 symbol.

    Examples:
        XAUUSD
        XAUUSDm
        XAUUSD.
        XAUUSD.pro
    """

    requested = requested_symbol.upper().strip()

    symbols = mt5.symbols_get()

    if symbols is None:
        return None

    # Exact match first.
    for symbol in symbols:
        if symbol.name.upper() == requested:
            return symbol.name

    # Then look for broker suffix/prefix variations.
    for symbol in symbols:
        name = symbol.name.upper()

        if (
            name.startswith(requested)
            or requested in name
        ):
            return symbol.name

    return None


def get_market_data(
    symbol: str,
    timeframe: str,
    candles: int = 500,
):

    if not mt5.initialize():
        return {
            "ok": False,
            "error": f"MT5 initialize failed: {mt5.last_error()}",
        }

    timeframe_key = timeframe.upper()

    if timeframe_key not in TIMEFRAME_MAP:
        return {
            "ok": False,
            "error": f"Unsupported timeframe: {timeframe}",
        }

    actual_symbol = find_symbol(symbol)

    if actual_symbol is None:

        return {
            "ok": False,
            "error": (
                f"Could not find broker symbol for "
                f"{symbol}."
            ),
        }

    if not mt5.symbol_select(
        actual_symbol,
        True,
    ):

        return {
            "ok": False,
            "error": (
                f"Could not select MT5 symbol: "
                f"{actual_symbol}"
            ),
        }

    rates = mt5.copy_rates_from_pos(
        actual_symbol,
        TIMEFRAME_MAP[timeframe_key],
        0,
        candles,
    )

    if rates is None or len(rates) == 0:

        return {
            "ok": False,
            "error": (
                f"No market data available for "
                f"{actual_symbol}."
            ),
        }

    df = pd.DataFrame(rates)

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s",
        utc=True,
    )

    df = df[
        [
            "time",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread",
            "real_volume",
        ]
    ]

    return {
        "ok": True,
        "requested_symbol": symbol,
        "symbol": actual_symbol,
        "timeframe": timeframe_key,
        "candles": len(df),
        "data": df,
    }