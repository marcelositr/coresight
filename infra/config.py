"""
CoreSight Configuration Module.
Type-safe, immutable configuration following Clean Code principles.

Provides structured access to application settings with backward compatibility.

Example:
    >>> from infra import config
    >>> threshold = config.THRESHOLDS.cpu  # Access via attribute
    >>> threshold = config.THRESHOLDS.get("cpu")  # Dict-style access
    >>> color = config.COLORS.green  # Enum-style access
    >>> color = config.COLORS["green"]  # Dict-style access
"""

import os
from typing import Dict, Optional


class _Thresholds:
    """
    Threshold configuration with dict-style and attribute access.

    Follows Single Responsibility: manages threshold values only.
    Supports both modern (attribute) and legacy (dict) access patterns.
    """

    def __init__(
        self,
        cpu: float = 90.0,
        ram: float = 90.0,
        disk: float = 90.0,
        network: float = 90.0,
    ) -> None:
        self._values: Dict[str, float] = {
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "network": network,
        }

    @property
    def cpu(self) -> float:
        """CPU usage threshold percentage."""
        return self._values["cpu"]

    @property
    def ram(self) -> float:
        """RAM usage threshold percentage."""
        return self._values["ram"]

    @property
    def disk(self) -> float:
        """Disk usage threshold percentage."""
        return self._values["disk"]

    @property
    def network(self) -> float:
        """Network usage threshold percentage."""
        return self._values["network"]

    def get(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """Dict-style access for backward compatibility."""
        return self._values.get(key, default)

    def __getitem__(self, key: str) -> float:
        """Bracket access for backward compatibility."""
        return self._values[key]

    def __repr__(self) -> str:
        return f"Thresholds({self._values})"


class _Colors:
    """
    ANSI color codes with dict-style and attribute access.

    Immutable constants following Singleton pattern.
    Supports both modern (attribute) and legacy (dict) access patterns.
    """

    def __init__(self) -> None:
        self._values: Dict[str, str] = {
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "reset": "\033[0m",
            "blink": "\033[5m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
        }

    @property
    def green(self) -> str:
        """Green ANSI color code."""
        return self._values["green"]

    @property
    def yellow(self) -> str:
        """Yellow ANSI color code."""
        return self._values["yellow"]

    @property
    def red(self) -> str:
        """Red ANSI color code."""
        return self._values["red"]

    @property
    def reset(self) -> str:
        """Reset ANSI color code."""
        return self._values["reset"]

    @property
    def blink(self) -> str:
        """Blink ANSI color code."""
        return self._values["blink"]

    @property
    def blue(self) -> str:
        """Blue ANSI color code."""
        return self._values["blue"]

    @property
    def cyan(self) -> str:
        """Cyan ANSI color code."""
        return self._values["cyan"]

    def __getitem__(self, key: str) -> str:
        """Dict-style access for backward compatibility."""
        return self._values[key]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Safe dict-style access with default."""
        return self._values.get(key, default)

    def __repr__(self) -> str:
        return f"Colors({list(self._values.keys())})"


# Module-level configuration instances (Singleton-like behavior)
THRESHOLDS = _Thresholds()
COLORS = _Colors()

# General Settings
REFRESH_INTERVAL: float = 1.0  # seconds
DEBUG: bool = True
CACHE_DIR: str = os.path.expanduser("~/.cache/CoreSight")

# Logging settings
LOG_LEVEL: str = "DEBUG" if DEBUG else "INFO"

# UI Dynamic Layout (mutable for runtime adjustments)
DYNAMIC_LABEL_WIDTH: int = 25
DYNAMIC_BAR_WIDTH: int = 30
