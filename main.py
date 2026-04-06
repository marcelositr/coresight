"""
CoreSight Unified Dashboard.
Professional Hybrid TUI for System Monitoring and CoreSight Hardware Trace.
Follows Senior Engineer standards and CoreSight Blueprint.

Architecture: Coordinator pattern with decomposed responsibilities.
- DataOrchestrator: Data collection and processing
- DashboardRenderer: UI formatting and rendering
- InputHandler: Terminal input and action dispatch
"""

import os
import sys
from typing import Any, Dict, Optional

# Import application layer (decomposed)
from app import DashboardRenderer, DataOrchestrator
from app.input_handler import InputHandler, create_default_input_handler
from core.topology_manager import TopologyManager
from core.trace_analyzer import TraceAnalyzer
from core.trace_capture import TraceCapture
from core.trace_decode import TraceDecode
from infra import utils
from system.alerts import Alerts

# Import System modules
from system.cpu import CPU
from system.disk import Disk
from system.logs import Logs
from system.network import Network
from system.ram import RAM


class CoreSightUnified:
    """
    Main Application Coordinator for CoreSight Dashboard.

    Follows Coordinator pattern: composes specialized orchestrators
    and manages the application lifecycle. Supports both System
    Monitoring and Hardware Trace Toolkit.

    Responsibilities:
    - Initialize and wire all dependencies
    - Run main application loop
    - Coordinate between orchestrators
    """

    def __init__(self, simulation: bool = True) -> None:
        """
        Initialize application and compose all orchestrators.

        Args:
            simulation: If True, use mock hardware topology.
        """
        self._running: bool = True
        self._simulation: bool = simulation
        self._view_mode: Dict[str, int] = {"mode": 1}  # 1: System, 2: CoreSight

        # Legacy UI state (for backward compatibility)
        self._terminal_width: int = 80
        self._terminal_height: int = 24
        self._last_formatted_output = []

        self._initialize_modules()
        self._compose_orchestrators()

    def _initialize_modules(self) -> None:
        """Instantiate all monitoring and CoreSight modules."""
        try:
            # System Monitors
            self._cpu = CPU()
            self._ram = RAM()
            self._disk = Disk()
            self._network = Network()
            self._logs = Logs()
            self._alerts = Alerts()

            # CoreSight Toolkit
            sysfs_base = "/sys/bus/coresight/devices/"

            if self._simulation and not os.path.exists(sysfs_base):
                sysfs_base = self._setup_mock_topology()

            self._topo = TopologyManager(base_path=sysfs_base)
            self._capture = TraceCapture()
            self._decoder = TraceDecode()
            self._analyzer = TraceAnalyzer()

            utils.log_message("main", "Industrial CoreSight modules initialized.")

        except Exception as e:
            utils.log_message(
                "main", f"Failed to initialize modules: {str(e)}", "CRITICAL"
            )
            sys.exit(1)

    def _setup_mock_topology(self) -> str:
        """Create mock CoreSight topology for simulation mode."""
        sysfs_base = "/tmp/coresight_mock/sys"
        os.makedirs(sysfs_base, exist_ok=True)

        devices = {
            "etm0": {"type": "1", "subtype": "etm"},
            "funnel0": {"type": "2", "subtype": "funnel"},
            "tmc_etr0": {"type": "3", "subtype": "etr"},
        }
        for dev, meta in devices.items():
            dpath = os.path.join(sysfs_base, dev)
            os.makedirs(dpath, exist_ok=True)
            with open(os.path.join(dpath, "type"), "w") as f:
                f.write(meta["type"])
            with open(os.path.join(dpath, "subtype"), "w") as f:
                f.write(meta["subtype"])
            with open(os.path.join(dpath, "enable_source"), "w") as f:
                f.write("0")
            with open(os.path.join(dpath, "enable_sink"), "w") as f:
                f.write("0")
            os.makedirs(os.path.join(dpath, "connection0"), exist_ok=True)

        try:
            os.symlink(
                os.path.join(sysfs_base, "funnel0"),
                os.path.join(sysfs_base, "etm0", "connection0", "device"),
            )
            os.symlink(
                os.path.join(sysfs_base, "tmc_etr0"),
                os.path.join(sysfs_base, "funnel0", "connection0", "device"),
            )
        except FileExistsError:
            pass

        return sysfs_base

    def _compose_orchestrators(self) -> None:
        """Wire up the three application orchestrators."""
        # Data layer
        self._orchestrator = DataOrchestrator(
            cpu=self._cpu,
            ram=self._ram,
            disk=self._disk,
            network=self._network,
            logs=self._logs,
            alerts=self._alerts,
            topology=self._topo,
            capture=self._capture,
        )

        # Presentation layer
        self._renderer = DashboardRenderer(
            orchestrator=self._orchestrator,
            analyzer=self._analyzer,
        )

        # Input layer (deferred setup - needs running state reference)
        self._input_handler: Optional[InputHandler] = None

    def _setup_input_handler(self) -> None:
        """Create and wire input handler with exit callback."""
        self._input_handler = create_default_input_handler(
            orchestrator=self._orchestrator,
            renderer=self._renderer,
            decoder=self._decoder,
            on_exit=self._stop,
            view_mode_ref=self._view_mode,
        )

    def _stop(self) -> None:
        """Signal application to stop running."""
        self._running = False

    @property
    def view_mode(self) -> int:
        """Current view mode (1: System, 2: CoreSight)."""
        return self._view_mode["mode"]

    # ========================================================================
    # BACKWARD COMPATIBILITY ALIASES
    # Delegate to orchestrators for existing code and tests.
    # ========================================================================

    @property
    def running(self) -> bool:
        """Legacy: access to running state."""
        return self._running

    @running.setter
    def running(self, value: bool) -> None:
        self._running = value

    @property
    def simulation(self) -> bool:
        """Legacy: access to simulation flag."""
        return self._simulation

    @property
    def formatted_output(self):
        """Legacy: access to last formatted output lines."""
        return getattr(self, "_last_formatted_output", [])

    @property
    def raw_data(self) -> Dict[str, Any]:
        """Legacy: access to collected raw data."""
        return self._orchestrator.raw_data

    @property
    def last_report(self) -> Dict[str, Any]:
        """Legacy: access to last analysis report."""
        return self._renderer.last_report

    @last_report.setter
    def last_report(self, value: Dict[str, Any]) -> None:
        self._renderer.last_report = value

    def collect_data(self) -> None:
        """Legacy: collect data from all monitors."""
        self._orchestrator.collect_all()

    def process_data(self) -> None:
        """Legacy: process alerts and adjust layout."""
        self._orchestrator.process_alerts()
        w, h = self._orchestrator.adjust_layout()
        self._terminal_width = w
        self._terminal_height = h

    def format_output(self) -> None:
        """Legacy: format output and store in formatted_output."""
        lines = self._renderer.format_output(self.view_mode)
        self._last_formatted_output = lines

    def render_screen(self) -> None:
        """Legacy: render stored formatted_output to screen."""
        self._renderer.render_screen(self.formatted_output)

    def run_analysis_action(self) -> None:
        """Legacy: run trace analysis with mock data."""
        self._renderer.run_analysis_action(self._decoder)

    def run(self) -> None:
        """
        Execute main application loop.

        Coordinates data refresh, rendering, and input handling
        until exit command received.
        """
        self._setup_input_handler()
        assert self._input_handler is not None  # Type narrowing
        self._input_handler.setup()

        try:
            while self._running:
                # Data refresh cycle
                self._orchestrator.refresh_cycle()

                # Rendering cycle
                lines = self._renderer.format_output(self.view_mode)
                self._renderer.render_screen(lines)

                # Input handling
                command = self._input_handler.read_input()
                if command:
                    self._input_handler.dispatch(command)

        finally:
            self._input_handler.cleanup()
            utils.clear_screen()
            print("CoreSight shutdown gracefully.")


if __name__ == "__main__":
    app = CoreSightUnified(simulation=True)
    app.run()
