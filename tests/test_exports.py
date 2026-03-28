from infinity_architecture_studio.exports import architecture_pack_to_markdown
from infinity_architecture_studio.models import ArchitecturePack, ProjectBrief, SavedProject


def test_markdown_export_contains_required_architecture_pack_sections():
    project = SavedProject.create(
        brief=ProjectBrief(
            project_name="Support Hub",
            problem_description="Customer support workspace.",
            core_goals="Handle tickets, escalations, and analytics.",
        ),
        architecture_pack=ArchitecturePack(
            executive_summary="Summary",
            recommended_stack="Stack",
            major_components="Components",
            high_level_data_flow="Flow",
            file_structure="Files",
            api_service_boundaries="APIs",
            implementation_roadmap="Roadmap",
            risks_open_questions="Risks",
        ),
        model="test-model",
    )

    markdown = architecture_pack_to_markdown(project)

    assert "# Support Hub" in markdown
    assert "## Architecture Pack" in markdown
    assert "### Executive Summary" in markdown
    assert "### Recommended Stack" in markdown
    assert "### Major Components and Responsibilities" in markdown
    assert "### High-Level Data Flow" in markdown
    assert "### File and Module Structure" in markdown
    assert "### API or Service Boundary Outline" in markdown
    assert "### Implementation Roadmap" in markdown
    assert "### Risks and Open Questions" in markdown
