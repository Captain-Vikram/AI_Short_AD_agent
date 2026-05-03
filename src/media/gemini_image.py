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


def generate_image(
    prompt: str,
    out_dir: str = "outputs",
    model: Optional[str] = None,
    image_size: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    filename_prefix: str = "gemini",
) -> List[str]:
    """Generate image(s) and save them to `out_dir`. Returns list of saved paths.

    - `model` defaults to `GEMINI_IMAGE_MODEL` from settings.
    - `image_size` accepts Gemini size tokens like `1K`, `2K`, `4K`, or `512`.
    - `aspect_ratio` is e.g. `16:9`, `1:1`, etc.
    """
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    os.makedirs(out_dir, exist_ok=True)
    model = model or settings.GEMINI_IMAGE_MODEL
    logger.info("Gemini image: generating with model=%s size=%s aspect=%s", model, image_size or "default", aspect_ratio or "default")

    # Step 0: Expand prompt for better quality
    rich_prompt = expand_prompt(prompt)

    if HAVE_GENAI:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Determine which method to use based on model name
            if "imagen" in model.lower():
                # Use generate_images for Imagen models
                cfg = types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    # image_size is not directly in GenerateImagesConfig in some SDK versions, 
                    # but aspect_ratio is.
                )
                response = client.models.generate_images(model=model, prompt=rich_prompt, config=cfg)
                saved: List[str] = []
                for i, gen_img in enumerate(response.generated_images):
                    out_path = os.path.join(out_dir, f"{filename_prefix}_{i}.png")
                    gen_img.image.save(out_path)
                    saved.append(out_path)
                if saved:
                    logger.info("Gemini image: saved %d image(s) via generate_images", len(saved))
                    return saved
            else:
                # Use generate_content for multimodal models that support IMAGE modality
                cfg = types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size),
                )
                response = client.models.generate_content(model=model, contents=[rich_prompt], config=cfg)
                saved: List[str] = []
                i = 0
                for part in response.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        img_data = part.inline_data.data
                        out_path = os.path.join(out_dir, f"{filename_prefix}_{i}.png")
                        _save_base64(img_data, out_path)
                        saved.append(out_path)
                        i += 1
                if saved:
                    logger.info("Gemini image: saved %d image(s) via generate_content", len(saved))
                    return saved
        except Exception as e:
            logger.warning("Gemini image: SDK generation failed: %s. Falling back.", e)

    # Fallback 1: attempt a direct HTTP call (legacy/custom)
    try:
        endpoint = settings.GEMINI_IMAGE_ENDPOINT or (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )
        # Only try HTTP if endpoint is specified or it looks like a gemini model
        if settings.GEMINI_IMAGE_ENDPOINT or "gemini" in model.lower():
            payload = {
                "contents": [{"parts": [{"text": rich_prompt}]}],
                "generationConfig": {
                    "response_modalities": ["IMAGE"],
                    "image_config": {"image_size": image_size, "aspect_ratio": aspect_ratio}
                },
            }
            headers = {"Content-Type": "application/json"}
            if settings.GEMINI_API_KEY:
                headers["x-goog-api-key"] = settings.GEMINI_API_KEY

            resp = httpx.post(endpoint, json=payload, headers=headers, timeout=120)
            if resp.status_code == 200:
                body = resp.json()
                parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                saved = []
                i = 0
                for part in parts:
                    inline = part.get("inline_data") or {}
                    b64 = inline.get("data")
                    if b64:
                        out_path = os.path.join(out_dir, f"{filename_prefix}_{i}.png")
                        _save_base64(b64, out_path)
                        saved.append(out_path)
                        i += 1
                if saved:
                    return saved
    except Exception as e:
        logger.warning("Gemini image: HTTP fallback failed: %s", e)

    # Fallback 2: Pollinations.ai with FLUX (Better than default)
    try:
        import urllib.parse
        # Truncate prompt to ~1000 chars to avoid URL length issues
        safe_prompt = rich_prompt[:1000]
        encoded_prompt = urllib.parse.quote(safe_prompt)
        width, height = _aspect_ratio_to_size(aspect_ratio)
        
        # Use FLUX model on Pollinations for significantly better quality
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true"
        resp = httpx.get(pollinations_url, timeout=60)
        resp.raise_for_status()
        out_path = os.path.join(out_dir, f"{filename_prefix}_pollinations.png")
        with open(out_path, "wb") as f:
            f.write(resp.content)
        logger.info("Gemini image: saved image to %s (via Pollinations.ai FLUX fallback)", out_path)
        return [out_path]
    except Exception as e:
        logger.error("Gemini image: All generation methods failed. Last error: %s", e)
        return []


if __name__ == "__main__":
    # quick smoke test (no external calls performed when SDK/keys are absent)
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    logger.info("gemini_image helper loaded; GEMINI_IMAGE_MODEL=%s", settings.GEMINI_IMAGE_MODEL)