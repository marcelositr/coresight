
import os
import shutil
import tempfile
import unittest
from modules.hardware_interface import HardwareInterface
from modules.topology_manager import TopologyManager
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
        
        # Setup mock dev node for sink
        self.sink_node = os.path.join(self.dev_path, "tmc_etr0")
        with open(self.sink_node, 'wb') as f:
            f.write(b"\xDE\xAD\xBE\xEF" * 100)
            
        # Initialize modules
        # Ensure TopologyManager is initialized with the correct base_path
        # Reset TopologyManager instance for testing
        TopologyManager._instance = None
        self.topo = TopologyManager(base_path=self.sysfs_path)
        self.capture = TraceCapture()
        self.sink = TraceSink(self.capture)

    def tearDown(self):
        shutil.rmtree(self.tmp_root)
        TopologyManager._instance = None

    def test_full_capture_flow(self):
        print("\n[STEP 1] Starting capture...")
        self.assertTrue(self.capture.capture_start("etm0", "tmc_etr0", buffer_kb=64))
        
        # Verify hardware state
        with open(os.path.join(self.sysfs_path, "etm0", "enable_source"), 'r') as f:
            self.assertEqual(f.read().strip(), "1")
        with open(os.path.join(self.sysfs_path, "tmc_etr0", "enable_sink"), 'r') as f:
            self.assertEqual(f.read().strip(), "1")
            
        # 2. Stop Capture
        print("[STEP 2] Stopping capture...")
        self.assertTrue(self.capture.capture_stop())
        
        # Verify hardware state after stop
        with open(os.path.join(self.sysfs_path, "etm0", "enable_source"), 'r') as f:
            self.assertEqual(f.read().strip(), "0")
        with open(os.path.join(self.sysfs_path, "tmc_etr0", "enable_sink"), 'r') as f:
            self.assertEqual(f.read().strip(), "0")
            
        # 3. Export Data
        print("[STEP 3] Exporting data...")
        out_file = os.path.join(self.tmp_root, "output.bin")
        self.assertTrue(self.sink.export_file(self.sink_node, out_file))
        self.assertTrue(os.path.exists(out_file))

if __name__ == "__main__":
    unittest.main()
