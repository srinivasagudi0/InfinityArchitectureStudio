from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


PACK_SECTION_TITLES = {
    "executive_summary": "Executive Summary",
    "recommended_stack": "Recommended Stack",
    "major_components": "Major Components and Responsibilities",
    "high_level_data_flow": "High-Level Data Flow",
    "file_structure": "File and Module Structure",
    "api_service_boundaries": "API or Service Boundary Outline",
    "implementation_roadmap": "Implementation Roadmap",
    "risks_open_questions": "Risks and Open Questions",
}


BRIEF_FIELD_TITLES = {
    "project_name": "Project Name",
    "problem_description": "Problem Description",
    "target_users": "Target Users",
    "core_goals": "Core Goals",
    "constraints": "Constraints",
    "preferred_stack": "Preferred Stack or Libraries",
    "integrations": "Integrations",
    "non_functional_requirements": "Non-Functional Requirements",
    "extra_notes": "Extra Notes",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ProjectBrief:
    project_name: str = ""
    problem_description: str = ""
    target_users: str = ""
    core_goals: str = ""
    constraints: str = ""
    preferred_stack: str = ""
    integrations: str = ""
    non_functional_requirements: str = ""
    extra_notes: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectBrief":
        values = {field_name: str(payload.get(field_name, "") or "") for field_name in BRIEF_FIELD_TITLES}
        return cls(**values)

    def display_rows(self) -> list[tuple[str, str]]:
        return [
            (label, getattr(self, field_name).strip() or "Not specified")
            for field_name, label in BRIEF_FIELD_TITLES.items()
        ]


@dataclass
class ArchitecturePack:
    executive_summary: str = ""
    recommended_stack: str = ""
    major_components: str = ""
    high_level_data_flow: str = ""
    file_structure: str = ""
    api_service_boundaries: str = ""
    implementation_roadmap: str = ""
    risks_open_questions: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArchitecturePack":
        values = {
            field_name: str(payload.get(field_name, "") or "")
            for field_name in PACK_SECTION_TITLES
        }
        return cls(**values)

    def section_items(self) -> list[tuple[str, str]]:
        return [
            (label, getattr(self, field_name).strip() or "No content generated.")
            for field_name, label in PACK_SECTION_TITLES.items()
        ]


@dataclass
class RevisionEntry:
    revision_number: int
    created_at: str
    instruction: str
    model: str
    architecture_pack: ArchitecturePack

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["architecture_pack"] = self.architecture_pack.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RevisionEntry":
        return cls(
            revision_number=int(payload.get("revision_number", 0) or 0),
            created_at=str(payload.get("created_at", "") or ""),
            instruction=str(payload.get("instruction", "") or ""),
            model=str(payload.get("model", "") or ""),
            architecture_pack=ArchitecturePack.from_dict(payload.get("architecture_pack", {})),
        )


@dataclass
class ProjectMetadata:
    project_id: str
    project_name: str
    created_at: str
    updated_at: str
    current_revision: int = 0
    last_model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectMetadata":
        return cls(
            project_id=str(payload.get("project_id", "") or ""),
            project_name=str(payload.get("project_name", "") or ""),
            created_at=str(payload.get("created_at", "") or ""),
            updated_at=str(payload.get("updated_at", "") or ""),
            current_revision=int(payload.get("current_revision", 0) or 0),
            last_model=str(payload.get("last_model", "") or ""),
        )


@dataclass
class SavedProject:
    metadata: ProjectMetadata
    brief: ProjectBrief
    latest_pack: ArchitecturePack
    revision_history: list[RevisionEntry] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        brief: ProjectBrief,
        architecture_pack: ArchitecturePack,
        model: str,
        instruction: str = "Initial generation",
    ) -> "SavedProject":
        timestamp = utc_now_iso()
        project_id = f"{brief.project_name.strip().lower().replace(' ', '-')[:40]}-{uuid4().hex[:8]}".strip("-")
        metadata = ProjectMetadata(
            project_id=project_id or f"project-{uuid4().hex[:8]}",
            project_name=brief.project_name.strip() or "Untitled Project",
            created_at=timestamp,
            updated_at=timestamp,
            current_revision=0,
            last_model="",
        )
        project = cls(metadata=metadata, brief=brief, latest_pack=architecture_pack)
        project.add_revision(architecture_pack=architecture_pack, instruction=instruction, model=model)
        return project

    def add_revision(self, architecture_pack: ArchitecturePack, instruction: str, model: str) -> None:
        revision_number = self.metadata.current_revision + 1
        timestamp = utc_now_iso()
        self.latest_pack = architecture_pack
        self.metadata.project_name = self.brief.project_name.strip() or self.metadata.project_name or "Untitled Project"
        self.metadata.updated_at = timestamp
        self.metadata.current_revision = revision_number
        self.metadata.last_model = model
        self.revision_history.append(
            RevisionEntry(
                revision_number=revision_number,
                created_at=timestamp,
                instruction=instruction,
                model=model,
                architecture_pack=architecture_pack,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "brief": self.brief.to_dict(),
            "latest_pack": self.latest_pack.to_dict(),
            "revision_history": [entry.to_dict() for entry in self.revision_history],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SavedProject":
        return cls(
            metadata=ProjectMetadata.from_dict(payload.get("metadata", {})),
            brief=ProjectBrief.from_dict(payload.get("brief", {})),
            latest_pack=ArchitecturePack.from_dict(payload.get("latest_pack", {})),
            revision_history=[
                RevisionEntry.from_dict(item)
                for item in payload.get("revision_history", [])
                if isinstance(item, dict)
            ],
        )
