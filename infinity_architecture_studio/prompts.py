from __future__ import annotations

import json

from .models import ArchitecturePack, ProjectBrief


SYSTEM_PROMPT = """You are Infinity Architecture Studio, an expert software architect.
Design modern, implementation-ready software systems from structured briefs.
Return only valid JSON with exactly these keys:
- executive_summary
- recommended_stack
- major_components
- high_level_data_flow
- file_structure
- api_service_boundaries
- implementation_roadmap
- risks_open_questions

Requirements:
- Stay within software/system architecture. Do not switch to building or physical architecture.
- Be concrete about components, boundaries, storage, and delivery sequence.
- Prefer bullet-friendly prose and short subsections inside each string value.
- Include tradeoffs and assumptions where useful.
- Do not wrap the JSON in markdown fences.
"""


def _format_brief(brief: ProjectBrief) -> str:
    rows = [f"{label}: {value}" for label, value in brief.display_rows()]
    return "\n".join(rows)


def _format_pack(pack: ArchitecturePack) -> str:
    rows = [f"{label}: {value}" for label, value in pack.section_items()]
    return "\n".join(rows)


def build_user_prompt(
    brief: ProjectBrief,
    previous_pack: ArchitecturePack | None = None,
    refinement_request: str | None = None,
) -> str:
    prompt_parts = [
        "Create a complete architecture pack from the following project brief.",
        "",
        "Project Brief",
        _format_brief(brief),
        "",
        "Output contract",
        (
            "Return a JSON object whose values are detailed strings. "
            "Each value should be implementation-ready and specific."
        ),
    ]

    if previous_pack is not None:
        prompt_parts.extend(
            [
                "",
                "Previous Architecture Pack",
                _format_pack(previous_pack),
            ]
        )

    if refinement_request:
        prompt_parts.extend(
            [
                "",
                "Refinement Request",
                refinement_request.strip(),
                "Update the architecture pack accordingly while keeping the full pack coherent.",
            ]
        )

    return "\n".join(prompt_parts)


def build_messages(
    brief: ProjectBrief,
    previous_pack: ArchitecturePack | None = None,
    refinement_request: str | None = None,
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(
                brief=brief,
                previous_pack=previous_pack,
                refinement_request=refinement_request,
            ),
        },
    ]


def format_pack_contract_example() -> str:
    return json.dumps(
        {
            "executive_summary": "...",
            "recommended_stack": "...",
            "major_components": "...",
            "high_level_data_flow": "...",
            "file_structure": "...",
            "api_service_boundaries": "...",
            "implementation_roadmap": "...",
            "risks_open_questions": "...",
        },
        indent=2,
    )
