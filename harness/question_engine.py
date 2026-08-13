from typing import List
from harness.models import Gap, GapCategory, Question, KnowledgeMap

class QuestionEngine:
    """
    Transforms detected gaps into prioritized, targeted questions to send back to the stakeholder/user.
    """

    def generate_questions(self, gaps: List[Gap], kmap: KnowledgeMap, max_questions: int = 3) -> List[Question]:
        questions: List[Question] = []

        # Sort gaps so highest priority (P1) comes first
        sorted_gaps = sorted(gaps, key=lambda g: g.priority.value)

        for gap in sorted_gaps[:max_questions]:
            q_text = self._formulate_question(gap, kmap)
            questions.append(Question(
                id=f"q_{gap.id}",
                gap_id=gap.id,
                target_id=gap.target_id,
                question_text=q_text,
                priority=gap.priority
            ))

        return questions

    def _formulate_question(self, gap: Gap, kmap: KnowledgeMap) -> str:
        match gap.category:
            case GapCategory.STRUCTURAL_ORPHANED_GOAL:
                goal = kmap.goals.get(gap.target_id)
                g_name = goal.description if goal else "this goal"
                return f"Who is the primary Actor or user role responsible for/performing: '{g_name}'?"

            case GapCategory.STRUCTURAL_MISSING_ENTITY:
                goal = kmap.goals.get(gap.target_id)
                g_name = goal.description if goal else "this goal"
                return f"What specific Data Entities or fields are being created, updated, or viewed during '{g_name}'?"

            case GapCategory.STRUCTURAL_FLOATING_CONSTRAINT:
                constraint = kmap.constraints.get(gap.target_id)
                c_name = constraint.description if constraint else "this constraint"
                return f"Which specific Goal or Data Entity does the constraint '{c_name}' apply to?"

            case GapCategory.SEMANTIC_JTBD_WHY:
                goal = kmap.goals.get(gap.target_id)
                g_name = goal.description if goal else "this feature"
                return f"For '{g_name}', what is the core underlying problem or motivation? What job does this solve for the user?"

            case GapCategory.SEMANTIC_JTBD_WHEN:
                goal = kmap.goals.get(gap.target_id)
                g_name = goal.description if goal else "this action"
                return f"Under what specific situation or trigger event does the user need to perform '{g_name}'?"

            case GapCategory.SEMANTIC_JTBD_OUTCOME:
                goal = kmap.goals.get(gap.target_id)
                g_name = goal.description if goal else "this requirement"
                return f"What is the expected success outcome or measurable benefit once '{g_name}' is accomplished?"

            case GapCategory.SEMANTIC_UNMEASURABLE_CONSTRAINT:
                constraint = kmap.constraints.get(gap.target_id)
                c_name = constraint.description if constraint else "this constraint"
                return f"The constraint '{c_name}' is qualitative. What quantitative SLA or objective criteria should engineers test against?"

            case GapCategory.SEMANTIC_UNHANDLED_FAILURE:
                goal = kmap.goals.get(gap.target_id)
                g_name = goal.description if goal else "this feature"
                return f"What should happen if '{g_name}' encounters an error or failure condition?"

            case _:
                return f"Could you provide more detail regarding: {gap.description}?"
