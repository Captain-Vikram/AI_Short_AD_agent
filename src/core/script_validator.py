"""Strict schema helpers for Agent 3 script output.

Agent 3 must produce a JSON array of scene objects. These helpers normalize and
validate that output before it reaches the media pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from pydantic import BaseModel, Field, ValidationError, field_validator


class SceneSpec(BaseModel):
    scene: int = Field(ge=1)
    narration: str = Field(min_length=1)
    image_prompt: str = Field(min_length=1)

    @field_validator("narration", "image_prompt")
    @classmethod
    def _strip_nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be empty")
        return cleaned


class ScriptSpec(BaseModel):
    scenes: List[SceneSpec]


def validate_scene_list(payload: Any) -> List[dict]:
    """Validate and normalize a scene list payload.

    Accepts a raw list or a dict with `scenes`/`items`.
    Returns a list of plain dicts sorted by scene number.
    """
    if isinstance(payload, dict):
        if isinstance(payload.get("scenes"), list):
            payload = payload["scenes"]
        elif isinstance(payload.get("items"), list):
            payload = payload["items"]
        else:
            raise ValueError("Expected a list of scenes or a dict containing 'scenes'")

    if not isinstance(payload, list):
        raise ValueError("Script payload must be a list of scenes")

    scenes = [SceneSpec.model_validate(item) for item in payload]
    scenes = sorted(scenes, key=lambda scene: scene.scene)

    seen = set()
    for scene in scenes:
        if scene.scene in seen:
            raise ValueError(f"Duplicate scene number: {scene.scene}")
        seen.add(scene.scene)

    return [scene.model_dump() for scene in scenes]


def load_script(path: str | Path) -> List[dict]:
    """Load and validate a JSON script from disk."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return validate_scene_list(payload)


def dump_script(script: List[dict], path: str | Path) -> str:
    """Write a validated scene list to disk."""
    validated = validate_scene_list(script)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(validated, handle, ensure_ascii=False, indent=2)
    return str(path)


__all__ = ["SceneSpec", "ScriptSpec", "validate_scene_list", "load_script", "dump_script", "ValidationError"]
