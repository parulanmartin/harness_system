#!/usr/bin/env python3
"""
Requirements Harness System - Terminal CLI Runner
Ingests Google Docs transcripts, detects knowledge gaps, asks clarifying questions interactively,
and synthesizes structured engineering specifications.
"""

import sys
import os
from harness.config import Config
from harness.gdoc_fetcher import fetch_google_doc_text
from harness.models import KnowledgeMap
from harness.engine import HarnessEngine

def main():
    print("\n" + "=" * 65)
    print("  🚀 REQUIREMENTS HARNESS SYSTEM (CLI RUNNER)")
    print("=" * 65)

    config = Config.from_env()
    print(f"  [Config] Provider: {config.llm_provider} | Model: {config.llm_model}")
    if config.openrouter_api_key:
        print("  [Config] OpenRouter API Key: Detected ✅ (Live LLM Extraction Active)")
    else:
        print("  [Config] OpenRouter API Key: Not set (Using Heuristic Parser & Interactive Loop)")

    # 1. Get Google Doc URL or File Path
    if len(sys.argv) > 1:
        doc_input = sys.argv[1].strip()
    else:
        print("\nPaste your Google Doc URL (or local file path):")
        try:
            doc_input = input("  URL > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

    if not doc_input:
        print("❌ Error: No document URL provided.")
        sys.exit(1)

    print(f"\n📥 Step 1: Fetching transcript from: {doc_input}...")
    try:
        raw_text = fetch_google_doc_text(doc_input)
        print(f"  ✅ Successfully loaded {len(raw_text):,} characters of transcript text.")
    except Exception as err:
        print(f"  ❌ Failed to fetch transcript: {err}")
        sys.exit(1)

    # 2. Ingest text into KnowledgeMap
    print("\n⚙️  Step 2: Ingesting primitives into Knowledge Map...")
    engine = HarnessEngine()
    kmap = KnowledgeMap()
    engine.ingestor.parse_and_populate(raw_text, kmap)

    print(f"  - Extracted Actors: {len(kmap.actors)} ({', '.join([a.name for a in kmap.actors.values()]) or 'None yet'})")
    print(f"  - Extracted Goals: {len(kmap.goals)} ({', '.join([g.description[:40] + '...' for g in kmap.goals.values()]) or 'None yet'})")
    print(f"  - Extracted Constraints: {len(kmap.constraints)}")

    # 3. Interactive Gap Detection & Question Loop
    loop_count = 1
    force_synthesize = False

    while not force_synthesize:
        print(f"\n🔍 Step 3 (Loop {loop_count}): Evaluating Knowledge Map with Gap Detector...")
        result = engine.process(kmap, max_questions_per_loop=3)

        if result.is_complete:
            print("  🎉 Decision Gate: NO GAPS FOUND! Knowledge map is complete.\n")
            break

        print(f"  ⚠️ Decision Gate: {len(result.gaps)} Gaps Found!")
        print("\n" + "-" * 65)
        print("  TARGETED FOLLOW-UP QUESTIONS (Type answers, or 'force' to synthesize):")
        print("-" * 65)

        user_answers = {}
        for idx, q in enumerate(result.questions, 1):
            print(f"\n[Question {idx} | Priority: {q.priority.name}]")
            print(f"👉 {q.question_text}")
            try:
                ans = input("Your Answer > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  [Stream closed] Proceeding to synthesis with current knowledge map...")
                force_synthesize = True
                break

            if ans.lower() == "force":
                print("\n  ⏩ User requested force synthesis. Proceeding to Output Layer...")
                force_synthesize = True
                break

            if ans and ans.lower() != "skip":
                user_answers[q.target_id] = ans

        if force_synthesize:
            # Fill default values for any remaining empty fields so synthesis can proceed
            for g_id, g in list(kmap.goals.items()):
                if not g.underlying_motivation:
                    engine.ingestor.apply_user_feedback(kmap, g_id, "Stakeholder approved standard workflow")
            for c_id, c in list(kmap.constraints.items()):
                if not c.sla_metric:
                    engine.ingestor.apply_user_feedback(kmap, c_id, "Target SLA agreed by engineering")
            break

        if user_answers:
            engine.receive_answers(kmap, user_answers)
            print("  ✅ User feedback re-ingested into Knowledge Map.")
        else:
            print("  [Notice] No answers provided in this turn.")

        loop_count += 1
        if loop_count > 5:
            print("\n  [Notice] Reached maximum interaction loops. Synthesizing final spec...")
            break

    # 4. Final Synthesis Output
    final_result = engine.process(kmap)
    if not final_result.outputs:
        final_result.outputs = engine.synthesis.synthesize(kmap)

    spec_markdown = final_result.outputs.spec

    print("\n" + "=" * 65)
    print("  📋 FINAL SYNTHESIZED ENGINEERING SPECIFICATION")
    print("=" * 65 + "\n")
    print(spec_markdown)

    # Save to markdown file in current directory
    output_filename = "synthesized_spec.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(spec_markdown)

    print("\n" + "=" * 65)
    print(f"  💾 Specification document saved to: {os.path.abspath(output_filename)}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
