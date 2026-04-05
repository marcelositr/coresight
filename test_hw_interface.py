
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
            
        # Create mgmt subdir
        self.mgmt_path = os.path.join(self.device_path, "mgmt")
        os.makedirs(self.mgmt_path)
        with open(os.path.join(self.mgmt_path, "devid"), 'w') as f:
            f.write("0x410b9d1")
            
        self.hw = HardwareInterface(sysfs_path=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_device_enable(self):
        success = self.hw.device_enable(self.device_name)
        self.assertTrue(success)
        with open(self.enable_node, 'r') as f:
            val = f.read().strip()
        self.assertEqual(val, "1")

    def test_device_disable(self):
        # First enable it
        with open(self.enable_node, 'w') as f:
            f.write("1")
            
        success = self.hw.device_disable(self.device_name)
        self.assertTrue(success)
        with open(self.enable_node, 'r') as f:
            val = f.read().strip()
        self.assertEqual(val, "0")

    def test_device_status(self):
        status = self.hw.device_status(self.device_name)
        self.assertEqual(status["name"], self.device_name)
        self.assertFalse(status["enabled"])
        self.assertEqual(status["mgmt"]["devid"], "0x410b9d1")
        
        # Enable and check again
        with open(self.enable_node, 'w') as f:
            f.write("1")
        status = self.hw.device_status(self.device_name)
        self.assertTrue(status["enabled"])

    def test_node_not_found(self):
        success = self.hw.device_enable("non_existent_device")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
