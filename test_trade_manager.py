import MetaTrader5 as mt5
from structure_engine import build_structure_trade
from market_data import find_symbol
from trade_manager import build_trade_plan


REQUESTED_SYMBOL = "XAUUSD"
RISK_LEVEL = "normal"


if not mt5.initialize():

    print("MT5 initialization failed:")
    print(mt5.last_error())

    raise SystemExit(1)


symbol = find_symbol(
    REQUESTED_SYMBOL
)

if symbol is None:

    raise SystemExit(
        f"Could not find {REQUESTED_SYMBOL}"
    )


if not mt5.symbol_select(
    symbol,
    True,
):

    raise SystemExit(
        f"Could not select {symbol}"
    )


tick = mt5.symbol_info_tick(
    symbol
)

if tick is None:

    raise SystemExit(
        f"No live price for {symbol}"
    )


entry = float(tick.ask)

# TEST VALUES ONLY.
# These are not sent to MT5.
support = entry - 2.0
resistance = entry + 2.0


plan = build_trade_plan
symbol=symbol,
action="BUY",
entry_price=entry,
support = entry - 0.50
resistance = entry + 0.50

swing_low = entry - 1.00
swing_high = entry + 1.00


structure = build_structure_trade(
    action="BUY",
    entry=entry,
    support=support,
    resistance=resistance,
    swing_low=swing_low,
    swing_high=swing_high,
    reward_ratio=2.0,
)


print("")
print("==========================================")
print("       AI MONSTER FX STRUCTURE")
print("==========================================")

for key, value in structure.items():
    print(f"{key}: {value}")


if not structure["ok"]:
    raise SystemExit(
        "Structure calculation failed."
    )


plan = build_trade_plan(
    symbol=symbol,
    action=structure["action"],
    entry_price=structure["entry"],
    support=structure["support"],
    resistance=structure["resistance"],
    risk_level=RISK_LEVEL,
    reward_ratio=structure["reward_ratio"],
    activate_trailing=True,
)