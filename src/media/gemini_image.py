"""Helpers for generating images with Gemini (Nano Banana) models.

This module prefers the official `google.genai` SDK when available but falls
back to a best-effort HTTP call that mirrors the SDK's structure. It tries to
handle the common response shapes documented in the Gemini Image Generation
docs (inline_data with base64 image parts).
"""
from __future__ import annotations

import base64
import os
import re
from typing import List, Optional, Tuple

import httpx

from config.settings import get_settings
from src.utils import get_logger
from src.utils import retry_with_backoff

try:
    from google import genai
    from google.genai import types
    HAVE_GENAI = True
except Exception:
    HAVE_GENAI = False


def _save_base64(b64: str, out_path: str) -> None:
    data = base64.b64decode(b64)
    with open(out_path, "wb") as f:
        f.write(data)


@retry_with_backoff(
    max_retries=3,
    initial_backoff=2.0,
    status_codes=[429, 500, 502, 503, 504],
    exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
    logger_name="gemini_image",
)
def expand_prompt(prompt: str) -> str:
    """Use Gemini text model to expand the image prompt for better quality."""
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    if not settings.GEMINI_API_KEY:
        return prompt

    if HAVE_GENAI:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            instruction = (
                "You are an expert prompt engineer for AI image generation. "
                "Expand the following short prompt into a detailed, high-quality description for an image generator. "
                "Include details about lighting, style, composition, and mood. "
                "Keep the core subject the same. Output ONLY the expanded prompt text."
            )
            response = client.models.generate_content(
                model=settings.GEMINI_TEXT_MODEL,
                contents=[f"{instruction}\n\nPrompt: {prompt}"]
            )
            expanded = response.text.strip()
            if expanded:
                logger.info("Gemini image: expanded prompt: %s...", expanded[:50])
                return expanded
        except Exception as e:
            logger.warning("Gemini image: SDK expansion failed: %s. Trying HTTP fallback.", e)
    
    # HTTP fallback for expansion
    try:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_TEXT_MODEL}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": f"Expand this image prompt: {prompt}"}]}],
            "systemInstruction": {"parts": [{"text": "You are a prompt engineer. Output ONLY the expanded prompt."}]}
        }
        headers = {"x-goog-api-key": settings.GEMINI_API_KEY}
        resp = httpx.post(endpoint, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # simplified extraction
        candidates = data.get("candidates") or []
        if candidates:
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            if text:
                return text
    except Exception as e:
        logger.warning("Gemini image: HTTP expansion failed: %s", e)

    return prompt


def _aspect_ratio_to_size(aspect_ratio: Optional[str], base: int = 1280) -> Tuple[int, int]:
    if not aspect_ratio:
        return 1024, 1024
    match = re.match(r"^\s*(\d+)\s*:\s*(\d+)\s*$", aspect_ratio)
    if not match:
        return 1024, 1024
    w_ratio = int(match.group(1))
    h_ratio = int(match.group(2))
    if w_ratio <= 0 or h_ratio <= 0:
        return 1024, 1024
    if w_ratio >= h_ratio:
        width = base
        height = max(1, round(base * h_ratio / w_ratio))
    else:
        height = base
        width = max(1, round(base * w_ratio / h_ratio))
    return width, height


def is_valid_image(path: str) -> bool:
    """Check if a file exists and is a valid, non-empty image."""
    if not path or not os.path.exists(path):
        return False
    if os.path.getsize(path) < 1000: # Very small files are likely error pages or corrupt
        return False
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def generate_image(
    prompt: str,
    out_dir: str = "outputs",
    model: Optional[str] = None,
    image_size: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    filename_prefix: str = "gemini",
) -> List[str]:
    """Generate image(s) and save them to `out_dir`. Returns list of saved paths.

    This function is designed to be 'fail-proof' by cascading through multiple 
    providers (Gemini -> Pollinations FLUX -> Pollinations Turbo -> Pollinations SDXL).
    """
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    os.makedirs(out_dir, exist_ok=True)
    
    primary_model = model or settings.GEMINI_IMAGE_MODEL
    rich_prompt = expand_prompt(prompt)
    width, height = _aspect_ratio_to_size(aspect_ratio)

    # Provider 1: Gemini (SDK or HTTP)
    if settings.GEMINI_API_KEY:
        try:
            logger.info("Gemini image: attempting Provider 1 (Gemini: %s)", primary_model)
            if HAVE_GENAI:
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                if "imagen" in primary_model.lower():
                    cfg = types.GenerateImagesConfig(number_of_images=1, aspect_ratio=aspect_ratio)
                    response = client.models.generate_images(model=primary_model, prompt=rich_prompt, config=cfg)
                    saved: List[str] = []
                    for i, gen_img in enumerate(response.generated_images):
                        out_path = os.path.join(out_dir, f"{filename_prefix}_{i}.png")
                        gen_img.image.save(out_path)
                        if is_valid_image(out_path):
                            saved.append(out_path)
                    if saved:
                        return saved
                else:
                    cfg = types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size),
                    )
                    response = client.models.generate_content(model=primary_model, contents=[rich_prompt], config=cfg)
                    saved = []
                    for i, part in enumerate(response.parts):
                        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                            out_path = os.path.join(out_dir, f"{filename_prefix}_{i}.png")
                            _save_base64(part.inline_data.data, out_path)
                            if is_valid_image(out_path):
                                saved.append(out_path)
                    if saved:
                        return saved
            
            # HTTP Fallback for Gemini
            endpoint = settings.GEMINI_IMAGE_ENDPOINT or f"https://generativelanguage.googleapis.com/v1beta/models/{primary_model}:generateContent"
            if "gemini" in primary_model.lower() or settings.GEMINI_IMAGE_ENDPOINT:
                payload = {
                    "contents": [{"parts": [{"text": rich_prompt}]}],
                    "generationConfig": {
                        "response_modalities": ["IMAGE"],
                        "image_config": {"image_size": image_size, "aspect_ratio": aspect_ratio}
                    },
                }
                resp = httpx.post(endpoint, json=payload, headers={"x-goog-api-key": settings.GEMINI_API_KEY}, timeout=120)
                if resp.status_code == 200:
                    body = resp.json()
                    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    saved = []
                    for i, part in enumerate(parts):
                        b64 = (part.get("inline_data") or {}).get("data")
                        if b64:
                            out_path = os.path.join(out_dir, f"{filename_prefix}_http_{i}.png")
                            _save_base64(b64, out_path)
                            if is_valid_image(out_path):
                                saved.append(out_path)
                    if saved:
                        return saved
        except Exception as e:
            logger.warning("Gemini image: Provider 1 failed: %s", e)

    # Provider 2: Pollinations FLUX (Highly Reliable)
    try:
        logger.info("Gemini image: attempting Provider 2 (Pollinations FLUX)")
        import urllib.parse
        encoded_prompt = urllib.parse.quote(rich_prompt[:1000])
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&seed={os.urandom(4).hex()}"
        resp = httpx.get(url, timeout=60)
        if resp.status_code == 200:
            out_path = os.path.join(out_dir, f"{filename_prefix}_pollinations_flux.png")
            with open(out_path, "wb") as f:
                f.write(resp.content)
            if is_valid_image(out_path):
                return [out_path]
    except Exception as e:
        logger.warning("Gemini image: Provider 2 failed: %s", e)

    # Provider 3: Pollinations Turbo (Alternative)
    try:
        logger.info("Gemini image: attempting Provider 3 (Pollinations Turbo)")
        import urllib.parse
        encoded_prompt = urllib.parse.quote(rich_prompt[:1000])
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=turbo&nologo=true&seed={os.urandom(4).hex()}"
        resp = httpx.get(url, timeout=60)
        if resp.status_code == 200:
            out_path = os.path.join(out_dir, f"{filename_prefix}_pollinations_turbo.png")
            with open(out_path, "wb") as f:
                f.write(resp.content)
            if is_valid_image(out_path):
                return [out_path]
    except Exception as e:
        logger.warning("Gemini image: Provider 3 failed: %s", e)

    # Provider 4: Pollinations SDXL (Final fallback API)
    try:
        logger.info("Gemini image: attempting Provider 4 (Pollinations SDXL)")
        import urllib.parse
        encoded_prompt = urllib.parse.quote(rich_prompt[:1000])
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={os.urandom(4).hex()}"
        resp = httpx.get(url, timeout=60)
        if resp.status_code == 200:
            out_path = os.path.join(out_dir, f"{filename_prefix}_pollinations_sdxl.png")
            with open(out_path, "wb") as f:
                f.write(resp.content)
            if is_valid_image(out_path):
                return [out_path]
    except Exception as e:
        logger.error("Gemini image: Provider 4 failed: %s", e)

    logger.error("Gemini image: All online generation providers failed for prompt: %s", prompt[:50])
    return []


if __name__ == "__main__":
    # quick smoke test (no external calls performed when SDK/keys are absent)
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    logger.info("gemini_image helper loaded; GEMINI_IMAGE_MODEL=%s", settings.GEMINI_IMAGE_MODEL)