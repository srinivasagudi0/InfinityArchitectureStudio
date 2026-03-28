from infinity_architecture_studio.models import ArchitecturePack, ProjectBrief
from infinity_architecture_studio.prompts import build_user_prompt


def test_prompt_builder_includes_brief_and_refinement_context():
    brief = ProjectBrief(
        project_name="Support Hub",
        problem_description="Customer support workspace for internal agents.",
        target_users="Support agents and operations managers",
        core_goals="Unify ticket handling, reporting, and escalation flows.",
        constraints="Team of 3 engineers, 8 week MVP",
        preferred_stack="FastAPI, React, Postgres",
        integrations="Zendesk, Slack, Okta",
        non_functional_requirements="Auditability, reliability, role-based access",
        extra_notes="Needs clean handoff from MVP to v2 analytics work.",
    )
    previous_pack = ArchitecturePack(
        executive_summary="Previous summary",
        recommended_stack="Previous stack",
        major_components="Previous components",
        high_level_data_flow="Previous flow",
        file_structure="Previous files",
        api_service_boundaries="Previous APIs",
        implementation_roadmap="Previous roadmap",
        risks_open_questions="Previous risks",
    )

    prompt = build_user_prompt(
        brief=brief,
        previous_pack=previous_pack,
        refinement_request="Prioritize SSO and stricter audit logging.",
    )

    assert "Support Hub" in prompt
    assert "Customer support workspace for internal agents." in prompt
    assert "FastAPI, React, Postgres" in prompt
    assert "Zendesk, Slack, Okta" in prompt
    assert "Previous Architecture Pack" in prompt
    assert "Previous summary" in prompt
    assert "Refinement Request" in prompt
    assert "Prioritize SSO and stricter audit logging." in prompt
