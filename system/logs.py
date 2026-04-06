"""
Logs Monitoring Module for CoreSight.
Encapsulates system log monitoring for critical errors using journalctl.

Refactored to use BaseMonitor Template Method pattern.
"""

from __future__ import annotations

import datetime
import subprocess
from dataclasses import dataclass
from typing import Dict, List

from infra import config, utils

from .base_monitor import BaseMonitor


@dataclass
class LogEntry:
    """Value object representing a single log entry."""

    timestamp: str
    level: str
    message: str

    def truncate(self, max_length: int = 55) -> str:
        """Truncate message if too long."""
        if len(self.message) > max_length:
            return self.message[: max_length - 3] + "..."
        return self.message


@dataclass
class LogsMetrics:
    """Container for log metrics."""

    entries: List[LogEntry]
    has_entries: bool

    @property
    def entry_count(self) -> int:
        """Number of log entries."""
        return len(self.entries)


class LogsMonitor(BaseMonitor[LogsMetrics]):
    """
    Monitors system logs for critical errors using journalctl.

    Extends BaseMonitor to inherit template method and common state.
    """

    _instance_name: str = "logs"
    _max_entries = 5
    _log_levels = "err..crit"
    _output_format = "short-iso"

    def __init__(self) -> None:
        """Initialize Logs monitor and record start time."""
        super().__init__()
        self._entries: List[LogEntry] = []
        self._start_time: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        utils.log_message(
            self._instance_name,
            f"Monitoring started at {self._start_time}",
            level="INFO",
        )

    def _do_refresh(self) -> None:
        """Collect new critical system log entries since start."""
        self._entries = []

        cmd = [
            "journalctl",
            "-p",
            self._log_levels,
            "--since",
            self._start_time,
            "--no-pager",
            "-o",
            self._output_format,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line or line.startswith("--"):
                    continue

                entry = self._parse_line(line)
                if entry:
                    self._entries.append(entry)

            self._entries = self._entries[-self._max_entries :]

        utils.log_message(
            self._instance_name,
            f"Update: {len(self._entries)} logs since start.",
            level="DEBUG",
        )

    def _handle_refresh_error(self, error: Exception) -> None:
        """Reset Logs state on error."""
        self._entries = []

    def _parse_line(self, line: str) -> LogEntry | None:
        """Parse a single log line into LogEntry."""
        parts = line.split(" ", 3)
        if len(parts) < 4:
            return None

        try:
            timestamp = parts[0].split("T")[1][:8]
            return LogEntry(timestamp=timestamp, level="ERR", message=parts[3])
        except (IndexError, ValueError):
            return None

    def get_metrics(self) -> LogsMetrics:
        """Get current log metrics."""
        return LogsMetrics(
            entries=self._entries.copy(), has_entries=len(self._entries) > 0
        )

    def get_data(self) -> List[Dict[str, str]]:
        """Get raw data for external systems."""
        return [
            {"time": e.timestamp, "level": e.level, "msg": e.message}
            for e in self._entries
        ]

    def format(self) -> List[str]:
        """Format log entries for dashboard display."""
        if not self._entries:
            return [
                f"  {config.COLORS['green']}No critical events since start.{config.COLORS['reset']}"
            ]

        lines = []
        for entry in self._entries:
            level_color = config.COLORS["red"]
            line = f"{entry.timestamp} | {level_color}[{entry.level}]{config.COLORS['reset']} | {entry.truncate()}"
            lines.append(line)

        return lines


# Backward compatibility alias
Logs = LogsMonitor
