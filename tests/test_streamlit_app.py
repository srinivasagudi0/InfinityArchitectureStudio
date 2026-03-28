from __future__ import annotations

from streamlit.testing.v1 import AppTest

from infinity_architecture_studio.models import ArchitecturePack, ProjectBrief, SavedProject
from infinity_architecture_studio.storage import ProjectStorage


def _button_by_label(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def _text_area_by_label(app: AppTest, label: str):
    return next(text_area for text_area in app.text_area if text_area.label == label)


def _sample_saved_project() -> SavedProject:
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


def test_streamlit_app_starts_and_shows_missing_api_key_warning(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("INFINITY_STORAGE_DIR", str(tmp_path))

    app = AppTest.from_file("streamlit_app.py")
    app.run()

    assert app.title[0].value == "Infinity Architecture Studio"
    assert any(
        "OPENAI_API_KEY is not configured" in warning.value
        for warning in app.warning
    )


def test_saved_project_reload_repopulates_form_and_results(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("INFINITY_STORAGE_DIR", str(tmp_path))

    storage = ProjectStorage(root_dir=tmp_path)
    project = _sample_saved_project()
    storage.save_project(project)

    app = AppTest.from_file("streamlit_app.py")
    app.run()
    app.selectbox[0].set_value(project.metadata.project_id)
    _button_by_label(app, "Open Selected Project").click()
    app.run()

    assert app.text_input[0].value == "Support Hub"
    assert _text_area_by_label(app, "Problem Description").value == "Customer support workspace."
    assert any(tab.label == "Executive Summary" for tab in app.tabs)
    assert any(markdown.value == "Summary" for markdown in app.markdown)
