"""
CPU Monitoring Module for CoreSight.
Encapsulates CPU metrics collection, processing, and formatting.

Refactored to use BaseMonitor Template Method pattern.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import psutil

from i18n import labels
from infra import config, utils

from .base_monitor import BaseMonitor


@dataclass
class CpuMetrics:
    """Value object representing CPU metrics."""

    per_core: List[float]
    total: float
    core_count: int

    @property
    def has_critical_usage(self) -> bool:
        """Check if any core exceeds threshold."""
        threshold = config.THRESHOLDS.get("cpu") or 90.0
        return any(pct >= threshold for pct in self.per_core) or self.total >= threshold


class CpuMonitor(BaseMonitor[CpuMetrics]):
    """
    Handles CPU metrics collection, processing, and formatting.

    Extends BaseMonitor to inherit:
    - Template Method refresh() with error handling
    - Common state (_bar_width, _label_width)
    - Legacy update() and to_string() implementations
    """

    MAX_CORES_DISPLAY = 8
    _instance_name: str = "cpu"

    def __init__(self) -> None:
        """Initialize CPU monitor with default state."""
        super().__init__()
        self._per_core: List[float] = []
        self._total: float = 0.0

    def _do_refresh(self) -> None:
        """Collect current CPU usage data from psutil."""
        self._per_core = psutil.cpu_percent(percpu=True)
        self._total = float(psutil.cpu_percent())

    def _handle_refresh_error(self, error: Exception) -> None:
        """Reset CPU state on error."""
        self._per_core = []
        self._total = 0.0

    def get_metrics(self) -> CpuMetrics:
        """Get current CPU metrics."""
        return CpuMetrics(
            per_core=self._per_core.copy(),
            total=self._total,
            core_count=len(self._per_core),
        )

    def get_data(self) -> Dict[str, Any]:
        """Get raw data dictionary for external systems."""
        return {"per_core": self._per_core.copy(), "total": self._total}

    def _format_core_line(self, index: int, percentage: float) -> str:
        """Format a single core line."""
        label = f"Core {index}"
        bar = utils.create_progress_bar(percentage, width=self._bar_width)
        return f"{label:>{self._label_width}} {bar} {percentage:6.2f} %"

    def _format_total_line(self, percentage: float) -> str:
        """Format the total CPU line."""
        label = f"{labels['cpu']} {labels['total']}"
        bar = utils.create_progress_bar(percentage, width=self._bar_width)
        return f"{label:>{self._label_width}} {bar} {percentage:6.2f} %"

    def format(self) -> List[str]:
        """Format metrics for dashboard display with dynamic widths."""
        # Refresh dynamic layout from config
        self._bar_width = getattr(config, "DYNAMIC_BAR_WIDTH", 30)
        self._label_width = getattr(config, "DYNAMIC_LABEL_WIDTH", 25)

        lines: List[str] = [self._format_total_line(self._total)]

        for i, pct in enumerate(self._per_core[: self.MAX_CORES_DISPLAY]):
            lines.append(self._format_core_line(i, pct))

        return lines

    def update(self) -> Tuple[List[float], float]:
        """Legacy method returning tuple for backward compatibility."""
        self.refresh()
        return self._per_core.copy(), self._total


# Backward compatibility alias
CPU = CpuMonitor
