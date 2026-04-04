"""
CoreSight Utility Functions.
Standardized for Senior Engineer requirements with robust ANSI handling,
type safety, and professional logging.
"""

import os
import datetime
import shutil
import re
import sys
from typing import Tuple, List, Optional, Any, Dict
import config

def get_terminal_size() -> Tuple[int, int]:
    """
    Retrieves the current terminal size with a fail-safe default.
    
    Returns:
        Tuple[int, int]: Columns and lines.
    """
    try:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines
    except Exception:
        return 80, 24

def get_visible_length(text: str) -> int:
    """
    Calculates the visible length of a string, excluding ANSI escape sequences.
    
    Args:
        text (str): The string to measure.
        
    Returns:
        int: The number of visible characters.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', text))

def format_bytes(n: int, suffix: str = 'B', width: int = 12) -> str:
    """
    Formats a number of bytes into a human-readable string (KB, MB, GB, etc.).
    
    Args:
        n (int): Number of bytes.
        suffix (str): The suffix to use (default 'B').
        width (int): Total width for right-alignment (default 12).
        
    Returns:
        str: Human-readable byte string.
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols)}
    val, sym = float(n), ""
    for s in reversed(symbols):
        if n >= prefix[s]:
            val, sym = float(n) / prefix[s], s
            break
    result = f"{val:8.2f} {sym}{suffix}"
    return result.rjust(width)

def create_progress_bar(percent: float, width: int = 20, threshold_key: str = "cpu") -> str:
    """
    Creates a high-tech ANSI-colored progress bar.
    
    Args:
        percent (float): Percentage (0.0 to 100.0).
        width (int): Number of blocks in the bar.
        threshold_key (str): Key to look up in config.THRESHOLDS.
        
    Returns:
        str: Colored progress bar string.
    """
    percent = max(0.0, min(100.0, percent))
    filled_len = int(width * percent / 100)
    bar = "█" * filled_len + " " * (width - filled_len)
    
    threshold = config.THRESHOLDS.get(threshold_key, 90.0)
    
    color = config.COLORS["green"]
    if percent >= threshold:
        color = config.COLORS["red"] + config.COLORS["blink"]
    elif percent >= 70:
        color = config.COLORS["yellow"]
    
    return f"{color}▕{bar}▏{config.COLORS['reset']}"

def draw_box_line(content: str, width: int, align: str = "left") -> str:
    """
    Wraps content with side borders (│), accounting for ANSI escape sequences.
    
    Args:
        content (str): The text content (can contain ANSI colors).
        width (int): Total width of the box.
        align (str): Alignment ('left', 'center', 'right').
        
    Returns:
        str: Formatted box line.
    """
    visible_len = get_visible_length(content)
    available_space = width - 4
    padding_needed = max(0, available_space - visible_len)

    if align == "left":
        return f"│ {content}{' ' * padding_needed} │"
    elif align == "right":
        return f"│ {' ' * padding_needed}{content} │"
    else: # center
        pad_left = padding_needed // 2
        pad_right = padding_needed - pad_left
        return f"│ {' ' * pad_left}{content}{' ' * pad_right} │"

def log_message(module_name: str, message: str, level: str = "INFO") -> None:
    """
    Standardized logging following the blueprint specification:
    "timestamp | module | level | message"
    
    Args:
        module_name (str): Name of the reporting module.
        message (str): Log message.
        level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Check if we should log based on level
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    config_level = getattr(config, "LOG_LEVEL", "INFO")
    
    if level not in levels:
        level = "INFO"
    if config_level not in levels:
        config_level = "INFO"
    
    if levels.index(level) < levels.index(config_level):
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"{timestamp} | {module_name:10} | {level:8} | {message}\n"
    
    try:
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        # We use a central log file for a professional feel
        log_file = os.path.join(config.CACHE_DIR, "coresight.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(formatted_msg)
    except Exception:
        # Fail-safe: if logging fails, we don't want to crash the app
        pass

def clear_screen() -> None:
    """
    Fail-safe screen clearing using ANSI escape codes.
    Moves cursor to home (1,1) and clears the screen.
    """
    try:
        sys_stdout = getattr(shutil, "sys", None) # Just a placeholder check
        # ANSI: \033[H (Home) \033[2J (Clear Entire Screen)
        print("\033[H\033[2J", end="", flush=True)
    except Exception:
        # Fallback for systems that might not support ANSI via print
        os.system('cls' if os.name == 'nt' else 'clear')
