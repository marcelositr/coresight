"""
CPU Monitoring Module for CoreSight.
Responsive Edition.
"""

import psutil
import config
import utils
from i18n import labels

class CPU:
    def __init__(self):
        self.cpu_percent_per_core = []
        self.cpu_percent_total = 0.0

    def update(self):
        try:
            self.cpu_percent_per_core = psutil.cpu_percent(percpu=True)
            self.cpu_percent_total = psutil.cpu_percent()
            return self.cpu_percent_per_core, self.cpu_percent_total
        except Exception: return [], 0.0

    def format(self):
        lines = []
        bar_w = getattr(config, 'DYNAMIC_BAR_WIDTH', 30)
        lbl_w = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        
        # Total
        lbl = f"{labels['cpu']} {labels['total']}"
        bar = utils.create_progress_bar(self.cpu_percent_total, width=bar_w)
        lines.append(f"{lbl:>{lbl_w}} {bar} {self.cpu_percent_total:6.2f} %")
        
        # Cores (max 8 in responsive to save vertical space if needed)
        for i, pct in enumerate(self.cpu_percent_per_core[:8]):
            lbl_c = f"Core {i}"
            bar_c = utils.create_progress_bar(pct, width=bar_w)
            lines.append(f"{lbl_c:>{lbl_w}} {bar_c} {pct:6.2f} %")
        return lines
