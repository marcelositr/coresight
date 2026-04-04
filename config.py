"""
CoreSight Configuration File.
Defines thresholds, colors, refresh intervals, and debug flags.
"""

import os

# General Settings
REFRESH_INTERVAL = 1.0  # seconds
DEBUG = True
CACHE_DIR = os.path.expanduser("~/.cache/CoreSight")

# Thresholds (%)
THRESHOLDS = {
    "cpu": 90.0,
    "ram": 90.0,
    "disk": 90.0,
    "network": 90.0,
}

# Colors (ANSI Escape Codes)
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "reset": "\033[0m",
    "blink": "\033[5m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
}

# Logging settings
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
