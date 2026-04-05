
import os
import shutil
import tempfile
import unittest
from modules.hardware_interface import HardwareInterface
from modules.buffer_manager import BufferManager
from modules.trace_route import TraceRoute
from modules.trace_capture import TraceCapture
from modules.trace_sink import TraceSink

class TestPhase1Integration(unittest.TestCase):
    def setUp(self):
        # Create temp dirs for sysfs and dev nodes
        self.tmp_root = tempfile.mkdtemp()
        self.sysfs_path = os.path.join(self.tmp_root, "sys")
        self.dev_path = os.path.join(self.tmp_root, "dev")
        os.makedirs(self.sysfs_path)
        os.makedirs(self.dev_path)
        
        # Setup mock devices in sysfs
        self.devices = ["etm0", "funnel0", "tmc_etr0"]
        for dev in self.devices:
            dev_dir = os.path.join(self.sysfs_path, dev)
            os.makedirs(dev_dir)
            with open(os.path.join(dev_dir, "enable_source"), 'w') as f:
                f.write("0")
            if "etr" in dev:
                with open(os.path.join(dev_dir, "buffer_size"), 'w') as f:
                    f.write("0")
        
        # Setup mock dev node for sink
        self.sink_node = os.path.join(self.dev_path, "tmc_etr0")
        with open(self.sink_node, 'wb') as f:
            f.write(b"\xDE\xAD\xBE\xEF" * 100) # Dummy trace data
            
        # Initialize modules
        self.hw = HardwareInterface(sysfs_path=self.sysfs_path)
        self.bm = BufferManager(self.hw)
        self.tr = TraceRoute(self.hw)
        self.capture = TraceCapture(self.hw, self.bm, self.tr)
        self.sink = TraceSink(self.capture)

    def tearDown(self):
        shutil.rmtree(self.tmp_root)

    def test_full_capture_flow(self):
        # 1. Start Capture
        config = {
            "sources": ["etm0"],
            "funnels": ["funnel0"],
            "sink": "tmc_etr0",
            "buffer_kb": 64
        }
        
        print("\n[STEP 1] Starting capture...")
        self.assertTrue(self.capture.capture_start(config))
        
        # Verify hardware state
        with open(os.path.join(self.sysfs_path, "etm0", "enable_source"), 'r') as f:
            self.assertEqual(f.read().strip(), "1")
        with open(os.path.join(self.sysfs_path, "tmc_etr0", "enable_source"), 'r') as f:
            self.assertEqual(f.read().strip(), "1")
        with open(os.path.join(self.sysfs_path, "tmc_etr0", "buffer_size"), 'r') as f:
            self.assertEqual(f.read().strip(), str(64 * 1024))
            
        # 2. Stop Capture
        print("[STEP 2] Stopping capture...")
        self.assertTrue(self.capture.capture_stop())
        
        # Verify hardware state after stop
        with open(os.path.join(self.sysfs_path, "etm0", "enable_source"), 'r') as f:
            self.assertEqual(f.read().strip(), "0")
        with open(os.path.join(self.sysfs_path, "tmc_etr0", "enable_source"), 'r') as f:
            self.assertEqual(f.read().strip(), "0")
            
        # 3. Export Data
        print("[STEP 3] Exporting data...")
        out_file = os.path.join(self.tmp_root, "output.bin")
        self.assertTrue(self.sink.export_file(self.sink_node, out_file))
        
        # Verify export content
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, 'rb') as f:
            content = f.read()
            self.assertTrue(content.startswith(b"\xDE\xAD\xBE\xEF"))
            self.assertEqual(len(content), 400)

        print("[OK] Full Phase 1 integration test passed!")

if __name__ == "__main__":
    unittest.main()
