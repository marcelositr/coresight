"""
Data Orchestrator for CoreSight Dashboard.

Handles data collection from all monitors and processing (alerts, layout).
Follows Single Responsibility Principle: only orchestrates data flow.
"""

from typing import Any, Dict

from core.topology_manager import DeviceType, TopologyManager
from core.trace_capture import TraceCapture
from infra import config, utils


class DataOrchestrator:
    """
    Orchestrates data collection and processing for both System and CoreSight contexts.

    Responsibilities:
    - Collect data from all monitor modules
    - Process alerts against thresholds
    - Adjust dynamic layout parameters

    Example:
        >>> orchestrator = DataOrchestrator(cpu, ram, disk, network, logs, alerts, topo, capture)
        >>> orchestrator.collect_all()
        >>> orchestrator.process_alerts()
    """

    def __init__(
        self,
        cpu: Any,
        ram: Any,
        disk: Any,
        network: Any,
        logs: Any,
        alerts: Any,
        topology: TopologyManager,
        capture: TraceCapture,
    ) -> None:
        """
        Initialize orchestrator with all monitor dependencies.

        Args:
            cpu: CPU monitor instance.
            ram: RAM monitor instance.
            disk: Disk monitor instance.
            network: Network monitor instance.
            logs: Logs monitor instance.
            alerts: Alerts monitor instance.
            topology: CoreSight topology manager.
            capture: Trace capture engine.
        """
        self._cpu = cpu
        self._ram = ram
        self._disk = disk
        self._network = network
        self._logs = logs
        self._alerts = alerts
        self._topology = topology
        self._capture = capture

        self._raw_data: Dict[str, Any] = {}

    @property
    def raw_data(self) -> Dict[str, Any]:
        """Access collected data (read-only reference)."""
        return self._raw_data

    def collect_all(self) -> None:
        """
        Step 1: Collect data from all monitoring and toolkit modules.

        Refreshes each monitor and stores results in raw_data dict.
        Updates hardware enable state from sysfs.
        """
        try:
            # System monitors
            self._raw_data["cpu_cores"], self._raw_data["cpu_total"] = (
                self._cpu.update()
            )
            self._raw_data["ram_data"] = self._ram.update()
            self._raw_data["disks_data"] = self._disk.update()
            self._raw_data["network_data"] = self._network.update()
            self._raw_data["logs_data"] = self._logs.update()

            # CoreSight hardware status (poll enable state)
            for name, dev in self._topology.devices.items():
                node = (
                    "enable_source" if dev.type == DeviceType.SOURCE else "enable_sink"
                )
                dev.enabled = self._topology.hw.safe_read(name, node) == "1"

            # Capture engine status
            self._raw_data["capture_status"] = self._capture.status()

        except Exception as e:
            utils.log_message(
                "orchestrator", f"Data collection error: {str(e)}", "ERROR"
            )

    def process_alerts(self) -> None:
        """
        Step 2: Run alert checks against current metrics.

        Checks CPU, RAM, Swap, and Disk usage against configured thresholds.
        """
        try:
            self._alerts.check_thresholds(
                cpu_total=self._raw_data.get("cpu_total", 0),
                ram_percent=self._ram.ram_percent,
                swap_percent=self._ram.swap_percent,
                disks_percents=[
                    d["percent"] for d in self._raw_data.get("disks_data", [])
                ],
            )
        except Exception as e:
            utils.log_message(
                "orchestrator", f"Alert processing error: {str(e)}", "ERROR"
            )

    def adjust_layout(self) -> tuple[int, int]:
        """
        Step 3: Calculate and adjust dynamic layout parameters based on terminal size.

        Proportional allocation:
        - label_width: 20% of inner width
        - bar_width: 35% of inner width
        - Leaves room for borders, padding, and value display

        Returns:
            Tuple of (terminal_width, terminal_height).
        """
        width, height = utils.get_terminal_size()

        inner_w = width - 4  # Account for outer borders │ │
        config.DYNAMIC_LABEL_WIDTH = max(10, int(inner_w * 0.16))
        config.DYNAMIC_BAR_WIDTH = max(8, int(inner_w * 0.28))

        return width, height

    def refresh_cycle(self) -> tuple[int, int]:
        """
        Execute full refresh cycle: collect -> process -> adjust layout.

        Returns:
            Tuple of (terminal_width, terminal_height).
        """
        self.collect_all()
        self.process_alerts()
        return self.adjust_layout()

    # Accessors for monitors (used by renderer)
    @property
    def cpu(self) -> Any:
        return self._cpu

    @property
    def ram(self) -> Any:
        return self._ram

    @property
    def disk(self) -> Any:
        return self._disk

    @property
    def network(self) -> Any:
        return self._network

    @property
    def logs(self) -> Any:
        return self._logs

    @property
    def alerts(self) -> Any:
        return self._alerts

    @property
    def topology(self) -> TopologyManager:
        return self._topology

    @property
    def capture(self) -> TraceCapture:
        return self._capture
