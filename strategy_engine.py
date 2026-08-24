from dataclasses import dataclass
from typing import Optional


# ============================================================
# AI MONSTER FX — STRATEGY ENGINE
# ============================================================

@dataclass
class StrategySettings:
    symbol: str = "XAUUSD"
    timeframe: str = "M1"

    risk_mode: str = "normal"
    risk_percent: float = 1.0

    stop_loss_enabled: bool = True
    initial_sl: float = 0.0

    take_profit_enabled: bool = True
    take_profit: float = 0.0

    trailing_enabled: bool = False
    trailing_sl: float = 0.0

    lot_increment: float = 0.01
    lot_decrement: float = 0.01


@dataclass
class StrategySignal:
    action: str
    symbol: str
    timeframe: str
    reason: str = ""


class StrategyEngine:

    VALID_ACTIONS = {
        "BUY",
        "SELL",
        "HOLD",
    }

    VALID_TIMEFRAMES = {
        "M1",
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
    }

    VALID_RISK_MODES = {
        "normal": 1.0,
        "high": 3.5,
        "aggressive": 5.0,
    }

    def __init__(self, settings: Optional[StrategySettings] = None):
        self.settings = settings or StrategySettings()

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    def update_settings(self, **kwargs):

        for key, value in kwargs.items():

            if not hasattr(self.settings, key):
                continue

            setattr(self.settings, key, value)

        self._validate_settings()

        return self.settings

    def _validate_settings(self):

        if self.settings.timeframe not in self.VALID_TIMEFRAMES:
            raise ValueError("Unsupported timeframe.")

        if self.settings.risk_mode not in self.VALID_RISK_MODES:
            raise ValueError("Unsupported risk mode.")

        self.settings.risk_percent = (
            self.VALID_RISK_MODES[self.settings.risk_mode]
        )

        if self.settings.initial_sl < 0:
            raise ValueError("Initial SL cannot be negative.")

        if self.settings.take_profit < 0:
            raise ValueError("Take profit cannot be negative.")

        if self.settings.trailing_sl < 0:
            raise ValueError("Trailing SL cannot be negative.")

        if self.settings.lot_increment < 0:
            raise ValueError("Lot increment cannot be negative.")

        if self.settings.lot_decrement < 0:
            raise ValueError("Lot decrement cannot be negative.")

    # --------------------------------------------------------
    # SIGNAL INTERFACE
    # --------------------------------------------------------

    def generate_signal(
        self,
        symbol: str,
        timeframe: str,
    ) -> StrategySignal:

        """
        This function is intentionally the strategy interface.

        Your existing trading strategy will provide the
        actual BUY / SELL / HOLD decision here.
        """

        return StrategySignal(
            action="HOLD",
            symbol=symbol,
            timeframe=timeframe,
            reason="Waiting for strategy signal.",
        )

    # --------------------------------------------------------
    # ORDER PARAMETERS
    # --------------------------------------------------------

    def build_order_parameters(
        self,
        signal: StrategySignal,
    ):

        if signal.action not in self.VALID_ACTIONS:
            raise ValueError("Invalid strategy action.")

        if signal.action == "HOLD":
            return {
                "execute": False,
                "reason": "Strategy returned HOLD.",
            }

        if not self.settings.stop_loss_enabled:
            stop_loss = None
        else:
            stop_loss = self.settings.initial_sl

        if not self.settings.take_profit_enabled:
            take_profit = None
        else:
            take_profit = self.settings.take_profit

        return {
            "execute": False,
            "action": signal.action,
            "symbol": signal.symbol,
            "timeframe": signal.timeframe,

            "risk_mode": self.settings.risk_mode,
            "risk_percent": self.settings.risk_percent,

            "stop_loss_enabled":
                self.settings.stop_loss_enabled,

            "stop_loss":
                stop_loss,

            "take_profit_enabled":
                self.settings.take_profit_enabled,

            "take_profit":
                take_profit,

            "trailing_enabled":
                self.settings.trailing_enabled,

            "trailing_sl":
                self.settings.trailing_sl,

            "lot_increment":
                self.settings.lot_increment,

            "lot_decrement":
                self.settings.lot_decrement,

            "reason":
                signal.reason,
        }