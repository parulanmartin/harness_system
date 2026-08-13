from dataclasses import dataclass
from typing import List, Optional
from harness.models import KnowledgeMap, Gap, Question, EngineeringOutputs
from harness.gap_detector import GapDetector
from harness.question_engine import QuestionEngine
from harness.ingestor import TranscriptIngestor
from harness.synthesis import SynthesisEngine

@dataclass
class HarnessResult:
    is_complete: bool
    gaps: List[Gap]
    questions: List[Question]
    outputs: Optional[EngineeringOutputs] = None

class HarnessEngine:
    """
    Core orchestrator that runs the Gap Detector evaluation loop.
    Determines whether the system needs more user input or can proceed to Synthesis.
    """

    def __init__(self):
        self.gap_detector = GapDetector()
        self.question_engine = QuestionEngine()
        self.ingestor = TranscriptIngestor()
        self.synthesis = SynthesisEngine()

    def process(self, kmap: KnowledgeMap, max_questions_per_loop: int = 3) -> HarnessResult:
        # Step 1: Run Gap Detector (Structural + JTBD Semantic Checks)
        gaps = self.gap_detector.evaluate(kmap)

        # Step 2: Decision Gate
        if gaps:
            # Gaps found -> Generate questions for feedback loop
            questions = self.question_engine.generate_questions(gaps, kmap, max_questions=max_questions_per_loop)
            return HarnessResult(
                is_complete=False,
                gaps=gaps,
                questions=questions,
                outputs=None
            )
        else:
            # No gaps -> Synthesize engineering outputs
            outputs = self.synthesis.synthesize(kmap)
            return HarnessResult(
                is_complete=True,
                gaps=[],
                questions=[],
                outputs=outputs
            )

    def receive_answers(self, kmap: KnowledgeMap, answers: dict[str, str]) -> None:
        """
        Ingests user responses to questions and updates KnowledgeMap primitives.
        """
        for target_id, feedback in answers.items():
            self.ingestor.apply_user_feedback(kmap, target_id, feedback)
