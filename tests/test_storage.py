from infinity_architecture_studio.models import ArchitecturePack, ProjectBrief, SavedProject
from infinity_architecture_studio.storage import ProjectStorage


def _sample_project() -> SavedProject:
    return SavedProject.create(
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


def test_save_load_roundtrip_preserves_project_state(tmp_path):
    storage = ProjectStorage(root_dir=tmp_path)
    project = _sample_project()

    storage.save_project(project)
    loaded = storage.load_project(project.metadata.project_id)

    assert loaded.to_dict() == project.to_dict()
