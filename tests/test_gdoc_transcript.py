import json
from harness.models import KnowledgeMap, Actor, Goal, Constraint, DataEntity
from harness.engine import HarnessEngine

TRANSCRIPT_SUMMARY = """
Meeting between Nathan Jenk and Martin Parulan (2026/08/12).
Key Topics:
- Edge Sensors & Informational Edge: Deploying niche sensors/cameras (e.g. ship passage tracking, temple traffic, hair salon supply chain) to collect ground-truth data indicators.
- Jobs To Be Done (JTBD): Identifying the core problem being solved rather than surface data collection.
- Core Requirements: Needs to be quantifiable, niche, and provide actionable informational edge for decision making.
"""

def main():
    print("=" * 70)
    print("  LIVE TEST: HARNESS SYSTEM PROCESSING GOOGLE DOC TRANSCRIPT")
    print("  Doc URL: https://docs.google.com/document/d/1pp7kBfFUskNZEHYEnn_N1AgmXxY55xqIJCBF3gXxRPk")
    print("=" * 70)

    engine = HarnessEngine()
    kmap = KnowledgeMap()

    # Step 1: Parse primitives extracted from the Google Doc transcript
    print("\n📥 [STEP 1: INGESTION LAYER]")
    print("Extracting core primitives from meeting transcript...")

    # Extracted Primitives from raw meeting transcript
    kmap.add_actor(Actor(id="nathan", name="Nathan Jenk", role="Strategy / System Architect"))
    kmap.add_actor(Actor(id="martin", name="Martin Parulan", role="Engineer / Researcher"))

    # Initial raw goals extracted from the transcript
    kmap.add_goal(Goal(
        id="g_edge_sensors",
        description="Deploy Edge Sensors to collect niche ground data indicators for informational edge",
        actor_ids=["martin"]
    ))
    kmap.add_constraint(Constraint(
        id="c_quantifiable",
        description="Data collected must be quantifiable and cost effective ($1/day per sensor)",
        target_id="g_edge_sensors",
        is_measurable=False,  # Unmeasurable initially (needs explicit SLA/metric)
        sla_metric=None
    ))

    print(f"  Extracted 2 Actors: Nathan Jenk, Martin Parulan")
    print(f"  Extracted Goal: '{kmap.goals['g_edge_sensors'].description}'")
    print(f"  Extracted Constraint: '{kmap.constraints['c_quantifiable'].description}'")

    # Step 2: Run Harness Core (Gap Detector)
    print("\n🔍 [STEP 2: HARNESS CORE - GAP DETECTOR EVALUATION]")
    res1 = engine.process(kmap)

    print(f"  Decision Gate Result: is_complete = {res1.is_complete}")
    print(f"  Identified {len(res1.gaps)} Knowledge Gaps:")
    for gap in res1.gaps:
        print(f"    - [{gap.priority.name}] {gap.category.value}: {gap.description}")

    # Step 3: Question Engine Formulates Targeted Questions
    print("\n❓ [STEP 3: QUESTION ENGINE FORMULATES TARGETED QUESTIONS]")
    print("The system halts synthesis and sends these prioritized questions to the stakeholder:")
    for idx, q in enumerate(res1.questions, 1):
        print(f"  Question {idx} ({q.priority.name}): {q.question_text}")

    # Step 4: Stakeholder responds to clarify JTBD & root problem
    print("\n💬 [STEP 4: USER RE-INGESTS ANSWERS BACK INTO HARNESS]")
    user_answers = {
        "g_edge_sensors": (
            "Actor: Engineer / Researcher\n"
            "Why: Solve the problem of asymmetric information delay by gathering ground-truth physical indicators before official public reports are released.\n"
            "When: When analyzing future market shifts or business performance in niche locations (e.g. shipping channels, local foot traffic).\n"
            "Outcome: Real-time structured data feed indicating activity metrics with an informational advantage.\n"
            "Entity: Edge Sensor Reading\n"
            "Error: Alert system if sensor camera feed is offline or data stream drops below 80% uptime."
        ),
        "c_quantifiable": "Cost <= $1.00 per sensor/day; Data sampling frequency >= 1 reading per minute."
    }

    engine.receive_answers(kmap, user_answers)

    # Step 5: Re-evaluate Harness Core
    print("\n🔄 [STEP 5: RE-EVALUATING HARNESS CORE]")
    res2 = engine.process(kmap)

    print(f"  Decision Gate Result: is_complete = {res2.is_complete}")
    if res2.is_complete:
        print("  ✅ All Gaps Resolved! Harness proceeds to Synthesis Layer.")
        print("\n" + "=" * 70)
        print("  FINAL SYNTHESIZED ENGINEERING SPECIFICATION")
        print("=" * 70)
        print(res2.outputs.spec)

if __name__ == "__main__":
    main()
