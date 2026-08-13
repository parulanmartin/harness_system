from typing import Dict, Any, List
from harness.models import KnowledgeMap, Actor, Goal, DataEntity, Constraint, Assumption

class TranscriptIngestor:
    """
    Ingests raw transcript / text (e.g. from Google Docs) and updates the KnowledgeMap graph with extracted primitives.
    Also merges follow-up user responses back into the state graph.
    """

    def parse_and_populate(self, raw_text: str, kmap: KnowledgeMap) -> None:
        """
        Parses raw text (simulating LLM structured extraction) into KnowledgeMap primitives.
        """
        # For demonstration & simulation, parser extracts structural nodes based on text structure or JSON hints
        # In production, this calls an LLM with JSON Schema structured outputs.
        pass

    def apply_user_feedback(self, kmap: KnowledgeMap, target_id: str, feedback_text: str) -> None:
        """
        Updates an existing primitive in the KnowledgeMap based on the user's answer to a follow-up question.
        """
        # If target is a Goal, update missing JTBD fields or actors
        if target_id in kmap.goals:
            g = kmap.goals[target_id]
            updated_actor_ids = list(g.actor_ids)
            updated_why = g.underlying_motivation
            updated_when = g.situation_trigger
            updated_outcome = g.desired_outcome
            updated_entities = list(g.entity_ids)
            updated_failures = list(g.failure_modes)

            # Heuristics to update target fields based on response content
            lines = feedback_text.split("\n")
            for line in lines:
                l_lower = line.lower()
                if "actor:" in l_lower or "role:" in l_lower or "actor" in l_lower:
                    actor_name = line.split(":")[-1].strip() if ":" in line else line.strip()
                    actor_id = actor_name.lower().replace(" ", "_")
                    if actor_id not in kmap.actors:
                        kmap.add_actor(Actor(id=actor_id, name=actor_name, role=actor_name))
                    if actor_id not in updated_actor_ids:
                        updated_actor_ids.append(actor_id)

                if "why:" in l_lower or "motivation:" in l_lower or "problem:" in l_lower:
                    updated_why = line.split(":")[-1].strip() if ":" in line else line.strip()

                if "when:" in l_lower or "trigger:" in l_lower or "situation:" in l_lower:
                    updated_when = line.split(":")[-1].strip() if ":" in line else line.strip()

                if "outcome:" in l_lower or "so that:" in l_lower or "benefit:" in l_lower:
                    updated_outcome = line.split(":")[-1].strip() if ":" in line else line.strip()

                if "entity:" in l_lower or "fields:" in l_lower:
                    entity_name = line.split(":")[-1].strip() if ":" in line else line.strip()
                    entity_id = entity_name.lower().replace(" ", "_")
                    if entity_id not in kmap.entities:
                        kmap.add_entity(DataEntity(id=entity_id, name=entity_name))
                    if entity_id not in updated_entities:
                        updated_entities.append(entity_id)

                if "error:" in l_lower or "failure:" in l_lower:
                    updated_failures.append(line.split(":")[-1].strip() if ":" in line else line.strip())

            # Fallbacks if explicit prefixes weren't used
            if not updated_why and len(feedback_text) > 5:
                updated_why = feedback_text
            if not updated_when and len(feedback_text) > 5:
                updated_when = f"When requested by user: {feedback_text}"
            if not updated_outcome and len(feedback_text) > 5:
                updated_outcome = f"Outcome achieved: {feedback_text}"

            kmap.goals[target_id] = Goal(
                id=g.id,
                description=g.description,
                actor_ids=updated_actor_ids,
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
