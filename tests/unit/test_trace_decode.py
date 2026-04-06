
import unittest
from core.trace_decode import TraceDecode

class TestTraceDecode(unittest.TestCase):
    def setUp(self):
        self.decoder = TraceDecode()
        self.sync = TraceDecode.SYNC_MARKER_ETM4

    def test_decode_empty(self):
        events = self.decoder.decode_stream(b"")
        self.assertEqual(len(events), 0)

    def test_decode_simple_packet(self):
        # Header 0x01 (BRANCH) after sync
        raw_data = self.sync + b"\x01\xDE\xAD\xBE\xEF"
        events = self.decoder.decode_stream(raw_data)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "BRANCH")
        self.assertEqual(events[0]["raw_header"], "0x1")

    def test_decode_multiple_packets(self):
        # TIMESTAMP (0x81) and CYCLE_COUNT (0x70)
        raw_data = (self.sync + b"\x81\x00\x01") + (self.sync + b"\x70\xFF")
        events = self.decoder.decode_stream(raw_data)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["type"], "TIMESTAMP")
        self.assertEqual(events[1]["type"], "CYCLE_COUNT")

    def test_decode_unknown_packet(self):
        # Random header 0x55
        raw_data = self.sync + b"\x55\xAA"
        events = self.decoder.decode_stream(raw_data)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "UNKNOWN")

    def test_status(self):
        self.decoder.decode_stream(self.sync + b"\x01")
        status = self.decoder.status()
        self.assertEqual(status["packets_processed"], 1)
        self.assertTrue(status["experimental"])

if __name__ == "__main__":
    unittest.main()
