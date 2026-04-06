"""
Base Monitor Protocol for CoreSight System Modules.

Defines the common interface and Template Method pattern for all system monitors.
Eliminates code duplication while preserving flexibility for specific implementations.

Following Clean Code and SOLID principles:
- Liskov Substitution: Any monitor can be used where BaseMonitor is expected
- Template Method: refresh() orchestrates _do_refresh() hook
- DRY: Common instance state (_bar_width, _label_width, _instance_name) defined once

Example:
    >>> class MyMonitor(BaseMonitor[MyMetrics]):
    ...     _instance_name = "my"
    ...     def _do_refresh(self) -> None:
    ...         self._value = collect_some_metric()
    ...     def get_metrics(self) -> MyMetrics:
    ...         return MyMetrics(value=self._value)
    ...     def format(self) -> List[str]:
    ...         return [f"value: {self._value}"]
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, List, TypeVar

from infra import config, utils


@dataclass
class MonitorState:
    """Value object representing common monitor state."""

    instance_name: str
    bar_width: int
    label_width: int
    is_healthy: bool


# Generic type for metrics
T = TypeVar("T")


class BaseMonitor(ABC, Generic[T]):
    """
    Abstract base class for all system monitors.

    Implements Template Method pattern:
    - refresh(): Template method that orchestrates _do_refresh() + error handling
    - _do_refresh(): Abstract hook where subclasses implement actual collection
    - update(): Legacy wrapper for backward compatibility
    - format(): Abstract hook for dashboard display
    - to_string(): Concrete method (shared implementation)

    Subclasses must implement:
    - _instance_name: str (class attribute)
    - _do_refresh(): Abstract method for data collection
    - get_metrics(): Return typed metrics object
    - format(): Return formatted lines for display

    Example:
        >>> class CpuMonitor(BaseMonitor[CpuMetrics]):
        ...     _instance_name = "cpu"
        ...     def _do_refresh(self) -> None:
        ...         self._total = psutil.cpu_percent()
        ...     def get_metrics(self) -> CpuMetrics:
        ...         return CpuMetrics(total=self._total)
        ...     def format(self) -> List[str]:
        ...         return [f"CPU: {self._total}%"]
    """

    _instance_name: str = "base"

    def __init__(self) -> None:
        """Initialize monitor with common layout settings."""
        self._bar_width: int = getattr(config, "DYNAMIC_BAR_WIDTH", 30)
        self._label_width: int = getattr(config, "DYNAMIC_LABEL_WIDTH", 25)
        self._healthy: bool = True

    # ========================================================================
    # TEMPLATE METHOD
    # ========================================================================

    def refresh(self) -> T:
        """
        Template method: collect data with standardized error handling.

        Orchestrates:
        1. Call subclass _do_refresh()
        2. Catch and log exceptions
        3. Return current metrics

        Returns:
            T: Typed metrics object.
        """
        try:
            self._do_refresh()
            self._healthy = True
        except Exception as e:
            utils.log_message(
                self._instance_name, f"Refresh failed: {e}", level="ERROR"
            )
            self._healthy = False
            self._handle_refresh_error(e)

        return self.get_metrics()

    # ========================================================================
    # ABSTRACT HOOKS (Must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    def _do_refresh(self) -> None:
        """
        Hook: Implement actual data collection logic.

        Called by refresh() within try/except block.
        Should populate internal state variables.
        """
        ...

    @abstractmethod
    def get_metrics(self) -> T:
        """
        Hook: Return current metrics as a typed object.

        Returns:
            T: Typed metrics dataclass.
        """
        ...

    @abstractmethod
    def format(self) -> List[str]:
        """
        Hook: Format metrics for dashboard display.

        Returns:
            List[str]: Formatted lines ready for display.
        """
        ...

    # ========================================================================
    # CONCRETE METHODS (Shared implementation)
    # ========================================================================

    def update(self) -> Any:
        """
        Legacy method for backward compatibility.

        Delegates to refresh() and returns raw data.
        Subclasses may override if return type differs historically.

        Returns:
            Raw data structure (varies by monitor).
        """
        self.refresh()
        return self.get_data()

    def to_string(self) -> str:
        """
        Get formatted output as single string.

        Shared implementation used by all monitors.

        Returns:
            str: Formatted output joined by newlines.
        """
        return "\n".join(self.format())

    def get_data(self) -> Any:
        """
        Hook: Return raw data for external systems.

        Default implementation returns empty dict.
        Subclasses should override to return actual data.

        Returns:
            Raw data structure (dict, list, etc).
        """
        return {}

    # ========================================================================
    # ERROR HANDLING HOOK (Optional override)
    # ========================================================================

    def _handle_refresh_error(self, error: Exception) -> None:
        """
        Hook: Handle refresh errors (e.g., reset state to defaults).

        Called automatically when _do_refresh() raises an exception.
        Default: no-op. Override to reset internal state.

        Args:
            error: The exception that was raised.
        """
        pass

    # ========================================================================
    # PROPERTIES AND STATE ACCESSORS
    # ========================================================================

    @property
    def instance_name(self) -> str:
        """Monitor instance identifier."""
        return self._instance_name

    @property
    def is_healthy(self) -> bool:
        """Check if monitor last refreshed successfully."""
        return self._healthy

    def get_state(self) -> MonitorState:
        """Get common monitor state as value object."""
        return MonitorState(
            instance_name=self._instance_name,
            bar_width=self._bar_width,
            label_width=self._label_width,
            is_healthy=self._healthy,
        )
