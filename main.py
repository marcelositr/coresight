"""
CoreSight Unified Dashboard.
Professional Hybrid TUI for System Monitoring and CoreSight Hardware Trace.
Follows Senior Engineer standards and CoreSight Blueprint.
"""

import time
import sys
import os
import datetime
import select
try:
    import tty
    import termios
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False
from typing import List, Dict, Any, Optional

import config
import utils
from i18n import labels

# Import System modules (original)
from modules.cpu import CPU
from modules.ram import RAM
from modules.disk import Disk
from modules.network import Network
from modules.logs import Logs
from modules.alerts import Alerts

# Import CoreSight modules (industrial)
from modules.topology_manager import TopologyManager, DeviceType
from modules.trace_capture import TraceCapture
from modules.trace_sink import TraceSink
from modules.trace_decode import TraceDecode
from modules.trace_analyzer import TraceAnalyzer
from modules.perf_bridge import PerfBridge

class CoreSightUnified:
    """
    Main Application Class for CoreSight Dashboard.
    Supports both System Monitoring and Hardware Trace Toolkit.
    """
    
    def __init__(self, simulation: bool = True) -> None:
        """
        Initializes the application, modules, and terminal state.
        """
        self.module_name: str = "main"
        self.running: bool = True
        self.simulation = simulation
        self.view_mode: int = 1 # 1: System, 2: CoreSight Toolkit
        
        # UI State
        self.terminal_width: int = 80
        self.terminal_height: int = 24
        self.formatted_output: List[str] = []
        
        # State storage for the pipeline
        self.raw_data: Dict[str, Any] = {}
        self.last_report: Dict[str, Any] = {"status": "empty"}
        
        self._initialize_modules()

    def _initialize_modules(self) -> None:
        """
        Instantiates all monitoring and toolkit modules with hardware discovery.
        """
        try:
            # 1. System Monitors
            self.cpu = CPU()
            self.ram = RAM()
            self.disk = Disk()
            self.network = Network()
            self.logs = Logs()
            self.alerts = Alerts()
            
            # 2. CoreSight Toolkit
            sysfs_base = "/sys/bus/coresight/devices/"
            
            # Check for real hardware first; fallback to mock if simulation and no real hw
            if self.simulation and not os.path.exists(sysfs_base):
                sysfs_base = "/tmp/coresight_mock/sys"
                os.makedirs(sysfs_base, exist_ok=True)
                # Create standard mock topology: ETM -> Funnel -> ETR
                devices = {
                    "etm0": {"type": "1", "subtype": "etm"},
                    "funnel0": {"type": "2", "subtype": "funnel"},
                    "tmc_etr0": {"type": "3", "subtype": "etr"}
                }
                for dev, meta in devices.items():
                    dpath = os.path.join(sysfs_base, dev)
                    os.makedirs(dpath, exist_ok=True)
                    with open(os.path.join(dpath, "type"), 'w') as f: f.write(meta["type"])
                    with open(os.path.join(dpath, "subtype"), 'w') as f: f.write(meta["subtype"])
                    with open(os.path.join(dpath, "enable_source"), 'w') as f: f.write("0")
                    with open(os.path.join(dpath, "enable_sink"), 'w') as f: f.write("0")
                    # Create connections node
                    os.makedirs(os.path.join(dpath, "connection0"), exist_ok=True)
                
                # Mock connections (hardlinked or logic-based symlinks)
                # For mock, we'll just let the TopologyManager find them if we link them correctly
                try:
                    os.symlink(os.path.join(sysfs_base, "funnel0"), os.path.join(sysfs_base, "etm0", "connection0", "device"))
                    os.symlink(os.path.join(sysfs_base, "tmc_etr0"), os.path.join(sysfs_base, "funnel0", "connection0", "device"))
                except FileExistsError: pass

            self.topo = TopologyManager(base_path=sysfs_base)
            self.capture = TraceCapture()
            self.sink = TraceSink(self.capture)
            self.decoder = TraceDecode()
            self.analyzer = TraceAnalyzer()
            self.perf = PerfBridge()

            utils.log_message(self.module_name, "Industrial CoreSight modules initialized.")

        except Exception as e:
            utils.log_message(self.module_name, f"Failed to initialize modules: {str(e)}", "CRITICAL")
            sys.exit(1)

    def collect_data(self) -> None:
        """
        Step 1: Mandatory Data Collection for both contexts (Dynamic Hardware).
        """
        try:
            # 1. System Monitors
            self.raw_data['cpu_cores'], self.raw_data['cpu_total'] = self.cpu.update()
            self.raw_data['ram_data'] = self.ram.update()
            self.raw_data['disks_data'] = self.disk.update()
            self.raw_data['network_data'] = self.network.update()
            self.raw_data['logs_data'] = self.logs.update()
            
            # 2. Toolkit Status (re-reading enabled state for UI)
            # In a real tool, we might only refresh on trigger, but for TUI we poll.
            for name, dev in self.topo.devices.items():
                node = "enable_source" if dev.type == DeviceType.SOURCE else "enable_sink"
                dev.enabled = (self.topo.hw.safe_read(name, node) == "1")
            
            self.capture_status = self.capture.status()
            
        except Exception as e:
            utils.log_message(self.module_name, f"Data collection error: {str(e)}", "ERROR")

    def process_data(self) -> None:
        """
        Step 2: Data Processing and Layout Updates.
        """
        try:
            # Alerts processing
            self.alerts.check_thresholds(
                cpu_total=self.raw_data.get('cpu_total', 0),
                ram_percent=self.ram.ram_percent,
                swap_percent=self.ram.swap_percent,
                disks_percents=[d['percent'] for d in self.raw_data.get('disks_data', [])]
            )
            
            self.terminal_width, self.terminal_height = utils.get_terminal_size()
            
            # Dynamic layout adjustments
            inner_w = self.terminal_width - 4
            config.DYNAMIC_LABEL_WIDTH = max(12, int(inner_w * 0.18))
            config.DYNAMIC_BAR_WIDTH = max(10, int(inner_w * 0.32))
            
        except Exception as e:
            utils.log_message(self.module_name, f"Data processing error: {str(e)}", "ERROR")

    def _format_system_view(self, w: int) -> List[str]:
        lines = []
        sections = [
            (labels['cpu'], self.cpu.format()),
            (labels['ram'], self.ram.format()),
            (labels['disk'], self.disk.format()),
            (labels['network'], self.network.format()),
            (labels['logs'], self.logs.format())
        ]
        for title, section_lines in sections:
            lines.append(utils.draw_box_line(f"{config.COLORS['blue']}■ {title}{config.COLORS['reset']}", w))
            for line in section_lines:
                lines.append(utils.draw_box_line(line, w))
            lines.append("├" + "─" * (w - 2) + "┤")
        return lines

    def _format_coresight_view(self, w: int) -> List[str]:
        lines = []
        # Real Topology List
        lines.append(utils.draw_box_line(f"{config.COLORS['blue']}■ {labels['hw_status']}{config.COLORS['reset']}", w))
        for name, dev in self.topo.devices.items():
            state_lbl = labels['enabled'] if dev.enabled else labels['disabled']
            color = config.COLORS['green'] if dev.enabled else config.COLORS['reset']
            lines.append(utils.draw_box_line(f"  {name:15} [{dev.subtype:8}] : {color}{state_lbl}{config.COLORS['reset']}", w))
        lines.append("├" + "─" * (w - 2) + "┤")

        # Capture Status
        lines.append(utils.draw_box_line(f"{config.COLORS['blue']}■ {labels['capture']}{config.COLORS['reset']}", w))
        is_cap = self.capture_status.get('capturing', False)
        cap_state = labels['active'] if is_cap else labels['idle']
        cap_color = config.COLORS['red'] + config.COLORS['blink'] if is_cap else config.COLORS['green']
        lines.append(utils.draw_box_line(f"  {labels['state']:12} : {cap_color}{cap_state}{config.COLORS['reset']}", w))
        if is_cap:
            path = self.capture_status.get('path', [])
            lines.append(utils.draw_box_line(f"  Path: {' -> '.join(path)}", w))
        lines.append("├" + "─" * (w - 2) + "┤")

        # Analysis
        lines.append(utils.draw_box_line(f"{config.COLORS['blue']}■ {labels['analysis']}{config.COLORS['reset']}", w))
        if self.last_report.get("status") == "empty":
            lines.append(utils.draw_box_line("  No analysis data available. Run 'A' to analyze.", w))
        else:
            summary = self.analyzer.get_summary_lines(self.last_report)
            for line in summary:
                lines.append(utils.draw_box_line(f"  {line}", w))
        lines.append("├" + "─" * (w - 2) + "┤")
        return lines

    def format_output(self) -> None:
        """
        Step 3: Output Formatting.
        """
        try:
            w = self.terminal_width
            lines = []
            
            # Header
            lines.append("┌" + "─" * (w - 2) + "┐")
            header_text = f" CoreSight Dashboard v1.2 | {datetime.datetime.now().strftime('%H:%M:%S')} "
            lines.append(utils.draw_box_line(f"{config.COLORS['cyan']}{header_text}{config.COLORS['reset']}", w, "center"))
            lines.append("├" + "─" * (w - 2) + "┤")

            # Tabs/Navigation Info
            nav_text = f" {labels['view_system']} | {labels['view_coresight']} "
            if self.view_mode == 1:
                nav_text = nav_text.replace(labels['view_system'], f"{config.COLORS['yellow']}{labels['view_system']}{config.COLORS['reset']}")
            else:
                nav_text = nav_text.replace(labels['view_coresight'], f"{config.COLORS['yellow']}{labels['view_coresight']}{config.COLORS['reset']}")
            lines.append(utils.draw_box_line(nav_text, w, "center"))
            lines.append("├" + "─" * (w - 2) + "┤")

            # Alerts Section (Global)
            alert_str = self.alerts.display_alert()
            if alert_str:
                lines.append(utils.draw_box_line(alert_str, w, "center"))
                lines.append("├" + "─" * (w - 2) + "┤")
                self.alerts.sound_alert()

            # Content based on View Mode
            if self.view_mode == 1:
                lines.extend(self._format_system_view(w))
            else:
                lines.extend(self._format_coresight_view(w))

            # Footer
            footer_text = " [1/2] View | [S/T/A] Trace | [ESC] Exit "
            lines.append(utils.draw_box_line(footer_text, w, "right"))
            lines.append("└" + "─" * (w - 2) + "┘")
            
            self.formatted_output = lines
        except Exception as e:
            utils.log_message(self.module_name, f"Output formatting error: {str(e)}", "ERROR")

    def render_screen(self) -> None:
        """
        Step 4: Screen Rendering.
        """
        utils.clear_screen()
        sys.stdout.write("\n".join(self.formatted_output))
        sys.stdout.flush()

    def run_analysis_action(self) -> None:
        if self.simulation:
            mock_data = (TraceDecode.SYNC_MARKER_ETM4 + b"\x01\x11" + TraceDecode.SYNC_MARKER_ETM4 + b"\x70\x22")
            events = self.decoder.decode_stream(mock_data)
            self.last_report = self.analyzer.analyze_events(events)

    def run(self) -> None:
        """Executes the main application loop."""
        fd = sys.stdin.fileno()
        old_settings = None
        if HAS_TERMIOS:
            try:
                old_settings = termios.tcgetattr(fd)
                tty.setcbreak(fd)
            except Exception: pass

        try:
            while self.running:
                self.collect_data()
                self.process_data()
                self.format_output()
                self.render_screen()
                
                if HAS_TERMIOS:
                    if select.select([sys.stdin], [], [], config.REFRESH_INTERVAL)[0]:
                        char = sys.stdin.read(1).upper()
                        if char == '\x1b' or char == '\x03': self.running = False
                        elif char == '1': self.view_mode = 1
                        elif char == '2': self.view_mode = 2
                        elif char == 'S': # Smart Start
                            sources = [n for n, d in self.topo.devices.items() if d.type == DeviceType.SOURCE]
                            sinks = [n for n, d in self.topo.devices.items() if d.type == DeviceType.SINK]
                            if sources and sinks:
                                try:
                                    self.capture.capture_start(sources[0], sinks[0])
                                except Exception as e:
                                    utils.log_message(self.module_name, f"Capture failed: {str(e)}", "ERROR")
                            else:
                                utils.log_message(self.module_name, "No valid CoreSight Source/Sink pair detected.", "ERROR")
                        elif char == 'T': # Stop
                            self.capture.capture_stop()
                        elif char == 'A': # Analyze
                            self.run_analysis_action()
                else:
                    time.sleep(config.REFRESH_INTERVAL)
                        
        finally:
            if HAS_TERMIOS and old_settings:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            utils.clear_screen()
            print("CoreSight shutdown gracefully.")

if __name__ == "__main__":
    app = CoreSightUnified(simulation=True)
    app.run()
