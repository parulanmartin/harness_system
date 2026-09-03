#!/usr/bin/env python3
"""
Requirements Harness System - Terminal CLI Runner
Features:
- Auto project detection from transcript text
- Google Sheets / Database-style persistent storage per project
- Interactive gap detection & JTBD question feedback loop
- Multi-transcript knowledge accumulation and synthesis
"""

import sys
import os
from dataclasses import replace
from harness.config import Config
from harness.gdoc_fetcher import fetch_google_doc_text
from harness.models import KnowledgeMap, Project
from harness.engine import HarnessEngine
from harness.project_registry import ProjectRegistry
from harness.project_detector import ProjectDetector
from harness.sheets_storage import SheetsStorage

def print_banner(config: Config):
    print("\n" + "=" * 70)
    print("  🚀 REQUIREMENTS HARNESS SYSTEM (CLI RUNNER)")
    print("=" * 70)
    print(f"  [Config] Provider: {config.llm_provider}")
    print(f"  [Models] Extract: {config.llm_model_extract} | Semantic/Detect: {config.llm_model_semantic}")
    if config.openrouter_api_key:
        print("  [OpenRouter] API Key: Detected ✅ (Live LLM Extraction Active)")
    else:
        print("  [OpenRouter] API Key: Not set (Using Heuristic Parser & Interactive Loop)")
    print(f"  [Storage] Workspace Directory: {os.path.abspath(config.local_storage_dir)}")
    print("=" * 70)

