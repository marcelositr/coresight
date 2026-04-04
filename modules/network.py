"""
Network Monitoring Module for CoreSight.
Responsive Edition with Fixed Column Alignment.
"""

import psutil
import time
import config
import utils
from i18n import labels

class Network:
    def __init__(self):
        self.interfaces = {}
        self.last_stats = psutil.net_io_counters(pernic=True)
        self.last_time = time.time()
        self.MAX_REF_SPEED = 10 * 1024 * 1024 

    def update(self):
        try:
            current_stats = psutil.net_io_counters(pernic=True)
            current_time = time.time()
            elapsed = current_time - self.last_time
            if elapsed <= 0: elapsed = 1.0
            self.interfaces = {}
            for interface, stats in current_stats.items():
                if interface == 'lo' or (stats.bytes_sent == 0 and stats.bytes_recv == 0): continue
                last = self.last_stats.get(interface)
                if last:
                    self.interfaces[interface] = {
                        'up': (stats.bytes_sent - last.bytes_sent) / elapsed,
                        'down': (stats.bytes_recv - last.bytes_recv) / elapsed
                    }
            self.last_stats, self.last_time = current_stats, current_time
            return self.interfaces
        except Exception: return {}

    def format(self):
        lines = []
        lbl_w = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        bar_w = int(getattr(config, 'DYNAMIC_BAR_WIDTH', 30) / 2)
        
        for iface, data in self.interfaces.items():
            up_pct = min(100, (data['up'] / self.MAX_REF_SPEED) * 100)
            down_pct = min(100, (data['down'] / self.MAX_REF_SPEED) * 100)
            
            up_bar = utils.create_progress_bar(up_pct, width=bar_w)
            down_bar = utils.create_progress_bar(down_pct, width=bar_w)
            
            # Use format_bytes with fixed width and add /s
            up_str = f"↑{utils.format_bytes(data['up'], suffix='B', width=12)}/s"
            down_str = f"↓{utils.format_bytes(data['down'], suffix='B', width=12)}/s"
            
            line = f"{iface:>{lbl_w}} {up_bar} {up_str} | {down_bar} {down_str}"
            lines.append(line)
        return lines
