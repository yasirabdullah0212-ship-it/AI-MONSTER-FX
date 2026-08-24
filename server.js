import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import crypto from "crypto";

dotenv.config();

const app = express();

const PORT = Number(process.env.PORT || 10000);
const BRIDGE_SECRET = process.env.BRIDGE_SECRET || "";

app.use(
  cors({
    origin: true,
    credentials: true,
  })
);

app.use(express.json({ limit: "1mb" }));

// ================================================================
// STATE
// ================================================================

const state = {
  mt5: {
    connected: false,
    lastHeartbeat: null,
    account: null,
    symbol: null,
    bid: 0,
    ask: 0,
    mode: "DEMO",
    timeframe: "M1",
  },

  market: {
    candles: [],
    lastCandle: null,
  },

  trading: {
    botRunning: false,
    lastCommandId: null,
    pendingCommand: null,
    lastAck: null,
  },

  positions: [],

  history: [],
};

// ================================================================
// HELPERS
// ================================================================

function now() {
  return new Date().toISOString();
}

function cleanNumber(value, fallback = 0) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : fallback;
}

function createId() {
  return crypto.randomUUID();
}

function bridgeAuthorized(req) {
  if (!BRIDGE_SECRET) {
    return false;
  }

  const supplied = String(
    req.headers["x-bridge-secret"] || ""
  );

  return supplied === BRIDGE_SECRET;
}

function requireBridge(req, res, next) {
  if (!bridgeAuthorized(req)) {
    return res.status(401).json({
      ok: false,
      error: "Unauthorized MT5 bridge",
    });
  }

  next();
}

function requireBody(req, res, next) {
  if (
    !req.body ||
    typeof req.body !== "object"
  ) {
    return res.status(400).json({
      ok: false,
      error: "Invalid JSON body",
    });
  }

  next();
}

function normalizePosition(position) {
  return {
    ticket:
      position.ticket ??
      position.id ??
      null,

    symbol:
      position.symbol ??
      position.SYMBOL ??
      "—",

    type:
      position.type ??
      "—",

    volume:
      cleanNumber(position.volume),

    price_open:
      cleanNumber(
        position.price_open ??
        position.open_price
      ),

    price_current:
      cleanNumber(
        position.price_current ??
        position.current_price
      ),

    sl:
      cleanNumber(position.sl),

    tp:
      cleanNumber(position.tp),

    profit:
      cleanNumber(position.profit),

    swap:
      cleanNumber(position.swap),

    time:
      position.time ??
      null,
  };
}

// ================================================================
// BASIC ROUTES
// ================================================================

app.get("/", (req, res) => {
  res.json({
    ok: true,
    service: "AI MONSTER FX Backend",
    status: "online",
    environment:
      process.env.NODE_ENV || "development",
    time: now(),
  });
});

app.get("/api/health", (req, res) => {
  res.json({
    ok: true,
    service: "AI MONSTER FX Backend",
    status: "healthy",
    mt5Connected: state.mt5.connected,
    botRunning: state.trading.botRunning,
    time: now(),
  });
});

// ================================================================
// MT5 STATUS
// ================================================================

app.get("/api/mt5/status", (req, res) => {
  const heartbeatAge =
    state.mt5.lastHeartbeat
      ? Date.now() -
        new Date(
          state.mt5.lastHeartbeat
        ).getTime()
      : null;

  const connected =
    state.mt5.connected &&
    heartbeatAge !== null &&
    heartbeatAge < 15000;

  state.mt5.connected = connected;

  res.json({
    ok: true,
    connected,
    mode: state.mt5.mode,
    botRunning:
      state.trading.botRunning,
    lastHeartbeat:
      state.mt5.lastHeartbeat,
    account:
      state.mt5.account,
    symbol:
      state.mt5.symbol,
    bid:
      state.mt5.bid,
    ask:
      state.mt5.ask,
    timeframe:
      state.mt5.timeframe,
  });
});
// ================================================================
// MT5 HEARTBEAT
// ================================================================

app.post(
  "/api/mt5/heartbeat",
  requireBridge,
  requireBody,
  (req, res) => {
    const body = req.body;

    state.mt5.connected = true;
    state.mt5.lastHeartbeat = now();

    state.mt5.account = {
      login:
        body.login ??
        body.account ??
        "—",

      account:
        body.account ??
        body.login ??
        "—",

      name:
        body.name ??
        body.accountName ??
        "MT5 Account",

      broker:
        body.broker ??
        body.company ??
        "—",

      server:
        body.server ??
        "—",

      currency:
        body.currency ??
        "USD",

      balance:
        cleanNumber(body.balance),

      equity:
        cleanNumber(body.equity),

      margin:
        cleanNumber(body.margin),

      free_margin:
        cleanNumber(
          body.free_margin ??
          body.freeMargin
        ),

      profit:
        cleanNumber(body.profit),

      connected: true,
    };

    state.mt5.symbol =
      body.SYMBOL ??
      body.symbol ??
      null;

    state.mt5.bid =
      cleanNumber(body.bid);

    state.mt5.ask =
      cleanNumber(body.ask);

    state.mt5.mode =
      String(
        body.mode ??
        "DEMO"
      ).toUpperCase() === "LIVE"
        ? "LIVE"
        : "DEMO";

    state.mt5.timeframe =
      body.timeframe ??
      "M1";

    res.json({
      ok: true,
      connected: true,
      serverTime: now(),
      botRunning:
        state.trading.botRunning,
    });
  }
);

