"""Chess engine service for the MCP platform."""

from .engine_wrapper import StockfishEngine, StockfishError

__all__ = ["StockfishEngine", "StockfishError"]
