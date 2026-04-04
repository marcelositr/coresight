"""
RAM Monitoring Module for CoreSight.
Responsive and Aligned.
"""

import psutil
import config
import utils
from i18n import labels

class RAM:
    def __init__(self):
        self.ram_percent, self.swap_percent = 0.0, 0.0
        self.ram_used, self.ram_total = 0, 0
        self.swap_used, self.swap_total = 0, 0

    def update(self):
        try:
            vm = psutil.virtual_memory()
            self.ram_percent, self.ram_used, self.ram_total = vm.percent, vm.used, vm.total
            sm = psutil.swap_memory()
            self.swap_percent, self.swap_used, self.swap_total = sm.percent, sm.used, sm.total
        except Exception: pass

    def format(self):
        lines = []
        bar_w = getattr(config, 'DYNAMIC_BAR_WIDTH', 30)
        lbl_w = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        
        lbl_r = f"{labels['ram']}"
        bar_r = utils.create_progress_bar(self.ram_percent, width=bar_w)
        # format_bytes already returns a string with width 12 and 2 decimals
        r_val = f"{self.ram_percent:6.2f} % ({utils.format_bytes(self.ram_used)} / {utils.format_bytes(self.ram_total)})"
        lines.append(f"{lbl_r:>{lbl_w}} {bar_r} {r_val}")
        
        lbl_s = f"{labels['swap']}"
        bar_s = utils.create_progress_bar(self.swap_percent, width=bar_w)
        s_val = f"{self.swap_percent:6.2f} % ({utils.format_bytes(self.swap_used)} / {utils.format_bytes(self.swap_total)})"
        lines.append(f"{lbl_s:>{lbl_w}} {bar_s} {s_val}")
        return lines
