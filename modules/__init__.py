"""
CoreSight Modules Package.
Contains hardware abstraction and trace processing components.
"""

from modules.hardware_interface import HardwareInterface
from modules.buffer_manager import BufferManager
from modules.trace_route import TraceRoute
from modules.trace_capture import TraceCapture
from modules.trace_sink import TraceSink
from modules.trace_decode import TraceDecode
from modules.trace_analyzer import TraceAnalyzer
from modules.perf_integration import PerfIntegration
