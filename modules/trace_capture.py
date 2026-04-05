"""
Trace Capture Module for CoreSight Toolkit.
Orchestrates the capture process: starts, stops, and manages overall state.
Follows Senior Engineer standards and Blueprint specifications.
"""

import utils
from typing import List, Dict, Any, Optional
from modules.hardware_interface import HardwareInterface
from modules.buffer_manager import BufferManager
from modules.trace_route import TraceRoute

class TraceCapture:
    """
    Orchestrates the trace capture session by managing sources, sinks, and routing.
    """
    
    def __init__(self, hw_interface: HardwareInterface, 
                 buffer_manager: BufferManager,
                 trace_route: TraceRoute) -> None:
        """
        Initializes the trace capture engine.
        
        Args:
            hw_interface (HardwareInterface): The hardware interface.
            buffer_manager (BufferManager): The buffer manager.
            trace_route (TraceRoute): The trace router.
        """
        self.module_name: str = "trace_capture"
        self.hw: HardwareInterface = hw_interface
        self.bm: BufferManager = buffer_manager
        self.tr: TraceRoute = trace_route
        self.capturing: bool = False
        self.active_session: Dict[str, Any] = {}
        utils.log_message(self.module_name, "TraceCapture engine initialized.", "DEBUG")

    def capture_start(self, config: Dict[str, Any]) -> bool:
        """
        Starts a trace capture session based on provided configuration.
        
        Args:
            config (Dict[str, Any]): Configuration containing 'sources', 'funnels', 'sink', 'buffer_kb'.
            
        Returns:
            bool: True if capture started successfully.
        """
        if self.capturing:
            utils.log_message(self.module_name, "Capture already in progress.", "WARNING")
            return False
            
        try:
            # 1. Setup Sink and Buffer
            sink_name = config.get('sink', 'tmc_etr0')
            buffer_kb = config.get('buffer_kb', 1024)
            if not self.bm.buffer_create(sink_name, buffer_kb):
                return False
                
            # 2. Setup Routing
            sources = config.get('sources', [])
            funnels = config.get('funnels', []) # Assuming one funnel for simplicity
            funnel_name = funnels[0] if funnels else "funnel0"
            
            for source in sources:
                self.tr.route_setup(source, funnel_name, sink_name)
                
            # 3. Enable Sink First (Recommended CoreSight sequence)
            if not self.hw.device_enable(sink_name):
                return False
                
            # 4. Enable Sources (ETMs)
            for source in sources:
                if not self.hw.device_enable(source):
                    # Attempt cleanup on partial failure
                    self.capture_stop()
                    return False
                    
            self.capturing = True
            self.active_session = config
            utils.log_message(self.module_name, f"Capture session started: {sources} -> {sink_name}", "INFO")
            return True
            
        except Exception as e:
            utils.log_message(self.module_name, f"Capture start failed: {str(e)}", "ERROR")
            self.capture_stop()
            return False

    def capture_stop(self) -> bool:
        """
        Stops the current trace capture session.
        
        Returns:
            bool: True if stopped successfully.
        """
        if not self.capturing:
            utils.log_message(self.module_name, "No capture session active.", "WARNING")
            return False
            
        try:
            sources = self.active_session.get('sources', [])
            sink_name = self.active_session.get('sink', 'tmc_etr0')
            
            # 1. Disable Sources First (ETMs)
            for source in sources:
                self.hw.device_disable(source)
                
            # 2. Disable Sink
            self.hw.device_disable(sink_name)
            
            # 3. Destroy Buffer reference
            self.bm.buffer_destroy(sink_name)
            
            # 4. Reset routing
            self.tr.route_reset()
            
            self.capturing = False
            utils.log_message(self.module_name, "Capture session stopped.", "INFO")
            return True
        except Exception as e:
            utils.log_message(self.module_name, f"Capture stop error: {str(e)}", "ERROR")
            return False

    def status(self) -> Dict[str, Any]:
        """
        Retrieves current capture engine status.
        
        Returns:
            Dict[str, Any]: Current status.
        """
        return {
            "capturing": self.capturing,
            "session": self.active_session
        }
