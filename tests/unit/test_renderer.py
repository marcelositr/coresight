"""Unit tests for app/renderer.py."""

import pytest

from app.renderer import DashboardRenderer
from infra import utils


class MockOrchestrator:
    class MockMonitor:
        def format(self):
            return ["mock line"]

    class MockTopology:
        devices = {}

    class MockAlerts:
        def display_alert(self):
            return ""

        def sound_alert(self):
            pass

    class MockCapture:
        def status(self):
            return {"capturing": False, "path": []}

    def __init__(self):
        self.cpu = self.MockMonitor()
        self.ram = self.MockMonitor()
        self.disk = self.MockMonitor()
        self.network = self.MockMonitor()
        self.logs = self.MockMonitor()
        self.topology = self.MockTopology()
        self.capture = self.MockCapture()
        self.alerts = self.MockAlerts()


class MockAnalyzer:
    def get_summary_lines(self, report):
        if report.get("status") == "empty":
            return ["No data"]
        return ["Events: 10"]


@pytest.fixture
def renderer():
    orch = MockOrchestrator()
    analyzer = MockAnalyzer()
    return DashboardRenderer(orch, analyzer)


class TestDashboardRenderer:
    def test_format_system_view(self, renderer):
        lines = renderer._format_system_view(80)
        assert len(lines) > 0
        assert all(isinstance(item, str) for item in lines)

    def test_format_coresight_view(self, renderer):
        lines = renderer._format_coresight_view(80)
        assert len(lines) > 0

    def test_format_header(self, renderer):
        lines = renderer._format_header(80)
        assert len(lines) == 3  # top border, text, separator
        assert lines[0].startswith("┌")
        assert lines[0].endswith("┐")

    def test_format_navigation(self, renderer):
        lines = renderer._format_navigation(80, 1)
        assert len(lines) == 2
        assert "Monitor" in lines[0] or "Sistema" in lines[0]

    def test_format_output_view1(self, renderer):
        lines = renderer.format_output(view_mode=1)
        assert len(lines) > 10
        assert lines[0].startswith("┌")
        assert lines[-1].startswith("└")

    def test_format_output_view2(self, renderer):
        lines = renderer.format_output(view_mode=2)
        assert len(lines) > 10

    def test_last_report_property(self, renderer):
        renderer.last_report = {"status": "test"}
        assert renderer.last_report["status"] == "test"

    def test_pad_line_fits(self, renderer):
        line = renderer._pad_line("hello", 20)
        assert line.startswith("│ ")
        assert line.endswith(" │")

    def test_pad_line_truncation(self, renderer):
        long_text = "A" * 100
        line = renderer._pad_line(long_text, 20)
        # Truncated content + ANSI reset + borders = may exceed width in raw len
        # But visible length should be <= width
        visible = utils.get_visible_length(line)
        assert visible <= 20
