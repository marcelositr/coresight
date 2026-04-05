"""
CoreSight Trace Capture Engine.
Orchestrates activation and deactivation in strict hardware order.
"""

from typing import List, Optional
from modules.topology_manager import TopologyManager
from modules.capture_validator import CaptureValidator
from modules.exceptions import CaptureError
from modules.debug_logger import logger

class TraceCapture:
    def __init__(self) -> None:
        # TopologyManager is a singleton, it will use default path unless initialized elsewhere
        self.topo = TopologyManager()
        self.validator = CaptureValidator(self.topo)
        self.active_path: List[str] = []

    def capture_start(self, source: str, sink: str, buffer_kb: int = 1024) -> bool:
        """Starts capture in strict order: Sink -> Links -> Source."""
        try:
            # Refresh topology to get latest state
            self.topo.refresh_topology()
            
            path = self.topo.find_path(source, sink)
            self.validator.validate_path(path)
            self.validator.validate_buffer_size(sink, buffer_kb)
            
            logger.capture(f"Activating path: {' -> '.join(path)}")
            
            # 1. Enable SINK first (path[-1])
            # Set buffer size if it's a TMC (ETR/ETF)
            if "tmc" in sink or "etr" in sink or "etf" in sink:
                self.topo.hw.safe_write(sink, "buffer_size", str(buffer_kb * 1024))
            
            self.topo.hw.safe_write(sink, "enable_sink", "1")
            
            # 2. Enable LINKS (path[1:-1]) from downstream to upstream (reverse order)
            links = path[1:-1]
            for link in reversed(links):
                # Links use enable_sink or enable_link depending on kernel version
                # We try common nodes
                try:
                    self.topo.hw.safe_write(link, "enable_sink", "1")
                except Exception:
                    # Fallback for older drivers
                    pass
                
            # 3. Enable SOURCE last (path[0])
            self.topo.hw.safe_write(source, "enable_source", "1")
            
            self.active_path = path
            logger.capture("Trace session active.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start capture: {str(e)}")
            self.capture_stop()
            raise CaptureError(str(e))

    def capture_stop(self) -> bool:
        """Stops capture in reverse order: Source -> Links -> Sink."""
        if not self.active_path: return False
        
        path = self.active_path
        logger.capture(f"Deactivating path: {' -> '.join(path)}")
        
        try:
            # 1. Disable SOURCE first
            self.topo.hw.safe_write(path[0], "enable_source", "0")
            
            # 2. Disable LINKS from upstream to downstream
            links = path[1:-1]
            for link in links:
                try:
                    self.topo.hw.safe_write(link, "enable_sink", "0")
                except Exception:
                    pass
                
            # 3. Disable SINK last
            self.topo.hw.safe_write(path[-1], "enable_sink", "0")
            
            self.active_path = []
            return True
        except Exception as e:
            logger.error(f"Error during capture stop: {str(e)}")
            return False

    def status(self) -> dict:
        """Returns the current capture engine status."""
        return {
            "capturing": len(self.active_path) > 0,
            "path": self.active_path
        }
