from __future__ import annotations

from typing import Any

import streamlit as st

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from infinity_architecture_studio.ai_client import (
        ArchitectureGenerationError,
        ArchitectureGenerator,
        ConfigurationError,
    )
    from infinity_architecture_studio.config import load_config
    from infinity_architecture_studio.exports import architecture_pack_to_markdown, saved_project_to_json
    from infinity_architecture_studio.models import ArchitecturePack, ProjectBrief, SavedProject, utc_now_iso
    from infinity_architecture_studio.storage import ProjectStorage
    from infinity_architecture_studio.validation import validate_project_brief
else:
    from .ai_client import (
        ArchitectureGenerationError,
        ArchitectureGenerator,
        ConfigurationError,
    )
    from .config import load_config
    from .exports import architecture_pack_to_markdown, saved_project_to_json
    from .models import ArchitecturePack, ProjectBrief, SavedProject, utc_now_iso
    from .storage import ProjectStorage
    from .validation import validate_project_brief


BRIEF_WIDGET_KEYS = {
    "project_name": "brief_project_name",
    "problem_description": "brief_problem_description",
    "target_users": "brief_target_users",
    "core_goals": "brief_core_goals",
    "constraints": "brief_constraints",
    "preferred_stack": "brief_preferred_stack",
    "integrations": "brief_integrations",
    "non_functional_requirements": "brief_non_functional_requirements",
    "extra_notes": "brief_extra_notes",
}


def _blank_brief() -> ProjectBrief:
    return ProjectBrief(
        project_name="",
        problem_description="",
        target_users="",
        core_goals="",
        constraints="",
        preferred_stack="Python, FastAPI, Postgres, React, or your preferred stack",
        integrations="",
        non_functional_requirements="Security, scalability, observability, maintainability",
        extra_notes="",
    )


def _initialize_session() -> None:
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "status_message" not in st.session_state:
        st.session_state.status_message = ""
    if "status_level" not in st.session_state:
        st.session_state.status_level = "info"
    if "selected_project_id" not in st.session_state:
        st.session_state.selected_project_id = ""
    if "refinement_request" not in st.session_state:
        st.session_state.refinement_request = ""
    for field_name, key in BRIEF_WIDGET_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = getattr(_blank_brief(), field_name)


def _sync_brief_to_widgets(brief: ProjectBrief) -> None:
    for field_name, key in BRIEF_WIDGET_KEYS.items():
        st.session_state[key] = getattr(brief, field_name)


def _read_brief_from_widgets() -> ProjectBrief:
    return ProjectBrief(
        **{
            field_name: str(st.session_state.get(key, "") or "")
            for field_name, key in BRIEF_WIDGET_KEYS.items()
        }
    )


def _new_project() -> None:
    st.session_state.current_project = None
    st.session_state.status_message = "Started a new project draft."
    st.session_state.status_level = "info"
    st.session_state.refinement_request = ""
    _sync_brief_to_widgets(_blank_brief())


def _set_status(message: str, level: str = "info") -> None:
    st.session_state.status_message = message
    st.session_state.status_level = level


def _load_selected_project(storage: ProjectStorage) -> None:
    project_id = st.session_state.get("selected_project_id", "")
    if not project_id:
        _set_status("Select a saved project before trying to open it.", "warning")
        return
    try:
        project = storage.load_project(project_id)
    except FileNotFoundError as exc:
        _set_status(str(exc), "error")
        return
    st.session_state.current_project = project
    st.session_state.refinement_request = ""
    _sync_brief_to_widgets(project.brief)
    _set_status(f"Loaded project '{project.metadata.project_name}'.", "success")


def _render_status() -> None:
    message = st.session_state.get("status_message", "")
    if not message:
        return
    level = st.session_state.get("status_level", "info")
    status_renderer = getattr(st, level, st.info)
    status_renderer(message)


def _update_project_with_generation(
    generated_pack: ArchitecturePack,
    model: str,
    brief: ProjectBrief,
    instruction: str,
) -> SavedProject:
    current_project: SavedProject | None = st.session_state.current_project
    if current_project is None:
        project = SavedProject.create(
            brief=brief,
            architecture_pack=generated_pack,
            model=model,
            instruction=instruction,
        )
    else:
        current_project.brief = brief
        current_project.add_revision(
            architecture_pack=generated_pack,
            instruction=instruction,
            model=model,
        )
        project = current_project
    st.session_state.current_project = project
    return project


