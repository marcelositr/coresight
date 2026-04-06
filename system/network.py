"""
Network Monitoring Module for CoreSight.
Encapsulates network interface throughput collection, processing, and formatting.

Refactored to use BaseMonitor Template Method pattern.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List

import psutil

from infra import config, utils

from .base_monitor import BaseMonitor


@dataclass
class InterfaceMetrics:
    """Value object representing a single network interface."""

    name: str
    upload_speed: float  # bytes per second
    download_speed: float  # bytes per second

    @property
    def upload_mbps(self) -> float:
        """Convert to megabytes per second."""
        return self.upload_speed / (1024 * 1024)

    @property
    def download_mbps(self) -> float:
        """Convert to megabytes per second."""
        return self.download_speed / (1024 * 1024)


@dataclass
class NetworkMetrics:
    """Container for all network interface metrics."""

    interfaces: Dict[str, InterfaceMetrics]
    reference_speed: int = 10 * 1024 * 1024  # 10 MB/s

    @property
    def interface_count(self) -> int:
        """Number of active interfaces."""
        return len(self.interfaces)


class NetworkMonitor(BaseMonitor[NetworkMetrics]):
    """
    Handles network interface throughput collection and formatting.

    Extends BaseMonitor to inherit template method and common state.
    """

    _instance_name: str = "network"
    _excluded_interfaces = {"lo"}
    _reference_speed: int = 10 * 1024 * 1024  # 10 MB/s reference for bars

    def __init__(self) -> None:
        """Initialize Network monitor with default state."""
        super().__init__()
        self._interfaces: Dict[str, InterfaceMetrics] = {}
        self._last_stats: Dict[str, Any] = {}
        self._last_time: float = 0.0

        self._initialize_stats()

    def _initialize_stats(self) -> None:
        """Initialize network stats for first reading."""
        try:
            self._last_stats = psutil.net_io_counters(pernic=True)
            self._last_time = time.time()
        except Exception as e:
            utils.log_message(self._instance_name, f"Init failed: {e}", level="ERROR")

    def _do_refresh(self) -> None:
        """Calculate current interface speeds."""
        self._interfaces = {}

        current_stats = psutil.net_io_counters(pernic=True)
        current_time = time.time()
        elapsed = current_time - self._last_time

        if elapsed <= 0:
            elapsed = 1.0

        for interface, stats in current_stats.items():
            if interface in self._excluded_interfaces:
                continue
            if stats.bytes_sent == 0 and stats.bytes_recv == 0:
                continue

            last = self._last_stats.get(interface)
            if last:
                self._interfaces[interface] = InterfaceMetrics(
                    name=interface,
                    upload_speed=max(0, (stats.bytes_sent - last.bytes_sent) / elapsed),
                    download_speed=max(
                        0, (stats.bytes_recv - last.bytes_recv) / elapsed
                    ),
                )

        self._last_stats = current_stats
        self._last_time = current_time

    def _handle_refresh_error(self, error: Exception) -> None:
        """Reset Network state on error."""
        self._interfaces = {}

    def get_metrics(self) -> NetworkMetrics:
        """Get current network metrics."""
        return NetworkMetrics(
            interfaces=self._interfaces.copy(), reference_speed=self._reference_speed
        )

    def get_data(self) -> Dict[str, Dict[str, float]]:
        """Get raw data for external systems."""
        return {
            iface: {"up": metrics.upload_speed, "down": metrics.download_speed}
            for iface, metrics in self._interfaces.items()
        }

    def _format_interface_line(self, metrics: InterfaceMetrics) -> str:
        """Format a single interface line."""
        half_bar = int(self._bar_width / 2)

        up_pct = min(100.0, (metrics.upload_speed / self._reference_speed) * 100.0)
        down_pct = min(100.0, (metrics.download_speed / self._reference_speed) * 100.0)

        up_bar = utils.create_progress_bar(up_pct, width=half_bar)
        down_bar = utils.create_progress_bar(down_pct, width=half_bar)

        up_str = (
            f"↑{utils.format_bytes(int(metrics.upload_speed), suffix='B', width=12)}/s"
        )
        down_str = f"↓{utils.format_bytes(int(metrics.download_speed), suffix='B', width=12)}/s"

        return f"{metrics.name:>{self._label_width}} {up_bar} {up_str} | {down_bar} {down_str}"

    def format(self) -> List[str]:
        """Format metrics for dashboard display with dynamic widths."""
        # Refresh dynamic layout from config
        self._bar_width = getattr(config, "DYNAMIC_BAR_WIDTH", 30)
        self._label_width = getattr(config, "DYNAMIC_LABEL_WIDTH", 25)

        return [self._format_interface_line(m) for m in self._interfaces.values()]


# Backward compatibility alias
Network = NetworkMonitor
