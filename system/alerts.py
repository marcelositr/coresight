"""
Alerts Management Module for CoreSight.
Encapsulates alert checking and notification when system thresholds are exceeded.

Refactored to use BaseMonitor Template Method pattern.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, List

from i18n import labels
from infra import config, utils

from .base_monitor import BaseMonitor


@dataclass
class AlertMetrics:
    """Value object representing alert state."""

    triggered: bool
    triggering_modules: List[str] = field(default_factory=list)

    @property
    def is_critical(self) -> bool:
        """Alias for triggered."""
        return self.triggered

    @property
    def module_count(self) -> int:
        """Number of modules that triggered alerts."""
        return len(self.triggering_modules)


class AlertsMonitor(BaseMonitor[AlertMetrics]):
    """
    Handles visual and sound alerts when system thresholds are exceeded.

    Extends BaseMonitor to inherit template method and common state.
    """

    _instance_name: str = "alerts"

    def __init__(self) -> None:
        """Initialize Alerts monitor with default state."""
        super().__init__()
        self._triggered: bool = False
        self._triggering_modules: List[str] = []

    @property
    def is_triggered(self) -> bool:
        """Check if any alert is currently triggered."""
        return self._triggered

    @property
    def triggered_modules(self) -> List[str]:
        """Get list of modules that triggered alerts."""
        return self._triggering_modules.copy()

    def _get_threshold(self, key: str) -> float:
        """Get threshold value from config."""
        return config.THRESHOLDS.get(key) or 90.0

    def _do_refresh(self) -> None:
        """
        Alerts don't auto-refresh via psutil — seu estado e controlado
        pelo metodo check() chamado externamente.
        """
        pass  # Alerts state is updated via check(), not auto-refreshed

    def _handle_refresh_error(self, error: Exception) -> None:
        """Reset alerts state on error."""
        self._triggered = False
        self._triggering_modules = []

    def check(
        self,
        cpu: float = 0.0,
        ram: float = 0.0,
        swap: float = 0.0,
        disks: list[float] | None = None,
        network: float = 0.0,
    ) -> bool:
        """
        Check metrics against thresholds.

        Args:
            cpu: Total CPU usage percentage.
            ram: RAM usage percentage.
            swap: Swap usage percentage.
            disks: List of disk usage percentages.
            network: Network usage (reserved for future).

        Returns:
            bool: True if any threshold exceeded.
        """
        self._triggered = False
        self._triggering_modules = []
        disks = disks or []

        if cpu >= self._get_threshold("cpu"):
            self._triggered = True
            self._triggering_modules.append("CPU")

        if ram >= self._get_threshold("ram"):
            self._triggered = True
            self._triggering_modules.append("RAM")

        if swap >= self._get_threshold("ram"):
            self._triggered = True
            self._triggering_modules.append("SWAP")

        for disk_pct in disks:
            if disk_pct >= self._get_threshold("disk"):
                self._triggered = True
                self._triggering_modules.append("DISK")
                break

        if self._triggered:
            utils.log_message(
                self._instance_name,
                f"ALERT by: {', '.join(self._triggering_modules)}",
                level="WARNING",
            )

        return self._triggered

    def check_thresholds(
        self,
        cpu_total: float,
        ram_percent: float,
        swap_percent: float,
        disks_percents: list[float],
        network_usage: float = 0.0,
    ) -> bool:
        """Legacy method for backward compatibility."""
        return self.check(
            cpu=cpu_total,
            ram=ram_percent,
            swap=swap_percent,
            disks=disks_percents,
            network=network_usage,
        )

    def update(self) -> bool:
        """Legacy method for backward compatibility."""
        return self._triggered

    def get_metrics(self) -> AlertMetrics:
        """Get current alert metrics."""
        return AlertMetrics(
            triggered=self._triggered,
            triggering_modules=self._triggering_modules.copy(),
        )

    def get_data(self) -> dict[str, Any]:
        """Get raw data for external systems."""
        return {
            "triggered": self._triggered,
            "modules": self._triggering_modules.copy(),
        }

    def format(self) -> list[str]:
        """Format alert for dashboard display."""
        alert_str = self.format_message()
        return [alert_str] if alert_str else []

    def format_message(self) -> str:
        """Format alert message string."""
        if not self._triggered:
            return ""

        alert_msg = f" !!! {labels['alerts'].upper()}: CRITICAL USAGE DETECTED [{', '.join(self._triggering_modules)}] !!! "
        return f"{config.COLORS['red']}{config.COLORS['blink']}{alert_msg}{config.COLORS['reset']}"

    def display_alert(self) -> str:
        """Alias for format_message."""
        return self.format_message()

    def display(self) -> str:
        """Alias for format_message."""
        return self.format_message()

    def beep(self) -> None:
        """Emit system beep if alert triggered."""
        if self._triggered:
            try:
                sys.stdout.write("\a")
                sys.stdout.flush()
            except Exception as e:
                utils.log_message(
                    self._instance_name, f"Beep failed: {e}", level="DEBUG"
                )

    def sound_alert(self) -> None:
        """Alias for beep()."""
        self.beep()


# Backward compatibility
Alerts = AlertsMonitor
