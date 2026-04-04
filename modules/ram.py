"""
RAM Monitoring Module for CoreSight.
Follows Senior Engineer standards with mandatory contract and type safety.
"""

from typing import List, Dict, Any
import psutil
import config
import utils
from i18n import labels

class RAM:
    """
    Handles memory (RAM and Swap) metrics collection, processing, and formatting.
    """
    def __init__(self) -> None:
        """
        Initializes the RAM module with default state.
        """
        self.ram_percent: float = 0.0
        self.ram_used: int = 0
        self.ram_total: int = 0
        self.swap_percent: float = 0.0
        self.swap_used: int = 0
        self.swap_total: int = 0
        self.module_name: str = "ram"

    def update(self) -> None:
        """
        Collects new RAM and Swap usage data.
        Updates internal state.
        """
        try:
            vm = psutil.virtual_memory()
            self.ram_percent = vm.percent
            self.ram_used = vm.used
            self.ram_total = vm.total
            
            sm = psutil.swap_memory()
            self.swap_percent = sm.percent
            self.swap_used = sm.used
            self.swap_total = sm.total
        except Exception as e:
            utils.log_message(self.module_name, f"Error updating RAM/Swap metrics: {str(e)}", level="ERROR")
            self.ram_percent = 0.0
            self.swap_percent = 0.0

    def get_data(self) -> Dict[str, Any]:
        """
        Returns the current internal state of RAM metrics.
        
        Returns:
            Dict[str, Any]: Dictionary containing RAM and Swap details.
        """
        return {
            "ram": {
                "percent": self.ram_percent,
                "used": self.ram_used,
                "total": self.ram_total
            },
            "swap": {
                "percent": self.swap_percent,
                "used": self.swap_used,
                "total": self.swap_total
            }
        }

    def format(self) -> List[str]:
        """
        Formats RAM metrics into a list of strings for dashboard display.
        
        Returns:
            List[str]: Formatted lines of text with progress bars and colors.
        """
        lines: List[str] = []
        bar_w: int = getattr(config, 'DYNAMIC_BAR_WIDTH', 30)
        lbl_w: int = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        
        # RAM usage
        lbl_r = f"{labels['ram']}"
        bar_r = utils.create_progress_bar(self.ram_percent, width=bar_w)
        r_val = f"{self.ram_percent:6.2f} % ({utils.format_bytes(self.ram_used)} / {utils.format_bytes(self.ram_total)})"
        lines.append(f"{lbl_r:>{lbl_w}} {bar_r} {r_val}")
        
        # Swap usage
        lbl_s = f"{labels['swap']}"
        bar_s = utils.create_progress_bar(self.swap_percent, width=bar_w)
        s_val = f"{self.swap_percent:6.2f} % ({utils.format_bytes(self.swap_used)} / {utils.format_bytes(self.swap_total)})"
        lines.append(f"{lbl_s:>{lbl_w}} {bar_s} {s_val}")
        
        return lines

    def display(self) -> str:
        """
        Returns the final string representation for the RAM module.
        
        Returns:
            str: All formatted lines joined by newlines.
        """
        return "\n".join(self.format())
