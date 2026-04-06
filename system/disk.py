"""
Disk Monitoring Module for CoreSight.
Encapsulates disk usage metrics collection, processing, and formatting.

Refactored to use BaseMonitor Template Method pattern.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import psutil

from infra import config, utils

from .base_monitor import BaseMonitor


@dataclass
class PartitionMetrics:
    """Value object representing a single partition's metrics."""

    mount: str
    total: int
    used: int
    percent: float

    @property
    def free(self) -> int:
        """Calculate free space in bytes."""
        return self.total - self.used

    @property
    def is_critical(self) -> bool:
        """Check if disk usage exceeds threshold."""
        threshold = config.THRESHOLDS.get("disk") or 90.0
        return self.percent >= threshold


@dataclass
class DiskMetrics:
    """Aggregate disk metrics container."""

    partitions: List[PartitionMetrics]

    @property
    def partition_count(self) -> int:
        """Number of partitions monitored."""
        return len(self.partitions)

    @property
    def has_critical(self) -> bool:
        """Check if any partition is critical."""
        return any(p.is_critical for p in self.partitions)


class DiskMonitor(BaseMonitor[DiskMetrics]):
    """
    Handles disk usage metrics collection, processing, and formatting.

    Extends BaseMonitor to inherit template method and common state.
    """

    _instance_name: str = "disk"
    _excluded_devices = {"loop"}
    _excluded_mounts = {"snap"}

    def __init__(self) -> None:
        """Initialize Disk monitor with default state."""
        super().__init__()
        self._partitions: List[PartitionMetrics] = []

    def _is_valid_partition(self, partition) -> bool:
        """Check if partition should be monitored."""
        if partition.fstype == "":
            return False
        if any(excl in partition.device for excl in self._excluded_devices):
            return False
        if any(excl in partition.mountpoint for excl in self._excluded_mounts):
            return False
        return True

    def _do_refresh(self) -> None:
        """Collect current disk usage data from psutil."""
        self._partitions = []
        partitions = psutil.disk_partitions()

        for partition in partitions:
            if not self._is_valid_partition(partition):
                continue

            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self._partitions.append(
                    PartitionMetrics(
                        mount=partition.mountpoint,
                        total=usage.total,
                        used=usage.used,
                        percent=usage.percent,
                    )
                )
            except (PermissionError, FileNotFoundError) as e:
                utils.log_message(
                    self._instance_name,
                    f"Skip partition {partition.mountpoint}: {e}",
                    level="DEBUG",
                )
            except Exception as e:
                utils.log_message(
                    self._instance_name,
                    f"Error reading disk {partition.mountpoint}: {e}",
                    level="ERROR",
                )

    def _handle_refresh_error(self, error: Exception) -> None:
        """Reset Disk state on error."""
        self._partitions = []

    def get_metrics(self) -> DiskMetrics:
        """Get current disk metrics."""
        return DiskMetrics(partitions=self._partitions.copy())

    def get_data(self) -> List[Dict[str, Any]]:
        """Get raw data list for external systems."""
        return [
            {"mount": p.mount, "total": p.total, "used": p.used, "percent": p.percent}
            for p in self._partitions
        ]

    def _format_partition_line(self, partition: PartitionMetrics) -> str:
        """Format a single partition line with adaptive detail."""
        mount = partition.mount
        if len(mount) > self._label_width:
            mount = "..." + mount[-(self._label_width - 3) :]

        bar = utils.create_progress_bar(partition.percent, width=self._bar_width)
        # Adaptive: show detail only if bar is wide enough
        if self._bar_width >= 18:
            value = f"{partition.percent:6.2f} % ({utils.format_bytes(partition.used, width=8)} / {utils.format_bytes(partition.total, width=8)})"
        else:
            value = f"{partition.percent:6.2f} %"
        return f"{mount:>{self._label_width}} {bar} {value}"

    def format(self) -> List[str]:
        """Format metrics for dashboard display with dynamic widths."""
        # Refresh dynamic layout from config
        self._bar_width = getattr(config, "DYNAMIC_BAR_WIDTH", 30)
        self._label_width = getattr(config, "DYNAMIC_LABEL_WIDTH", 25)

        return [self._format_partition_line(p) for p in self._partitions]


# Backward compatibility alias
Disk = DiskMonitor
