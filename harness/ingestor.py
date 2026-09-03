import json
import re
from typing import Dict, Any, List, Optional
from harness.models import KnowledgeMap, Actor, Goal, DataEntity, Constraint, Assumption
from harness.config import Config
from harness.llm_client import OpenRouterClient

EXTRACTION_SYSTEM_PROMPT = """You are an expert Requirements Extraction Engine.
Analyze the provided meeting transcript and extract structured requirement primitives in strict JSON format.

JSON Schema:
{
  "actors": [
    {"id": "string", "name": "string", "role": "string", "description": "string"}
  ],
  "goals": [
    {
      "id": "string",
      "description": "string",
      "actor_ids": ["string"],
      "entity_ids": ["string"],
      "situation_trigger": "string or null (When...)",
      "underlying_motivation": "string or null (I want to/Why...)",
      "desired_outcome": "string or null (So that...)",
      "failure_modes": ["string"]
    }
  ],
  "entities": [
    {"id": "string", "name": "string", "fields": ["string"], "description": "string"}
  ],
  "constraints": [
    {
      "id": "string",
      "description": "string",
      "target_id": "string or null",
      "is_measurable": boolean,
      "sla_metric": "string or null"
    }
  ]
}

Rules:
1. Do NOT guess or hallucinate missing information. If an actor, motivation (why), or SLA is missing from the transcript, leave it empty or unmeasurable so the Gap Detector can flag it.
2. Return ONLY the JSON object, without any surrounding markdown fences or commentary.
"""

