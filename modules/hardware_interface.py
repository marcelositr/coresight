"""
Stateless Hardware Interface for CoreSight.
Handles robust sysfs I/O operations with safety checks and retries.
"""

import os
import time
from typing import Optional, List
from modules.exceptions import SysfsError
from modules.debug_logger import logger

class HardwareInterface:
    """Provides safe and stateless access to CoreSight sysfs nodes."""
    
    def __init__(self, base_path: str = "/sys/bus/coresight/devices/") -> None:
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            logger.warning(f"CoreSight bus not found at {self.base_path}")

    def safe_read(self, device: str, node: str) -> str:
        """Reads a sysfs node safely."""
        path = os.path.join(self.base_path, device, node)
        try:
            if not os.path.exists(path):
                return ""
            with open(path, 'r') as f:
                content = f.read().strip()
                logger.sysfs_io(f"READ {path} -> {content}")
                return content
        except Exception as e:
            raise SysfsError(f"Failed to read {path}: {str(e)}")

    def safe_write(self, device: str, node: str, value: str, retries: int = 3) -> bool:
        """Writes to a sysfs node with retry logic for EBUSY/EAGAIN."""
        path = os.path.join(self.base_path, device, node)
        last_error: Optional[Exception] = None
        
        for attempt in range(retries):
            try:
                if not os.path.exists(path):
                    raise SysfsError(f"Node {path} does not exist.")
                
                with open(path, 'w') as f:
                    f.write(value)
                logger.sysfs_io(f"WRITE {path} <- {value}")
                return True
            except (BlockingIOError, PermissionError, OSError) as e:
                last_error = e
                logger.sysfs_io(f"RETRY {attempt+1}/{retries} for {path} due to {str(e)}")
                time.sleep(0.1)
                continue
        
        raise SysfsError(f"Failed to write {value} to {path} after {retries} attempts. Error: {str(last_error)}")

    def list_raw_devices(self) -> List[str]:
        """Lists all raw directory names in the coresight bus."""
        try:
            if not os.path.exists(self.base_path):
                return []
            return [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]
        except Exception as e:
            raise SysfsError(f"Failed to list devices: {str(e)}")
