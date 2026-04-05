
import unittest
import os
import tempfile
import shutil
from modules.perf_integration import PerfIntegration

class TestPerfIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.perf = PerfIntegration()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_record_session_simulation(self):
        # Even if cs_etm is not supported, it should create a mock file in simulation mode
        out_path = os.path.join(self.tmp_dir, "perf.data")
        success = self.perf.record_session(1, out_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_path))
        
        with open(out_path, 'rb') as f:
            header = f.read(8)
            self.assertEqual(header, b"PERFFILE")

    def test_extract_trace_simulation(self):
        out_path = os.path.join(self.tmp_dir, "perf.data")
        self.perf.record_session(1, out_path)
        
        trace_data = self.perf.extract_trace(out_path)
        self.assertTrue(len(trace_data) > 0)
        self.assertIn(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80", trace_data)

    def test_status(self):
        status = self.perf.status()
        self.assertIn("perf_available", status)
        self.assertIn("cs_etm_supported", status)

if __name__ == "__main__":
    unittest.main()
