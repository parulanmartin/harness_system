import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from harness.models import KnowledgeMap, Actor, Goal, DataEntity, Constraint, Assumption, EngineeringOutputs
from harness.config import Config

class SheetsStorage:
    """
    Storage layer managing per-project structured tables (simulating Google Sheets tabs / DB tables).
    Saves and loads KnowledgeMaps, merges multi-transcript data, and stores final synthesized outputs.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.base_dir = self.config.local_storage_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_project_file_path(self, project_id: str) -> str:
        proj_dir = os.path.join(self.base_dir, project_id)
        os.makedirs(proj_dir, exist_ok=True)
        return os.path.join(proj_dir, "knowledge_map.json")

    def _get_outputs_file_path(self, project_id: str) -> str:
        proj_dir = os.path.join(self.base_dir, project_id)
        os.makedirs(proj_dir, exist_ok=True)
        return os.path.join(proj_dir, "outputs_history.json")

    def load_knowledge_map(self, project_id: str) -> KnowledgeMap:
        """
        Loads the existing KnowledgeMap for a project from storage.
        """
        path = self._get_project_file_path(project_id)
        if not os.path.exists(path):
            return KnowledgeMap()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return KnowledgeMap.from_dict(data)
        except Exception as err:
            print(f"[Warning] Failed to load knowledge map for project '{project_id}': {err}")
            return KnowledgeMap()

    def save_knowledge_map(self, project_id: str, kmap: KnowledgeMap, source_doc_url: str = "") -> None:
        """
        Saves the KnowledgeMap to project storage and logs the transcript run.
        """
        path = self._get_project_file_path(project_id)
        data = kmap.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def merge_knowledge_map(self, existing: KnowledgeMap, new_kmap: KnowledgeMap) -> KnowledgeMap:
        """
        Merges new extracted primitives into the existing KnowledgeMap with deduplication.
        """
        # 1. Merge Actors
        for a_id, new_actor in new_kmap.actors.items():
            if a_id not in existing.actors:
                match = next((a for a in existing.actors.values() if a.name.lower() == new_actor.name.lower()), None)
                if match:
                    existing.actors[match.id] = Actor(
                        id=match.id,
                        name=match.name,
                        role=new_actor.role or match.role,
                        description=new_actor.description or match.description,
                        source_doc=new_actor.source_doc or match.source_doc,
                        extracted_at=new_actor.extracted_at
                    )
                else:
                    existing.add_actor(new_actor)
            else:
                existing.add_actor(new_actor)

        # 2. Merge Entities
        for e_id, new_entity in new_kmap.entities.items():
            if e_id not in existing.entities:
                match = next((e for e in existing.entities.values() if e.name.lower() == new_entity.name.lower()), None)
                if match:
                    combined_fields = list(set(match.fields + new_entity.fields))
                    existing.entities[match.id] = DataEntity(
                        id=match.id,
                        name=match.name,
                        fields=combined_fields,
                        description=new_entity.description or match.description,
                        source_doc=new_entity.source_doc or match.source_doc,
                        extracted_at=new_entity.extracted_at
                    )
                else:
                    existing.add_entity(new_entity)
            else:
                existing.add_entity(new_entity)

        # 3. Merge Goals
        for g_id, new_goal in new_kmap.goals.items():
            if g_id in existing.goals:
                old_goal = existing.goals[g_id]
                existing.goals[g_id] = Goal(
                    id=g_id,
                    description=new_goal.description or old_goal.description,
                    actor_ids=list(set(old_goal.actor_ids + new_goal.actor_ids)),
                    entity_ids=list(set(old_goal.entity_ids + new_goal.entity_ids)),
                    situation_trigger=new_goal.situation_trigger or old_goal.situation_trigger,
                    underlying_motivation=new_goal.underlying_motivation or old_goal.underlying_motivation,
                    desired_outcome=new_goal.desired_outcome or old_goal.desired_outcome,
                    failure_modes=list(set(old_goal.failure_modes + new_goal.failure_modes)),
                    source_doc=new_goal.source_doc or old_goal.source_doc,
                    extracted_at=new_goal.extracted_at
                )
            else:
                existing.add_goal(new_goal)

        # 4. Merge Constraints
        for c_id, new_constraint in new_kmap.constraints.items():
            if c_id not in existing.constraints:
                existing.add_constraint(new_constraint)
            else:
                old_c = existing.constraints[c_id]
                existing.constraints[c_id] = Constraint(
                    id=c_id,
                    description=new_constraint.description or old_c.description,
                    target_id=new_constraint.target_id or old_c.target_id,
                    is_measurable=new_constraint.is_measurable or old_c.is_measurable,
                    sla_metric=new_constraint.sla_metric or old_c.sla_metric,
                    source_doc=new_constraint.source_doc or old_c.source_doc,
                    extracted_at=new_constraint.extracted_at
                )

        # 5. Merge Assumptions
        for asm_id, new_asm in new_kmap.assumptions.items():
            if asm_id not in existing.assumptions:
                existing.add_assumption(new_asm)
            else:
                old_asm = existing.assumptions[asm_id]
                existing.assumptions[asm_id] = Assumption(
                    id=asm_id,
                    description=new_asm.description or old_asm.description,
                    validated=new_asm.validated or old_asm.validated,
                    source_doc=new_asm.source_doc or old_asm.source_doc,
                    extracted_at=new_asm.extracted_at
                )

        return existing

    def save_outputs(self, project_id: str, outputs: EngineeringOutputs) -> None:
        """
        Appends synthesized outputs to the project outputs history.
        """
        path = self._get_outputs_file_path(project_id)
        history = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        entry = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "requirements": outputs.requirements,
            "jtbd_matrix": outputs.jtbd_matrix,
            "acceptance_criteria": outputs.acceptance_criteria,
            "spec": outputs.spec
        }
        history.append(entry)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
