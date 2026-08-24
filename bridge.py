import os
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5
from flask import Flask, jsonify, request
from flask_cors import CORS


# ============================================================
# AI MONSTER FX
# MT5 BRIDGE
# ============================================================

HOST = "0.0.0.0"
PORT = int(os.getenv("MT5_BRIDGE_PORT", "5001"))


app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": "*"
        }
    }
)


# ============================================================
# TIMEFRAMES
# ============================================================

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}


# ============================================================
# HELPERS
# ============================================================

def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def ensure_mt5():
    """
    Make sure the Python process is connected
    to the locally running MT5 terminal.
    """

    terminal = mt5.terminal_info()

    if terminal is not None:
        return True

    return bool(
        mt5.initialize()
    )


def find_symbol(requested_symbol):
    """
    Find the actual broker symbol.

    Example:

        XAUUSD
            ↓
        XAUUSDm

    or:

        XAUUSD
            ↓
        XAUUSD247m
    """

    requested = (
        requested_symbol
        .upper()
        .strip()
    )

    symbols = mt5.symbols_get()

    if symbols is None:
        return None

    # Exact match.
    for symbol in symbols:

        if (
            symbol.name.upper()
            == requested
        ):
            return symbol.name

    # Prefix match.
    for symbol in symbols:

        name = symbol.name.upper()

        if name.startswith(
            requested
        ):
            return symbol.name

    # Contains match.
    for symbol in symbols:

        name = symbol.name.upper()

        if requested in name:
            return symbol.name

    return None


def select_symbol(symbol):
    """
    Select a symbol in MT5 Market Watch.
    """

    if not mt5.symbol_select(
        symbol,
        True,
    ):
        return False

    return True


# ============================================================
# ACCOUNT
# ============================================================

def get_account_data():

    account = mt5.account_info()

    if account is None:

        return {
            "connected": False,
            "error": str(
                mt5.last_error()
            ),
        }

    return {
        "connected": True,
        "login": int(
            account.login
        ),
        "server": account.server,
        "name": account.name,
        "currency": account.currency,

        "balance": float(
            account.balance
        ),

        "equity": float(
            account.equity
        ),

        "margin": float(
            account.margin
        ),

        "free_margin": float(
            account.margin_free
        ),

        "profit": float(
            account.profit
        ),

        "leverage": int(
            account.leverage
        ),

        "trade_allowed": bool(
            account.trade_allowed
        ),

        "trade_expert": bool(
            account.trade_expert
        ),
    }


# ============================================================
# POSITIONS
# ============================================================

def get_positions():

    positions = mt5.positions_get()

    if positions is None:
        return []

    result = []

    for position in positions:

        result.append({
            "ticket": int(
                position.ticket
            ),

            "symbol": position.symbol,

            "type": int(
                position.type
            ),

            "volume": float(
                position.volume
            ),
            "price_open": float(
                position.price_open
            ),

            "price_current": float(
                position.price_current
            ),

            "stop_loss": float(
                position.sl
            ),

            "take_profit": float(
                position.tp
            ),

            "profit": float(
                position.profit
            ),

            "swap": float(
                position.swap
            ),

            "magic": int(
                position.magic
            ),

            "comment": position.comment,

            "time": int(
                position.time
            ),
        })

    return result


# ============================================================
# SYMBOL INFORMATION
# ============================================================

def get_symbol_data(symbol):

    actual_symbol = find_symbol(
        symbol
    )

    if actual_symbol is None:

        return {
            "ok": False,
            "error": (
                f"Symbol not found: {symbol}"
            ),
        }

    if not select_symbol(
        actual_symbol
    ):

        return {
            "ok": False,
            "error": (
                f"Could not select: "
                f"{actual_symbol}"
            ),
        }

    info = mt5.symbol_info(
        actual_symbol
    )

    tick = mt5.symbol_info_tick(
        actual_symbol
    )

    if info is None:

        return {
            "ok": False,
            "error": (
                f"Could not read "
                f"{actual_symbol}"
            ),
        }

    data = {
        "ok": True,

        "requested_symbol": symbol,

        "symbol": actual_symbol,

        "description": info.description,

        "currency_base": info.currency_base,

        "currency_profit": info.currency_profit,

        "digits": int(
            info.digits
        ),

        "point": float(
            info.point
        ),

        "trade_tick_size": float(
            info.trade_tick_size
        ),

        "trade_tick_value": float(
            info.trade_tick_value
        ),

        "volume_min": float(
            info.volume_min
        ),

        "volume_max": float(
            info.volume_max
        ),

        "volume_step": float(
            info.volume_step
        ),

        "spread": int(
            info.spread
        ),

        "trade_mode": int(
            info.trade_mode
        ),

        "visible": bool(
            info.visible
        ),
    }

    if tick is not None:

        data["bid"] = float(
            tick.bid
        )

        data["ask"] = float(
            tick.ask
        )

        data["last"] = float(
            tick.last
        )

        data["time"] = int(
            tick.time
        )

    return data


# ============================================================
# MARKET DATA
# ============================================================

