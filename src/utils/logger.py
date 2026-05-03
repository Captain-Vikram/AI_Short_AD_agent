"""Central logging setup for the project.

Provides a Rich console handler plus a file handler that writes to `run.log`.
Call `get_logger()` from modules instead of configuring logging locally.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

_CONFIGURED = False
_CONSOLE = Console()


def configure_logging(log_file: str = "run.log", level: int = logging.INFO, force: bool = False) -> None:
    """Configure the root logger once with Rich console output and file logging."""
    global _CONFIGURED

    root = logging.getLogger()
    if _CONFIGURED and not force:
        return

    if force:
        for handler in list(root.handlers):
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass

    install_rich_traceback(show_locals=False)
    root.setLevel(level)

    console_handler = RichHandler(
        console=_CONSOLE,
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=False,
        markup=True,
        omit_repeated_times=False,
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    file_path = Path(log_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

    root.addHandler(console_handler)
    root.addHandler(file_handler)
    _CONFIGURED = True


def get_logger(name: Optional[str] = None, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger.

    The first call installs the shared console/file logging handlers.
    """
    if log_file is None:
        log_file = "run.log"
    configure_logging(log_file=log_file, level=level)
    return logging.getLogger(name)


def log_json(logger: logging.Logger, label: str, data: Any, level: int = logging.INFO) -> None:
    """Log a JSON payload in a readable format."""
    try:
        payload = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    except Exception:
        payload = repr(data)
    logger.log(level, "%s\n%s", label, payload)
