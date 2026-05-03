from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Local LLM (LM Studio)
    LLM_PROVIDER: str = "lmstudio"
    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_API_KEY: str = "lm-studio"
    LM_STUDIO_MODEL: Optional[str] = None

    # Gemini / Google
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_IMAGE_ENDPOINT: Optional[str] = None
    GEMINI_TEXT_MODEL: str = "gemini-2.5-flash"
    GEMINI_IMAGE_MODEL: str = "nano-banana"

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-001"
    OPENROUTER_REFERRER: Optional[str] = None
    OPENROUTER_TITLE: Optional[str] = "Internship Agent Dev"

    # TTS
    TTS_PROVIDER: str = "edge-tts"
    TTS_FALLBACK: Optional[str] = "elevenlabs"
    EDGE_TTS_VOICE: str = "en-US-AriaNeural"
    EDGE_TTS_LANGUAGE: str = "en-US"
    EDGE_TTS_OUTPUT_FORMAT: str = "audio-24khz-48kbitrate-mono-mp3"

    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = None
    ELEVENLABS_MODEL_ID: Optional[str] = "eleven_multilingual_v2"

    # Scene timing
    SCENE_MIN_DURATION_SECONDS: float = 1.0
    SCENE_GAP_SECONDS: float = 0.2

    # Image generation resilience
    IMAGE_RETRY_ATTEMPTS: int = 3
    USE_PLACEHOLDER_IMAGES: bool = True

    # Video layout + image aspect ratio
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    VIDEO_ASPECT_RATIO: str = "9:16"
    IMAGE_ASPECT_RATIO: Optional[str] = None
    IMAGE_SIZE: Optional[str] = None

    # Apify + Remotion + misc
    APIFY_API_TOKEN: Optional[str] = None
    APIFY_META_ADS_ACTOR_ID: Optional[str] = None
    APIFY_META_ADS_TARGET_URL: Optional[str] = None
    APIFY_META_ADS_COUNTRY: str = "US"
    APIFY_META_ADS_SEARCH_QUERY: str = "trading"
    APIFY_META_ADS_PAGE_ID: Optional[str] = None
    APIFY_META_ADS_AD_ID: Optional[str] = None
    APIFY_META_ADS_ACTIVE_STATUS: str = "active"
    APIFY_META_ADS_AD_TYPE: str = "all"
    APIFY_META_ADS_MEDIA_TYPE: str = "all"
    APIFY_META_ADS_IS_TARGETED_COUNTRY: bool = False
    APIFY_META_ADS_CONTENT_LANGUAGES: Optional[str] = None
    APIFY_META_ADS_SORT_MODE: str = "start_date"
    APIFY_META_ADS_SORT_DIRECTION: str = "desc"
    APIFY_META_ADS_MAX_CONCURRENCY: int = 1
    APIFY_META_ADS_REQUEST_HANDLER_TIMEOUT_SECS: int = 900
    APIFY_META_ADS_PROXY_URL: Optional[str] = None
    APIFY_META_ADS_MAX_AGE_DAYS: int = 30

    # Google Drive / Docs
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_DRIVE_FILE_ID: Optional[str] = None
    GOOGLE_DRIVE_SCOPES: str = "https://www.googleapis.com/auth/drive.readonly"

    REMOTION_APP_DIR: str = "remotion-app"
    REMOTION_ENTRY_POINT: str = "src/index.tsx"
    REMOTION_COMPOSITION_ID: str = "Video"
    RENDER_OUTPUT_DIR: str = "out"
    RUN_LOG_FILE: str = "run.log"


def parse_model_size_from_name(name: str) -> int:
    if not name:
        return 0
    m = re.search(r"(\d+)(b)\b", name.lower())
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 0
    m2 = re.search(r"(\d+)b", name.lower())
    if m2:
        try:
            return int(m2.group(1))
        except Exception:
            return 0
    return 0


def parse_model_size_from_spec(spec: Dict[str, Any]) -> int:
    if not isinstance(spec, dict):
        return 0
    for key in ("parameter_count", "param_count", "params", "num_parameters", "size"):
        val = spec.get(key)
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
    return 0


def autodetect_lmstudio_model(settings: Settings) -> Optional[str]:
    """Try to query the LM Studio `/models` endpoint and pick the model
    that appears to have the largest parameter size. Returns the model id/name
    or None if detection failed.
    """
    base = settings.LM_STUDIO_BASE_URL.rstrip("/")
    url = f"{base}/models"
    headers = {}
    if settings.LM_STUDIO_API_KEY and settings.LM_STUDIO_API_KEY != "lm-studio":
        headers["Authorization"] = f"Bearer {settings.LM_STUDIO_API_KEY}"
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models: List[Any] = []
        if isinstance(data, dict):
            for key in ("data", "models", "model_specs", "model_list"):
                if key in data and isinstance(data[key], list):
                    models = data[key]
                    break
            if not models:
                # try to collect dict values that look like model specs
                for v in data.values():
                    if isinstance(v, dict) and ("id" in v or "name" in v):
                        models.append(v)
        elif isinstance(data, list):
            models = data

        best_name = None
        best_size = -1
        for m in models:
            if isinstance(m, str):
                name = m
                size = parse_model_size_from_name(name)
            elif isinstance(m, dict):
                name = m.get("id") or m.get("name") or m.get("model")
                size = parse_model_size_from_spec(m)
                if size == 0:
                    size = parse_model_size_from_name(name or "")
            else:
                continue
            if size > best_size:
                best_size = size
                best_name = name
        return best_name
    except Exception:
        return None


@lru_cache(maxsize=2)
def get_settings(auto_detect_lmstudio_model: bool = False) -> Settings:
    s = Settings()
    # Autodetect only when explicitly requested to avoid network calls at import time.
    if auto_detect_lmstudio_model and (
        not s.LM_STUDIO_MODEL or (isinstance(s.LM_STUDIO_MODEL, str) and s.LM_STUDIO_MODEL.lower() == "auto")
    ):
        detected = autodetect_lmstudio_model(s)
        if detected:
            s.LM_STUDIO_MODEL = detected
    return s


if __name__ == "__main__":
    s = get_settings(auto_detect_lmstudio_model=True)
    from logger import get_logger

    logger = get_logger(__name__, log_file=s.RUN_LOG_FILE)
    logger.info("LM_STUDIO_MODEL: %s", s.LM_STUDIO_MODEL)