"""
RAM Monitoring Module for CoreSight.
Encapsulates memory (RAM and Swap) metrics collection, processing, and formatting.

Refactored to use BaseMonitor Template Method pattern.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import psutil

from i18n import labels
from infra import config, utils

from .base_monitor import BaseMonitor


@dataclass
class MemoryMetrics:
    """Value object representing memory metrics."""

    ram_percent: float
    ram_used: int
    ram_total: int
    swap_percent: float
    swap_used: int
    swap_total: int

    @property
    def ram_free(self) -> int:
        """Calculate free RAM in bytes."""
        return self.ram_total - self.ram_used

    @property
    def swap_free(self) -> int:
        """Calculate free Swap in bytes."""
        return self.swap_total - self.swap_used

    def has_critical_usage(self, threshold: float = 90.0) -> bool:
        """Check if RAM or Swap exceeds threshold."""
        return self.ram_percent >= threshold or self.swap_percent >= threshold


class RamMonitor(BaseMonitor[MemoryMetrics]):
    """
    Handles memory (RAM and Swap) metrics collection, processing, and formatting.

    Extends BaseMonitor to inherit template method and common state.
    """

    _instance_name: str = "ram"

    def __init__(self) -> None:
        """Initialize RAM monitor with default state."""
        super().__init__()
        self._ram_percent: float = 0.0
        self._ram_used: int = 0
        self._ram_total: int = 0
        self._swap_percent: float = 0.0
        self._swap_used: int = 0
        self._swap_total: int = 0

    def _do_refresh(self) -> None:
        """Collect current memory usage data from psutil."""
        vm = psutil.virtual_memory()
        self._ram_percent = vm.percent
        self._ram_used = vm.used
        self._ram_total = vm.total

        sm = psutil.swap_memory()
        self._swap_percent = sm.percent
        self._swap_used = sm.used
        self._swap_total = sm.total

    def _handle_refresh_error(self, error: Exception) -> None:
        """Reset RAM state on error."""
        self._ram_percent = 0.0
        self._swap_percent = 0.0

    def get_metrics(self) -> MemoryMetrics:
        """Get current memory metrics."""
        return MemoryMetrics(
            ram_percent=self._ram_percent,
            ram_used=self._ram_used,
            ram_total=self._ram_total,
            swap_percent=self._swap_percent,
            swap_used=self._swap_used,
            swap_total=self._swap_total,
        )

    def get_data(self) -> Dict[str, Any]:
        """Get raw data dictionary for external systems."""
        return {
            "ram": {
                "percent": self._ram_percent,
                "used": self._ram_used,
                "total": self._ram_total,
            },
            "swap": {
                "percent": self._swap_percent,
                "used": self._swap_used,
                "total": self._swap_total,
            },
        }

    def _format_memory_line(
        self, label: str, percent: float, used: int, total: int
    ) -> str:
        """Format a single memory line with adaptive detail."""
        bar = utils.create_progress_bar(percent, width=self._bar_width)
        # Adaptive: show detail only if bar is wide enough
        if self._bar_width >= 18:
            value = f"{percent:6.2f} % ({utils.format_bytes(used, width=8)} / {utils.format_bytes(total, width=8)})"
        else:
            value = f"{percent:6.2f} %"
        return f"{label:>{self._label_width}} {bar} {value}"

    def format(self) -> List[str]:
        """Format metrics for dashboard display with dynamic widths."""
        # Refresh dynamic layout from config
        self._bar_width = getattr(config, "DYNAMIC_BAR_WIDTH", 30)
        self._label_width = getattr(config, "DYNAMIC_LABEL_WIDTH", 25)

        ram_label = labels["ram"]
        swap_label = labels["swap"]

        return [
            self._format_memory_line(
                ram_label, self._ram_percent, self._ram_used, self._ram_total
            ),
            self._format_memory_line(
                swap_label, self._swap_percent, self._swap_used, self._swap_total
            ),
        ]

    # Properties for backward compatibility
    @property
    def ram_percent(self) -> float:
        return self._ram_percent

    @property
    def swap_percent(self) -> float:
        return self._swap_percent


# Backward compatibility alias
RAM = RamMonitor
