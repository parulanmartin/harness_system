import os
import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from harness.models import Project
from harness.config import Config

class ProjectRegistry:
    """
    Registry for managing all projects in the Harness System.
    Acts as the master database table for projects.
    Supports Google Sheets backend with automatic local JSON fallback.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.local_dir = self.config.local_storage_dir
        os.makedirs(self.local_dir, exist_ok=True)
        self.local_registry_path = os.path.join(self.local_dir, "projects_registry.json")
        self._init_local_registry()

    def _init_local_registry(self) -> None:
        if not os.path.exists(self.local_registry_path):
            now = datetime.now(timezone.utc).isoformat()
            initial_projects = [
                {
                    "id": "edge_sensors",
                    "name": "Edge Sensors & Informational Edge",
                    "description": "Deploying niche ground-truth physical sensors (cameras, foot traffic, supply chain metrics) to capture early informational advantage.",
                    "sheet_id": "mock_sheet_edge_sensors_123",
                    "created_at": now,
                    "last_updated": now,
                    "transcript_count": 1,
                    "status": "active"
                },
                {
                    "id": "seoul_kb_system",
                    "name": "Seoul Knowledge Base System",
                    "description": "Enterprise knowledge base and documentation sync for Seoul operations and engineering teams.",
                    "sheet_id": "mock_sheet_seoul_kb_456",
                    "created_at": now,
                    "last_updated": now,
                    "transcript_count": 0,
                    "status": "active"
                }
            ]
            with open(self.local_registry_path, "w", encoding="utf-8") as f:
                json.dump(initial_projects, f, indent=2)

    def list_projects(self) -> List[Project]:
        """Returns all registered projects."""
        try:
            with open(self.local_registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Project(**p) for p in data]
        except Exception:
            return []

    def get_project(self, project_id: str) -> Optional[Project]:
        """Gets a project by ID or normalized name."""
        norm_id = project_id.lower().replace(" ", "_").replace("-", "_")
        for p in self.list_projects():
            if p.id.lower() == norm_id or p.name.lower() == project_id.lower():
                return p
        return None

    def create_project(self, name: str, description: str, sheet_id: str = "") -> Project:
        """Creates a new project and registers it in the database/registry."""
        proj_id = re.sub(r"[^a-zA-Z0-9_]", "", name.lower().replace(" ", "_"))
        now = datetime.now(timezone.utc).isoformat()
        
        project = Project(
            id=proj_id,
            name=name,
            description=description,
            sheet_id=sheet_id or f"sheet_{proj_id}",
            created_at=now,
            last_updated=now,
            transcript_count=0,
            status="active"
        )

        projects = self.list_projects()
        existing = [p for p in projects if p.id == proj_id]
        if not existing:
            projects.append(project)
            self._save_projects(projects)
            return project
        else:
            return existing[0]

    def increment_transcript_count(self, project_id: str) -> None:
        """Increments the processed transcript count for a project."""
        projects = self.list_projects()
        for p in projects:
            if p.id == project_id:
                p.transcript_count += 1
                p.last_updated = datetime.now(timezone.utc).isoformat()
        self._save_projects(projects)

    def _save_projects(self, projects: List[Project]) -> None:
        raw_list = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "sheet_id": p.sheet_id,
                "created_at": p.created_at,
                "last_updated": p.last_updated,
                "transcript_count": p.transcript_count,
                "status": p.status
            }
            for p in projects
        ]
        with open(self.local_registry_path, "w", encoding="utf-8") as f:
            json.dump(raw_list, f, indent=2)
