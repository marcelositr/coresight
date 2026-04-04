"""
Alerts Management Module for CoreSight.
Follows Senior Engineer standards with mandatory contract and type safety.
"""

from typing import List, Dict, Any, Optional
import sys
import config
import utils
from i18n import labels

class Alerts:
    """
    Handles visual and sound alerts when system thresholds are exceeded.
    """
    def __init__(self) -> None:
        """
        Initializes the Alerts module with default state.
        """
        self.alert_triggered: bool = False
        self.triggering_modules: List[str] = []
        self.module_name: str = "alerts"

    def update(self) -> bool:
        """
        Standard update method. For Alerts, this might not do much 
        as it depends on external data passed to check_thresholds.
        
        Returns:
            bool: Current alert status.
        """
        return self.alert_triggered

    def check_thresholds(self, 
                         cpu_total: float, 
                         ram_percent: float, 
                         swap_percent: float, 
                         disks_percents: List[float], 
                         network_usage: float = 0.0) -> bool:
        """
        Checks current values against thresholds defined in config.py.
        Logs warnings when thresholds are exceeded.
        
        Args:
            cpu_total: Total CPU usage percentage.
            ram_percent: RAM usage percentage.
            swap_percent: Swap usage percentage.
            disks_percents: List of disk usage percentages.
            network_usage: Network usage metric (reserved for future use).
            
        Returns:
            bool: True if any threshold is exceeded, False otherwise.
        """
        try:
            self.alert_triggered = False
            self.triggering_modules = []
            
            # Check CPU
            if cpu_total >= config.THRESHOLDS.get("cpu", 90.0):
                self.alert_triggered = True
                self.triggering_modules.append("CPU")
            
            # Check RAM
            if ram_percent >= config.THRESHOLDS.get("ram", 90.0):
                self.alert_triggered = True
                self.triggering_modules.append("RAM")

            # Check Swap (using same RAM threshold or specific if added)
            if swap_percent >= config.THRESHOLDS.get("ram", 90.0):
                self.alert_triggered = True
                self.triggering_modules.append("SWAP")
            
            # Check Disks
            for disk_pct in disks_percents:
                if disk_pct >= config.THRESHOLDS.get("disk", 90.0):
                    self.alert_triggered = True
                    self.triggering_modules.append("DISK")
                    break
            
            if self.alert_triggered:
                utils.log_message(self.module_name, 
                                  f"ALERT TRIGGERED by: {', '.join(self.triggering_modules)}", 
                                  level="WARNING")
            
            return self.alert_triggered
        except Exception as e:
            utils.log_message(self.module_name, f"Error checking thresholds: {str(e)}", level="ERROR")
            return False

    def get_data(self) -> Dict[str, Any]:
        """
        Returns the current internal state of alerts.
        
        Returns:
            Dict[str, Any]: Alert status and triggering modules.
        """
        return {
            "triggered": self.alert_triggered,
            "modules": self.triggering_modules
        }

    def format(self) -> List[str]:
        """
        Formats alert status into a list of strings for dashboard display.
        
        Returns:
            List[str]: Formatted alert message if triggered, empty list otherwise.
        """
        alert_str = self.display_alert()
        return [alert_str] if alert_str else []

    def display_alert(self) -> str:
        """
        Returns a blinking red string if alert is triggered.
        
        Returns:
            str: Formatted alert message or empty string.
        """
        if not self.alert_triggered:
            return ""
            
        alert_msg = f" !!! {labels['alerts'].upper()}: CRITICAL USAGE DETECTED [{', '.join(self.triggering_modules)}] !!! "
        return f"{config.COLORS['red']}{config.COLORS['blink']}{alert_msg}{config.COLORS['reset']}"

    def display(self) -> str:
        """
        Returns the final string representation for the Alerts module.
        
        Returns:
            str: Formatted alert message.
        """
        return self.display_alert()

    def sound_alert(self) -> None:
        """
        Emits a system beep if alert is triggered.
        """
        if self.alert_triggered:
            try:
                # System beep using ASCII bell character
                sys.stdout.write('\a')
                sys.stdout.flush()
            except Exception as e:
                utils.log_message(self.module_name, f"Error sounding alert: {str(e)}", level="DEBUG")
