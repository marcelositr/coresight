
import os
import shutil
import tempfile
import unittest
from core.hardware_interface import HardwareInterface
from core.topology_manager import TopologyManager
from core.trace_capture import TraceCapture
from core.trace_sink import TraceSink
from core.trace_decode import TraceDecode

class TestPhase2Integration(unittest.TestCase):
    def setUp(self):
        # Create temp dirs for sysfs and dev nodes
        self.tmp_root = tempfile.mkdtemp()
        self.sysfs_path = os.path.join(self.tmp_root, "sys")
        self.dev_path = os.path.join(self.tmp_root, "dev")
        os.makedirs(self.sysfs_path)
        os.makedirs(self.dev_path)
        
        # Setup mock devices in sysfs
        self.devices = {
            "etm0": {"type": "1", "subtype": "etm"},
            "tmc_etr0": {"type": "3", "subtype": "etr"}
        }
        for dev, meta in self.devices.items():
            dev_dir = os.path.join(self.sysfs_path, dev)
            os.makedirs(dev_dir)
            with open(os.path.join(dev_dir, "type"), 'w') as f: f.write(meta["type"])
            with open(os.path.join(dev_dir, "subtype"), 'w') as f: f.write(meta["subtype"])
            with open(os.path.join(dev_dir, "enable_source"), 'w') as f: f.write("0")
            with open(os.path.join(dev_dir, "enable_sink"), 'w') as f: f.write("0")
            with open(os.path.join(dev_dir, "buffer_size"), 'w') as f: f.write("0")
        
        # Mock connection etm0 -> tmc_etr0
        os.makedirs(os.path.join(self.sysfs_path, "etm0", "connection0"), exist_ok=True)
        os.symlink(os.path.join(self.sysfs_path, "tmc_etr0"), os.path.join(self.sysfs_path, "etm0", "connection0", "device"))
        
        # Generate complex mock trace data with sync markers and headers
        self.sync = TraceDecode.SYNC_MARKER_ETM4
        self.mock_trace = (
            self.sync + b"\x01\x11\x22" + # BRANCH packet
            self.sync + b"\x81\xAA\xBB" + # TIMESTAMP packet
            self.sync + b"\x70\x01"       # CYCLE_COUNT packet
        )
        
        self.sink_node = os.path.join(self.dev_path, "tmc_etr0")
        with open(self.sink_node, 'wb') as f:
            f.write(self.mock_trace)
            
        # Initialize all modules with mock path
        TopologyManager._instance = None  # Reset singleton
        self.topo = TopologyManager(base_path=self.sysfs_path)
        self.capture = TraceCapture()
        self.sink = TraceSink(self.capture)
        self.decoder = TraceDecode()

    def tearDown(self):
        shutil.rmtree(self.tmp_root)
        TopologyManager._instance = None

    def test_full_pipeline_capture_to_decode(self):
        print("\n[PHASE 2] Starting Full Pipeline Integration Test...")
        
        # 1. Capture Lifecycle
        self.assertTrue(self.capture.capture_start("etm0", "tmc_etr0", buffer_kb=64))
        self.assertTrue(self.capture.capture_stop())
        
        # 2. Export Lifecycle
        out_file = os.path.join(self.tmp_root, "captured_trace.bin")
        self.assertTrue(self.sink.export_file(self.sink_node, out_file))
        
        # 3. Decode Lifecycle (The core of Phase 2)
        with open(out_file, 'rb') as f:
            captured_bytes = f.read()
            
        print(f"[STEP] Captured {len(captured_bytes)} bytes. Starting Decode...")
        events = self.decoder.decode_stream(captured_bytes)
        
        # 4. Validation
        self.assertEqual(len(events), 3, "Should have found 3 packets separated by sync markers")
        
        types = [e["type"] for e in events]
        self.assertIn("BRANCH", types)
        self.assertIn("TIMESTAMP", types)
        self.assertIn("CYCLE_COUNT", types)
        
        print("[OK] Full pipeline validation successful: Hardware -> Capture -> Sink -> Decode")

if __name__ == "__main__":
    unittest.main()
