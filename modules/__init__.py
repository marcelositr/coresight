"""
CoreSight Modules Package.
Updated for industrial-grade hardware diagnostics.
"""

from modules.exceptions import CoreSightError, SysfsError, TopologyError, CaptureError, ValidationError
from modules.debug_logger import logger
from modules.hardware_interface import HardwareInterface
from modules.topology_manager import TopologyManager, DeviceType, CoreSightDevice
from modules.capture_validator import CaptureValidator
from modules.trace_capture import TraceCapture
from modules.trace_sink import TraceSink
from modules.trace_decode import TraceDecode
from modules.trace_analyzer import TraceAnalyzer
from modules.perf_bridge import PerfBridge
