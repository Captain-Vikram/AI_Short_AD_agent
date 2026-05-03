"""Asset assembly boundary for the media pipeline."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from config.settings import get_settings
from src.utils import get_logger, log_json
from src.core.script_validator import load_script
from src.media.gemini_image import generate_image
from src.media.tts import synthesize


def _estimate_duration_seconds(narration: str) -> float:
    words = len(narration.split())
    return max(1.0, words / 3.0)


def _audio_duration_seconds(audio_path: str) -> Optional[float]:
    try:
        from mutagen import File  # type: ignore
    except Exception:
        return None

    try:
        audio = File(audio_path)
        if audio and getattr(audio, "info", None) and getattr(audio.info, "length", None):
            length = float(audio.info.length)
            if length > 0:
                return length
    except Exception:
        return None

    return None


def _create_placeholder_image(scene_idx: int, prompt: str, out_dir: str, width: int, height: int) -> Optional[str]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    os.makedirs(out_dir, exist_ok=True)
    image = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    title = f"Scene {scene_idx}"
    prompt_text = (prompt or "").encode("ascii", "ignore").decode().strip()
    if len(prompt_text) > 160:
        prompt_text = prompt_text[:157] + "..."

    draw.text((40, 40), title, fill=(248, 250, 252), font=font)
    draw.text((40, 90), prompt_text, fill=(226, 232, 240), font=font)

    out_path = os.path.join(out_dir, f"scene{scene_idx}_placeholder.png")
    image.save(out_path, format="PNG")
    return out_path


def _format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds * 1000) % 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


def _generate_srt(scenes: List[Dict[str, Any]], out_path: str) -> str:
    lines = []
    for i, scene in enumerate(scenes, 1):
        start = scene["start"]
        end = start + scene["duration"]
        text = scene["narration"].strip()
        lines.append(f"{i}")
        lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
        lines.append(text)
        lines.append("")
    content = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def build_remotion_props(script_path: str = "script.json", assets_dir: str = "assets", remotion_props_path: str = "remotion_props.json") -> str:
    """Create image/audio assets from a validated script and write Remotion props."""
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)

    logger.info("Director: loading validated script from %s", script_path)
    script = load_script(script_path)

    os.makedirs(assets_dir, exist_ok=True)
    images_dir = os.path.join(assets_dir, "images")
    audio_dir = os.path.join(assets_dir, "audio")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    scenes_out: List[Dict[str, Any]] = []
    current_time = 0.0
    missing_images: List[int] = []
    placeholder_images: List[int] = []
    missing_audio: List[int] = []
    gap_seconds = max(0.0, float(settings.SCENE_GAP_SECONDS))
    min_duration = max(0.1, float(settings.SCENE_MIN_DURATION_SECONDS))
    retry_attempts = max(1, int(settings.IMAGE_RETRY_ATTEMPTS))
    video_width = max(1, int(settings.VIDEO_WIDTH))
    video_height = max(1, int(settings.VIDEO_HEIGHT))
    image_aspect_ratio = settings.IMAGE_ASPECT_RATIO or settings.VIDEO_ASPECT_RATIO
    image_size = settings.IMAGE_SIZE

    for entry in script:
        scene_idx = int(entry["scene"])
        narration = entry["narration"]
        image_prompt = entry["image_prompt"]

        logger.info("Director: generating scene %s assets", scene_idx)
        images: List[str] = []
        for attempt in range(1, retry_attempts + 1):
            image_file = generate_image(
                image_prompt,
                out_dir=str(images_dir),
                filename_prefix=f"scene{scene_idx}",
                aspect_ratio=image_aspect_ratio,
                image_size=image_size,
            )
            if image_file:
                images = [image_file]
            if images:
                break
            logger.warning("Director: image attempt %s/%s failed for scene %s", attempt, retry_attempts, scene_idx)

        image_path = images[0] if images else None
        if not images:
            missing_images.append(scene_idx)
            logger.warning("Director: no image generated for scene %s (prompt=%s)", scene_idx, image_prompt)
            if settings.USE_PLACEHOLDER_IMAGES:
                placeholder = _create_placeholder_image(scene_idx, image_prompt, images_dir, video_width, video_height)
                if placeholder:
                    image_path = placeholder
                    placeholder_images.append(scene_idx)
                    logger.info("Director: placeholder image created for scene %s", scene_idx)

        audio_path = os.path.join(audio_dir, f"scene_{scene_idx}.mp3")
        synthesize(narration, audio_path)
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            missing_audio.append(scene_idx)
            logger.warning("Director: audio missing/empty for scene %s at %s", scene_idx, audio_path)

        audio_duration = _audio_duration_seconds(audio_path)
        if audio_duration is None:
            logger.warning("Director: audio duration unavailable for scene %s; install mutagen for accurate timing", scene_idx)
        duration = audio_duration or _estimate_duration_seconds(narration)
        duration = max(min_duration, duration)
        scenes_out.append(
            {
                "scene": scene_idx,
                "image": image_path,
                "audio": audio_path,
                "narration": narration,
                "start": current_time,
                "duration": duration,
                "audio_duration": audio_duration,
                "image_prompt": image_prompt,
            }
        )
        current_time += duration + gap_seconds

    asset_report = {
        "total_scenes": len(scenes_out),
        "missing_images": missing_images,
        "placeholder_images": placeholder_images,
        "missing_audio": missing_audio,
        "images_generated": len(scenes_out) - len(missing_images),
        "audio_generated": len(scenes_out) - len(missing_audio),
        "gap_seconds": gap_seconds,
        "min_duration_seconds": min_duration,
        "image_retry_attempts": retry_attempts,
        "video_width": video_width,
        "video_height": video_height,
        "video_aspect_ratio": settings.VIDEO_ASPECT_RATIO,
        "image_aspect_ratio": image_aspect_ratio,
        "image_size": image_size,
    }

    video_config = {
        "width": video_width,
        "height": video_height,
        "aspect_ratio": settings.VIDEO_ASPECT_RATIO,
    }
    srt_path = os.path.join(assets_dir, "subtitles.srt")
    _generate_srt(scenes_out, srt_path)
    logger.info("Director: generated subtitles at %s", srt_path)

    remotion_props = {
        "scenes": scenes_out,
        "total_duration": current_time,
        "video": video_config,
        "asset_report": asset_report,
        "subtitles": srt_path,
    }
    log_json(logger, "Director: remotion props", remotion_props)
    log_json(logger, "Director: asset report", asset_report)
    report_path = os.path.join(assets_dir, "asset_report.json")
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(asset_report, handle, ensure_ascii=False, indent=2)
    logger.info("Director: wrote asset report to %s", report_path)
    with open(remotion_props_path, "w", encoding="utf-8") as handle:
        json.dump(remotion_props, handle, ensure_ascii=False, indent=2)

    logger.info("Director: wrote remotion props to %s", remotion_props_path)
    return remotion_props_path


__all__ = ["build_remotion_props"]
