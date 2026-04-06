"""Unit tests for system/base_monitor.py."""


from system.base_monitor import BaseMonitor, MonitorState


class DummyMonitor(BaseMonitor[str]):
    """Concrete implementation for testing BaseMonitor."""

    _instance_name = "dummy"

    def __init__(self):
        super().__init__()
        self._value = "initial"
        self._raise_on_refresh = False

    def _do_refresh(self) -> None:
        if self._raise_on_refresh:
            raise RuntimeError("simulated error")
        self._value = "refreshed"

    def _handle_refresh_error(self, error: Exception) -> None:
        self._value = "error_state"

    def get_metrics(self) -> str:
        return self._value

    def get_data(self) -> dict:
        return {"value": self._value}

    def format(self) -> list:
        return [f"Dummy: {self._value}"]


class TestMonitorState:
    def test_creation(self):
        state = MonitorState(
            instance_name="test", bar_width=20, label_width=10, is_healthy=True
        )
        assert state.instance_name == "test"
        assert state.bar_width == 20
        assert state.label_width == 10
        assert state.is_healthy is True


class TestBaseMonitor:
    def test_refresh_success(self):
        m = DummyMonitor()
        result = m.refresh()
        assert result == "refreshed"
        assert m.is_healthy is True

    def test_refresh_error(self):
        m = DummyMonitor()
        m._raise_on_refresh = True
        result = m.refresh()
        assert result == "error_state"
        assert m.is_healthy is False

    def test_to_string(self):
        m = DummyMonitor()
        m.refresh()
        s = m.to_string()
        assert "Dummy:" in s

    def test_update_calls_refresh(self):
        m = DummyMonitor()
        result = m.update()
        assert isinstance(result, dict)
        assert "value" in result

    def test_get_state(self):
        m = DummyMonitor()
        state = m.get_state()
        assert isinstance(state, MonitorState)
        assert state.instance_name == "dummy"
        assert state.is_healthy is True

    def test_properties(self):
        m = DummyMonitor()
        assert m.instance_name == "dummy"
        assert m.is_healthy is True

    def test_default_get_data(self):
        """Test that base get_data returns empty dict by default."""

        class MinimalMonitor(BaseMonitor[dict]):
            _instance_name = "minimal"

            def _do_refresh(self):
                pass

            def get_metrics(self):
                return {}

            def format(self):
                return []

        m = MinimalMonitor()
        assert m.get_data() == {}
