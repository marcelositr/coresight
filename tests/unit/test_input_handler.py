"""Unit tests for app/input_handler.py."""


from app.input_handler import InputHandler


class TestInputHandler:
    def test_creation(self):
        h = InputHandler()
        assert h._commands == {}

    def test_register_and_dispatch(self):
        h = InputHandler()
        called = []
        h.register("X", lambda: called.append("X"))
        result = h.dispatch("X")
        assert result is True
        assert called == ["X"]

    def test_dispatch_unknown_command(self):
        h = InputHandler()
        result = h.dispatch("Z")
        assert result is False

    def test_is_exit_command_esc(self):
        h = InputHandler()
        assert h.is_exit_command("\x1b") is True

    def test_is_exit_command_ctrlc(self):
        h = InputHandler()
        assert h.is_exit_command("\x03") is True

    def test_is_exit_command_regular(self):
        h = InputHandler()
        assert h.is_exit_command("A") is False
        assert h.is_exit_command("S") is False

    def test_is_exit_command_none(self):
        h = InputHandler()
        assert h.is_exit_command(None) is False


class TestInputHandlerWithoutTermios:
    def test_read_input_no_termios(self):
        h = InputHandler(refresh_interval=0.01)
        h._termios_available = False
        result = h.read_input()
        assert result is None

    def test_setup_no_termios(self):
        h = InputHandler()
        h._termios_available = False
        h.setup()  # Should not raise

    def test_cleanup_no_termios(self):
        h = InputHandler()
        h._termios_available = False
        h.cleanup()  # Should not raise
