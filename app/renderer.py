"""
Dashboard Renderer for CoreSight Dashboard.

Handles all UI formatting and screen rendering.
Follows Single Responsibility Principle: only formats and displays output.
"""

import datetime
import sys
from typing import Any, Dict, List

from i18n import labels
from infra import config, utils


class DashboardRenderer:
    """
    Handles dashboard output formatting and screen rendering.

    Responsibilities:
    - Format System Monitoring view
    - Format CoreSight Toolkit view
    - Build header, footer, navigation
    - Render to terminal

    Example:
        >>> renderer = DashboardRenderer(orchestrator, analyzer)
        >>> lines = renderer.format_output(view_mode=1)
        >>> renderer.render_screen(lines)
    """

    def __init__(self, orchestrator: Any, analyzer: Any) -> None:
        """
        Initialize renderer with data dependencies.

        Args:
            orchestrator: DataOrchestrator instance (provides monitors and data).
            analyzer: TraceAnalyzer instance for analysis view.
        """
        self._orchestrator = orchestrator
        self._analyzer = analyzer
        self._last_report: Dict[str, Any] = {"status": "empty"}

    @property
    def last_report(self) -> Dict[str, Any]:
        """Access last analysis report."""
        return self._last_report

    @last_report.setter
    def last_report(self, value: Dict[str, Any]) -> None:
        """Set analysis report."""
        self._last_report = value

    def _pad_line(self, content: str, width: int) -> str:
        """
        Pad or truncate content line to fit box width with ANSI-aware handling.

        Wraps content between │ borders, accounting for ANSI escape codes
        in visible length calculation.

        Args:
            content: Text with optional ANSI codes.
            width: Total box width.

        Returns:
            Formatted line with │ borders, padded or truncated.
        """
        visible_len = utils.get_visible_length(content)
        available = width - 5  # "│ " (2) + " │" (2) + 1 buffer (prevent wrap)

        if visible_len > available:
            # Truncate content to fit (ANSI-aware)
            truncated = self._truncate_ansi_content(content, available)
            return f"│ {truncated} │"
        else:
            padding = available - visible_len
            return f"│ {content}{' ' * padding} │"

    def _truncate_ansi_content(self, content: str, max_visible: int) -> str:
        """Truncate ANSI content string to maximum visible length."""
        if max_visible <= 0:
            return ""

        result = []
        visible_count = 0
        i = 0
        in_escape = False

        while i < len(content) and visible_count < max_visible:
            char = content[i]
            if char == "\x1b":
                # Start of ANSI escape sequence
                in_escape = True
                result.append(char)
            elif in_escape:
                result.append(char)
                if char in "mKJH":
                    in_escape = False
            else:
                result.append(char)
                visible_count += 1
            i += 1

        # Close any open ANSI codes
        if in_escape:
            result.append("\033[0m")  # Reset
        elif "\033[0m" not in content[:i]:
            result.append("\033[0m")

        return "".join(result)

    def _format_system_view(self, width: int) -> List[str]:
        """Format System Monitoring view lines with responsive layout."""
        lines = []
        orchestrator = self._orchestrator

        sections = [
            (labels["cpu"], orchestrator.cpu.format()),
            (labels["ram"], orchestrator.ram.format()),
            (labels["disk"], orchestrator.disk.format()),
            (labels["network"], orchestrator.network.format()),
            (labels["logs"], orchestrator.logs.format()),
        ]

        for title, section_lines in sections:
            lines.append(
                utils.draw_box_line(
                    f"{config.COLORS['blue']}■ {title}{config.COLORS['reset']}", width
                )
            )
            for line in section_lines:
                # Pad or truncate content line to fit box width
                lines.append(self._pad_line(line, width))
            lines.append("├" + "─" * (width - 3) + "┤")

        return lines

    def _format_coresight_view(self, width: int) -> List[str]:
        """Format CoreSight Toolkit view lines with responsive layout."""
        lines = []
        orchestrator = self._orchestrator
        topo = orchestrator.topology
        capture = orchestrator.capture

        # Real Topology List
        lines.append(
            utils.draw_box_line(
                f"{config.COLORS['blue']}■ {labels['hw_status']}{config.COLORS['reset']}",
                width,
            )
        )
        for name, dev in topo.devices.items():
            state_lbl = labels["enabled"] if dev.enabled else labels["disabled"]
            color = config.COLORS["green"] if dev.enabled else config.COLORS["reset"]
            content = f"  {name:15} [{dev.subtype:8}] : {color}{state_lbl}{config.COLORS['reset']}"
            lines.append(self._pad_line(content, width))
        lines.append("├" + "─" * (width - 3) + "┤")

        # Capture Status
        lines.append(
            utils.draw_box_line(
                f"{config.COLORS['blue']}■ {labels['capture']}{config.COLORS['reset']}",
                width,
            )
        )
        capture_status = capture.status()
        is_cap = capture_status.get("capturing", False)
        cap_state = labels["active"] if is_cap else labels["idle"]
        cap_color = (
            config.COLORS["red"] + config.COLORS["blink"]
            if is_cap
            else config.COLORS["green"]
        )
        content = (
            f"  {labels['state']:12} : {cap_color}{cap_state}{config.COLORS['reset']}"
        )
        lines.append(self._pad_line(content, width))
        if is_cap:
            path = capture_status.get("path", [])
            lines.append(self._pad_line(f"  Path: {' -> '.join(path)}", width))
        lines.append("├" + "─" * (width - 3) + "┤")

        # Analysis
        lines.append(
            utils.draw_box_line(
                f"{config.COLORS['blue']}■ {labels['analysis']}{config.COLORS['reset']}",
                width,
            )
        )
        if self._last_report.get("status") == "empty":
            lines.append(
                self._pad_line(
                    "  No analysis data available. Run 'A' to analyze.", width
                )
            )
        else:
            summary = self._analyzer.get_summary_lines(self._last_report)
            for line in summary:
                lines.append(self._pad_line(f"  {line}", width))
        lines.append("├" + "─" * (width - 3) + "┤")

        return lines

    def _format_header(self, width: int) -> List[str]:
        """Format dashboard header with timestamp."""
        lines = []
        lines.append("┌" + "─" * (width - 3) + "┐")
        header_text = f" CoreSight Dashboard v1.2 | {datetime.datetime.now().strftime('%H:%M:%S')} "
        lines.append(
            utils.draw_box_line(
                f"{config.COLORS['cyan']}{header_text}{config.COLORS['reset']}",
                width,
                "center",
            )
        )
        lines.append("├" + "─" * (width - 3) + "┤")
        return lines

    def _format_navigation(self, width: int, view_mode: int) -> List[str]:
        """Format tab/navigation bar."""
        lines = []
        nav_text = f" {labels['view_system']} | {labels['view_coresight']} "
        if view_mode == 1:
            nav_text = nav_text.replace(
                labels["view_system"],
                f"{config.COLORS['yellow']}{labels['view_system']}{config.COLORS['reset']}",
            )
        else:
            nav_text = nav_text.replace(
                labels["view_coresight"],
                f"{config.COLORS['yellow']}{labels['view_coresight']}{config.COLORS['reset']}",
            )
        lines.append(utils.draw_box_line(nav_text, width, "center"))
        lines.append("├" + "─" * (width - 3) + "┤")
        return lines

    def _format_alerts(self, width: int) -> List[str]:
        """Format global alerts section."""
        lines = []
        alerts = self._orchestrator.alerts
        alert_str = alerts.display_alert()
        if alert_str:
            lines.append(utils.draw_box_line(alert_str, width, "center"))
            lines.append("├" + "─" * (width - 3) + "┤")
            alerts.sound_alert()
        return lines

    def _format_footer(self, width: int) -> List[str]:
        """Format dashboard footer with controls."""
        lines = []
        footer_text = " [1/2] View | [S/T/A] Trace | [ESC] Exit "
        lines.append(utils.draw_box_line(footer_text, width, "right"))
        lines.append("└" + "─" * (width - 3) + "┘")
        return lines

    def format_output(self, view_mode: int) -> List[str]:
        """
        Build complete dashboard output for given view mode.

        Reads real terminal size and passes to all formatters.

        Args:
            view_mode: 1 for System, 2 for CoreSight.

        Returns:
            List of formatted lines ready for rendering.
        """
        width, _ = utils.get_terminal_size()
        width = max(60, width)  # minimum 60 cols for readability

        lines = []

        # Header
        lines.extend(self._format_header(width))

        # Navigation
        lines.extend(self._format_navigation(width, view_mode))

        # Alerts
        lines.extend(self._format_alerts(width))

        # Content
        if view_mode == 1:
            lines.extend(self._format_system_view(width))
        else:
            lines.extend(self._format_coresight_view(width))

        # Footer
        lines.extend(self._format_footer(width))

        return lines

    def render_screen(self, lines: List[str]) -> None:
        """
        Clear screen and render formatted lines.

        Args:
            lines: List of formatted output lines.
        """
        utils.clear_screen()
        sys.stdout.write("\n".join(lines))
        sys.stdout.flush()

    def run_analysis_action(self, decoder: Any) -> None:
        """
        Execute trace analysis action with mock data.

        Args:
            decoder: TraceDecode instance for decoding mock data.
        """
        mock_data = (
            type(decoder).SYNC_MARKER_ETM4
            + b"\x01\x11"
            + type(decoder).SYNC_MARKER_ETM4
            + b"\x70\x22"
        )
        events = decoder.decode_stream(mock_data)
        self._last_report = self._analyzer.analyze_events(events)
