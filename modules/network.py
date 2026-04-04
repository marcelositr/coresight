"""
Network Monitoring Module for CoreSight.
Follows Senior Engineer standards with mandatory contract and type safety.
"""

from typing import List, Dict, Any
import psutil
import time
import config
import utils
from i18n import labels

class Network:
    """
    Handles network interface throughput collection and formatting.
    """
    def __init__(self) -> None:
        """
        Initializes the Network module with default state and last stats.
        """
        self.interfaces: Dict[str, Dict[str, float]] = {}
        self.last_stats = psutil.net_io_counters(pernic=True)
        self.last_time: float = time.time()
        self.MAX_REF_SPEED: int = 10 * 1024 * 1024  # 10 MB/s as reference for bars
        self.module_name: str = "network"

    def update(self) -> Dict[str, Dict[str, float]]:
        """
        Calculates interface speeds (bytes/sec) since the last update.
        Updates internal state and returns data for backward compatibility.
        
        Returns:
            Dict[str, Dict[str, float]]: Upload and download speeds per interface.
        """
        try:
            current_stats = psutil.net_io_counters(pernic=True)
            current_time = time.time()
            elapsed = current_time - self.last_time
            
            # Avoid division by zero
            if elapsed <= 0:
                elapsed = 1.0
            
            self.interfaces = {}
            for interface, stats in current_stats.items():
                # Filter inactive or loopback interfaces
                if interface == 'lo' or (stats.bytes_sent == 0 and stats.bytes_recv == 0):
                    continue
                
                last = self.last_stats.get(interface)
                if last:
                    self.interfaces[interface] = {
                        'up': (stats.bytes_sent - last.bytes_sent) / elapsed,
                        'down': (stats.bytes_recv - last.bytes_recv) / elapsed
                    }
            
            self.last_stats, self.last_time = current_stats, current_time
            return self.interfaces
        except Exception as e:
            utils.log_message(self.module_name, f"Error updating network metrics: {str(e)}", level="ERROR")
            return {}

    def get_data(self) -> Dict[str, Dict[str, float]]:
        """
        Returns the current internal state of network metrics.
        
        Returns:
            Dict[str, Dict[str, float]]: Current interface speed data.
        """
        return self.interfaces

    def format(self) -> List[str]:
        """
        Formats network metrics into a list of strings for dashboard display.
        
        Returns:
            List[str]: Formatted lines of text with upload/download indicators and bars.
        """
        lines: List[str] = []
        lbl_w: int = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        bar_w: int = int(getattr(config, 'DYNAMIC_BAR_WIDTH', 30) / 2)
        
        for iface, data in self.interfaces.items():
            # Calculate percentages relative to reference speed
            up_pct = min(100.0, (data['up'] / self.MAX_REF_SPEED) * 100.0)
            down_pct = min(100.0, (data['down'] / self.MAX_REF_SPEED) * 100.0)
            
            up_bar = utils.create_progress_bar(up_pct, width=bar_w)
            down_bar = utils.create_progress_bar(down_pct, width=bar_w)
            
            # Formatted strings for bytes/s
            up_str = f"↑{utils.format_bytes(data['up'], suffix='B', width=12)}/s"
            down_str = f"↓{utils.format_bytes(data['down'], suffix='B', width=12)}/s"
            
            line = f"{iface:>{lbl_w}} {up_bar} {up_str} | {down_bar} {down_str}"
            lines.append(line)
        
        return lines

    def display(self) -> str:
        """
        Returns the final string representation for the Network module.
        
        Returns:
            str: All formatted lines joined by newlines.
        """
        return "\n".join(self.format())
