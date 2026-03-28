from __future__ import annotations

import json

from .models import ArchitecturePack, PACK_SECTION_TITLES


def _extract_json_object(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Response did not contain a JSON object.")
    return cleaned[start : end + 1]


def parse_architecture_pack(text: str) -> ArchitecturePack:
    json_blob = _extract_json_object(text)
    try:
        payload = json.loads(json_blob)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Response was not valid JSON: {exc.msg}.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Response JSON must be an object.")

    missing = [field_name for field_name in PACK_SECTION_TITLES if field_name not in payload]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Response JSON is missing required fields: {missing_list}.")

    return ArchitecturePack.from_dict(payload)