// ================================================================
// MT5 CANDLE
// ================================================================

app.post(
  "/api/mt5/candle",
  requireBridge,
  requireBody,
  (req, res) => {
    const body = req.body;

    const candle = {
      symbol:
        body.SYMBOL ??
        body.symbol ??
        state.mt5.symbol,

      timeframe:
        body.timeframe ??
        "M1",

      open:
        cleanNumber(body.open),

      high:
        cleanNumber(body.high),

      low:
        cleanNumber(body.low),

      close:
        cleanNumber(body.close),

      volume:
        cleanNumber(body.volume),

      startTime:
        body.startTime ??
        null,

      endTime:
        body.endTime ??
        null,

      complete:
        Boolean(body.complete),

      receivedAt:
        now(),
    };

    state.market.lastCandle = candle;

    state.market.candles.push(candle);

    // Keep memory bounded.
    if (
      state.market.candles.length >
      1000
    ) {
      state.market.candles =
        state.market.candles.slice(-1000);
    }

    res.json({
      ok: true,
      received: true,
      candle,
    });
  }
);

// ================================================================
// ACCOUNT DATA FOR DASHBOARD
// ================================================================

app.get("/api/account", (req, res) => {
  const heartbeatAge =
    state.mt5.lastHeartbeat
      ? Date.now() -
        new Date(
          state.mt5.lastHeartbeat
        ).getTime()
      : null;

  const connected =
    state.mt5.connected &&
    heartbeatAge !== null &&
    heartbeatAge < 15000;

  state.mt5.connected = connected;

  const account =
    state.mt5.account || {
      connected: false,
      balance: 0,
      equity: 0,
      margin: 0,
      free_margin: 0,
      profit: 0,
      currency: "USD",
    };

  res.json({
    ok: true,

    connected,

    account: {
      ...account,
      connected,
    },

    positions:
      state.positions,

    mode:
      state.mt5.mode,

    botRunning:
      state.trading.botRunning,
  });
});

// ================================================================
// POSITIONS
// ================================================================

app.get(
  "/api/positions",
  (req, res) => {
    res.json({
      ok: true,
      positions:
        state.positions,
      count:
        state.positions.length,
    });
  }
);
// ================================================================
// MT5 POSITION UPDATE
// ================================================================

app.post(
  "/api/mt5/positions",
  requireBridge,
  requireBody,
  (req, res) => {
    const incoming =
      Array.isArray(req.body.positions)
        ? req.body.positions
        : [];

    state.positions =
      incoming.map(normalizePosition);

    res.json({
      ok: true,
      count:
        state.positions.length,
    });
  }
);

// ================================================================
// SYMBOL DATA
// ================================================================

app.get(
  "/api/symbol",
  (req, res) => {
    const symbol =
      req.query.symbol ||
      state.mt5.symbol;

    const lastCandle =
      state.market.candles
        .filter(
          (candle) =>
            candle.symbol === symbol
        )
        .at(-1);

    res.json({
      ok: true,

      symbol,

      bid:
        state.mt5.symbol === symbol
          ? state.mt5.bid
          : cleanNumber(
              lastCandle?.close
            ),

      ask:
        state.mt5.symbol === symbol
          ? state.mt5.ask
          : cleanNumber(
              lastCandle?.close
            ),

      support:
        null,

      resistance:
        null,

      timeframe:
        state.mt5.timeframe,

      mode:
        state.mt5.mode,
    });
  }
);

// ================================================================
// CANDLES FOR DASHBOARD
// ================================================================

app.get(
  "/api/candles",
  (req, res) => {
    const symbol =
      req.query.symbol ||
      state.mt5.symbol;

    const timeframe =
      req.query.timeframe ||
      "M1";

    const count = Math.min(
      Math.max(
        Number(req.query.count || 500),
        1
      ),
      1000
    );

    const candles =
      state.market.candles
        .filter(
          (candle) =>
            candle.symbol === symbol &&
            candle.timeframe === timeframe
        )
        .slice(-count);

    res.json({
      ok: true,
      symbol,
      timeframe,
      candles,
    });
  }
);

// ================================================================
// START BOT
// ================================================================

app.post(
  "/api/trading/start",
  (req, res) => {
    if (!state.mt5.connected) {
      return res.status(409).json({
        ok: false,
        error:
          "MT5 bridge is not connected.",
      });
    }

    state.trading.botRunning = true;

    const command = {
      id: createId(),
      action: "START_BOT",
      mode: state.mt5.mode,
      createdAt: now(),
    };

    state.trading.pendingCommand =
      command;

    res.json({
      ok: true,
      botRunning: true,
      command,
    });
  }
);

