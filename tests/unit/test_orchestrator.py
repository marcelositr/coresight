"""Unit tests for app/orchestrator.py."""

import pytest

from app.orchestrator import DataOrchestrator


class MockMonitor:
    """Mock monitor that returns predictable data."""

    def __init__(self, per_core=None, total=50.0):
        self._per_core = per_core or [50.0, 50.0]
        self._total = total
        self.ram_percent = 50.0
        self.swap_percent = 30.0

    def update(self):
        return self._per_core, self._total


class MockTopology:
    def __init__(self):
        self.devices = {}

    class MockHW:
        def safe_read(self, dev, node):
            return "0"

    hw = MockHW()


class MockCapture:
    def status(self):
        return {"capturing": False, "path": []}


class MockAlerts:
    def check_thresholds(self, **kwargs):
        pass


@pytest.fixture
def orchestrator():
    cpu = MockMonitor()
    ram = MockMonitor()
    disk = MockMonitor()
    network = MockMonitor()
    logs = MockMonitor()
    alerts = MockAlerts()
    topo = MockTopology()
    capture = MockCapture()
    return DataOrchestrator(cpu, ram, disk, network, logs, alerts, topo, capture)  # type: ignore[arg-type]


class TestDataOrchestrator:
    def test_collect_all(self, orchestrator):
        orchestrator.collect_all()
        assert "cpu_total" in orchestrator.raw_data
        assert orchestrator.raw_data["cpu_total"] == 50.0

    def test_process_alerts(self, orchestrator):
        orchestrator.collect_all()
        orchestrator.process_alerts()  # Should not raise

    def test_adjust_layout(self, orchestrator):
        w, h = orchestrator.adjust_layout()
        assert isinstance(w, int)
        assert isinstance(h, int)
        assert w >= 60

    def test_refresh_cycle(self, orchestrator):
        w, h = orchestrator.refresh_cycle()
        assert w >= 60
        assert h >= 20

    def test_raw_data_property(self, orchestrator):
        assert isinstance(orchestrator.raw_data, dict)

    def test_accessors(self, orchestrator):
        assert orchestrator.cpu is not None
        assert orchestrator.ram is not None
        assert orchestrator.topology is not None
        assert orchestrator.capture is not None
        assert orchestrator.alerts is not None