def _sync_project_brief_from_widgets() -> SavedProject | None:
    current_project: SavedProject | None = st.session_state.current_project
    if current_project is None:
        return None
    current_project.brief = _read_brief_from_widgets()
    current_project.metadata.project_name = (
        current_project.brief.project_name.strip()
        or current_project.metadata.project_name
        or "Untitled Project"
    )
    current_project.metadata.updated_at = utc_now_iso()
    return current_project


def _render_sidebar(storage: ProjectStorage, config_has_api_key: bool) -> None:
    with st.sidebar:
        st.header("Workspace")
        st.button("New Project", on_click=_new_project, use_container_width=True)

        projects = storage.list_projects()
        project_options = {project.metadata.project_id: project for project in projects}
        option_ids = [""] + list(project_options.keys())
        st.selectbox(
            "Saved Projects",
            options=option_ids,
            key="selected_project_id",
            format_func=lambda project_id: (
                "Select a saved project"
                if not project_id
                else f"{project_options[project_id].metadata.project_name} "
                f"(rev {project_options[project_id].metadata.current_revision})"
            ),
        )

        if st.button("Open Selected Project", use_container_width=True):
            _load_selected_project(storage)

        current_project: SavedProject | None = st.session_state.current_project
        if current_project is not None:
            st.divider()
            if st.button("Save Current Project", use_container_width=True):
                synced_project = _sync_project_brief_from_widgets() or current_project
                path = storage.save_project(synced_project)
                _set_status(f"Saved project to {path}.", "success")

            st.download_button(
                "Export Markdown",
                data=architecture_pack_to_markdown(current_project),
                file_name=f"{current_project.metadata.project_id}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                "Export JSON",
                data=saved_project_to_json(current_project),
                file_name=f"{current_project.metadata.project_id}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.divider()
        st.caption(
            "Generation is enabled."
            if config_has_api_key
            else "Set OPENAI_API_KEY to enable architecture generation."
        )


def _brief_inputs() -> None:
    st.text_input("Project Name", key=BRIEF_WIDGET_KEYS["project_name"], placeholder="Customer Support Platform")
    st.text_area(
        "Problem Description",
        key=BRIEF_WIDGET_KEYS["problem_description"],
        height=120,
        placeholder="Describe the product, business problem, and expected outcome.",
    )
    st.text_area(
        "Target Users",
        key=BRIEF_WIDGET_KEYS["target_users"],
        height=80,
        placeholder="Who will use this system and what do they need?",
    )
    st.text_area(
        "Core Goals",
        key=BRIEF_WIDGET_KEYS["core_goals"],
        height=100,
        placeholder="List the essential capabilities and delivery goals.",
    )
    st.text_area(
        "Constraints",
        key=BRIEF_WIDGET_KEYS["constraints"],
        height=80,
        placeholder="Budget, team size, deadlines, compliance, existing systems, or other constraints.",
    )
    st.text_area(
        "Preferred Stack or Libraries",
        key=BRIEF_WIDGET_KEYS["preferred_stack"],
        height=80,
    )
    st.text_area(
        "Integrations",
        key=BRIEF_WIDGET_KEYS["integrations"],
        height=80,
        placeholder="External APIs, data providers, auth providers, queues, storage, or vendor systems.",
    )
    st.text_area(
        "Non-Functional Requirements",
        key=BRIEF_WIDGET_KEYS["non_functional_requirements"],
        height=80,
    )
    st.text_area(
        "Extra Notes",
        key=BRIEF_WIDGET_KEYS["extra_notes"],
        height=100,
        placeholder="Any additional context, future scope, or preferences.",
    )


def _render_pack(pack: ArchitecturePack) -> None:
    tabs = st.tabs([label for label, _ in pack.section_items()])
    for tab, (_, value) in zip(tabs, pack.section_items()):
        with tab:
            st.markdown(value)


def _render_revision_history(project: SavedProject) -> None:
    if not project.revision_history:
        return
    with st.expander("Revision History", expanded=False):
        for entry in reversed(project.revision_history):
            st.markdown(
                "\n".join(
                    [
                        f"**Revision {entry.revision_number}**",
                        f"- Timestamp: {entry.created_at}",
                        f"- Model: {entry.model or 'Not recorded'}",
                        f"- Instruction: {entry.instruction}",
                    ]
                )
            )
            st.divider()


def _render_brief_summary(brief: ProjectBrief) -> None:
    with st.expander("Current Brief", expanded=False):
        for label, value in brief.display_rows():
            st.markdown(f"**{label}**")
            st.write(value)


def render_app() -> None:
    st.set_page_config(
        page_title="Infinity Architecture Studio",
        page_icon="🏗️",
        layout="wide",
    )
    _initialize_session()

    config = load_config()
    storage = ProjectStorage(config=config)
    _render_sidebar(storage=storage, config_has_api_key=config.has_api_key)

    st.title("Infinity Architecture Studio")
    st.caption("Guided software architecture planning with local save/load and export support.")

    if not config.has_api_key:
        st.warning(
            "OPENAI_API_KEY is not configured. You can still draft briefs, load saved projects, and review exports, "
            "but generation and refinement are disabled until the key is set."
        )

    _render_status()

    left_col, right_col = st.columns([1.1, 1.2], gap="large")
    with left_col:
        st.subheader("Project Brief")
        _brief_inputs()

        generate_disabled = not config.has_api_key
        if st.button("Generate Architecture Pack", type="primary", disabled=generate_disabled):
            brief = _read_brief_from_widgets()
            errors = validate_project_brief(brief)
            if errors:
                error_lines = "\n".join(f"- {message}" for message in errors.values())
                _set_status(f"Please fix the following issues before generating:\n{error_lines}", "error")
                st.rerun()

            generator = ArchitectureGenerator(config=config)
            try:
                with st.spinner("Generating architecture pack..."):
                    result = generator.generate_architecture_pack(brief=brief)
            except (ConfigurationError, ArchitectureGenerationError) as exc:
                _set_status(str(exc), "error")
                st.rerun()

            project = _update_project_with_generation(
                generated_pack=result.architecture_pack,
                model=result.model,
                brief=brief,
                instruction="Initial generation" if st.session_state.current_project is None else "Regenerated from brief",
            )
            _set_status(
                f"Generated architecture pack for '{project.metadata.project_name}'. Save it from the sidebar when ready.",
                "success",
            )
            st.rerun()

    with right_col:
        current_project: SavedProject | None = st.session_state.current_project
        st.subheader("Architecture Pack")
        if current_project is None:
            st.info("Complete the brief and generate an architecture pack to see results here.")
            return

        _render_pack(current_project.latest_pack)
        _render_brief_summary(current_project.brief)
        _render_revision_history(current_project)

        st.subheader("Refine Current Pack")
        st.text_area(
            "Refinement Request",
            key="refinement_request",
            height=100,
            placeholder="Ask for changes such as a different stack, stronger security posture, or a phased roadmap.",
        )
        refine_disabled = not config.has_api_key
        if st.button("Apply Refinement", disabled=refine_disabled):
            refinement_request = str(st.session_state.get("refinement_request", "") or "").strip()
            if not refinement_request:
                _set_status("Enter a refinement request before applying a revision.", "warning")
                st.rerun()

            brief = _read_brief_from_widgets()
            errors = validate_project_brief(brief)
            if errors:
                error_lines = "\n".join(f"- {message}" for message in errors.values())
                _set_status(f"Please fix the following issues before refining:\n{error_lines}", "error")
                st.rerun()

            generator = ArchitectureGenerator(config=config)
            try:
                with st.spinner("Refining architecture pack..."):
                    result = generator.generate_architecture_pack(
                        brief=brief,
                        previous_pack=current_project.latest_pack,
                        refinement_request=refinement_request,
                    )
            except (ConfigurationError, ArchitectureGenerationError) as exc:
                _set_status(str(exc), "error")
                st.rerun()

            project = _update_project_with_generation(
                generated_pack=result.architecture_pack,
                model=result.model,
                brief=brief,
                instruction=refinement_request,
            )
            st.session_state.refinement_request = ""
            _set_status(
                f"Applied refinement and created revision {project.metadata.current_revision}.",
                "success",
            )
            st.rerun()


if __name__ == "__main__":
    render_app()
