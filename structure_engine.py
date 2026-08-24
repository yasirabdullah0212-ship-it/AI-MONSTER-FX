import math


FIB_LEVELS = {
    "23.6": 0.236,
    "38.2": 0.382,
    "50.0": 0.500,
    "61.8": 0.618,
    "78.6": 0.786,
}


def calculate_fibonacci(
    swing_low,
    swing_high,
):
    if swing_high <= swing_low:
        raise ValueError("Invalid swing range.")

    distance = swing_high - swing_low

    return {
        name: swing_high - distance * ratio
        for name, ratio in FIB_LEVELS.items()
    }


def build_structure_trade(
    action,
    entry,
    support,
    resistance,
    swing_low,
    swing_high,
    reward_ratio=2.0,
):
    action = action.upper()

    if action not in ("BUY", "SELL"):
        return {
            "ok": False,
            "error": "Action must be BUY or SELL.",
        }

    if entry <= 0:
        return {
            "ok": False,
            "error": "Invalid entry.",
        }

    if support <= 0 or resistance <= support:
        return {
            "ok": False,
            "error": "Invalid support/resistance.",
        }

    if swing_low <= 0 or swing_high <= swing_low:
        return {
            "ok": False,
            "error": "Invalid swing range.",
        }

    fib = calculate_fibonacci(
        swing_low,
        swing_high,
    )

    structure_range = resistance - support

    # Small structure buffer.
    # This is based on market structure,
    # not a fixed $1 stop.
    buffer = structure_range * 0.03

    if action == "BUY":

        # Stop below support.
        stop_loss = support - buffer

        risk_distance = entry - stop_loss

        if risk_distance <= 0:
            return {
                "ok": False,
                "error": "BUY entry is below the structure stop.",
            }

        # Prefer resistance as the first structural target.
        structural_target = resistance

        minimum_target = (
            entry
            + risk_distance * reward_ratio
        )

        take_profit = max(
            structural_target,
            minimum_target,
        )

    else:

        # Stop above resistance.
        stop_loss = resistance + buffer

        risk_distance = stop_loss - entry

        if risk_distance <= 0:
            return {
                "ok": False,
                "error": "SELL entry is above the structure stop.",
            }

        structural_target = support

        minimum_target = (
            entry
            - risk_distance * reward_ratio
        )

        take_profit = min(
            structural_target,
            minimum_target,
        )

    return {
        "ok": True,
        "action": action,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_distance": risk_distance,
        "reward_ratio": reward_ratio,
        "support": support,
        "resistance": resistance,
        "swing_low": swing_low,
        "swing_high": swing_high,
        "fibonacci": fib,
    }