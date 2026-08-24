import math
import MetaTrader5 as mt5


RISK_LEVELS = {
    "normal": 1.0,
    "high": 3.5,
    "aggressive": 5.0,
}


def get_risk_percent(level):
    level = str(level).lower().strip()

    if level not in RISK_LEVELS:
        raise ValueError(
            "Risk level must be normal, high, or aggressive."
        )

    return RISK_LEVELS[level]


def calculate_position_size(
    symbol,
    entry_price,
    stop_loss_price,
    risk_level="normal",
):

    if entry_price <= 0:
        return {
            "ok": False,
            "error": "Invalid entry price.",
        }

    if stop_loss_price <= 0:
        return {
            "ok": False,
            "error": "Invalid stop-loss price.",
        }

    risk_percent = get_risk_percent(
        risk_level
    )

    account = mt5.account_info()

    if account is None:
        return {
            "ok": False,
            "error": "Could not read MT5 account.",
        }

    info = mt5.symbol_info(symbol)

    if info is None:
        return {
            "ok": False,
            "error": f"MT5 symbol not found: {symbol}",
        }

    balance = float(account.balance)

    risk_money = (
        balance * risk_percent / 100.0
    )

    tick_size = float(
        info.trade_tick_size
    )

    tick_value = float(
        info.trade_tick_value
    )

    volume_min = float(
        info.volume_min
    )

    volume_max = float(
        info.volume_max
    )

    volume_step = float(
        info.volume_step
    )

    stop_distance = abs(
        entry_price - stop_loss_price
    )

    if tick_size <= 0:
        return {
            "ok": False,
            "error": "Invalid tick size.",
        }

    if tick_value <= 0:
        return {
            "ok": False,
            "error": "Invalid tick value.",
        }

    if volume_step <= 0:
        return {
            "ok": False,
            "error": "Invalid broker volume step.",
        }

    if stop_distance <= 0:
        return {
            "ok": False,
            "error": "Invalid stop-loss distance.",
        }

    ticks = (
        stop_distance / tick_size
    )

    risk_per_lot = (
        ticks * tick_value
    )

    if risk_per_lot <= 0:
        return {
            "ok": False,
            "error": "Invalid risk-per-lot calculation.",
        }

    raw_volume = (
        risk_money / risk_per_lot
    )

    # Respect the broker's actual volume step.
    # We round DOWN so we never intentionally exceed
    # the selected risk percentage.
    stepped_volume = (
        math.floor(
            raw_volume / volume_step
        )
        * volume_step
    )

    stepped_volume = round(
        stepped_volume,
        8,
    )

    # This is the broker's actual minimum,
    # not an artificial minimum created by us.
    if stepped_volume < volume_min:

        return {
            "ok": False,
            "error": (
                "Calculated position is too small "
                "for the broker's executable volume."
            ),
            "calculated_volume": raw_volume,
            "broker_min_volume": volume_min,
            "broker_step": volume_step,
            "risk_percent": risk_percent,
            "risk_money": risk_money,
        }

    if stepped_volume > volume_max:

        stepped_volume = volume_max

        stepped_volume = math.floor(
            stepped_volume / volume_step
        ) * volume_step

        stepped_volume = round(
            stepped_volume,
            8,
        )

    return {
        "ok": True,

        "symbol": symbol,

        "risk_level": risk_level,

        "risk_percent": risk_percent,

        "account_balance": round(
            balance,
            2,
        ),

        "risk_money": round(
            risk_money,
            4,
        ),

        "entry_price": entry_price,

        "stop_loss_price": stop_loss_price,

        "stop_distance": stop_distance,

        "tick_size": tick_size,

        "tick_value": tick_value,

        "risk_per_lot": risk_per_lot,

        "calculated_volume": raw_volume,
        "volume": stepped_volume,

        "broker_volume_min": volume_min,

        "broker_volume_max": volume_max,

        "broker_volume_step": volume_step,
    }