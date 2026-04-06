"""Unit tests for infra/config.py."""

import pytest

from infra import config


class TestThresholds:
    def test_attribute_access(self):
        assert config.THRESHOLDS.cpu == 90.0
        assert config.THRESHOLDS.ram == 90.0
        assert config.THRESHOLDS.disk == 90.0
        assert config.THRESHOLDS.network == 90.0

    def test_dict_access(self):
        assert config.THRESHOLDS["cpu"] == 90.0
        assert config.THRESHOLDS["ram"] == 90.0
        assert config.THRESHOLDS["disk"] == 90.0
        assert config.THRESHOLDS["network"] == 90.0

    def test_get_method(self):
        assert config.THRESHOLDS.get("cpu") == 90.0
        assert config.THRESHOLDS.get("nonexistent") is None
        assert config.THRESHOLDS.get("nonexistent", 50.0) == 50.0

    def test_invalid_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            _ = config.THRESHOLDS["invalid"]

    def test_repr(self):
        assert "cpu" in repr(config.THRESHOLDS)


class TestColors:
    def test_attribute_access(self):
        assert config.COLORS.green == "\033[92m"
        assert config.COLORS.yellow == "\033[93m"
        assert config.COLORS.red == "\033[91m"
        assert config.COLORS.reset == "\033[0m"
        assert config.COLORS.blink == "\033[5m"
        assert config.COLORS.blue == "\033[94m"
        assert config.COLORS.cyan == "\033[96m"

    def test_dict_access(self):
        assert config.COLORS["green"] == "\033[92m"
        assert config.COLORS["reset"] == "\033[0m"

    def test_get_method(self):
        assert config.COLORS.get("green") == "\033[92m"
        assert config.COLORS.get("nonexistent") is None
        assert config.COLORS.get("nonexistent", "X") == "X"

    def test_invalid_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            _ = config.COLORS["invalid"]


class TestConfigConstants:
    def test_refresh_interval(self):
        assert config.REFRESH_INTERVAL == 1.0

    def test_debug(self):
        assert config.DEBUG is True

    def test_cache_dir(self):
        assert "CoreSight" in config.CACHE_DIR

    def test_log_level(self):
        assert config.LOG_LEVEL == "DEBUG"

    def test_dynamic_layout(self):
        # Values may have been changed by other tests via orchestrator.adjust_layout()
        assert isinstance(config.DYNAMIC_LABEL_WIDTH, int)
        assert isinstance(config.DYNAMIC_BAR_WIDTH, int)
        assert config.DYNAMIC_LABEL_WIDTH >= 10
        assert config.DYNAMIC_BAR_WIDTH >= 8
