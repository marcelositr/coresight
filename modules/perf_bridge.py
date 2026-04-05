"""
CoreSight Perf Bridge.
Interfaces with Linux perf for cs_etm auxtrace recording.
"""

import subprocess
import os
from typing import Optional
from modules.debug_logger import logger

class PerfBridge:
    def __init__(self) -> None:
        self.module_name = "perf_bridge"

    def record_cs_etm(self, duration: int, output: str = "perf.data", cpu: Optional[int] = None) -> bool:
        """Runs a real perf record session for cs_etm."""
        cmd = ["perf", "record", "-e", "cs_etm//", "-o", output]
        if cpu is not None:
            cmd.extend(["-C", str(cpu)])
        else:
            cmd.append("-a")
            
        cmd.extend(["sleep", str(duration)])
        
        logger.capture(f"Running perf: {' '.join(cmd)}")
        try:
            # We use capture_output=False to let the user see the progress if running from CLI
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Perf recording failed: {str(e)}")
            return False

    def inject_metadata(self, input_file: str) -> bool:
        """Uses perf inject to fix up cs_etm auxtrace data."""
        if not os.path.exists(input_file):
            return False
            
        output_file = input_file + ".injected"
        cmd = ["perf", "inject", "--cs-etm", "-i", input_file, "-o", output_file]
        logger.capture(f"Injecting metadata: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
