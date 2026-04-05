"""
Trace Analyzer Module for CoreSight Toolkit.
Performs statistical analysis and performance metric extraction from decoded trace events.
Follows Senior Engineer standards and Blueprint specifications.
"""

import utils
from typing import List, Dict, Any, Optional

class TraceAnalyzer:
    """
    Analyzes decoded CoreSight events to extract performance insights and execution statistics.
    """
    
    def __init__(self) -> None:
        """
        Initializes the analyzer module.
        """
        self.module_name: str = "trace_analyzer"
        utils.log_message(self.module_name, "TraceAnalyzer initialized.", "DEBUG")

    def analyze_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes a list of decoded events and generates a statistical report.
        
        Args:
            events (List[Dict[str, Any]]): List of events from TraceDecode.
            
        Returns:
            Dict[str, Any]: Analysis report.
        """
        if not events:
            utils.log_message(self.module_name, "No events to analyze.", "WARNING")
            return {"status": "empty"}

        report: Dict[str, Any] = {
            "total_events": len(events),
            "packet_distribution": {},
            "performance": {
                "total_cycles": 0,
                "branch_count": 0,
                "branch_density": 0.0
            },
            "data_stats": {
                "total_bytes": 0,
                "average_packet_size": 0.0
            }
        }

        total_bytes = 0
        
        for event in events:
            etype = event.get("type", "UNKNOWN")
            esize = event.get("size", 0)
            
            # 1. Distribution
            report["packet_distribution"][etype] = report["packet_distribution"].get(etype, 0) + 1
            
            # 2. Performance Metrics
            if etype == "CYCLE_COUNT":
                # In a real scenario, we would parse the value from the packet data
                # For now, we'll increment based on dummy data if available
                report["performance"]["total_cycles"] += 1 
            elif etype == "BRANCH":
                report["performance"]["branch_count"] += 1
                
            # 3. Data Stats
            total_bytes += esize

        # Post-processing
        if report["total_events"] > 0:
            report["performance"]["branch_density"] = report["performance"]["branch_count"] / report["total_events"]
            report["data_stats"]["total_bytes"] = total_bytes
            report["data_stats"]["average_packet_size"] = total_bytes / report["total_events"]

        utils.log_message(self.module_name, f"Analysis complete for {len(events)} events.", "INFO")
        return report

    def get_summary_lines(self, report: Dict[str, Any]) -> List[str]:
        """
        Formats the report into human-readable lines for display/logging.
        
        Args:
            report (Dict[str, Any]): The generated report.
            
        Returns:
            List[str]: Formatted lines.
        """
        if report.get("status") == "empty":
            return ["No trace data analyzed."]
            
        perf = report["performance"]
        dist = report["packet_distribution"]
        
        lines = [
            f"Total Events:    {report['total_events']}",
            f"Total Cycles:    {perf['total_cycles']}",
            f"Branch Density:  {perf['branch_density']:.2%}",
            f"Avg Packet Size: {report['data_stats']['average_packet_size']:.2f} bytes",
            "Packet Distribution:"
        ]
        
        for ptype, count in dist.items():
            lines.append(f"  - {ptype:12}: {count}")
            
        return lines
