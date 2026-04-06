"""Unit tests for infra/exceptions.py."""

import pytest

from infra.exceptions import CaptureError, SysfsError, TopologyError


class TestExceptions:
    def test_sysfs_error(self):
        with pytest.raises(SysfsError):
            raise SysfsError("test")

    def test_topology_error(self):
        with pytest.raises(TopologyError):
            raise TopologyError("test")

    def test_capture_error(self):
        with pytest.raises(CaptureError):
            raise CaptureError("test")

    def test_exception_message(self):
        try:
            raise SysfsError("read failed")
        except SysfsError as e:
            assert "read failed" in str(e)

    def test_inherits_from_exception(self):
        assert issubclass(SysfsError, Exception)
        assert issubclass(TopologyError, Exception)
        assert issubclass(CaptureError, Exception)
