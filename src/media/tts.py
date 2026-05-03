"""TTS helper with ElevenLabs (default) and Edge TTS fallback.

Usage:
    from src.media.tts import synthesize
    synthesize("Hello world", "out.mp3")
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional, Tuple

from config.settings import get_settings
from src.utils import get_logger
from src.utils import retry_with_backoff

@retry_with_backoff(
    max_retries=3,
    initial_backoff=2.0,
    logger_name="tts",
)
def synthesize_edge(text: str, out_path: str, voice: Optional[str] = None) -> List[Dict[str, Any]]:
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    voice = voice or settings.EDGE_TTS_VOICE
    try:
        import edge_tts
    except Exception as exc:  # pragma: no cover - runtime import
        raise RuntimeError("edge-tts is not installed") from exc

    subtitles: List[Dict[str, Any]] = []

    async def _amain() -> None:
        communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
        with open(out_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    subtitles.append({
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,
                        "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                    })

    asyncio.run(_amain())
    logger.info("TTS: saved Edge audio to %s with %d word boundaries", out_path, len(subtitles))
    return subtitles


@retry_with_backoff(
    max_retries=3,
    initial_backoff=5.0,
    logger_name="tts",
)
def synthesize_elevenlabs(text: str, out_path: str, voice: Optional[str] = None, model: Optional[str] = None) -> List[Dict[str, Any]]:
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
    # ElevenLabs Python library doesn't easily expose word-level timestamps in the basic 'generate' call.
    # We return empty list for now to avoid breaking the contract.
    return []


def synthesize(text: str, out_path: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Pick the configured TTS provider and synthesize audio to `out_path`.

    Returns:
        Tuple of (audio_path, list of word-level subtitles)
    """
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    primary = settings.TTS_PROVIDER or "elevenlabs"
    fallback = settings.TTS_FALLBACK
    logger.info("TTS: using primary provider %s", primary)

    def _call_provider(provider: str) -> List[Dict[str, Any]]:
        if provider == "edge-tts":
            return synthesize_edge(text, out_path)
        if provider == "elevenlabs":
            return synthesize_elevenlabs(text, out_path)
        raise ValueError(f"Unknown TTS provider: {provider}")

    try:
        subs = _call_provider(primary)
        return out_path, subs
    except Exception as e:
        if fallback and fallback != primary:
            logger.warning("TTS: primary provider %s failed (%s), falling back to %s", primary, e, fallback)
            try:
                subs = _call_provider(fallback)
                return out_path, subs
            except Exception as fe:
                logger.error("TTS: fallback provider %s also failed: %s", fallback, fe)
        raise

    return out_path, []



if __name__ == "__main__":
    # quick smoke
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    logger.info("TTS helper loaded; primary=%s", settings.TTS_PROVIDER)