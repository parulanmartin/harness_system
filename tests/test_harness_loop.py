import unittest
from harness.models import KnowledgeMap, Actor, Goal, DataEntity, Constraint
from harness.engine import HarnessEngine

class TestHarnessLoop(unittest.TestCase):

    def test_harness_end_to_end_loop(self):
        engine = HarnessEngine()
        kmap = KnowledgeMap()

        # Step 1: Initial Ingestion from raw transcript produces partial knowledge map
        # Feature request: "Export audit logs to CSV"
        kmap.add_goal(Goal(
            id="g_export",
            description="Export audit logs to CSV"
        ))
        kmap.add_constraint(Constraint(
            id="c_speed",
            description="Must be fast",
            target_id="g_export"
        ))

        # Evaluate iteration 1
        res1 = engine.process(kmap)
        self.assertFalse(res1.is_complete)
        self.assertGreater(len(res1.gaps), 0)
        self.assertGreater(len(res1.questions), 0)

        # Verify high priority question was asked for missing Actor / Motivation
        q_texts = [q.question_text for q in res1.questions]
        self.assertTrue(any("Actor" in q for q in q_texts) or any("problem" in q or "job" in q for q in q_texts))

        # Step 2: Simulate User responding to questions
        answers = {
            "g_export": (
                "Actor: Compliance Auditor\n"
                "Why: Need to perform quarterly security audits for SOC2 compliance\n"
                "When: When preparing for quarterly compliance reviews\n"
                "Outcome: Maintain audit trail and satisfy SOC2 compliance standards\n"
                "Entity: Audit Log\n"
                "Error: Alert user if log date range exceeds 90 days limit"
            ),
            "c_speed": "< 2 seconds for up to 100,000 log records"
        }

        engine.receive_answers(kmap, answers)

        # Evaluate iteration 2
        res2 = engine.process(kmap)

        # Verify loop completes and generates final outputs
        self.assertTrue(res2.is_complete)
        self.assertEqual(len(res2.gaps), 0)
        self.assertIsNotNone(res2.outputs)

        # Check generated engineering outputs
        outputs = res2.outputs
        self.assertGreater(len(outputs.requirements), 0)
        self.assertEqual(len(outputs.jtbd_matrix), 1)
        self.assertEqual(outputs.jtbd_matrix[0]["actor"], "Compliance Auditor")
        self.assertIn("quarterly compliance reviews", outputs.jtbd_matrix[0]["situation"])
        self.assertIn("REQ-G_EXPORT", outputs.requirements[0])
        self.assertIn("# Engineering Specification", outputs.spec)

if __name__ == "__main__":
    unittest.main()
