"""
Trace Sink Module for CoreSight Toolkit.
Handles exporting trace data to persistent storage.
Follows Senior Engineer standards and Blueprint specifications.
"""

import os
import shutil
from infra import utils
from typing import Dict, Any
from core.trace_capture import TraceCapture

class TraceSink:
    """
    Exports captured trace data from hardware nodes (e.g., /dev/tmc_etr0)
    to persistent files for analysis.
    """
    
    def __init__(self, capture_engine: TraceCapture) -> None:
        """
        Initializes the trace sink module.
        
        Args:
            capture_engine (TraceCapture): The capture engine instance.
        """
        self.module_name: str = "trace_sink"
        self.capture: TraceCapture = capture_engine
        utils.log_message(self.module_name, "TraceSink initialized.", "DEBUG")

    def export_file(self, device_node: str, destination_path: str) -> bool:
        """
        Exports data from a device node to a file.
        
        Args:
            device_node (str): Path to the device node (e.g., '/dev/tmc_etr0').
            destination_path (str): Path to the output file.
            
        Returns:
            bool: True if export was successful.
        """
        # In a real system, we'd check if the capture is stopped or if we can read on the fly.
        # For this toolkit, we assume the capture is active or recently stopped.
        
        utils.log_message(self.module_name, f"Exporting trace from {device_node} to {destination_path}", "INFO")
        
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            if not os.path.exists(device_node):
                utils.log_message(self.module_name, f"Device node not found: {device_node}", "ERROR")
                return False
                
            # Perform raw byte copy
            with open(device_node, 'rb') as f_in:
                with open(destination_path, 'wb') as f_out:
                    # We might want to limit the read size based on the buffer configuration
                    shutil.copyfileobj(f_in, f_out)
                    
            utils.log_message(self.module_name, f"Trace data exported to {destination_path}", "INFO")
            return True
            
        except Exception as e:
            utils.log_message(self.module_name, f"Export failed: {str(e)}", "ERROR")
            return False

    def status(self) -> Dict[str, Any]:
        """
        Retrieves current sink status.
        
        Returns:
            Dict[str, Any]: Status information.
        """
        return {
            "module": self.module_name,
            "ready": True
        }
