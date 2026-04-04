"""
CoreSight Main Entry Point.
Professional Rendering Pipeline with Responsive Layout and Keyboard Support.
Follows Senior Engineer standards and Blueprint 2-09.
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

# Import modules
from modules.cpu import CPU
from modules.ram import RAM
from modules.disk import Disk
from modules.network import Network
from modules.logs import Logs
from modules.alerts import Alerts

class CoreSight:
    """
    Main Application Class for CoreSight Dashboard.
    Implements a strict rendering pipeline: collect -> process -> format -> render.
    """
    
    def __init__(self) -> None:
        """
        Initializes the application, modules, and terminal state.
        """
        self.module_name: str = "main"
        self._initialize_modules()
        self.running: bool = True
        self.terminal_width: int = 80
        self.terminal_height: int = 24
        self.last_render: float = 0
        
        # State storage for the pipeline
        self.raw_data: Dict[str, Any] = {}
        self.formatted_output: List[str] = []

    def _initialize_modules(self) -> None:
        """
        Instantiates all monitoring modules.
        """
        try:
            self.cpu = CPU()
            self.ram = RAM()
            self.disk = Disk()
            self.network = Network()
            self.logs = Logs()
            self.alerts = Alerts()
            utils.log_message(self.module_name, "Modules initialized successfully.")
        except Exception as e:
            utils.log_message(self.module_name, f"Failed to initialize modules: {str(e)}", "CRITICAL")
            sys.exit(1)

    def collect_data(self) -> None:
        """
        Step 1: Mandatory Data Collection.
        Updates all modules to gather fresh metrics.
        """
        try:
            # Each update call returns data, which we store in raw_data if needed
            self.raw_data['cpu_cores'], self.raw_data['cpu_total'] = self.cpu.update()
            self.raw_data['ram_data'] = self.ram.update()
            self.raw_data['disks_data'] = self.disk.update()
            self.raw_data['network_data'] = self.network.update()
            self.raw_data['logs_data'] = self.logs.update()
        except Exception as e:
            utils.log_message(self.module_name, f"Data collection error: {str(e)}", "ERROR")

    def process_data(self) -> None:
        """
        Step 2: Mandatory Data Processing.
        Analyzes collected data for alerts and logic.
        """
        try:
            # Check thresholds for alerts
            self.alerts.check_thresholds(
                cpu_total=self.raw_data.get('cpu_total', 0),
                ram_percent=self.ram.ram_percent,
                swap_percent=self.ram.swap_percent,
                disks_percents=[d['percent'] for d in self.raw_data.get('disks_data', [])]
            )
            
            # Update terminal size for layout calculations
            self.terminal_width, self.terminal_height = utils.get_terminal_size()
            
            # Dynamic layout adjustments
            inner_w = self.terminal_width - 4
            config.DYNAMIC_LABEL_WIDTH = max(12, int(inner_w * 0.18))
            config.DYNAMIC_BAR_WIDTH = max(10, int(inner_w * 0.32))
            
        except Exception as e:
            utils.log_message(self.module_name, f"Data processing error: {str(e)}", "ERROR")

    def format_output(self) -> None:
        """
        Step 3: Mandatory Output Formatting.
        Prepares the visual representation of the data.
        """
        try:
            w = self.terminal_width
            lines = []
            
            # 1. Header and Top Border
            lines.append("┌" + "─" * (w - 2) + "┐")
            header_text = f" CoreSight Dashboard v1.1 | {datetime.datetime.now().strftime('%H:%M:%S')} "
            lines.append(utils.draw_box_line(f"{config.COLORS['cyan']}{header_text}{config.COLORS['reset']}", w, "center"))
            lines.append("├" + "─" * (w - 2) + "┤")

            # 2. Alerts Section (Dynamic)
            alert_str = self.alerts.display_alert()
            if alert_str:
                lines.append(utils.draw_box_line(alert_str, w, "center"))
                lines.append("├" + "─" * (w - 2) + "┤")
                self.alerts.sound_alert()

            # 3. Main Content Sections
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

            # 4. Footer and Bottom Border
            footer_text = " [ESC / Ctrl+C] EXIT | [DEBUG] ACTIVE " if config.DEBUG else " [ESC / Ctrl+C] EXIT "
            lines.append(utils.draw_box_line(footer_text, w, "right"))
            lines.append("└" + "─" * (w - 2) + "┘")
            
            self.formatted_output = lines
            
        except Exception as e:
            utils.log_message(self.module_name, f"Output formatting error: {str(e)}", "ERROR")
            self.formatted_output = ["Error formatting dashboard output."]

    def render_screen(self) -> None:
        """
        Step 4: Mandatory Screen Rendering.
        Displays the formatted dashboard to the terminal.
        """
        try:
            utils.clear_screen()
            dashboard_str = "\n".join(self.formatted_output)
            sys.stdout.write(dashboard_str)
            sys.stdout.flush()
        except Exception as e:
            utils.log_message(self.module_name, f"Render error: {str(e)}", "ERROR")

    def run(self) -> None:
        """
        Executes the main application loop with professional terminal handling.
        """
        # Save terminal settings to restore later
        fd = sys.stdin.fileno()
        old_settings = None
        if HAS_TERMIOS:
            try:
                old_settings = termios.tcgetattr(fd)
                # Set terminal to cbreak mode (capture keys without Enter)
                tty.setcbreak(fd)
            except (termios.error, Exception):
                old_settings = None

        try:
            utils.log_message(self.module_name, "Application started.")
            
            while self.running:
                # Execute Pipeline
                self.collect_data()
                self.process_data()
                self.format_output()
                self.render_screen()
                
                # Check for keyboard input with a timeout
                # select() allows us to wait for REFRESH_INTERVAL or a key press
                if HAS_TERMIOS:
                    if select.select([sys.stdin], [], [], config.REFRESH_INTERVAL)[0]:
                        char = sys.stdin.read(1)
                        if char == '\x1b' or char == '\x03': # ESC (\x1b) or Ctrl+C (\x03)
                            self.running = False
                else:
                    # Fallback for Windows or non-TTY
                    time.sleep(config.REFRESH_INTERVAL)
                        
        except KeyboardInterrupt:
            self.running = False
        except Exception as e:
            utils.log_message(self.module_name, f"Fatal error in main loop: {str(e)}", "CRITICAL")
        finally:
            # Restore terminal settings
            if HAS_TERMIOS and old_settings:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except (termios.error, Exception):
                    pass
            
            utils.clear_screen()
            print(f"{config.COLORS['green']}CoreSight shutdown gracefully.{config.COLORS['reset']}")
            utils.log_message(self.module_name, "Application shutdown.")

if __name__ == "__main__":
    app = CoreSight()
    app.run()
