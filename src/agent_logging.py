"""Structured logging for AgentWorld. Zero cognitive code. Pure infrastructure."""
import logging as _stdlib_logging
import sys

_logger: _stdlib_logging.Logger | None = None


def setup(level: str = "INFO", verbose: bool = False):
    """Configure root logger. Call once at startup."""
    global _logger
    _logger = _stdlib_logging.getLogger("agentworld")
    _logger.setLevel(_stdlib_logging.DEBUG if verbose else getattr(_stdlib_logging, level.upper(), _stdlib_logging.INFO))
    _logger.handlers.clear()
    h = _stdlib_logging.StreamHandler(sys.stderr)
    h.setFormatter(_stdlib_logging.Formatter(
        fmt="%(asctime)s [%(levelname)-5s] %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    _logger.addHandler(h)


def get(name: str = "") -> _stdlib_logging.Logger:
    parent = _logger or _stdlib_logging.getLogger("agentworld")
    return parent.getChild(name) if name else parent


def debug(msg, *args):
    get().debug(msg, *args)


def info(msg, *args):
    get().info(msg, *args)


def warning(msg, *args):
    get().warning(msg, *args)
