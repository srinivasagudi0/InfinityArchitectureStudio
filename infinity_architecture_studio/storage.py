from __future__ import annotations

import json
from pathlib import Path

from .config import AppConfig, load_config
from .models import SavedProject


class ProjectStorage:
    def __init__(self, root_dir: Path | None = None, config: AppConfig | None = None) -> None:
        self._config = config or load_config()
        self.root_dir = Path(root_dir or self._config.storage_dir)
        self.projects_dir = self.root_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def project_path(self, project_id: str) -> Path:
        return self.projects_dir / f"{project_id}.json"

    def save_project(self, project: SavedProject) -> Path:
        path = self.project_path(project.metadata.project_id)
        path.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")
        return path

    def load_project(self, project_id: str) -> SavedProject:
        path = self.project_path(project_id)
        if not path.exists():
            raise FileNotFoundError(f"No saved project found for '{project_id}'.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return SavedProject.from_dict(payload)

    def list_projects(self) -> list[SavedProject]:
        projects: list[SavedProject] = []
        for path in sorted(self.projects_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                projects.append(SavedProject.from_dict(payload))
            except json.JSONDecodeError:
                continue
        return sorted(projects, key=lambda project: project.metadata.updated_at, reverse=True)
