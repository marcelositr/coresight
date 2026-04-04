"""
Alerts Management Module for CoreSight.
Handles visual and sound alerts when system thresholds are exceeded.
"""

import sys
import config
import utils
from i18n import labels

class Alerts:
    def __init__(self):
        self.alert_triggered = False
        self.triggering_modules = []
        self.module_name = "alerts"

    def check_thresholds(self, cpu_total, ram_percent, swap_percent, disks_percents, network_usage=0):
        """
        Checks current values against thresholds defined in config.py.
        """
        try:
            self.alert_triggered = False
            self.triggering_modules = []
            
            # Check CPU
            if cpu_total >= config.THRESHOLDS.get("cpu", 90):
                self.alert_triggered = True
                self.triggering_modules.append("CPU")
            
            # Check RAM
            if ram_percent >= config.THRESHOLDS.get("ram", 90):
                self.alert_triggered = True
                self.triggering_modules.append("RAM")

            # Check Swap (using same RAM threshold or specific if added)
            if swap_percent >= config.THRESHOLDS.get("ram", 90):
                self.alert_triggered = True
                self.triggering_modules.append("SWAP")
            
            # Check Disks
            for disk_pct in disks_percents:
                if disk_pct >= config.THRESHOLDS.get("disk", 90):
                    self.alert_triggered = True
                    self.triggering_modules.append("DISK")
                    break
            
            # Network usage check can be more complex, for now we use a simple placeholder logic
            # as defined in the blueprint inputs.
            
            if self.alert_triggered:
                utils.log_message(self.module_name, 
                                  f"ALERT TRIGGERED by: {', '.join(self.triggering_modules)}", 
                                  level="WARNING")
            
            return self.alert_triggered
        except Exception as e:
            utils.log_message(self.module_name, f"Error checking thresholds: {str(e)}", level="ERROR")
            return False

    def display_alert(self):
        """
        Returns a blinking red string if alert is triggered.
        """
        if not self.alert_triggered:
            return ""
            
        alert_msg = f" !!! {labels['alerts'].upper()}: CRITICAL USAGE DETECTED [{', '.join(self.triggering_modules)}] !!! "
        return f"{config.COLORS['red']}{config.COLORS['blink']}{alert_msg}{config.COLORS['reset']}"

    def sound_alert(self):
        """
        Emits a system beep.
        """
        if self.alert_triggered:
            # System beep using ASCII bell character
            sys.stdout.write('\a')
            sys.stdout.flush()

# Self-test logic
if __name__ == "__main__":
    alerts_mgr = Alerts()
    # Simulate a trigger
    triggered = alerts_mgr.check_thresholds(cpu_total=95, ram_percent=40, swap_percent=10, disks_percents=[20, 30])
    print(f"Triggered: {triggered}")
    print(f"Display: {alerts_mgr.display_alert()}")
    alerts_mgr.sound_alert()
