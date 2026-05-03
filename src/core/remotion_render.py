"""Remotion render bridge for the Python pipeline."""
from __future__ import annotations

import json
import shutil
import subprocess
import os
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import get_settings
from src.utils import get_logger, log_json


def _resolve_asset_path(asset_path: str, base_dir: Path) -> Path:
    path = Path(asset_path)
    if not path.is_absolute():
        return base_dir / path
    return path


def _resolve_npx_executable() -> str:
    if os.name == "nt":
        for name in ("npx.cmd", "npx"):
            resolved = shutil.which(name)
            if resolved:
                return resolved
    resolved = shutil.which("npx")
    if resolved:
        return resolved
    raise RuntimeError("npx not found on PATH. Install Node.js (includes npm/npx) and reopen the terminal.")


def _resolve_remotion_executable(app_dir: Path) -> tuple[str, bool]:
    bin_dir = app_dir / "node_modules" / ".bin"
    if os.name == "nt":
        candidates = ["remotion.cmd", "remotion"]
    else:
        candidates = ["remotion"]

    for name in candidates:
        candidate = bin_dir / name
        if candidate.exists():
            return str(candidate), False

    return _resolve_npx_executable(), True


def prepare_remotion_assets(
    remotion_app_dir: str | Path,
    remotion_props_path: str | Path = "remotion_props.json",
    output_props_path: Optional[str | Path] = None,
    design_path: Optional[str | Path] = None,
) -> str:
    """Copy assets into the Remotion public folder and normalize props."""
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)

    app_dir = Path(remotion_app_dir).resolve()
    props_path = Path(remotion_props_path)
    props_base = props_path.parent

    if not app_dir.exists():
        raise FileNotFoundError(f"Remotion app directory not found: {app_dir}")
    if not props_path.exists():
        raise FileNotFoundError(f"Remotion props file not found: {props_path}")

    public_assets_dir = app_dir / "public" / "assets"
    images_dir = public_assets_dir / "images"
    audio_dir = public_assets_dir / "audio"
    images_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    with props_path.open("r", encoding="utf-8") as handle:
        props: Dict[str, Any] = json.load(handle)

    if design_path:
        design_file = Path(design_path)
        if not design_file.is_absolute():
            design_file = props_base / design_file
        if design_file.exists():
            with design_file.open("r", encoding="utf-8") as handle:
                design = json.load(handle)
            props["design"] = design
        else:
            logger.warning("Remotion: design file not found: %s", design_file)

    scenes = props.get("scenes", [])
    for scene in scenes:
        image = scene.get("image")
        if image:
            image_path = _resolve_asset_path(str(image), props_base)
            if image_path.exists():
                dest = images_dir / image_path.name
                shutil.copy2(image_path, dest)
                scene["image"] = f"assets/images/{image_path.name}"
            else:
                logger.warning("Remotion: image missing for scene %s: %s", scene.get("scene"), image_path)
                scene["image"] = None

        audio = scene.get("audio")
        if audio:
            audio_path = _resolve_asset_path(str(audio), props_base)
            if audio_path.exists():
                dest = audio_dir / audio_path.name
                shutil.copy2(audio_path, dest)
                scene["audio"] = f"assets/audio/{audio_path.name}"
            else:
                logger.warning("Remotion: audio missing for scene %s: %s", scene.get("scene"), audio_path)
                scene["audio"] = None

    props["scenes"] = scenes
    log_json(logger, "Remotion: normalized props", props)

    output_path = Path(output_props_path) if output_props_path else (app_dir / "remotion_props.json")
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(props, handle, ensure_ascii=False, indent=2)

    logger.info("Remotion: wrote normalized props to %s", output_path)
    return str(output_path)


def render_video(
    remotion_props_path: str = "remotion_props.json",
    design_path: Optional[str] = None,
    remotion_app_dir: Optional[str] = None,
    entry_point: Optional[str] = None,
    composition_id: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Render a video using Remotion CLI and return the output path."""
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)

    app_dir = Path(remotion_app_dir or settings.REMOTION_APP_DIR).resolve()
    entry = entry_point or settings.REMOTION_ENTRY_POINT
    composition = composition_id or settings.REMOTION_COMPOSITION_ID

    if not app_dir.exists():
        raise FileNotFoundError(f"Remotion app directory not found: {app_dir}")

    output_dir = app_dir / settings.RENDER_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_output = Path(output_path) if output_path else (output_dir / "video.mp4")

    normalized_props = prepare_remotion_assets(
        app_dir,
        remotion_props_path,
        app_dir / "remotion_props.json",
        design_path=design_path,
    )

    remotion_exe, use_npx = _resolve_remotion_executable(app_dir)
    output_arg = str(resolved_output)
    props_arg = str(normalized_props)
    if Path(output_arg).is_absolute() and str(resolved_output).startswith(str(app_dir)):
        output_arg = str(Path(output_arg).relative_to(app_dir))
    if Path(props_arg).is_absolute() and str(normalized_props).startswith(str(app_dir)):
        props_arg = str(Path(props_arg).relative_to(app_dir))

    cmd = [remotion_exe]
    if use_npx:
        cmd.append("remotion")
    cmd.extend(
        [
            "render",
            entry,
            composition,
            output_arg,
            "--props",
            props_arg,
        ]
    )

    logger.info("Remotion: running %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(app_dir))
    logger.info("Remotion: render complete -> %s", resolved_output)
    return str(resolved_output)


__all__ = ["prepare_remotion_assets", "render_video"]
