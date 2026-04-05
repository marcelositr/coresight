"""
Hardware Interface Module for CoreSight Toolkit.
Abstraction layer for accessing and configuring CoreSight hardware via sysfs.
Follows Senior Engineer standards and Blueprint specifications.
"""

import os
import utils
from typing import Dict, Any, Optional

class HardwareInterface:
    """
    Handles direct interaction with CoreSight hardware components through the Linux sysfs interface.
    Default path: /sys/bus/coresight/devices/
    """
    
    def __init__(self, sysfs_path: str = "/sys/bus/coresight/devices/") -> None:
        """
        Initializes the hardware interface.
        
        Args:
            sysfs_path (str): The base path for CoreSight devices in sysfs.
        """
        self.module_name: str = "hw_interface"
        self.base_path: str = sysfs_path
        utils.log_message(self.module_name, f"HardwareInterface initialized with path: {self.base_path}", "DEBUG")

    def _write_sysfs(self, device_name: str, node: str, value: str) -> bool:
        """
        Internal helper to write a value to a sysfs node.
        
        Args:
            device_name (str): Name of the CoreSight device (e.g., 'etm0').
            node (str): The specific attribute node (e.g., 'enable_source').
            value (str): The value to write.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        path = os.path.join(self.base_path, device_name, node)
        try:
            if not os.path.exists(path):
                utils.log_message(self.module_name, f"Node not found: {path}", "ERROR")
                return False
                
            with open(path, 'w') as f:
                f.write(value)
            utils.log_message(self.module_name, f"Wrote '{value}' to {path}", "DEBUG")
            return True
        except Exception as e:
            utils.log_message(self.module_name, f"Failed to write to {path}: {str(e)}", "ERROR")
            return False

    def _read_sysfs(self, device_name: str, node: str) -> Optional[str]:
        """
        Internal helper to read a value from a sysfs node.
        
        Args:
            device_name (str): Name of the CoreSight device.
            node (str): The specific attribute node.
            
        Returns:
            Optional[str]: The content of the node, or None if failed.
        """
        path = os.path.join(self.base_path, device_name, node)
        try:
            if not os.path.exists(path):
                utils.log_message(self.module_name, f"Node not found: {path}", "DEBUG")
                return None
                
            with open(path, 'r') as f:
                content = f.read().strip()
            return content
        except Exception as e:
            utils.log_message(self.module_name, f"Failed to read from {path}: {str(e)}", "ERROR")
            return None

    def device_enable(self, device_name: str) -> bool:
        """
        Enables a CoreSight device.
        
        Args:
            device_name (str): Name of the device to enable.
            
        Returns:
            bool: True if enabled successfully.
        """
        # For sources (ETM), the node is typically 'enable_source'
        # For sinks (ETR/ETF), it might be handled differently by the driver
        # but common practice in many scripts is writing 1 to an enable node.
        success = self._write_sysfs(device_name, "enable_source", "1")
        if success:
            utils.log_message(self.module_name, f"Device {device_name} enabled.", "INFO")
        return success

    def device_disable(self, device_name: str) -> bool:
        """
        Disables a CoreSight device.
        
        Args:
            device_name (str): Name of the device to disable.
            
        Returns:
            bool: True if disabled successfully.
        """
        success = self._write_sysfs(device_name, "enable_source", "0")
        if success:
            utils.log_message(self.module_name, f"Device {device_name} disabled.", "INFO")
        return success

    def device_status(self, device_name: str) -> Dict[str, Any]:
        """
        Retrieves the status and configuration of a CoreSight device.
        
        Args:
            device_name (str): Name of the device.
            
        Returns:
            Dict[str, Any]: Dictionary containing status information.
        """
        status: Dict[str, Any] = {
            "name": device_name,
            "enabled": False,
            "mgmt": {}
        }
        
        enabled_raw = self._read_sysfs(device_name, "enable_source")
        if enabled_raw == "1":
            status["enabled"] = True
            
        # Try to read some management registers if available (e.g., DEVID, DEVTYPE)
        # These are usually in a 'mgmt' subdirectory or prefixed in newer kernels
        mgmt_nodes = ["devid", "devtype", "authstatus"]
        mgmt_data: Dict[str, str] = {}
        for node in mgmt_nodes:
            val = self._read_sysfs(device_name, f"mgmt/{node}")
            if val:
                mgmt_data[node] = val
        
        status["mgmt"] = mgmt_data
                
        return status
