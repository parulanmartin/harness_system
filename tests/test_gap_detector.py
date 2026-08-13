import unittest
from harness.models import KnowledgeMap, Actor, Goal, DataEntity, Constraint, GapCategory, GapPriority
from harness.gap_detector import GapDetector

class TestGapDetector(unittest.TestCase):

    def test_structural_orphaned_goal_detection(self):
        kmap = KnowledgeMap()
        # Add a goal with no assigned actor
        kmap.add_goal(Goal(id="g1", description="Export report to PDF"))

        detector = GapDetector()
        gaps = detector.evaluate(kmap)

        orphan_gaps = [g for g in gaps if g.category == GapCategory.STRUCTURAL_ORPHANED_GOAL]
        self.assertEqual(len(orphan_gaps), 1)
        self.assertEqual(orphan_gaps[0].target_id, "g1")
        self.assertEqual(orphan_gaps[0].priority, GapPriority.P1)

    def test_jtbd_why_motivation_check(self):
        kmap = KnowledgeMap()
        # Add actor and goal, but no motivation (the "Why")
        kmap.add_actor(Actor(id="admin", name="Admin", role="System Admin"))
        kmap.add_goal(Goal(
            id="g1",
            description="Add CSV Download Button",
            actor_ids=["admin"],
            entity_ids=["logs"]
        ))

        detector = GapDetector()
        gaps = detector.evaluate(kmap)

        why_gaps = [g for g in gaps if g.category == GapCategory.SEMANTIC_JTBD_WHY]
        self.assertEqual(len(why_gaps), 1)
        self.assertEqual(why_gaps[0].target_id, "g1")
        self.assertEqual(why_gaps[0].priority, GapPriority.P1)

    def test_unmeasurable_constraint_check(self):
        kmap = KnowledgeMap()
        kmap.add_constraint(Constraint(
            id="c1",
            description="System must be ultra fast",
            target_id="g1",
            is_measurable=False,
            sla_metric=None
        ))

        detector = GapDetector()
        gaps = detector.evaluate(kmap)

        unmeasurable_gaps = [g for g in gaps if g.category == GapCategory.SEMANTIC_UNMEASURABLE_CONSTRAINT]
        self.assertEqual(len(unmeasurable_gaps), 1)
        self.assertEqual(unmeasurable_gaps[0].target_id, "c1")

if __name__ == "__main__":
    unittest.main()
