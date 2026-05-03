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
    """Get the duration of an audio file in seconds using mutagen."""
    if not audio_path or not os.path.exists(audio_path):
        return None
        
    try:
        # Try as MP3 first
        if audio_path.lower().endswith(".mp3"):
            from mutagen.mp3 import MP3
            audio = MP3(audio_path)
            if audio.info and audio.info.length:
                return float(audio.info.length)
        
        # Fallback to general file detection
        from mutagen import File
        audio = File(audio_path)
        if audio is not None and audio.info and hasattr(audio.info, "length"):
            return float(audio.info.length)
    except Exception as e:
        print(f"Error reading audio duration for {audio_path}: {e}")
        
    return None


def _create_placeholder_image(scene_idx: int, prompt: str, out_dir: str, width: int, height: int) -> Optional[str]:
    """Create a high-quality placeholder image if all generation providers fail."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except Exception:
        # If PIL is missing, we can't do much but return None or a 1x1 dummy
        return None

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"scene{scene_idx}_placeholder.png")
    
    try:
        # Create a nice gradient background (dark blue/slate)
        base_color = (15, 23, 42)  # Slate 900
        secondary_color = (30, 41, 59) # Slate 800
        
        image = Image.new("RGB", (width, height), color=base_color)
        draw = ImageDraw.Draw(image)
        
        # Simple vertical gradient
        for y in range(height):
            r = int(base_color[0] + (secondary_color[0] - base_color[0]) * y / height)
            g = int(base_color[1] + (secondary_color[1] - base_color[1]) * y / height)
            b = int(base_color[2] + (secondary_color[2] - base_color[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Try to load a font, fall back to default
        font_large = None
        font_small = None
        try:
            # Common paths for fonts on Windows/Linux
            font_paths = [
                "C:\\Windows\\Fonts\\arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/TTF/DejaVuSans.ttf"
            ]
            for p in font_paths:
                if os.path.exists(p):
                    font_large = ImageFont.truetype(p, 60)
                    font_small = ImageFont.truetype(p, 30)
                    break
        except Exception:
            pass
        
        if not font_large:
            font_large = ImageFont.load_default()
        if not font_small:
            font_small = ImageFont.load_default()

        # Add some 'technical' lines for a structured look
        draw.rectangle([20, 20, width - 20, height - 20], outline=(51, 65, 85), width=2)
        draw.line([20, 120, width - 20, 120], fill=(51, 65, 85), width=1)

        title = f"SCENE {scene_idx} - PLACEHOLDER"
        draw.text((50, 50), title, fill=(248, 250, 252), font=font_large)

        # Wrap prompt text
        prompt_text = (prompt or "").encode("ascii", "ignore").decode().strip()
        margin = 60
        max_width = width - (margin * 2)
        
        words = prompt_text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            # getbbox is modern, textsize is legacy
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), test_line, font=font_small)
                w = bbox[2] - bbox[0]
            else:
                w, _ = draw.textsize(test_line, font=font_small)
            
            if w <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        y_offset = 160
        for line in lines[:15]: # Limit to 15 lines
            draw.text((margin, y_offset), line, fill=(148, 163, 184), font=font_small)
            y_offset += 45

        # Final footer
        footer = "Generation failed. Using fallback asset."
        draw.text((50, height - 80), footer, fill=(100, 116, 139), font=font_small)

        image.save(out_path, format="PNG")
        return out_path
    except Exception:
        # Last resort: simple solid color image
        try:
            image = Image.new("RGB", (width, height), color=(15, 23, 42))
            image.save(out_path, format="PNG")
            return out_path
        except Exception:
            return None


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
    gap_seconds = max(0.5, float(settings.SCENE_GAP_SECONDS))
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
        audio_path, scene_subtitles = synthesize(narration, audio_path)
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
                "subtitles": scene_subtitles,
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

    total_duration = current_time
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
        "total_duration": total_duration,
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
