
import os
import shutil
import tempfile
import unittest
from modules.hardware_interface import HardwareInterface
from modules.buffer_manager import BufferManager
from modules.trace_route import TraceRoute
from modules.trace_capture import TraceCapture
from modules.trace_sink import TraceSink
from modules.trace_decode import TraceDecode
from modules.trace_analyzer import TraceAnalyzer

class TestPhase3Integration(unittest.TestCase):
    def setUp(self):
        # Setup mock environment
        self.tmp_root = tempfile.mkdtemp()
        self.sysfs_path = os.path.join(self.tmp_root, "sys")
        self.dev_path = os.path.join(self.tmp_root, "dev")
        os.makedirs(self.sysfs_path)
        os.makedirs(self.dev_path)
        
        # Setup mock ETM and Sink
        dev_dir = os.path.join(self.sysfs_path, "tmc_etr0")
        os.makedirs(dev_dir)
        with open(os.path.join(dev_dir, "enable_source"), 'w') as f: f.write("0")
        with open(os.path.join(dev_dir, "buffer_size"), 'w') as f: f.write("0")
        os.makedirs(os.path.join(self.sysfs_path, "etm0"))
        with open(os.path.join(self.sysfs_path, "etm0", "enable_source"), 'w') as f: f.write("0")

        # Generate trace data: 2 BRANCH, 2 CYCLE_COUNT, 1 TIMESTAMP
        self.sync = TraceDecode.SYNC_MARKER_ETM4
        self.mock_trace = (
            self.sync + b"\x01\xAA" + # BRANCH
            self.sync + b"\x01\xBB" + # BRANCH
            self.sync + b"\x70\xCC" + # CYCLE_COUNT
            self.sync + b"\x70\xDD" + # CYCLE_COUNT
            self.sync + b"\x81\xEE"   # TIMESTAMP
        )
        
        self.sink_node = os.path.join(self.dev_path, "tmc_etr0")
        with open(self.sink_node, 'wb') as f:
            f.write(self.mock_trace)
            
        # Initialize the full toolkit
        self.hw = HardwareInterface(sysfs_path=self.sysfs_path)
        self.bm = BufferManager(self.hw)
        self.tr = TraceRoute(self.hw)
        self.capture = TraceCapture(self.hw, self.bm, self.tr)
        self.sink = TraceSink(self.capture)
        self.decoder = TraceDecode()
        self.analyzer = TraceAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.tmp_root)

    def test_end_to_end_analysis_pipeline(self):
        print("\n[PHASE 3] Starting End-to-End Analysis Pipeline Test...")
        
        # 1. Capture & Sink
        config = {"sources": ["etm0"], "sink": "tmc_etr0", "buffer_kb": 128}
        self.capture.capture_start(config)
        self.capture.capture_stop()
        
        out_file = os.path.join(self.tmp_root, "final_trace.bin")
        self.sink.export_file(self.sink_node, out_file)
        
        # 2. Decode
        with open(out_file, 'rb') as f:
            data = f.read()
        events = self.decoder.decode_stream(data)
        self.assertEqual(len(events), 5)
        
        # 3. Analyze
        report = self.analyzer.analyze_events(events)
        summary = self.analyzer.get_summary_lines(report)
        
        print("\n--- GENERATED ANALYSIS REPORT ---")
        for line in summary:
            print(f"  {line}")
        print("---------------------------------\n")
        
        # 4. Final Validations
        self.assertEqual(report["total_events"], 5)
        self.assertEqual(report["performance"]["branch_count"], 2)
        self.assertEqual(report["performance"]["total_cycles"], 2)
        self.assertEqual(report["performance"]["branch_density"], 0.4) # 2/5
        self.assertEqual(report["packet_distribution"]["TIMESTAMP"], 1)
        
        print("[OK] End-to-end analysis pipeline validated successfully!")

if __name__ == "__main__":
    unittest.main()
