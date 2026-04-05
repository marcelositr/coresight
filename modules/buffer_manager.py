"""
Buffer Manager Module for CoreSight Toolkit.
Manages trace buffer allocation and configuration for sinks (ETR/ETF).
Follows Senior Engineer standards and Blueprint specifications.
"""

import utils
from typing import Dict, Any, Optional
from modules.hardware_interface import HardwareInterface

class BufferManager:
    """
    Manages CoreSight buffers, primarily by configuring sink device capacities.
    """
    
    def __init__(self, hw_interface: HardwareInterface) -> None:
        """
        Initializes the buffer manager.
        
        Args:
            hw_interface (HardwareInterface): The hardware interface to use.
        """
        self.module_name: str = "buffer_mgr"
        self.hw: HardwareInterface = hw_interface
        self.active_buffers: Dict[str, int] = {} # device_name -> size
        utils.log_message(self.module_name, "BufferManager initialized.", "DEBUG")

    def buffer_create(self, sink_name: str, size_kb: int) -> bool:
        """
        Configures a buffer for a specific sink device.
        In sysfs, this often corresponds to the 'buffer_size' node.
        
        Args:
            sink_name (str): Name of the sink device (e.g., 'tmc_etr0').
            size_kb (int): Size of the buffer in Kilobytes.
            
        Returns:
            bool: True if configured successfully.
        """
        # Node name might vary by kernel version (buffer_size or similar)
        # For ETR, it's usually 'buffer_size'
        node = "buffer_size"
        
        # Note: CoreSight sinks usually need to be disabled to change buffer size
        self.hw.device_disable(sink_name)
        
        # Convert KB to bytes if the driver expects bytes, or keep as KB. 
        # Most CoreSight sysfs nodes for size expect bytes or have specific units.
        # We'll assume bytes for this implementation as it's common in low-level.
        size_bytes = size_kb * 1024
        
        success = self.hw._write_sysfs(sink_name, node, str(size_bytes))
        if success:
            self.active_buffers[sink_name] = size_bytes
            utils.log_message(self.module_name, f"Buffer of {size_bytes} bytes created for {sink_name}", "INFO")
        else:
            utils.log_message(self.module_name, f"Failed to create buffer for {sink_name}", "ERROR")
            
        return success

    def buffer_destroy(self, sink_name: str) -> bool:
        """
        'Destroys' a buffer by resetting it to a minimum size or disabling the sink.
        
        Args:
            sink_name (str): Name of the sink device.
            
        Returns:
            bool: True if successful.
        """
        if sink_name in self.active_buffers:
            self.hw.device_disable(sink_name)
            del self.active_buffers[sink_name]
            utils.log_message(self.module_name, f"Buffer destroyed for {sink_name}", "INFO")
            return True
        return False

    def buffer_status(self, sink_name: str) -> Dict[str, Any]:
        """
        Retrieves the current buffer status for a sink.
        
        Args:
            sink_name (str): Name of the sink device.
            
        Returns:
            Dict[str, Any]: Status information.
        """
        size_raw = self.hw._read_sysfs(sink_name, "buffer_size")
        
        return {
            "sink": sink_name,
            "configured_size": self.active_buffers.get(sink_name, 0),
            "sysfs_size": size_raw or "unknown",
            "active": sink_name in self.active_buffers
        }