// ================================================================
// STOP BOT
// ================================================================

app.post(
  "/api/trading/stop",
  (req, res) => {
    state.trading.botRunning = false;

    const command = {
      id: createId(),
      action: "STOP_BOT",
      mode: state.mt5.mode,
      createdAt: now(),
    };

    state.trading.pendingCommand =
      command;

    res.json({
      ok: true,
      botRunning: false,
      command,
    });
  }
);

// ================================================================
// GET COMMAND FOR EA
// ================================================================

app.get(
  "/api/mt5/command",
  requireBridge,
  (req, res) => {
    if (!state.trading.pendingCommand) {
      return res.json({
        ok: true,
        action: "NONE",
      });
    }

    const command =
      state.trading.pendingCommand;

    res.json({
      ok: true,
      ...command,
    });
  }
);

// ================================================================
// SEND TRADING COMMAND
// ================================================================

app.post(
  "/api/trading/order",
  (req, res) => {
    if (!state.mt5.connected) {
      return res.
      status(409).json({
        ok: false,
        error:
          "MT5 bridge is not connected.",
      });
    }

    if (!state.trading.botRunning) {
      return res.status(409).json({
        ok: false,
        error:
          "Trading bot is stopped.",
      });
    }

    const {
      action,
      symbol,
      volume,
      sl,
      tp,
    } = req.body || {};

    const normalizedAction =
      String(action || "")
        .toUpperCase();

    if (
      normalizedAction !== "BUY" &&
      normalizedAction !== "SELL"
    ) {
      return res.status(400).json({
        ok: false,
        error:
          "Action must be BUY or SELL.",
      });
    }

    const command = {
      id: createId(),

      action:
        normalizedAction,

      mode:
        state.mt5.mode,

      SYMBOL:
        symbol ||
        state.mt5.symbol,

      volume:
        cleanNumber(volume, 0.01),

      sl:
        cleanNumber(sl, 0),

      tp:
        cleanNumber(tp, 0),

      createdAt:
        now(),
    };

    state.trading.lastCommandId =
      command.id;

    state.trading.pendingCommand =
      command;

    res.json({
      ok: true,
      command,
    });
  }
);

// ================================================================
// COMMAND ACKNOWLEDGEMENT
// ================================================================

app.post(
  "/api/mt5/command/ack",
  requireBridge,
  requireBody,
  (req, res) => {
    const ack = {
      ...req.body,
      receivedAt: now(),
    };

    state.trading.lastAck = ack;

    if (
      state.trading.pendingCommand &&
      ack.id ===
        state.trading.pendingCommand.id
    ) {
      state.trading.pendingCommand =
        null;
    }

    if (
      ack.action === "START_BOT" &&
      ack.status === "STARTED"
    ) {
      state.trading.botRunning = true;
    }

    if (
      ack.action === "STOP_BOT" &&
      ack.status === "STOPPED"
    ) {
      state.trading.botRunning = false;
    }

    if (
      ack.status === "DONE" &&
      ack.ticket
    ) {
      state.history.push({
        ...ack,
        recordedAt: now(),
      });

      if (
        state.history.length >
        1000
      ) {
        state.history =
          state.history.slice(-1000);
      }
    }

    res.json({
      ok: true,
      received: true,
    });
  }
);

// ================================================================
// TRADING STATUS
// ================================================================

app.get(
  "/api/trading/status",
  (req, res) => {
    res.json({
      ok: true,

      botRunning:
        state.trading.botRunning,

      mt5Connected:
        state.mt5.connected,

      mode:
        state.mt5.mode,

      pendingCommand:
        state.trading.pendingCommand,

      lastAck:
        state.trading.lastAck,
    });
  }
);

// ================================================================
// TRADE HISTORY
// ================================================================

app.get(
  "/api/trading/history",
  (req, res) => {
    res.json({
      ok: true,
      history:
        state.history,
    });
  }
);

// ================================================================
// 404
// ================================================================

app.use(
  (req, res) => {
    res.status(404).json({
      ok: false,
      error: "Endpoint not found",
      path: req.originalUrl,
    });
  }
);

// ================================================================
// ERROR HANDLER
// ================================================================

app.use(
  (err, req, res, next) => {
    console.error(
      "SERVER ERROR:",
      err
    );

    res.status(500).json({
      ok: false,
      error:
        "Internal server error",
    });
  }
);

// ================================================================
// START
// ================================================================

app.listen(
  PORT,
  "0.0.0.0",
  () => {
    console.log(
      "========================================"
    );

    console.log(
      "AI MONSTER FX BACKEND"
    );
    console.log(
      `Running on port ${PORT}`
    );

    console.log(
      `Environment: ${
        process.env.NODE_ENV ||
        "development"
      }`
    );

    console.log(
      `Bridge authentication: ${
        BRIDGE_SECRET
          ? "ENABLED"
          : "NOT CONFIGURED"
      }`
    );

    console.log(
      "MT5 API: READY"
    );

    console.log(
      "========================================"
    );
  }
);