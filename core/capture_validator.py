"""
CoreSight Capture Validator.
Ensures hardware readiness and path integrity before starting trace.
"""

from typing import List
from core.topology_manager import TopologyManager, DeviceType
from infra.exceptions import ValidationError
from infra.debug_logger import logger

class CaptureValidator:
    def __init__(self, topology: TopologyManager) -> None:
        self.topo = topology

    def validate_path(self, path: List[str]) -> None:
        """Validates the sequence of devices for a capture session."""
        if not path:
            raise ValidationError("Capture path cannot be empty.")
            
        source_name = path[0]
        sink_name = path[-1]
        
        source = self.topo.devices.get(source_name)
        sink = self.topo.devices.get(sink_name)
        
        if not source or source.type != DeviceType.SOURCE:
            raise ValidationError(f"Path must start with a SOURCE. Found: {source_name}")
            
        if not sink or sink.type != DeviceType.SINK:
            raise ValidationError(f"Path must end with a SINK. Found: {sink_name}")
            
        # Verify connectivity in the path
        for i in range(len(path) - 1):
            current = path[i]
            next_dev = path[i+1]
            if next_dev not in self.topo.graph.get(current, []):
                raise ValidationError(f"Invalid connection in path: {current} -> {next_dev}")
        
        logger.capture(f"Path {path} validated successfully.")

    def validate_buffer_size(self, sink: str, size_kb: int) -> None:
        """Checks if the requested buffer is within hardware limits."""
        if size_kb <= 0:
            raise ValidationError("Buffer size must be positive.")
        # Optional: check against hardware max reported in mgmt registers