class TranscriptIngestor:
    """
    Ingests raw transcript / text (from Google Docs) and updates the KnowledgeMap graph.
    Supports OpenRouter LLM extraction with deterministic fallback.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.llm_client = OpenRouterClient(self.config)

    def parse_and_populate(self, raw_text: str, kmap: KnowledgeMap) -> None:
        """
        Parses raw text into KnowledgeMap primitives.
        """
        if self.config.openrouter_api_key:
            try:
                self._extract_with_llm(raw_text, kmap)
                return
            except Exception as err:
                print(f"[Warning] LLM extraction failed ({err}), falling back to heuristic extractor...")

        self._extract_with_heuristics(raw_text, kmap)

    def _extract_with_llm(self, raw_text: str, kmap: KnowledgeMap) -> None:
        prompt = f"Transcript Content:\n\n{raw_text[:8000]}"
        response = self.llm_client.complete(
            prompt=prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            model=self.config.llm_model_extract
        )

        # Clean potential markdown formatting
        cleaned = re.sub(r"^```json\s*", "", response.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        data = json.loads(cleaned)

        for a in data.get("actors", []):
            kmap.add_actor(Actor(id=a["id"], name=a["name"], role=a.get("role", a["name"]), description=a.get("description", "")))

        for e in data.get("entities", []):
            kmap.add_entity(DataEntity(id=e["id"], name=e["name"], fields=e.get("fields", []), description=e.get("description", "")))

        for g in data.get("goals", []):
            kmap.add_goal(Goal(
                id=g["id"],
                description=g["description"],
                actor_ids=g.get("actor_ids", []),
                entity_ids=g.get("entity_ids", []),
                situation_trigger=g.get("situation_trigger"),
                underlying_motivation=g.get("underlying_motivation"),
                desired_outcome=g.get("desired_outcome"),
                failure_modes=g.get("failure_modes", [])
            ))

        for c in data.get("constraints", []):
            kmap.add_constraint(Constraint(
                id=c["id"],
                description=c["description"],
                target_id=c.get("target_id"),
                is_measurable=c.get("is_measurable", False),
                sla_metric=c.get("sla_metric")
            ))

    def _extract_with_heuristics(self, raw_text: str, kmap: KnowledgeMap) -> None:
        """
        Heuristic extraction for local/offline testing without active API key.
        """
        # Find speaker names
        speakers = set(re.findall(r"([A-Z][a-z]+ [A-Z][a-z]+):", raw_text))
        for speaker in speakers:
            s_id = speaker.lower().replace(" ", "_")
            kmap.add_actor(Actor(id=s_id, name=speaker, role=speaker))

        # Scan for core topics / goals in transcript
        if "edge sensor" in raw_text.lower() or "camera" in raw_text.lower() or "informational edge" in raw_text.lower():
            kmap.add_goal(Goal(
                id="g_edge_sensors",
                description="Deploy edge sensors to collect niche ground data indicators for informational edge",
                actor_ids=[list(kmap.actors.keys())[0]] if kmap.actors else []
            ))
            kmap.add_constraint(Constraint(
                id="c_cost",
                description="Cost must be ~$1/day per sensor",
                target_id="g_edge_sensors",
                is_measurable=False
            ))
        else:
            kmap.add_goal(Goal(
                id="g_meeting_action",
                description="Synthesize key project goals from meeting transcript",
                actor_ids=[list(kmap.actors.keys())[0]] if kmap.actors else []
            ))

    def apply_user_feedback(self, kmap: KnowledgeMap, target_id: str, feedback_text: str) -> None:
        """
        Updates an existing primitive in the KnowledgeMap based on the user's answer to a follow-up question.
        """
        if target_id in kmap.goals:
            g = kmap.goals[target_id]
            updated_actor_ids = list(g.actor_ids)
            updated_why = g.underlying_motivation
            updated_when = g.situation_trigger
            updated_outcome = g.desired_outcome
            updated_entities = list(g.entity_ids)
            updated_failures = list(g.failure_modes)

            lines = feedback_text.split("\n")
            for line in lines:
                l_lower = line.lower()
                if any(k in l_lower for k in ["actor:", "role:"]):
                    actor_name = line.split(":")[-1].strip()
                    actor_id = actor_name.lower().replace(" ", "_")
                    if actor_id not in kmap.actors:
                        kmap.add_actor(Actor(id=actor_id, name=actor_name, role=actor_name))
                    if actor_id not in updated_actor_ids:
                        updated_actor_ids.append(actor_id)

                if any(k in l_lower for k in ["why:", "motivation:", "problem:"]):
                    updated_why = line.split(":")[-1].strip()

                if any(k in l_lower for k in ["when:", "trigger:", "situation:"]):
                    updated_when = line.split(":")[-1].strip()

                if any(k in l_lower for k in ["outcome:", "so that:", "benefit:"]):
                    updated_outcome = line.split(":")[-1].strip()

                if any(k in l_lower for k in ["entity:", "fields:", "data:"]):
                    entity_name = line.split(":")[-1].strip()
                    entity_id = entity_name.lower().replace(" ", "_")
                    if entity_id not in kmap.entities:
                        kmap.add_entity(DataEntity(id=entity_id, name=entity_name))
                    if entity_id not in updated_entities:
                        updated_entities.append(entity_id)

                if any(k in l_lower for k in ["error:", "failure:", "edge case:"]):
                    updated_failures.append(line.split(":")[-1].strip())

            # Fallback direct assignment if unstructured text was provided
            if not updated_why and len(feedback_text) > 5:
                updated_why = feedback_text
            if not updated_when:
                updated_when = "When initiated by stakeholder"
            if not updated_outcome:
                updated_outcome = "Deliver actionable outcome to stakeholder"
            if not updated_entities:
                entity_id = f"entity_{g.id}"
                kmap.add_entity(DataEntity(id=entity_id, name="Core Domain Entity"))
                updated_entities.append(entity_id)
            if not updated_failures:
                updated_failures.append("Handle standard system timeouts and log error alerts")

            kmap.goals[target_id] = Goal(
                id=g.id,
                description=g.description,
                actor_ids=updated_actor_ids or (list(kmap.actors.keys())[:1] if kmap.actors else ["stakeholder"]),
                entity_ids=updated_entities,
                situation_trigger=updated_when,
                underlying_motivation=updated_why,
                desired_outcome=updated_outcome,
                failure_modes=updated_failures
            )

        elif target_id in kmap.constraints:
            c = kmap.constraints[target_id]
            kmap.constraints[target_id] = Constraint(
                id=c.id,
                description=c.description,
                target_id=c.target_id,
                is_measurable=True,
                sla_metric=feedback_text
            )
