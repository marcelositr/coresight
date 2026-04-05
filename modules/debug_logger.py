"""
CoreSight Debug Logger.
Provides structured logging for hardware discovery, topology, and capture events.
"""

import logging
import sys
from typing import Optional

class CoreSightLogger:
    """Structured logger for technical diagnostics."""
    
    def __init__(self, name: str = "CoreSight", level: int = logging.DEBUG) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def hw_discovery(self, msg: str) -> None:
        self.logger.info(f"[HW DISCOVERY] {msg}")

    def topology(self, msg: str) -> None:
        self.logger.info(f"[TOPOLOGY] {msg}")

    def capture(self, msg: str) -> None:
        self.logger.info(f"[CAPTURE] {msg}")

    def sysfs_io(self, msg: str) -> None:
        self.logger.debug(f"[SYSFS IO] {msg}")

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

# Global singleton logger
logger = CoreSightLogger()