def main():
    config = Config.from_env()
    print_banner(config)

    registry = ProjectRegistry(config)
    detector = ProjectDetector(config, registry)
    storage = SheetsStorage(config)
    engine = HarnessEngine()

    # Handle --list-projects flag
    if "--list-projects" in sys.argv:
        print("\n📁 REGISTERED PROJECTS (Master Database):")
        projects = registry.list_projects()
        if not projects:
            print("  No projects registered yet.")
        for p in projects:
            print(f"\n  • [{p.id}] {p.name}")
            print(f"    Description: {p.description}")
            print(f"    Transcripts Ingested: {p.transcript_count} | Sheet ID: {p.sheet_id}")
        print("\n")
        return

    # Check for explicit project flag
    explicit_project_name = None
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        if idx + 1 < len(sys.argv):
            explicit_project_name = sys.argv[idx + 1].strip()

    # 1. Get Google Doc URL or File Path
    doc_input = None
    args_without_flags = [arg for arg in sys.argv[1:] if not arg.startswith("--") and arg != explicit_project_name]
    if args_without_flags:
        doc_input = args_without_flags[0].strip()

    if not doc_input:
        print("\nPaste your Google Doc URL (or local transcript file path):")
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

    # 2. Project Selection / Auto-Detection
    target_project: Project = None

    if explicit_project_name:
        existing_proj = registry.get_project(explicit_project_name)
        if existing_proj:
            target_project = existing_proj
            print(f"\n📁 Using specified project: '{target_project.name}' (ID: {target_project.id})")
        else:
            print(f"\n📁 Creating new project from flag: '{explicit_project_name}'")
            target_project = registry.create_project(
                name=explicit_project_name,
                description=f"Project container for {explicit_project_name}"
            )
    else:
        print("\n🧠 Step 2: Auto-detecting project from transcript...")
        detection = detector.detect_project(raw_text)

        if detection.matched_project and detection.confidence >= 0.5:
            p = detection.matched_project
            print("\n" + "-" * 70)
            print(f"  🔍 Recommended Match: '{p.name}' ({int(detection.confidence * 100)}% confidence)")
            print(f"  Description: {p.description}")
            print(f"  Reasoning: {detection.reasoning}")
            print("-" * 70)
            print("  Options:")
            print(f"    [1] Confirm: '{p.name}' (Recommended)")
            print("    [2] Select a different existing project")
            print("    [3] Create a new project")

            try:
                choice = input("\n  Your choice [1/2/3] (default 1) > ").strip()
            except (EOFError, KeyboardInterrupt):
                choice = "1"

            if choice == "2":
                print("\n  Available projects:")
                all_projs = registry.list_projects()
                for idx, proj in enumerate(all_projs, 1):
                    print(f"    [{idx}] {proj.name}")
                p_idx = int(input("  Select project number > ").strip()) - 1
                target_project = all_projs[p_idx]
            elif choice == "3":
                new_name = input("  New project name > ").strip()
                new_desc = input("  New project description > ").strip()
                target_project = registry.create_project(new_name, new_desc)
            else:
                target_project = p

        else:
            print(f"\n  ℹ️  No strong match found ({detection.reasoning}).")
            default_name = detection.suggested_new_name or "New Project"
            default_desc = detection.suggested_new_description or "Auto-generated project"
            print(f"  Suggested Name: {default_name}")
            
            try:
                create_choice = input(f"  Create project '{default_name}'? [Y/n/custom] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                create_choice = "y"

            if create_choice in ["n", "custom"]:
                custom_name = input("  Project name > ").strip()
                custom_desc = input("  Project description > ").strip()
                target_project = registry.create_project(custom_name, custom_desc)
            else:
                target_project = registry.create_project(default_name, default_desc)

    print(f"\n🎯 Active Project: '{target_project.name}' [ID: {target_project.id}]")

    # 3. Load Existing Knowledge Map for Project & Ingest New Transcript
    print(f"\n💾 Step 3: Loading existing knowledge map for '{target_project.id}' from storage...")
    existing_kmap = storage.load_knowledge_map(target_project.id)
    print(f"  - Existing Actors: {len(existing_kmap.actors)} | Goals: {len(existing_kmap.goals)} | Entities: {len(existing_kmap.entities)}")

    print("\n⚙️  Step 4: Extracting primitives from transcript...")
    new_extracted_kmap = KnowledgeMap()
    engine.ingestor.parse_and_populate(raw_text, new_extracted_kmap)

    # Set source doc on new primitives using immutable replace
    for a_id, a in list(new_extracted_kmap.actors.items()):
        new_extracted_kmap.actors[a_id] = replace(a, source_doc=doc_input)
    for g_id, g in list(new_extracted_kmap.goals.items()):
        new_extracted_kmap.goals[g_id] = replace(g, source_doc=doc_input)
    for c_id, c in list(new_extracted_kmap.constraints.items()):
        new_extracted_kmap.constraints[c_id] = replace(c, source_doc=doc_input)
    for e_id, e in list(new_extracted_kmap.entities.items()):
        new_extracted_kmap.entities[e_id] = replace(e, source_doc=doc_input)
    for asm_id, asm in list(new_extracted_kmap.assumptions.items()):
        new_extracted_kmap.assumptions[asm_id] = replace(asm, source_doc=doc_input)

    print(f"  - Extracted in this call: {len(new_extracted_kmap.actors)} Actors, {len(new_extracted_kmap.goals)} Goals, {len(new_extracted_kmap.constraints)} Constraints")

    # Merge with deduplication
    kmap = storage.merge_knowledge_map(existing_kmap, new_extracted_kmap)
    print(f"  - Combined Knowledge Map: {len(kmap.actors)} Total Actors, {len(kmap.goals)} Total Goals, {len(kmap.entities)} Entities")

    # 4. Interactive Gap Detection & Question Loop
    loop_count = 1
    force_synthesize = False

    while not force_synthesize:
        print(f"\n🔍 Step 5 (Loop {loop_count}): Evaluating combined Knowledge Map with Gap Detector...")
        result = engine.process(kmap, max_questions_per_loop=3)

        if result.is_complete:
            print("  🎉 Decision Gate: NO GAPS FOUND! Knowledge map is complete.\n")
            break

        print(f"  ⚠️ Decision Gate: {len(result.gaps)} Knowledge Gaps Identified!")
        print("\n" + "-" * 70)
        print("  TARGETED FOLLOW-UP QUESTIONS (Type your answers or 'force' to synthesize):")
        print("-" * 70)

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

    # 5. Save Updated Knowledge Map to Storage
    storage.save_knowledge_map(target_project.id, kmap, source_doc_url=doc_input)
    registry.increment_transcript_count(target_project.id)
    print(f"\n💾 Step 6: Saved updated Knowledge Map to '{target_project.name}' project storage.")

    # 6. Final Synthesis Output
    final_result = engine.process(kmap)
    if not final_result.outputs:
        final_result.outputs = engine.synthesis.synthesize(kmap)

    outputs = final_result.outputs
    storage.save_outputs(target_project.id, outputs)

    # 7. Live Google Sheets Cloud Synchronization
    sheet_url = None
    if os.path.exists("google_token.json"):
        try:
            from harness.sheets_api import GoogleSheetsClient
            sheets_client = GoogleSheetsClient()
            print("\n☁️  Step 7: Syncing project to Google Drive & Google Sheets...")
            sheet_url = sheets_client.sync_project_to_sheet(target_project, kmap, outputs, source_doc_url=doc_input)
            print(f"  ✅ Live Google Sheet updated: {sheet_url}")
        except Exception as err:
            print(f"  [Notice] Google Sheets cloud sync skipped ({err})")

    print("\n" + "=" * 70)
    print(f"  📋 FINAL SYNTHESIZED SPECIFICATION FOR: '{target_project.name}'")
    print("=" * 70 + "\n")
    print(outputs.spec)

    # Save to local markdown file
    output_filename = f"synthesized_spec_{target_project.id}.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(outputs.spec)

    print("\n" + "=" * 70)
    print(f"  💾 Specification document saved to: {os.path.abspath(output_filename)}")
    print(f"  📊 Local Project Data: {os.path.abspath(os.path.join(config.local_storage_dir, target_project.id))}")
    if sheet_url:
        print(f"  🌐 Live Google Sheet: {sheet_url}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