def get_candles(
    symbol,
    timeframe="M1",
    count=500,
):

    timeframe = (
        timeframe
        .upper()
        .strip()
    )

    if timeframe not in TIMEFRAME_MAP:

        raise ValueError(
            "Unsupported timeframe. "
            "Use M1, M5, M15, M30, H1 or H4."
        )

    actual_symbol = find_symbol(
        symbol
    )

    if actual_symbol is None:

        raise ValueError(
            f"Symbol not found: {symbol}"
        )

    if not select_symbol(
        actual_symbol
    ):

        raise ValueError(
            f"Could not select: "
            f"{actual_symbol}"
        )

    count = max(
        1,
        min(
            int(count),
            5000,
        ),
    )

    rates = mt5.copy_rates_from_pos(
        actual_symbol,
        TIMEFRAME_MAP[timeframe],
        0,
        count,
    )

    if rates is None:

        raise ValueError(
            "MT5 returned no rates: "
            f"{mt5.last_error()}"
        )

    candles = []

    for rate in rates:

        candles.append({
            "time": int(
                rate["time"]
                ),

            "open": float(
                rate["open"]
            ),

            "high": float(
                rate["high"]
            ),

            "low": float(
                rate["low"]
            ),

            "close": float(
                rate["close"]
            ),

            "volume": int(
                rate["tick_volume"]
            ),

            "spread": int(
                rate["spread"]
            ),

            "real_volume": int(
                rate["real_volume"]
            ),
        })

    return {
        "symbol": actual_symbol,
        "requested_symbol": symbol,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles,
    }


# ============================================================
# SYMBOL LIST
# ============================================================

def get_symbols():

    symbols = mt5.symbols_get()

    if symbols is None:
        return []

    result = []

    for symbol in symbols:

        result.append({
            "name": symbol.name,
            "description": symbol.description,
            "visible": bool(
                symbol.visible
            ),
            "digits": int(
                symbol.digits
            ),
            "volume_min": float(
                symbol.volume_min
            ),
            "volume_max": float(
                symbol.volume_max
            ),
            "volume_step": float(
                symbol.volume_step
            ),
        })

    return result


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():

    return jsonify({
        "ok": True,
        "service": (
            "AI MONSTER FX MT5 Bridge"
        ),
        "status": "online",
        "time": utc_now(),
    })


@app.get("/health")
def health():

    connected = ensure_mt5()

    return jsonify({
        "ok": True,
        "connected": connected,
        "service": (
            "AI MONSTER FX MT5 Bridge"
        ),
        "time": utc_now(),
    })


@app.get("/api/health")
def api_health():

    connected = ensure_mt5()

    return jsonify({
        "ok": True,
        "connected": connected,
        "service": (
            "AI MONSTER FX MT5 Bridge"
        ),
        "time": utc_now(),
    })


@app.get("/api/account")
def account():

    if not ensure_mt5():

        return jsonify({
            "ok": False,
            "connected": False,
            "error": (
                "MT5 terminal is not connected."
            ),
        }), 503

    return jsonify({
        "ok": True,
        "time": utc_now(),
        "account": get_account_data(),
        "positions": get_positions(),
    })


@app.get("/api/mt5/status")
def mt5_status():

    if not ensure_mt5():

        return jsonify({
            "ok": False,
            "connected": False,
            "error": (
                "MT5 terminal is not connected."
            ),
        }), 503

    return jsonify({
        "ok": True,
        "connected": True,
        "account": get_account_data(),
        "positions": get_positions(),
        "time": utc_now(),
    })


@app.get("/api/positions")
def positions():

    if not ensure_mt5():

        return jsonify({
            "ok": False,
            "connected": False,
            "positions": [],
        }), 503

    return jsonify({
        "ok": True,
        "connected": True,
        "positions": get_positions(),
        "time": utc_now(),
    })


@app.get("/api/symbol")
def symbol():

    if not ensure_mt5():

        return jsonify({
            "ok": False,
            "error": (
                "MT5 terminal is not connected."
            ),
        }), 503

    requested = request.args.get(
        "symbol",
        "XAUUSD",
    )

    return jsonify(
        get_symbol_data(
            requested
        )
    )


@app.get("/api/symbols")
def symbols():

    if not ensure_mt5():

        return jsonify({
            "ok": False,
            "symbols": [],
            "error": (
                "MT5 terminal is not connected."
            ),
        }), 503

    data = get_symbols()

    return jsonify({
        "ok": True,
        "count": len(data),
        "symbols": data,
        "time": utc_now(),
    })


@app.get("/api/candles")
@app.get("/candles")
def candles():

    if not ensure_mt5():

        return jsonify({
            "ok": False,
            "candles": [],
            "error": (
                "MT5 terminal is not connected."
            ),
        }), 503

    symbol = request.args.get(
        "symbol",
        "XAUUSD",
    )

    timeframe = request.args.get(
        "timeframe",
        "M1",
    )

    try:

        count = int(
            request.args.get(
                "count",
                500,
            )
        )

        result = get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
        )

        return jsonify({
            "ok": True,
            **result,
            "time": utc_now(),
        })

    except Exception as error:

        return jsonify({
            "ok": False,
            "candles": [],
            "error": str(error),
            "time": utc_now(),
        }), 400


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        "        AI MONSTER FX MT5 BRIDGE"
    )
    print(
        "=========================================="
    )

    print(
        f"Starting bridge on "
        f"http://localhost:{PORT}"
    )

    if ensure_mt5():

        print(
            "MT5: CONNECTED"
        )

        account = mt5.account_info()

        if account:

            print(
                f"Account: {account.login}"
            )

            print(
                f"Server: {account.server}"
            )

            print(
                f"Balance: "
                f"{account.balance}"
            )

            print(
                f"Equity: "
                f"{account.equity}"
            )

            print(
                f"Trade allowed: "
                f"{account.trade_allowed}"
            )

    else:

        print(
            "MT5: NOT CONNECTED"
        )

        print(
            "Open MT5 and log into your account."
        )

    print(
        "=========================================="
    )
    print("")

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        threaded=True,
    )