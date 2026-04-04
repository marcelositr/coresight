"""
Disk Monitoring Module for CoreSight.
Follows Senior Engineer standards with mandatory contract and type safety.
"""

from typing import List, Dict, Any
import psutil
import config
import utils
from i18n import labels

class Disk:
    """
    Handles disk usage metrics collection, processing, and formatting.
    """
    def __init__(self) -> None:
        """
        Initializes the Disk module with default state.
        """
        self.disks: List[Dict[str, Any]] = []
        self.module_name: str = "disk"

    def update(self) -> List[Dict[str, Any]]:
        """
        Collects new disk usage data for all relevant partitions.
        Updates internal state and returns data for backward compatibility.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing disk metrics.
        """
        try:
            self.disks = []
            partitions = psutil.disk_partitions()
            for partition in partitions:
                # Filter out loop devices, empty fstypes, and snap mountpoints
                if 'loop' in partition.device or partition.fstype == '' or 'snap' in partition.mountpoint:
                    continue
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.disks.append({
                        'mount': partition.mountpoint,
                        'total': usage.total,
                        'used': usage.used,
                        'percent': usage.percent
                    })
                except (PermissionError, FileNotFoundError) as e:
                    utils.log_message(self.module_name, f"Skip partition {partition.mountpoint}: {str(e)}", level="DEBUG")
                    continue
                except Exception as e:
                    utils.log_message(self.module_name, f"Error reading disk {partition.mountpoint}: {str(e)}", level="ERROR")
                    continue
            return self.disks
        except Exception as e:
            utils.log_message(self.module_name, f"Error updating disk metrics: {str(e)}", level="ERROR")
            return []

    def get_data(self) -> List[Dict[str, Any]]:
        """
        Returns the current internal state of disk metrics.
        
        Returns:
            List[Dict[str, Any]]: Current disk usage data.
        """
        return self.disks

    def format(self) -> List[str]:
        """
        Formats disk metrics into a list of strings for dashboard display.
        
        Returns:
            List[str]: Formatted lines of text with progress bars and colors.
        """
        lines: List[str] = []
        bar_w: int = getattr(config, 'DYNAMIC_BAR_WIDTH', 30)
        lbl_w: int = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        
        for disk in self.disks:
            mount = disk['mount']
            # Truncate mount path if it's too long
            if len(mount) > lbl_w:
                mount = "..." + mount[-(lbl_w-3):]
            
            bar = utils.create_progress_bar(disk['percent'], width=bar_w)
            val = f"{disk['percent']:6.2f} % ({utils.format_bytes(disk['used'])} / {utils.format_bytes(disk['total'])})"
            lines.append(f"{mount:>{lbl_w}} {bar} {val}")
        
        return lines

    def display(self) -> str:
        """
        Returns the final string representation for the Disk module.
        
        Returns:
            str: All formatted lines joined by newlines.
        """
        return "\n".join(self.format())

# For backward compatibility with existing imports
Disco = Disk
