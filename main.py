"""
CoreSight Main Entry Point.
Responsive Layout with Keyboard Support (ESC and Ctrl+C).
"""

import time
import sys
import os
import datetime
import select
import tty
import termios
import config
import utils
from i18n import labels

# Import modules
from modules.cpu import CPU
from modules.ram import RAM
from modules.disk import Disco
from modules.network import Network
from modules.logs import Logs
from modules.alerts import Alerts

class CoreSight:
    def __init__(self):
        self.initialize_modules()
        self.running = True

    def initialize_modules(self):
        self.cpu = CPU()
        self.ram = RAM()
        self.disk = Disco()
        self.network = Network()
        self.logs = Logs()
        self.alerts = Alerts()

    def build_dashboard(self, width):
        # 1. Update data
        cpu_cores, cpu_total = self.cpu.update()
        self.ram.update()
        disks_data = self.disk.update()
        self.network.update()
        self.logs.update()

        # 2. Alerts check
        self.alerts.check_thresholds(
            cpu_total=cpu_total,
            ram_percent=self.ram.ram_percent,
            swap_percent=self.ram.swap_percent,
            disks_percents=[d['percent'] for d in disks_data]
        )

        # 3. Dynamic width calculation for modules
        inner_w = width - 4
        config.DYNAMIC_LABEL_WIDTH = max(12, int(inner_w * 0.18))
        config.DYNAMIC_BAR_WIDTH = max(10, int(inner_w * 0.32))

        output = []
        output.append("┌" + "─" * (width - 2) + "┐")
        
        header_text = f" CoreSight Dashboard v1.0 | {datetime.datetime.now().strftime('%H:%M:%S')} "
        output.append(utils.draw_box_line(f"{config.COLORS['cyan']}{header_text}{config.COLORS['reset']}", width, "center"))
        output.append("├" + "─" * (width - 2) + "┤")

        alert_str = self.alerts.display_alert()
        if alert_str:
            output.append(utils.draw_box_line(alert_str, width, "center"))
            output.append("├" + "─" * (width - 2) + "┤")
            self.alerts.sound_alert()

        def add_section(title, lines):
            output.append(utils.draw_box_line(f"{config.COLORS['blue']}■ {title}{config.COLORS['reset']}", width))
            for line in lines:
                output.append(utils.draw_box_line(line, width))
            output.append("├" + "─" * (width - 2) + "┤")

        add_section(labels['cpu'], self.cpu.format())
        add_section(labels['ram'], self.ram.format())
        add_section(labels['disk'], self.disk.format())
        add_section(labels['network'], self.network.format())
        add_section(labels['logs'], self.logs.format())

        # FOOTER UPDATED WITH ESC
        footer_text = " [ESC / Ctrl+C] EXIT | [DEBUG] ACTIVE " if config.DEBUG else " [ESC / Ctrl+C] EXIT "
        output.append(utils.draw_box_line(footer_text, width, "right"))
        output.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(output)

    def main_loop(self):
        # Save terminal settings to restore later
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Set terminal to cbreak mode (capture keys without Enter)
            tty.setcbreak(fd)
            
            while self.running:
                w, h = utils.get_terminal_size()
                dashboard = self.build_dashboard(w)
                utils.clear_screen()
                sys.stdout.write(dashboard)
                sys.stdout.flush()
                
                # Check for keyboard input with a timeout (replaces time.sleep)
                if select.select([sys.stdin], [], [], config.REFRESH_INTERVAL)[0]:
                    char = sys.stdin.read(1)
                    if char == '\x1b': # ESC key hex code
                        self.running = False
                        
        except KeyboardInterrupt:
            self.running = False
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            utils.clear_screen()
            print(f"{config.COLORS['green']}CoreSight shutdown gracefully.{config.COLORS['reset']}")

if __name__ == "__main__":
    app = CoreSight()
    app.main_loop()
