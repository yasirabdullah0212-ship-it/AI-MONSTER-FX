from risk_engine import calculate_position_size


RISK_MODES = {
    "normal": 1.0,
    "high": 3.5,
    "aggressive": 5.0,
}


def build_trade_plan(
    symbol,
    action,
    entry_price,
    support,
    resistance,
    risk_level="normal",
    reward_ratio=2.0,
    activate_trailing=True,
    trailing_distance=None,
):
    """
    Builds a trade plan.

    IMPORTANT:
    This function does NOT place an MT5 order.
    """

    action = action.upper()

    if action not in ("BUY", "SELL"):
        return {
            "ok": False,
            "error": "Action must be BUY or SELL.",
        }

    if entry_price <= 0:
        return {
            "ok": False,
            "error": "Invalid entry price.",
        }

    if support <= 0 or resistance <= 0:
        return {
            "ok": False,
            "error": "Invalid support/resistance.",
        }

    if resistance <= support:
        return {
            "ok": False,
            "error": "Resistance must be above support.",
        }

    if reward_ratio <= 0:
        return {
            "ok": False,
            "error": "Reward ratio must be positive.",
        }

    market_range = resistance - support

    # Give the stop some room beyond the structure.
    structure_buffer = market_range * 0.05

    if action == "BUY":

        stop_loss = support - structure_buffer

        risk_distance = (
            entry_price - stop_loss
        )

        if risk_distance <= 0:
            return {
                "ok": False,
                "error": "Invalid BUY stop-loss distance.",
            }

        take_profit = (
            entry_price
            + risk_distance * reward_ratio
        )

    else:

        stop_loss = resistance + structure_buffer

        risk_distance = (
            stop_loss - entry_price
        )

        if risk_distance <= 0:
            return {
                "ok": False,
                "error": "Invalid SELL stop-loss distance.",
            }

        take_profit = (
            entry_price
            - risk_distance * reward_ratio
        )

    risk_result = calculate_position_size(
        symbol=symbol,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        risk_level=risk_level,
    )

    if not risk_result.get("ok"):

        return {
            "ok": False,
            "error": risk_result.get(
                "error",
                "Risk calculation failed.",
            ),
            "risk": risk_result,
        }

    return {
        "ok": True,
        "symbol": symbol,
        "action": action,
        "entry": round(entry_price, 5),
        "stop_loss": round(stop_loss, 5),
        "take_profit": round(take_profit, 5),
        "risk_distance": round(
            risk_distance,
            5,
        ),
        "reward_ratio": reward_ratio,
        "risk_level": risk_level,
        "risk_percent": RISK_MODES[risk_level],
        "volume": risk_result["volume"],
        "trailing_enabled": activate_trailing,
        "trailing_distance": trailing_distance,
    }