"""Unit tests for system monitors (CPU, RAM, Disk, Network, Logs, Alerts)."""


from system.alerts import AlertMetrics, AlertsMonitor
from system.cpu import CpuMetrics, CpuMonitor
from system.disk import DiskMetrics, DiskMonitor
from system.logs import LogsMetrics, LogsMonitor
from system.network import NetworkMetrics, NetworkMonitor
from system.ram import MemoryMetrics, RamMonitor


class TestCpuMonitor:
    def test_refresh_returns_metrics(self):
        m = CpuMonitor()
        result = m.refresh()
        assert isinstance(result, CpuMetrics)

    def test_get_metrics(self):
        m = CpuMonitor()
        m.refresh()
        metrics = m.get_metrics()
        assert isinstance(metrics, CpuMetrics)
        assert hasattr(metrics, "total")
        assert hasattr(metrics, "per_core")

    def test_format_returns_list(self):
        m = CpuMonitor()
        m.refresh()
        lines = m.format()
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_update_returns_tuple(self):
        m = CpuMonitor()
        per_core, total = m.update()
        assert isinstance(per_core, list)
        assert isinstance(total, float)

    def test_is_healthy(self):
        m = CpuMonitor()
        m.refresh()
        assert m.is_healthy is True


class TestRamMonitor:
    def test_refresh_returns_metrics(self):
        m = RamMonitor()
        result = m.refresh()
        assert isinstance(result, MemoryMetrics)

    def test_format_returns_list(self):
        m = RamMonitor()
        m.refresh()
        lines = m.format()
        assert len(lines) >= 2  # RAM + Swap

    def test_properties(self):
        m = RamMonitor()
        m.refresh()
        assert 0 <= m.ram_percent <= 100
        assert 0 <= m.swap_percent <= 100


class TestDiskMonitor:
    def test_refresh_returns_metrics(self):
        m = DiskMonitor()
        result = m.refresh()
        assert isinstance(result, DiskMetrics)

    def test_format_returns_list(self):
        m = DiskMonitor()
        m.refresh()
        lines = m.format()
        assert isinstance(lines, list)

    def test_partitions_filtered(self):
        m = DiskMonitor()
        m.refresh()
        metrics = m.get_metrics()
        for p in metrics.partitions:
            assert p.mount  # No empty mountpoints


class TestNetworkMonitor:
    def test_refresh_returns_metrics(self):
        m = NetworkMonitor()
        result = m.refresh()
        assert isinstance(result, NetworkMetrics)

    def test_format_returns_list(self):
        m = NetworkMonitor()
        m.refresh()
        lines = m.format()
        assert isinstance(lines, list)


class TestLogsMonitor:
    def test_refresh_returns_metrics(self):
        m = LogsMonitor()
        result = m.refresh()
        assert isinstance(result, LogsMetrics)

    def test_format_returns_list(self):
        m = LogsMonitor()
        m.refresh()
        lines = m.format()
        assert isinstance(lines, list)


class TestAlertsMonitor:
    def test_check_below_threshold(self):
        m = AlertsMonitor()
        result = m.check(cpu=50.0, ram=50.0, swap=50.0, disks=[50.0])
        assert result is False
        assert m.is_triggered is False

    def test_check_above_threshold_cpu(self):
        m = AlertsMonitor()
        result = m.check(cpu=95.0, ram=50.0, swap=50.0, disks=[50.0])
        assert result is True
        assert "CPU" in m.triggered_modules

    def test_check_above_threshold_ram(self):
        m = AlertsMonitor()
        result = m.check(cpu=50.0, ram=95.0, swap=50.0, disks=[50.0])
        assert result is True
        assert "RAM" in m.triggered_modules

    def test_check_above_threshold_disk(self):
        m = AlertsMonitor()
        result = m.check(cpu=50.0, ram=50.0, swap=50.0, disks=[95.0])
        assert result is True
        assert "DISK" in m.triggered_modules

    def test_format_message_when_triggered(self):
        m = AlertsMonitor()
        m.check(cpu=95.0, ram=50.0, swap=50.0, disks=[50.0])
        msg = m.format_message()
        assert "CRITICAL" in msg

    def test_format_message_when_not_triggered(self):
        m = AlertsMonitor()
        m.check(cpu=50.0, ram=50.0, swap=50.0, disks=[50.0])
        msg = m.format_message()
        assert msg == ""

    def test_get_metrics(self):
        m = AlertsMonitor()
        m.check(cpu=95.0)
        metrics = m.get_metrics()
        assert isinstance(metrics, AlertMetrics)
        assert metrics.triggered is True

    def test_check_thresholds_legacy(self):
        m = AlertsMonitor()
        result = m.check_thresholds(
            cpu_total=95.0, ram_percent=50.0, swap_percent=50.0, disks_percents=[50.0]
        )
        assert result is True

    def test_beep_no_crash(self):
        m = AlertsMonitor()
        m.check(cpu=95.0)
        m.beep()  # Should not crash
