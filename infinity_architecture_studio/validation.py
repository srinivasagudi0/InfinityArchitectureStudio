from __future__ import annotations

from .models import ProjectBrief


REQUIRED_BRIEF_FIELDS = {
    "project_name": "Project Name",
    "problem_description": "Problem Description",
    "core_goals": "Core Goals",
}


def validate_project_brief(brief: ProjectBrief) -> dict[str, str]:
    errors: dict[str, str] = {}
    for field_name, label in REQUIRED_BRIEF_FIELDS.items():
        value = getattr(brief, field_name, "")
        if not str(value).strip():
            errors[field_name] = f"{label} is required."
    return errors
