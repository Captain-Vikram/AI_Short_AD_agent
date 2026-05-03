"""TTS helper with Edge TTS (default) and ElevenLabs fallback.

Usage:
    from src.media.tts import synthesize
    synthesize("Hello world", "out.mp3")
"""
from __future__ import annotations

import asyncio
import os
from typing import Optional

from config.settings import get_settings
from src.utils import get_logger
from src.utils import retry_with_backoff

@retry_with_backoff(
    max_retries=3,
    initial_backoff=2.0,
    logger_name="tts",
)
def synthesize_edge(text: str, out_path: str, voice: Optional[str] = None) -> None:
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    voice = voice or settings.EDGE_TTS_VOICE
    try:
        import edge_tts
    except Exception as exc:  # pragma: no cover - runtime import
        raise RuntimeError("edge-tts is not installed") from exc

    communicate = edge_tts.Communicate(text, voice)
    asyncio.run(communicate.save(out_path))
    logger.info("TTS: saved Edge audio to %s", out_path)


@retry_with_backoff(
    max_retries=3,
    initial_backoff=5.0,
    logger_name="tts",
)
def synthesize_elevenlabs(text: str, out_path: str, voice: Optional[str] = None, model: Optional[str] = None) -> None:
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    try:
        from elevenlabs import set_api_key, generate, save
    except Exception as exc:  # pragma: no cover - runtime import
        raise RuntimeError("elevenlabs package not available") from exc

    if not settings.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not configured")
    set_api_key(settings.ELEVENLABS_API_KEY)
    voice = voice or settings.ELEVENLABS_VOICE_ID
    model = model or settings.ELEVENLABS_MODEL_ID
    audio = generate(text=text, voice=voice, model=model)
    save(audio, out_path)
    logger.info("TTS: saved ElevenLabs audio to %s", out_path)


def synthesize(text: str, out_path: str) -> str:
    """Pick the configured TTS provider and synthesize audio to `out_path`.

    Falls back to `ELEVENLABS` when Edge fails and `TTS_FALLBACK` includes it.
    """
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    primary = settings.TTS_PROVIDER or "edge-tts"
    logger.info("TTS: using primary provider %s", primary)
    try:
        if primary == "edge-tts":
            synthesize_edge(text, out_path)
            return out_path
        if primary == "elevenlabs":
            synthesize_elevenlabs(text, out_path)
            return out_path
    except Exception:
        # try fallback
        if settings.TTS_FALLBACK and "elevenlabs" in (settings.TTS_FALLBACK or "") and settings.ELEVENLABS_API_KEY:
            logger.warning("TTS: primary provider failed, falling back to ElevenLabs")
            synthesize_elevenlabs(text, out_path)
            return out_path
        raise

    return out_path


if __name__ == "__main__":
    # quick smoke
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    logger.info("TTS helper loaded; primary=%s", settings.TTS_PROVIDER)