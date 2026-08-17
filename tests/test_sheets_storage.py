import unittest
import os
import shutil
from harness.config import Config
from harness.models import KnowledgeMap, Actor, Goal, DataEntity, Constraint, EngineeringOutputs
from harness.sheets_storage import SheetsStorage

class TestSheetsStorage(unittest.TestCase):

    def setUp(self):
        self.test_dir = "data/test_sheets_storage"
        os.makedirs(self.test_dir, exist_ok=True)
        self.cfg = Config(local_storage_dir=self.test_dir)
        self.storage = SheetsStorage(self.cfg)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_knowledge_map(self):
        kmap = KnowledgeMap()
        kmap.add_actor(Actor(id="a1", name="Alice", role="Lead Dev"))
        kmap.add_goal(Goal(id="g1", description="Build API", actor_ids=["a1"]))
        kmap.add_entity(DataEntity(id="e1", name="User Token", fields=["id", "token"]))

        self.storage.save_knowledge_map("test_proj", kmap)

        loaded_kmap = self.storage.load_knowledge_map("test_proj")
        self.assertIn("a1", loaded_kmap.actors)
        self.assertEqual(loaded_kmap.actors["a1"].name, "Alice")
        self.assertIn("g1", loaded_kmap.goals)
        self.assertIn("e1", loaded_kmap.entities)

    def test_merge_multi_transcript_knowledge(self):
        # Call 1: Discussed actors and initial goal
        call1_kmap = KnowledgeMap()
        call1_kmap.add_actor(Actor(id="a1", name="Alice", role="Engineer"))
        call1_kmap.add_goal(Goal(id="g1", description="Build Login", actor_ids=["a1"]))

        # Call 2: Discussed new goal + enriched actor role + added data entity
        call2_kmap = KnowledgeMap()
        call2_kmap.add_actor(Actor(id="a1", name="Alice", role="Principal Architect"))
        call2_kmap.add_goal(Goal(id="g2", description="Export Audit Logs", actor_ids=["a1"]))
        call2_kmap.add_entity(DataEntity(id="e1", name="Session", fields=["ip", "exp"]))

        # Merge
        merged = self.storage.merge_knowledge_map(call1_kmap, call2_kmap)

        # Alice should be updated, and both goals should exist
        self.assertEqual(len(merged.actors), 1)
        self.assertEqual(merged.actors["a1"].role, "Principal Architect")
        self.assertEqual(len(merged.goals), 2)
        self.assertIn("g1", merged.goals)
        self.assertIn("g2", merged.goals)
        self.assertEqual(len(merged.entities), 1)

    def test_save_outputs_history(self):
        outputs = EngineeringOutputs(
            requirements=["REQ-1: Test"],
            spec="# Spec Title\nContent",
            jtbd_matrix=[{"actor": "User", "situation": "When", "motivation": "Want", "outcome": "So"}],
            acceptance_criteria=["GIVEN / WHEN / THEN"]
        )
        self.storage.save_outputs("test_proj", outputs)
        history_file = os.path.join(self.test_dir, "test_proj", "outputs_history.json")
        self.assertTrue(os.path.exists(history_file))

if __name__ == "__main__":
    unittest.main()
