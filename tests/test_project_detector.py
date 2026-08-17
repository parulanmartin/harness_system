import unittest
import os
import shutil
from harness.config import Config
from harness.project_registry import ProjectRegistry
from harness.project_detector import ProjectDetector

class TestProjectDetector(unittest.TestCase):

    def setUp(self):
        self.test_dir = "data/test_detector"
        os.makedirs(self.test_dir, exist_ok=True)
        self.cfg = Config(local_storage_dir=self.test_dir, openrouter_api_key="")
        self.registry = ProjectRegistry(self.cfg)
        self.detector = ProjectDetector(self.cfg, self.registry)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_detect_edge_sensors_project(self):
        sample_transcript = (
            "Nathan: We should look into edge sensors and cameras placed along the sea. "
            "It gives us an informational edge over public market data."
        )
        res = self.detector.detect_project(sample_transcript)
        self.assertIsNotNone(res.matched_project)
        self.assertEqual(res.matched_project.id, "edge_sensors")
        self.assertGreater(res.confidence, 0.5)

    def test_detect_new_project(self):
        sample_transcript = (
            "Alex: Let's discuss our new crypto arbitrage trading bot strategy for DEX liquidity pools."
        )
        res = self.detector.detect_project(sample_transcript)
        # Should not match edge_sensors or seoul_kb
        if res.matched_project:
            self.assertNotEqual(res.matched_project.id, "edge_sensors")
        else:
            self.assertIsNotNone(res.suggested_new_name)

if __name__ == "__main__":
    unittest.main()
