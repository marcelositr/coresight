"""Unit tests for core/trace_capture.py."""



from core.topology_manager import TopologyManager
from core.trace_capture import TraceCapture


class TestTraceCapture:
    def test_status_idle(self):
        TopologyManager._instance = None
        cap = TraceCapture()
        status = cap.status()
        assert status["capturing"] is False
        assert status["path"] == []

    def test_capture_stop_when_idle(self):
        TopologyManager._instance = None
        cap = TraceCapture()
        result = cap.capture_stop()
        assert result is False

    # Note: capture_start/stop require full sysfs mock with buffer_size node
    # These are covered by integration tests (test_phase1_integration.py)
