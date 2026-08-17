from typing import List, Optional
from harness.models import (
    KnowledgeMap, Gap, GapCategory, GapPriority, Goal, Constraint
)
from harness.config import Config
from harness.llm_client import OpenRouterClient

class GapDetector:
    """
    Evaluates a KnowledgeMap against Structural and Semantic (JTBD-focused) rules.
    Returns a list of identified Gaps ordered by priority.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.llm_client = OpenRouterClient(self.config)

    def evaluate(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps: List[Gap] = []
        
        # 1. Structural Checks (Code & Graph Traversal)
        gaps.extend(self._check_orphaned_goals(kmap))
        gaps.extend(self._check_missing_entities(kmap))
        gaps.extend(self._check_floating_constraints(kmap))

        # 2. Semantic Checks (JTBD & Problem Discovery Framework)
        gaps.extend(self._check_jtbd_why(kmap))
        gaps.extend(self._check_jtbd_when(kmap))
        gaps.extend(self._check_jtbd_outcome(kmap))
        gaps.extend(self._check_unmeasurable_constraints(kmap))
        gaps.extend(self._check_unhandled_failure_modes(kmap))

        # Sort by Priority: P1 Blocker first, then P2, then P3
        gaps.sort(key=lambda g: g.priority.value)
        return gaps

    def _check_orphaned_goals(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for g_id, goal in kmap.goals.items():
            if not goal.actor_ids:
                gaps.append(Gap(
                    id=f"gap_orphan_{g_id}",
                    category=GapCategory.STRUCTURAL_ORPHANED_GOAL,
                    target_id=g_id,
                    description=f"Goal '{goal.description}' is missing an assigned Actor.",
                    priority=GapPriority.P1
                ))
        return gaps

    def _check_missing_entities(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for g_id, goal in kmap.goals.items():
            if not goal.entity_ids:
                gaps.append(Gap(
                    id=f"gap_entity_{g_id}",
                    category=GapCategory.STRUCTURAL_MISSING_ENTITY,
                    target_id=g_id,
                    description=f"Goal '{goal.description}' does not reference any Data Entity.",
                    priority=GapPriority.P2
                ))
        return gaps

    def _check_floating_constraints(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for c_id, constraint in kmap.constraints.items():
            if not constraint.target_id or (
                constraint.target_id not in kmap.goals and constraint.target_id not in kmap.entities
            ):
                gaps.append(Gap(
                    id=f"gap_floating_{c_id}",
                    category=GapCategory.STRUCTURAL_FLOATING_CONSTRAINT,
                    target_id=c_id,
                    description=f"Constraint '{constraint.description}' is floating (not attached to any Goal or Entity).",
                    priority=GapPriority.P2
                ))
        return gaps

    def _check_jtbd_why(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for g_id, goal in kmap.goals.items():
            if not goal.underlying_motivation or len(goal.underlying_motivation.strip()) < 5:
                gaps.append(Gap(
                    id=f"gap_jtbd_why_{g_id}",
                    category=GapCategory.SEMANTIC_JTBD_WHY,
                    target_id=g_id,
                    description=f"Goal '{goal.description}' lacks the underlying user motivation (the 'Why'/root problem).",
                    priority=GapPriority.P1
                ))
        return gaps

    def _check_jtbd_when(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for g_id, goal in kmap.goals.items():
            if not goal.situation_trigger or len(goal.situation_trigger.strip()) < 5:
                gaps.append(Gap(
                    id=f"gap_jtbd_when_{g_id}",
                    category=GapCategory.SEMANTIC_JTBD_WHEN,
                    target_id=g_id,
                    description=f"Goal '{goal.description}' lacks a defined situation or trigger context (the 'When').",
                    priority=GapPriority.P2
                ))
        return gaps

    def _check_jtbd_outcome(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for g_id, goal in kmap.goals.items():
            if not goal.desired_outcome or len(goal.desired_outcome.strip()) < 5:
                gaps.append(Gap(
                    id=f"gap_jtbd_outcome_{g_id}",
                    category=GapCategory.SEMANTIC_JTBD_OUTCOME,
                    target_id=g_id,
                    description=f"Goal '{goal.description}' lacks a measurable desired success outcome (the 'So That').",
                    priority=GapPriority.P2
                ))
        return gaps

    def _check_unmeasurable_constraints(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for c_id, constraint in kmap.constraints.items():
            if not constraint.is_measurable or not constraint.sla_metric:
                gaps.append(Gap(
                    id=f"gap_unmeasurable_{c_id}",
                    category=GapCategory.SEMANTIC_UNMEASURABLE_CONSTRAINT,
                    target_id=c_id,
                    description=f"Constraint '{constraint.description}' is vague/unmeasurable (missing SLA or metric).",
                    priority=GapPriority.P2
                ))
        return gaps

    def _check_unhandled_failure_modes(self, kmap: KnowledgeMap) -> List[Gap]:
        gaps = []
        for g_id, goal in kmap.goals.items():
            if not goal.failure_modes:
                gaps.append(Gap(
                    id=f"gap_failure_{g_id}",
                    category=GapCategory.SEMANTIC_UNHANDLED_FAILURE,
                    target_id=g_id,
                    description=f"Goal '{goal.description}' has no defined error states or edge case failure modes.",
                    priority=GapPriority.P3
                ))
        return gaps
