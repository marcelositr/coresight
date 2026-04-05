
import os
import shutil
import tempfile
import unittest
from modules.hardware_interface import HardwareInterface

class TestHardwareInterface(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate sysfs
        self.test_dir = tempfile.mkdtemp()
        self.device_name = "etm0"
        self.device_path = os.path.join(self.test_dir, self.device_name)
        os.makedirs(self.device_path)
        
        # Create nodes
        self.enable_node = os.path.join(self.device_path, "enable_source")
        with open(self.enable_node, 'w') as f:
            f.write("0")
            
        # Create type and subtype
        with open(os.path.join(self.device_path, "type"), 'w') as f: f.write("1")
        with open(os.path.join(self.device_path, "subtype"), 'w') as f: f.write("etm")
            
        self.hw = HardwareInterface(base_path=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_safe_write(self):
        success = self.hw.safe_write(self.device_name, "enable_source", "1")
        self.assertTrue(success)
        with open(self.enable_node, 'r') as f:
            val = f.read().strip()
        self.assertEqual(val, "1")

    def test_safe_read(self):
        val = self.hw.safe_read(self.device_name, "subtype")
        self.assertEqual(val, "etm")

    def test_list_raw_devices(self):
        devices = self.hw.list_raw_devices()
        self.assertIn("etm0", devices)

if __name__ == "__main__":
    unittest.main()
