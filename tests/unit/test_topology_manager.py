"""Unit tests for core/topology_manager.py."""

import os
import tempfile

import pytest

from core.topology_manager import (
    CoreSightDevice,
    DeviceType,
    TopologyError,
    TopologyManager,
)


@pytest.fixture
def mock_sysfs():
    """Create a mock sysfs topology for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = os.path.join(tmpdir, "sys")
        os.makedirs(base)

        # etm0 -> funnel0 -> tmc_etr0
        devices = {
            "etm0": {"type": "1", "subtype": "etm"},
            "funnel0": {"type": "2", "subtype": "funnel"},
            "tmc_etr0": {"type": "3", "subtype": "etr"},
        }
        for name, meta in devices.items():
            dpath = os.path.join(base, name)
            os.makedirs(dpath)
            with open(os.path.join(dpath, "type"), "w") as f:
                f.write(meta["type"])
            with open(os.path.join(dpath, "subtype"), "w") as f:
                f.write(meta["subtype"])
            with open(os.path.join(dpath, "enable_source"), "w") as f:
                f.write("0")
            with open(os.path.join(dpath, "enable_sink"), "w") as f:
                f.write("0")
            os.makedirs(os.path.join(dpath, "connection0"))

        os.symlink(
            os.path.join(base, "funnel0"),
            os.path.join(base, "etm0", "connection0", "device"),
        )
        os.symlink(
            os.path.join(base, "tmc_etr0"),
            os.path.join(base, "funnel0", "connection0", "device"),
        )

        yield base


class TestCoreSightDevice:
    def test_creation(self):
        dev = CoreSightDevice(
            name="etm0", path="/sys/etm0", type=DeviceType.SOURCE, subtype="etm"
        )
        assert dev.name == "etm0"
        assert dev.type == DeviceType.SOURCE
        assert dev.enabled is False


class TestTopologyManager:
    def test_singleton(self, mock_sysfs):
        # Reset singleton for test isolation
        TopologyManager._instance = None
        t1 = TopologyManager(base_path=mock_sysfs)
        t2 = TopologyManager(base_path=mock_sysfs)
        assert t1 is t2

    def test_devices_discovered(self, mock_sysfs):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        assert len(topo.devices) == 3
        assert "etm0" in topo.devices
        assert "funnel0" in topo.devices
        assert "tmc_etr0" in topo.devices

    def test_device_types(self, mock_sysfs):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        assert topo.devices["etm0"].type == DeviceType.SOURCE
        assert topo.devices["funnel0"].type == DeviceType.LINK
        assert topo.devices["tmc_etr0"].type == DeviceType.SINK

    def test_find_path(self, mock_sysfs):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        path = topo.find_path("etm0", "tmc_etr0")
        assert path == ["etm0", "funnel0", "tmc_etr0"]

    def test_find_path_invalid_source(self, mock_sysfs):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        with pytest.raises(TopologyError):
            topo.find_path("nonexistent", "tmc_etr0")

    def test_find_path_no_route(self, mock_sysfs):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        with pytest.raises(TopologyError):
            topo.find_path("tmc_etr0", "etm0")  # reverse direction, no route

    def test_refresh_topology(self, mock_sysfs):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        topo.refresh_topology()
        assert len(topo.devices) == 3

    def test_print_topology(self, mock_sysfs, capsys):
        TopologyManager._instance = None
        topo = TopologyManager(base_path=mock_sysfs)
        topo.print_topology()
        captured = capsys.readouterr()
        assert "etm0" in captured.out
