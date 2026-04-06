"""
CoreSight Utility Module.
Refactored following Clean Code principles with separated responsibilities.

Provides:
- TerminalFormatter: ANSI formatting (progress bars, boxes, visibility)
- FileLogger: Centralized file logging
- Standalone utilities: get_terminal_size, format_bytes, clear_screen

All legacy functions are preserved for backward compatibility.

Example:
    >>> from infra import utils
    >>> # Legacy usage (backward compatible)
    >>> utils.create_progress_bar(75.0, width=20)
    >>> utils.log_message("module", "message", "INFO")
    >>> # New OOP usage
    >>> formatter = utils.TerminalFormatter()
    >>> formatter.draw_box_line("Title", 80)
"""

import datetime
import os
import re
import shutil
from typing import List, Optional, Tuple

from . import config

# Module-level regex constant for ANSI escape sequences
_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class TerminalFormatter:
    """
    Handles ANSI terminal formatting operations.

    Single Responsibility: Format strings with ANSI colors, progress bars,
    and box borders. State regarding dynamic widths is encapsulated.

    Example:
        >>> formatter = TerminalFormatter()
        >>> formatter.draw_box_line("Title", 80)
        '│ Title                                                              │'
    """

    def __init__(self) -> None:
        """Initialize formatter."""
        pass  # Uses module-level _ANSI_ESCAPE constant

    def get_visible_length(self, text: str) -> int:
        """
        Calculate visible length of string excluding ANSI escape sequences.

        Args:
            text: String that may contain ANSI codes.

        Returns:
            Number of visible characters.
        """
        return len(_ANSI_ESCAPE.sub("", text))

    def create_progress_bar(
        self, percent: float, width: int = 20, threshold_key: str = "cpu"
    ) -> str:
        """
        Create ANSI-colored progress bar.

        Args:
            percent: Percentage (0.0 to 100.0).
            width: Number of blocks in the bar.
            threshold_key: Key to look up in config.THRESHOLDS.

        Returns:
            Colored progress bar string.
        """
        percent = max(0.0, min(100.0, percent))
        filled_len = int(width * percent / 100)
        bar = "█" * filled_len + " " * (width - filled_len)

        threshold = config.THRESHOLDS.get(threshold_key) or 90.0

        color = config.COLORS["green"]
        if percent >= threshold:
            color = config.COLORS["red"] + config.COLORS["blink"]
        elif percent >= 70:
            color = config.COLORS["yellow"]

        return f"{color}▕{bar}▏{config.COLORS['reset']}"

    def draw_box_line(self, content: str, width: int, align: str = "left") -> str:
        """
        Wrap content with side borders, accounting for ANSI escape sequences.

        Args:
            content: Text content (can contain ANSI colors).
            width: Total width of the box.
            align: Alignment ('left', 'center', 'right').

        Returns:
            Formatted box line.
        """
        visible_len = self.get_visible_length(content)
        available_space = width - 5  # "│ " (2) + " │" (2) + 1 buffer
        padding_needed = max(0, available_space - visible_len)

        if align == "left":
            return f"│ {content}{' ' * padding_needed} │"
        elif align == "right":
            return f"│ {' ' * padding_needed}{content} │"
        else:  # center
            pad_left = padding_needed // 2
            pad_right = padding_needed - pad_left
            return f"│ {' ' * pad_left}{content}{' ' * pad_right} │"


class FileLogger:
    """
    Handles file-based logging following blueprint specification.

    Single Responsibility: Write structured log messages to file.
    Format: "timestamp | module | level | message"

    Example:
        >>> logger = FileLogger()
        >>> logger.log("module", "message", "INFO")
    """

    _levels: List[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(
        self, log_dir: Optional[str] = None, log_file_name: str = "coresight.log"
    ) -> None:
        """
        Initialize logger.

        Args:
            log_dir: Directory for log files. Defaults to config.CACHE_DIR.
            log_file_name: Name of the log file.
        """
        self._log_dir = log_dir or config.CACHE_DIR
        self._log_file = os.path.join(self._log_dir, log_file_name)

    def log(self, module_name: str, message: str, level: str = "INFO") -> None:
        """
        Write structured log message following blueprint spec.

        Args:
            module_name: Name of the reporting module.
            message: Log message.
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        if level not in self._levels:
            level = "INFO"

        config_level_str = getattr(config, "LOG_LEVEL", "INFO")
        if config_level_str not in self._levels:
            config_level_str = "INFO"

        if self._levels.index(level) < self._levels.index(config_level_str):
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"{timestamp} | {module_name:10} | {level:8} | {message}\n"

        try:
            os.makedirs(self._log_dir, exist_ok=True)
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg)
        except Exception:
            pass  # Fail-safe: don't crash the app if logging fails


# Module-level instances (Singleton-like behavior)
_formatter = TerminalFormatter()
_logger = FileLogger()


# ============================================================================
# BACKWARD COMPATIBLE FUNCTIONS
# These functions delegate to the OOP classes above.
# All existing code continues to work without changes.
# ============================================================================


def get_terminal_size() -> Tuple[int, int]:
    """
    Retrieve current terminal size with fail-safe default.

    Returns:
        Tuple of (columns, lines).
    """
    try:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines
    except Exception:
        return 80, 24


def get_visible_length(text: str) -> int:
    """
    Calculate visible length of string excluding ANSI escape sequences.

    Legacy wrapper for backward compatibility.

    Args:
        text: String that may contain ANSI codes.

    Returns:
        Number of visible characters.
    """
    return _formatter.get_visible_length(text)


def format_bytes(n: int, suffix: str = "B", width: int = 12) -> str:
    """
    Format number of bytes into human-readable string.

    Args:
        n: Number of bytes.
        suffix: Suffix to use (default 'B').
        width: Total width for right-alignment (default 12).

    Returns:
        Human-readable byte string.
    """
    symbols = ("K", "M", "G", "T", "P", "E", "Z", "Y")
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols)}
    val, sym = float(n), ""
    for s in reversed(symbols):
        if n >= prefix[s]:
            val, sym = float(n) / prefix[s], s
            break
    result = f"{val:8.2f} {sym}{suffix}"
    return result.rjust(width)


def create_progress_bar(
    percent: float, width: int = 20, threshold_key: str = "cpu"
) -> str:
    """
    Create ANSI-colored progress bar.

    Legacy wrapper for backward compatibility.

    Args:
        percent: Percentage (0.0 to 100.0).
        width: Number of blocks in the bar.
        threshold_key: Key to look up in config.THRESHOLDS.

    Returns:
        Colored progress bar string.
    """
    return _formatter.create_progress_bar(percent, width, threshold_key)


def draw_box_line(content: str, width: int, align: str = "left") -> str:
    """
    Wrap content with side borders, accounting for ANSI escape sequences.

    Legacy wrapper for backward compatibility.

    Args:
        content: Text content (can contain ANSI colors).
        width: Total width of the box.
        align: Alignment ('left', 'center', 'right').

    Returns:
        Formatted box line.
    """
    return _formatter.draw_box_line(content, width, align)


def log_message(module_name: str, message: str, level: str = "INFO") -> None:
    """
    Standardized logging following blueprint specification.

    Legacy wrapper for backward compatibility.

    Args:
        module_name: Name of the reporting module.
        message: Log message.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    _logger.log(module_name, message, level)


def clear_screen() -> None:
    """
    Fail-safe screen clearing using ANSI escape codes.
    Moves cursor to home (1,1) and clears the screen.
    """
    try:
        print("\033[H\033[2J", end="", flush=True)
    except Exception:
        os.system("cls" if os.name == "nt" else "clear")
