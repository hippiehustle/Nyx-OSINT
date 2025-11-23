"""Logging infrastructure using structlog."""

import json
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colors
init(autoreset=True)


class ColoredConsoleRenderer:
    """Render log messages with colors for console output."""

    def __call__(self, logger: Any, name: str, event_dict: dict[str, Any]) -> str:
        """Render colored output."""
        level = event_dict.pop("level", "info").upper()
        timestamp = event_dict.pop("timestamp", "")
        message = event_dict.pop("event", "")

        level_colors = {
            "DEBUG": Fore.CYAN,
            "INFO": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Fore.RED + Style.BRIGHT,
        }

        color = level_colors.get(level, Fore.WHITE)
        prefix = f"{color}[{level}]{Style.RESET_ALL}"

        # Format remaining context
        context = " ".join(f"{k}={v}" for k, v in event_dict.items())
        if context:
            return f"{prefix} {timestamp} {message} {context}"
        return f"{prefix} {timestamp} {message}"


class JSONRenderer:
    """Render log messages as JSON for file output."""

    def __call__(self, logger: Any, name: str, event_dict: dict[str, Any]) -> str:
        """Render JSON output."""
        return json.dumps(event_dict)


def setup_logging(
    level: str = "INFO",
    log_file: str = "logs/nyx.log",
    max_file_size: int = 10485760,
    backup_count: int = 5,
) -> None:
    """Configure structlog and standard logging."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging for libraries
    stdlib_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_file_size, backupCount=backup_count
    )
    stdlib_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout),
            stdlib_handler,
        ],
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a named logger instance."""
    return structlog.get_logger(name)


# Initialize with defaults
_default_logger = logging.getLogger("nyx")


def configure_console_logging() -> None:
    """Configure console logging with colors."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            ColoredConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_json_logging(log_file: str = "logs/nyx.json") -> None:
    """Configure JSON logging for structured analysis."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
