
import unittest
from modules.trace_analyzer import TraceAnalyzer

class TestTraceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TraceAnalyzer()

    def test_analyze_empty(self):
        report = self.analyzer.analyze_events([])
        self.assertEqual(report["status"], "empty")

    def test_analyze_stats(self):
        events = [
            {"type": "BRANCH", "size": 4},
            {"type": "TIMESTAMP", "size": 8},
            {"type": "CYCLE_COUNT", "size": 2},
            {"type": "BRANCH", "size": 4}
        ]
        
        report = self.analyzer.analyze_events(events)
        
        self.assertEqual(report["total_events"], 4)
        self.assertEqual(report["packet_distribution"]["BRANCH"], 2)
        self.assertEqual(report["packet_distribution"]["CYCLE_COUNT"], 1)
        self.assertEqual(report["performance"]["total_cycles"], 1)
        self.assertEqual(report["performance"]["branch_count"], 2)
        self.assertEqual(report["performance"]["branch_density"], 0.5)
        self.assertEqual(report["data_stats"]["total_bytes"], 18)
        self.assertEqual(report["data_stats"]["average_packet_size"], 4.5)

    def test_summary_format(self):
        events = [{"type": "BRANCH", "size": 4}]
        report = self.analyzer.analyze_events(events)
        lines = self.analyzer.get_summary_lines(report)
        
        self.assertTrue(any("Total Events:    1" in line for line in lines))
        self.assertTrue(any("- BRANCH      : 1" in line for line in lines))

if __name__ == "__main__":
    unittest.main()
