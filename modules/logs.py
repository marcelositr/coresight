"""
Logs Monitoring Module for CoreSight.
Monitors system logs for critical errors using journalctl.
Only shows logs that occurred AFTER the monitoring started.
"""

import subprocess
import datetime
import config
import utils
from i18n import labels

class Logs:
    def __init__(self):
        self.log_entries = []
        self.module_name = "logs"
        # Record the exact start time to filter out past logs
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        utils.log_message(self.module_name, f"Monitoring started at {self.start_time}", level="INFO")

    def update(self):
        """
        Collects new critical system log entries since the application started.
        """
        try:
            # Command to get logs since the application start time
            cmd = [
                "journalctl", 
                "-p", "err..crit", 
                "--since", self.start_time, 
                "--no-pager", 
                "-o", "short-iso"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                new_entries = []
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line or line.startswith('--'): continue
                    
                    parts = line.split(' ', 3)
                    if len(parts) >= 4:
                        # Extract HH:MM:SS from ISO format
                        timestamp = parts[0].split('T')[1][:8]
                        message = parts[3]
                        new_entries.append({
                            'time': timestamp,
                            'level': 'ERR',
                            'msg': message
                        })
                
                # Keep only the most recent 5 entries to avoid dashboard overflow
                self.log_entries = new_entries[-5:]
            
            utils.log_message(self.module_name, f"Update: {len(self.log_entries)} logs since start.", level="DEBUG")
            return self.log_entries
        except Exception as e:
            utils.log_message(self.module_name, f"Error updating logs: {str(e)}", level="ERROR")
            return []

    def format(self):
        """
        Formats logs in aligned columns for the dashboard.
        """
        formatted_lines = []
        if not self.log_entries:
            # Show a clean message if no new errors occurred
            return [f"  {config.COLORS['green']}No critical events since start.{config.COLORS['reset']}"]

        for entry in self.log_entries:
            msg = entry['msg'][:55] + "..." if len(entry['msg']) > 55 else entry['msg']
            level_color = config.COLORS["red"]
            line = f"{entry['time']} | {level_color}[{entry['level']}]{config.COLORS['reset']} | {msg}"
            formatted_lines.append(line)
        return formatted_lines

    def display(self):
        """
        Returns formatted string.
        """
        return "\n".join(self.format())

if __name__ == "__main__":
    logs_monitor = Logs()
    import time
    print("Waiting for new logs (try to trigger one or wait)...")
    time.sleep(2)
    logs_monitor.update()
    print(logs_monitor.display())
