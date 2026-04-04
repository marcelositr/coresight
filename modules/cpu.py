"""
CPU Monitoring Module for CoreSight.
Follows Senior Engineer standards with mandatory contract and type safety.
"""

from typing import List, Dict, Any, Tuple
import psutil
import config
import utils
from i18n import labels

class CPU:
    """
    Handles CPU metrics collection, processing, and formatting.
    """
    def __init__(self) -> None:
        """
        Initializes the CPU module with default state.
        """
        self.cpu_percent_per_core: List[float] = []
        self.cpu_percent_total: float = 0.0
        self.module_name: str = "cpu"

    def update(self) -> Tuple[List[float], float]:
        """
        Collects new CPU usage data.
        Maintains backward compatibility by returning expected values.
        
        Returns:
            Tuple[List[float], float]: List of per-core percentages and total percentage.
        """
        try:
            self.cpu_percent_per_core = psutil.cpu_percent(percpu=True)
            self.cpu_percent_total = float(psutil.cpu_percent())
            return self.cpu_percent_per_core, self.cpu_percent_total
        except Exception as e:
            utils.log_message(self.module_name, f"Error updating CPU metrics: {str(e)}", level="ERROR")
            self.cpu_percent_per_core = []
            self.cpu_percent_total = 0.0
            return self.cpu_percent_per_core, self.cpu_percent_total

    def get_data(self) -> Dict[str, Any]:
        """
        Returns the current internal state of CPU metrics.
        
        Returns:
            Dict[str, Any]: Dictionary containing per-core and total CPU usage.
        """
        return {
            "per_core": self.cpu_percent_per_core,
            "total": self.cpu_percent_total
        }

    def format(self) -> List[str]:
        """
        Formats CPU metrics into a list of strings for dashboard display.
        
        Returns:
            List[str]: Formatted lines of text with progress bars and colors.
        """
        lines: List[str] = []
        bar_w: int = getattr(config, 'DYNAMIC_BAR_WIDTH', 30)
        lbl_w: int = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        
        # Total CPU usage
        lbl = f"{labels['cpu']} {labels['total']}"
        bar = utils.create_progress_bar(self.cpu_percent_total, width=bar_w)
        lines.append(f"{lbl:>{lbl_w}} {bar} {self.cpu_percent_total:6.2f} %")
        
        # Cores (max 8 in responsive to save vertical space if needed)
        for i, pct in enumerate(self.cpu_percent_per_core[:8]):
            lbl_c = f"Core {i}"
            bar_c = utils.create_progress_bar(pct, width=bar_w)
            lines.append(f"{lbl_c:>{lbl_w}} {bar_c} {pct:6.2f} %")
        
        return lines

    def display(self) -> str:
        """
        Returns the final string representation for the CPU module.
        
        Returns:
            str: All formatted lines joined by newlines.
        """
        return "\n".join(self.format())
