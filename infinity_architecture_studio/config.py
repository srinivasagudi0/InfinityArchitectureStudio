from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str | None
    openai_model: str
    openai_temperature: float
    openai_max_completion_tokens: int
    storage_dir: Path

    @property
    def has_api_key(self) -> bool:
        return bool(self.openai_api_key)


def _read_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid float.") from exc


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid integer.") from exc


def load_config() -> AppConfig:
    storage_dir = Path(os.getenv("INFINITY_STORAGE_DIR", "project_data"))
    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openai_temperature=_read_float("OPENAI_TEMPERATURE", 0.3),
        openai_max_completion_tokens=_read_int("OPENAI_MAX_OUTPUT_TOKENS", 1800),
        storage_dir=storage_dir,
    )
