from market_data import get_market_data
from market_strategy import MarketStrategy


SYMBOL = "XAUUSD"
TIMEFRAME = "M1"


result = get_market_data(
    SYMBOL,
    TIMEFRAME,
    500,
)


if not result["ok"]:
    print("MARKET DATA ERROR:")
    print(result["error"])
    raise SystemExit(1)


strategy = MarketStrategy()

signal = strategy.analyze(
    result["data"]
)


print("")
print("==========================================")
print("       AI MONSTER FX STRATEGY TEST")
print("==========================================")
print(f"Requested:    {SYMBOL}")
print(f"MT5 Symbol:   {result['symbol']}")
print(f"Timeframe:    {TIMEFRAME}")
print(f"Candles:      {result['candles']}")
print("------------------------------------------")
print(f"Action:       {signal.action}")
print(f"Score:        {signal.score}/{signal.max_score}")
print(f"Support:      {signal.support}")
print(f"Resistance:   {signal.resistance}")
print(f"Fibonacci:    {signal.fibonacci_zone}")
print(f"Reason:       {signal.reason}")
print("==========================================")
print("")