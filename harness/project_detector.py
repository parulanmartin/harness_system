import json
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from harness.models import Project
from harness.config import Config
from harness.project_registry import ProjectRegistry
from harness.llm_client import OpenRouterClient

@dataclass
class ProjectDetectionResult:
    matched_project: Optional[Project]
    confidence: float
    reasoning: str
    suggested_new_name: Optional[str] = None
    suggested_new_description: Optional[str] = None

DETECTION_SYSTEM_PROMPT = """You are an intelligent Project Classifier for a software requirements engineering system.
Analyze the provided meeting transcript snippet and compare it against the list of existing projects.

Determine:
1. Does this transcript belong to one of the existing projects?
2. Or is it discussing a completely new project?

Respond in strict JSON format:
{
  "matched_project_id": "string or null",
  "confidence": 0.85,
  "reasoning": "Explain why this transcript matches this project or why it is new.",
  "suggested_new_name": "string (if new project, suggest a concise title)",
  "suggested_new_description": "string (if new project, summarize its scope)"
}

Do NOT wrap in markdown fences. Return ONLY the JSON object.
"""

class ProjectDetector:
    """
    Analyzes meeting transcripts and matches them against registered projects.
    Uses DeepSeek V4-Flash via OpenRouter with heuristic fallback.
    """

    def __init__(self, config: Optional[Config] = None, registry: Optional[ProjectRegistry] = None):
        self.config = config or Config.from_env()
        self.registry = registry or ProjectRegistry(self.config)
        self.llm_client = OpenRouterClient(self.config)

    def detect_project(self, transcript_text: str) -> ProjectDetectionResult:
        projects = self.registry.list_projects()
        if not projects:
            return ProjectDetectionResult(
                matched_project=None,
                confidence=0.0,
                reasoning="No existing projects registered in the database.",
                suggested_new_name="Project Alpha",
                suggested_new_description="Extracted from first meeting transcript."
            )

        if self.config.openrouter_api_key:
            try:
                return self._detect_with_llm(transcript_text, projects)
            except Exception as err:
                print(f"[Warning] LLM project detection failed ({err}), falling back to heuristic matching...")

        return self._detect_with_heuristics(transcript_text, projects)

    def _detect_with_llm(self, transcript_text: str, projects: List[Project]) -> ProjectDetectionResult:
        projects_summary = [
            {"id": p.id, "name": p.name, "description": p.description}
            for p in projects
        ]

        prompt = (
            f"Existing Projects:\n{json.dumps(projects_summary, indent=2)}\n\n"
            f"Transcript Sample (first 3000 chars):\n{transcript_text[:3000]}\n"
        )

        response = self.llm_client.complete(
            prompt=prompt,
            system_prompt=DETECTION_SYSTEM_PROMPT,
            model=self.config.llm_model_detect
        )

        cleaned = re.sub(r"^```json\s*", "", response.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        data = json.loads(cleaned)

        matched_id = data.get("matched_project_id")
        confidence = float(data.get("confidence", 0.0))
        reasoning = data.get("reasoning", "")
        suggested_name = data.get("suggested_new_name")
        suggested_desc = data.get("suggested_new_description")

        matched_project = next((p for p in projects if p.id == matched_id), None) if matched_id else None

        return ProjectDetectionResult(
            matched_project=matched_project,
            confidence=confidence,
            reasoning=reasoning,
            suggested_new_name=suggested_name,
            suggested_new_description=suggested_desc
        )

    def _detect_with_heuristics(self, transcript_text: str, projects: List[Project]) -> ProjectDetectionResult:
        """
        Keyword matching heuristic when OpenRouter key is not set.
        """
        text_lower = transcript_text.lower()

        # Score projects based on keyword overlap
        scores = {}
        for p in projects:
            score = 0
            # Check name words
            for word in p.name.lower().split():
                if len(word) > 3 and word in text_lower:
                    score += 2
            # Check description words
            for word in p.description.lower().split():
                if len(word) > 4 and word in text_lower:
                    score += 1
            scores[p.id] = score

        best_id, best_score = max(scores.items(), key=lambda x: x[1]) if scores else (None, 0)

        if best_score >= 3:
            matched_proj = self.registry.get_project(best_id)
            return ProjectDetectionResult(
                matched_project=matched_proj,
                confidence=min(0.5 + (best_score * 0.1), 0.95),
                reasoning=f"Matched project '{matched_proj.name}' based on relevant domain terms in transcript."
            )

        return ProjectDetectionResult(
            matched_project=None,
            confidence=0.0,
            reasoning="Transcript does not strongly match any existing project keywords.",
            suggested_new_name="New Requirements Project",
            suggested_new_description="Auto-generated project container for transcript requirements."
        )
