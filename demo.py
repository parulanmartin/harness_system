import json
from harness.models import KnowledgeMap, Goal, Constraint
from harness.engine import HarnessEngine

def main():
    print("=" * 60)
    print("  REQUIREMENTS HARNESS SYSTEM DEMO")
    print("=" * 60)

    engine = HarnessEngine()
    kmap = KnowledgeMap()

    # Input: Raw meeting notes extracted into initial primitive nodes
    print("\n[Step 1] Ingesting initial transcript notes...")
    print("  Raw note: 'We need a button to export audit logs to CSV. Needs to be fast.'")

    kmap.add_goal(Goal(
        id="g_export",
        description="Export audit logs to CSV"
    ))
    kmap.add_constraint(Constraint(
        id="c_fast",
        description="Needs to be fast",
        target_id="g_export"
    ))

    # Evaluate loop 1
    print("\n[Step 2] Running Harness Core (Gap Detector)...")
    res1 = engine.process(kmap)

    if not res1.is_complete:
        print(f"  ❌ Decision Gate: Gaps Found ({len(res1.gaps)} gaps identified)")
        print("\n[Step 3] Question Engine Formulates Targeted Questions:")
        for idx, q in enumerate(res1.questions, 1):
            print(f"  Question {idx} [{q.priority.name}]: {q.question_text}")

        # Simulate user re-ingesting answers
        print("\n[Step 4] Re-ingesting User Answers back into Ingestion Layer...")
        answers = {
            "g_export": (
                "Actor: Security Auditor\n"
                "Why: Need quarterly audit reporting to comply with SOC2 standards\n"
                "When: When preparing for quarterly compliance reviews\n"
                "Outcome: Exported CSV file containing timestamped audit logs for compliance review\n"
                "Entity: Security Audit Log\n"
                "Error: Display error toast if date range exceeds 90 days"
            ),
            "c_fast": "Latency must be < 2 seconds for exports up to 50,000 records"
        }
        
        for tid, ans in answers.items():
            print(f"  -> Answer for '{tid}':\n{ans}\n")

        engine.receive_answers(kmap, answers)

        print("[Step 5] Re-evaluating Harness Core (Gap Detector)...")
        res2 = engine.process(kmap)

        if res2.is_complete:
            print("  ✅ Decision Gate: NO GAPS FOUND! Proceeding to Synthesis Engine...")
            print("\n" + "=" * 60)
            print("  FINAL SYNTHESIZED SPECIFICATION OUTPUT")
            print("=" * 60)
            print(res2.outputs.spec)

if __name__ == "__main__":
    main()
