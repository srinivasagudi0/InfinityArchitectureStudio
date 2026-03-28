from __future__ import annotations

import json

from .models import SavedProject


def saved_project_to_json(project: SavedProject) -> str:
    return json.dumps(project.to_dict(), indent=2)


def architecture_pack_to_markdown(project: SavedProject) -> str:
    lines = [
        f"# {project.metadata.project_name}",
        "",
        f"- Project ID: `{project.metadata.project_id}`",
        f"- Created: {project.metadata.created_at}",
        f"- Updated: {project.metadata.updated_at}",
        f"- Revision: {project.metadata.current_revision}",
        f"- Model: {project.metadata.last_model or 'Not recorded'}",
        "",
        "## Project Brief",
        "",
    ]

    for label, value in project.brief.display_rows():
        lines.extend(
            [
                f"### {label}",
                value,
                "",
            ]
        )

    lines.append("## Architecture Pack")
    lines.append("")

    for label, value in project.latest_pack.section_items():
        lines.extend(
            [
                f"### {label}",
                value,
                "",
            ]
        )

    if project.revision_history:
        lines.append("## Revision History")
        lines.append("")
        for entry in project.revision_history:
            lines.extend(
                [
                    f"### Revision {entry.revision_number}",
                    f"- Timestamp: {entry.created_at}",
                    f"- Model: {entry.model or 'Not recorded'}",
                    f"- Instruction: {entry.instruction}",
                    "",
                ]
            )

    return "\n".join(lines).strip() + "\n"
