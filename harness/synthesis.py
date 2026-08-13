from typing import List, Dict
from harness.models import KnowledgeMap, EngineeringOutputs

class SynthesisEngine:
    """
    Produces final engineering-ready outputs (PRD/Spec, JTBD Matrix, Requirements, Acceptance Criteria)
    from a fully verified KnowledgeMap.
    """

    def synthesize(self, kmap: KnowledgeMap) -> EngineeringOutputs:
        requirements: List[str] = []
        jtbd_matrix: List[Dict[str, str]] = []
        acceptance_criteria: List[str] = []

        # 1. Generate JTBD Matrix
        for g_id, goal in kmap.goals.items():
            actors_str = ", ".join([kmap.actors[a].name for a in goal.actor_ids if a in kmap.actors]) or "User"
            jtbd_matrix.append({
                "actor": actors_str,
                "situation": goal.situation_trigger or "When working in system",
                "motivation": goal.underlying_motivation or goal.description,
                "outcome": goal.desired_outcome or "Accomplish task efficiently"
            })

            # 2. Generate Functional Requirements
            requirements.append(
                f"REQ-{g_id.upper()}: As a {actors_str}, I want to {goal.description} so that {goal.desired_outcome or 'I achieve my goal'}."
            )

            # 3. Generate Acceptance Criteria (Given / When / Then)
            acceptance_criteria.append(
                f"SCENARIO-{g_id.upper()}: Happy Path\n"
                f"  GIVEN {actors_str} is in context: '{goal.situation_trigger or 'Standard workflow'}'\n"
                f"  WHEN they perform: '{goal.description}'\n"
                f"  THEN the system achieves: '{goal.desired_outcome or 'Success state'}'"
            )

            for idx, f_mode in enumerate(goal.failure_modes, 1):
                acceptance_criteria.append(
                    f"SCENARIO-{g_id.upper()}-ERR-{idx}: Edge Case / Exception\n"
                    f"  GIVEN {actors_str} encounters error condition: '{f_mode}'\n"
                    f"  THEN system should display appropriate error and prevent invalid state."
                )

        # 4. Generate Non-Functional Requirements from Constraints
        for c_id, constraint in kmap.constraints.items():
            sla = f" (SLA: {constraint.sla_metric})" if constraint.sla_metric else ""
            requirements.append(f"NFR-{c_id.upper()}: System must adhere to constraint: '{constraint.description}'{sla}.")

        # 5. Format Full Engineering Spec Document
        spec_doc = self._generate_spec_markdown(kmap, requirements, jtbd_matrix, acceptance_criteria)

        return EngineeringOutputs(
            requirements=requirements,
            spec=spec_doc,
            jtbd_matrix=jtbd_matrix,
            acceptance_criteria=acceptance_criteria
        )

    def _generate_spec_markdown(
        self,
        kmap: KnowledgeMap,
        requirements: List[str],
        jtbd_matrix: List[Dict[str, str]],
        acceptance_criteria: List[str]
    ) -> str:
        lines = [
            "# Engineering Specification & Requirements",
            "",
            "## 1. Executive Summary & JTBD Matrix",
            "| Actor | Situation (When...) | Motivation (I want to...) | Desired Outcome (So that...) |",
            "|-------|----------------------|---------------------------|------------------------------|"
        ]

        for item in jtbd_matrix:
            lines.append(f"| {item['actor']} | {item['situation']} | {item['motivation']} | {item['outcome']} |")

        lines.extend([
            "",
            "## 2. Functional & Non-Functional Requirements",
        ])
        for req in requirements:
            lines.append(f"- {req}")

        lines.extend([
            "",
            "## 3. Data Entities",
        ])
        for e_id, entity in kmap.entities.items():
            fields_str = f" (Fields: {', '.join(entity.fields)})" if entity.fields else ""
            lines.append(f"- **{entity.name}**{fields_str}: {entity.description or 'Core domain data entity.'}")

        lines.extend([
            "",
            "## 4. Acceptance Criteria & Edge Cases",
        ])
        for ac in acceptance_criteria:
            lines.append(f"```text\n{ac}\n```")

        return "\n".join(lines)
