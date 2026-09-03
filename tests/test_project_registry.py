import unittest
import os
import shutil
from harness.config import Config
from harness.project_registry import ProjectRegistry

class TestProjectRegistry(unittest.TestCase):

    def setUp(self):
        self.test_dir = "data/test_registry"
        os.makedirs(self.test_dir, exist_ok=True)
        self.cfg = Config(local_storage_dir=self.test_dir)
        self.registry = ProjectRegistry(self.cfg)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_list_projects_default(self):
        projects = self.registry.list_projects()
        self.assertGreaterEqual(len(projects), 2)
        project_ids = [p.id for p in projects]
        self.assertIn("edge_sensors", project_ids)

    def test_create_and_get_project(self):
        new_proj = self.registry.create_project("Alpha Test", "Testing new project creation")
        self.assertEqual(new_proj.id, "alpha_test")
        self.assertEqual(new_proj.name, "Alpha Test")

        fetched = self.registry.get_project("alpha_test")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Alpha Test")

    def test_increment_transcript_count(self):
        proj = self.registry.create_project("Count Test", "Counting transcripts")
        initial_count = proj.transcript_count
        self.registry.increment_transcript_count("count_test")
        updated = self.registry.get_project("count_test")
        self.assertEqual(updated.transcript_count, initial_count + 1)

if __name__ == "__main__":
    unittest.main()
