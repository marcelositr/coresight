"""
Logs Monitoring Module for CoreSight.
Follows Senior Engineer standards with mandatory contract and type safety.
"""

from typing import List, Dict, Any
import subprocess
import datetime
import config
import utils
from i18n import labels

class Logs:
    """
    Monitors system logs for critical errors using journalctl.
    """
    def __init__(self) -> None:
        """
        Initializes the Logs module and records start time to filter entries.
        """
        self.log_entries: List[Dict[str, str]] = []
        self.module_name: str = "logs"
        # Record the exact start time to filter out past logs
        self.start_time: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        utils.log_message(self.module_name, f"Monitoring started at {self.start_time}", level="INFO")

    def update(self) -> List[Dict[str, str]]:
        """
        Collects new critical system log entries since the application started.
        Returns data for backward compatibility.
        
        Returns:
            List[Dict[str, str]]: Recent log entries.
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
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                new_entries = []
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line or line.startswith('--'):
                        continue
                    
                    parts = line.split(' ', 3)
                    if len(parts) >= 4:
                        # Extract HH:MM:SS from ISO format (e.g., 2023-10-27T10:20:30+0000)
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

    def get_data(self) -> List[Dict[str, str]]:
        """
        Returns the current internal state of log entries.
        
        Returns:
            List[Dict[str, str]]: Current logs.
        """
        return self.log_entries

    def format(self) -> List[str]:
        """
        Formats log entries into a list of strings for dashboard display.
        
        Returns:
            List[str]: Formatted lines of text with colors.
        """
        formatted_lines: List[str] = []
        if not self.log_entries:
            # Show a clean message if no new errors occurred
            return [f"  {config.COLORS['green']}No critical events since start.{config.COLORS['reset']}"]

        for entry in self.log_entries:
            # Truncate long messages
            msg = entry['msg'][:55] + "..." if len(entry['msg']) > 55 else entry['msg']
            level_color = config.COLORS["red"]
            line = f"{entry['time']} | {level_color}[{entry['level']}]{config.COLORS['reset']} | {msg}"
            formatted_lines.append(line)
        
        return formatted_lines

    def display(self) -> str:
        """
        Returns the final string representation for the Logs module.
        
        Returns:
            str: All formatted lines joined by newlines.
        """
        return "\n".join(self.format())
