import MetaTrader5 as mt5

from risk_engine import calculate_position_size
from market_data import find_symbol


REQUESTED_SYMBOL = "XAUUSD"


if not mt5.initialize():
    print("MT5 initialization failed:")
    print(mt5.last_error())
    raise SystemExit(1)


symbol = find_symbol(REQUESTED_SYMBOL)

if symbol is None:
    print(f"Could not find broker symbol for {REQUESTED_SYMBOL}.")
    raise SystemExit(1)


print("")
print("==========================================")
print("       AI MONSTER FX RISK TEST")
print("==========================================")
print(f"Requested symbol: {REQUESTED_SYMBOL}")
print(f"MT5 symbol:       {symbol}")


symbol_info = mt5.symbol_info(symbol)

if symbol_info is None:
    print("Could not read symbol information.")
    raise SystemExit(1)


if not symbol_info.visible:
    if not mt5.symbol_select(symbol, True):
        print(f"Could not select {symbol}.")
        raise SystemExit(1)


tick = mt5.symbol_info_tick(symbol)

if tick is None:
    print(f"Could not get live price for {symbol}.")
    raise SystemExit(1)


entry = float(tick.ask)

# TEST ONLY.
# This is not an order.
stop_loss = entry - 1.0


print(f"Live ask:          {entry}")
print(f"Test stop loss:    {stop_loss}")
print("------------------------------------------")


for level in [
    "normal",
    "high",
    "aggressive",
]:

    result = calculate_position_size(
        symbol=symbol,
        entry_price=entry,
        stop_loss_price=stop_loss,
        risk_level=level,
    )

    print("")
    print(f"RISK MODE: {level.upper()}")

    if not result.get("ok"):
        print("Status: ERROR")
        print(f"Reason: {result.get('error')}")

        if "calculated_volume" in result:
            print(
                f"Calculated volume: "
                f"{result['calculated_volume']}"
            )

        if "broker_min_volume" in result:
            print(
                f"Broker minimum: "
                f"{result['broker_min_volume']}"
            )

        continue

    print("Status: OK")
    print(
        f"Risk: {result['risk_percent']}%"
    )
    print(
        f"Risk money: ${result['risk_money']}"
    )
    print(
        f"Calculated volume: {result['volume']}"
    )
    print(
        f"Broker min: {result['broker_volume_min']}"
    )
    print(
        f"Broker max: {result['broker_volume_max']}"
    )
    print(
        f"Volume step: {result['broker_volume_step']}"
    )


print("")
print("==========================================")
print("             TEST COMPLETE")
print("==========================================")