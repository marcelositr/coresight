"""
CoreSight Application Layer.

Contains the decomposed application orchestrators following Clean Code principles:
- DataOrchestrator: Data collection and processing
- DashboardRenderer: UI formatting and rendering
- InputHandler: Terminal input and action dispatch
"""

from .input_handler import InputHandler
from .orchestrator import DataOrchestrator
from .renderer import DashboardRenderer

__all__ = ["DataOrchestrator", "DashboardRenderer", "InputHandler"]
