from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from .config import AppConfig, load_config
from .models import ArchitecturePack, ProjectBrief
from .prompts import build_messages
from .result_shaping import parse_architecture_pack


class ConfigurationError(RuntimeError):
    """Raised when the local runtime config is incomplete."""


class ArchitectureGenerationError(RuntimeError):
    """Raised when the model call or response handling fails."""


@dataclass
class GenerationResult:
    architecture_pack: ArchitecturePack
    model: str
    raw_response: str


class ArchitectureGenerator:
    def __init__(
        self,
        config: AppConfig | None = None,
        client_factory=OpenAI,
    ) -> None:
        self.config = config or load_config()
        self._client_factory = client_factory

    def _build_client(self) -> OpenAI:
        if not self.config.openai_api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is not set. Add it to your environment before generating an architecture pack."
            )
        return self._client_factory(api_key=self.config.openai_api_key)

    def generate_architecture_pack(
        self,
        brief: ProjectBrief,
        previous_pack: ArchitecturePack | None = None,
        refinement_request: str | None = None,
    ) -> GenerationResult:
        client = self._build_client()
        messages = build_messages(
            brief=brief,
            previous_pack=previous_pack,
            refinement_request=refinement_request,
        )

        try:
            response = client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=self.config.openai_temperature,
                max_completion_tokens=self.config.openai_max_completion_tokens,
            )
        except Exception as exc:  # noqa: BLE001 - surface readable app errors
            raise ArchitectureGenerationError(
                f"OpenAI request failed: {exc}"
            ) from exc

        content = response.choices[0].message.content or ""
        if not content.strip():
            raise ArchitectureGenerationError("The model returned an empty response.")

        try:
            architecture_pack = parse_architecture_pack(content)
        except ValueError as exc:
            raise ArchitectureGenerationError(
                f"Could not parse the model output into an architecture pack: {exc}"
            ) from exc

        return GenerationResult(
            architecture_pack=architecture_pack,
            model=self.config.openai_model,
            raw_response=content,
        )
