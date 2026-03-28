from infinity_architecture_studio.models import ProjectBrief
from infinity_architecture_studio.validation import validate_project_brief


def test_validate_project_brief_rejects_missing_required_fields():
    errors = validate_project_brief(ProjectBrief())

    assert errors == {
        "project_name": "Project Name is required.",
        "problem_description": "Problem Description is required.",
        "core_goals": "Core Goals is required.",
    }
