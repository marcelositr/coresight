"""
Input Handler for CoreSight Dashboard.

Handles terminal input setup, reading, and action dispatch.
Follows Single Responsibility Principle: only manages user input.
"""

import select
import sys
import time
from typing import Any, Callable, Dict, Optional

from core.topology_manager import DeviceType
from infra import config, utils


class InputHandler:
    """
    Manages terminal input configuration and command dispatch.

    Responsibilities:
    - Set up terminal in cbreak mode
    - Read keyboard input non-blocking
    - Dispatch commands to action handlers
    - Restore terminal on cleanup

    Example:
        >>> handler = InputHandler()
        >>> handler.setup()
        >>> try:
        ...     cmd = handler.read_input()
        ...     if cmd:
        ...         handler.dispatch(cmd)
        ... finally:
        ...     handler.cleanup()
    """

    def __init__(self, refresh_interval: float = config.REFRESH_INTERVAL) -> None:
        """
        Initialize input handler.

        Args:
            refresh_interval: Seconds to wait for input before timeout.
        """
        self._refresh_interval = refresh_interval
        self._fd: Optional[int] = None
        self._old_settings: Optional[Any] = None
        self._termios_available = False

        # Command registry
        self._commands: Dict[str, Callable] = {}

        # Try to import terminal modules
        try:
            import termios
            import tty

            self._tty = tty
            self._termios = termios
            self._termios_available = True
        except ImportError:
            self._termios_available = False

    def setup(self) -> None:
        """
        Configure terminal for non-blocking input (cbreak mode).

        Must be called before read_input().
        """
        if not self._termios_available:
            return

        self._fd = sys.stdin.fileno()
        try:
            assert self._fd is not None  # Type narrowing for type checker
            self._old_settings = self._termios.tcgetattr(self._fd)
            self._tty.setcbreak(self._fd)
        except Exception as e:
            utils.log_message("input", f"Terminal setup failed: {e}", "WARNING")
            self._old_settings = None

    def cleanup(self) -> None:
        """Restore original terminal settings."""
        if not self._termios_available:
            return
        if self._old_settings is not None and self._fd is not None:
            try:
                self._termios.tcsetattr(
                    self._fd, self._termios.TCSADRAIN, self._old_settings
                )
            except Exception:
                pass

    def read_input(self) -> Optional[str]:
        """
        Read single keyboard command (non-blocking with timeout).

        Returns:
            Uppercase command character, or None if no input.
        """
        if not self._termios_available:
            time.sleep(self._refresh_interval)
            return None

        if select.select([sys.stdin], [], [], self._refresh_interval)[0]:
            char = sys.stdin.read(1).upper()
            return char if char else None
        return None

    def register(self, command: str, handler: Callable) -> None:
        """
        Register a command handler.

        Args:
            command: Single character command (uppercase).
            handler: Callable to execute when command received.
        """
        self._commands[command] = handler

    def dispatch(self, command: str) -> bool:
        """
        Execute handler for given command.

        Args:
            command: Command character.

        Returns:
            True if command was handled, False otherwise.
        """
        handler = self._commands.get(command)
        if handler:
            handler()
            return True
        return False

    def is_exit_command(self, command: Optional[str]) -> bool:
        """
        Check if command signals application exit.

        Args:
            command: Command character or None.

        Returns:
            True if command is ESC or Ctrl+C.
        """
        return command in ("\x1b", "\x03", "ESC", "EXIT")


def create_default_input_handler(
    orchestrator: Any,
    renderer: Any,
    decoder: Any,
    on_exit: Callable,
    view_mode_ref: Dict[str, int],
) -> InputHandler:
    """
    Factory function to create InputHandler with all standard commands wired.

    Args:
        orchestrator: DataOrchestrator instance.
        renderer: DashboardRenderer instance.
        decoder: TraceDecode instance.
        on_exit: Callable to set running=False.
        view_mode_ref: Dict with 'mode' key for view switching.

    Returns:
        Configured InputHandler ready for use.
    """
    handler = InputHandler()

    # Exit commands
    handler.register("\x1b", on_exit)  # ESC
    handler.register("\x03", on_exit)  # Ctrl+C

    # View switching
    handler.register("1", lambda: view_mode_ref.update(mode=1))
    handler.register("2", lambda: view_mode_ref.update(mode=2))

    # Trace capture commands
    def start_capture():
        sources = [
            n
            for n, d in orchestrator.topology.devices.items()
            if d.type == DeviceType.SOURCE
        ]
        sinks = [
            n
            for n, d in orchestrator.topology.devices.items()
            if d.type == DeviceType.SINK
        ]
        if sources and sinks:
            try:
                orchestrator.capture.capture_start(sources[0], sinks[0])
            except Exception as e:
                utils.log_message("input", f"Capture failed: {str(e)}", "ERROR")
        else:
            utils.log_message(
                "input", "No valid CoreSight Source/Sink pair detected.", "ERROR"
            )

    handler.register("S", start_capture)
    handler.register("T", orchestrator.capture.capture_stop)
    handler.register("A", lambda: renderer.run_analysis_action(decoder))

    return handler
