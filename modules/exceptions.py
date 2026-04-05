"""
CoreSight Toolkit Exceptions.
Hierarchical error definitions for hardware, topology, and capture failures.
"""

class CoreSightError(Exception):
    """Base exception for all CoreSight Toolkit errors."""
    pass

class SysfsError(CoreSightError):
    """Raised when an I/O operation on sysfs nodes fails."""
    pass

class TopologyError(CoreSightError):
    """Raised when the hardware graph is inconsistent or invalid."""
    pass

class CaptureError(CoreSightError):
    """Raised when a trace capture session fails to start, stop, or configure."""
    pass

class ValidationError(CoreSightError):
    """Raised when pre-capture or hardware validation fails."""
    pass
