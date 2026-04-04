"""
CoreSight Utility Functions.
Fixed for ANSI-aware alignment and pixel-perfect borders.
"""

import os
import datetime
import config
import shutil
import re

def get_terminal_size():
    size = shutil.get_terminal_size((80, 24))
    return size.columns, size.lines

def get_visible_length(text):
    """Calculates the length of text excluding ANSI escape codes."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', text))

def format_bytes(n, suffix='B', width=12):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols)}
    val, sym = float(n), ""
    for s in reversed(symbols):
        if n >= prefix[s]:
            val, sym = float(n) / prefix[s], s
            break
    result = f"{val:8.2f} {sym}{suffix}"
    return result.rjust(width)

def create_progress_bar(percent, width=20):
    percent = max(0, min(100, percent))
    filled_len = int(width * percent / 100)
    bar = "█" * filled_len + " " * (width - filled_len)
    color = config.COLORS["green"]
    if percent >= config.THRESHOLDS.get("cpu", 90):
        color = config.COLORS["red"] + config.COLORS["blink"]
    elif percent >= 70:
        color = config.COLORS["yellow"]
    return f"{color}▕{bar}▏{config.COLORS['reset']}"

def draw_box_line(content, width, align="left"):
    """Wraps content with side borders, accounting for ANSI colors."""
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

def log_message(module_name, message, level="INFO"):
    if not config.DEBUG and level == "DEBUG": return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(config.CACHE_DIR, f"{module_name}.log")
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")

def clear_screen():
    print("\033[H\033[J", end="") 
