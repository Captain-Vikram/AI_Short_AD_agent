"""Scaffold CrewAI-style agents wired to local tool wrappers.

This module provides simple, testable functions that implement the four main
agents in the plan: Researcher, Strategist, Copywriter, and Director. They are
written so they work without the `crewai` package (fallback orchestration).

When `crewai` is available you can wrap these callables into proper agent
objects or tools.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from config.settings import get_settings
from src.core.director import build_remotion_props
from src.core.remotion_render import render_video
from src.utils import get_logger, log_json
from src.core.script_validator import validate_scene_list
from src.media.gdrive_helper import fetch_doc_text
from src.media.apify_helper import run_meta_ads_actor
from src.utils import retry_with_backoff

def _settings() -> Any:
    return get_settings(auto_detect_lmstudio_model=True)


def _logger():
    settings = _settings()
    return get_logger(__name__, log_file=settings.RUN_LOG_FILE)


def _extract_text_from_llm_response(data: Any) -> str:
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices:
            first = choices[0]
            if isinstance(first, dict):
                if "message" in first and isinstance(first["message"], dict):
                    content = first["message"].get("content", "")
                    if content:
                        return str(content)
                if "text" in first and first.get("text"):
                    return str(first.get("text"))

        candidates = data.get("candidates") or []
        if candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content")
                if isinstance(content, dict):
                    parts = content.get("parts") or []
                    text_parts = []
                    for part in parts:
                        if isinstance(part, dict) and part.get("text"):
                            text_parts.append(str(part["text"]))
                    if text_parts:
                        return "".join(text_parts)

                parts = first.get("parts") or []
                text_parts = []
                for part in parts:
                    if isinstance(part, dict) and part.get("text"):
                        text_parts.append(str(part["text"]))
                if text_parts:
                    return "".join(text_parts)

        if "output" in data:
            out = data["output"]
            if isinstance(out, list):
                text = "".join(
                    [str(x.get("content") or x.get("text") or "") for x in out if isinstance(x, dict)]
                )
                if text:
                    return text
            if out:
                return str(out)

        if data.get("text"):
            return str(data["text"])

    if isinstance(data, list):
        text_parts = []
        for item in data:
            if isinstance(item, dict) and item.get("text"):
                text_parts.append(str(item["text"]))
        if text_parts:
            return "".join(text_parts)

    return json.dumps(data)


@retry_with_backoff(
    max_retries=3,
    initial_backoff=2.0,
    status_codes=[429, 500, 502, 503, 504],
    exceptions=httpx.HTTPStatusError,
    logger_name="agents",
)
def _call_gemini_text(system: str, user: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    settings = _settings()
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model or settings.GEMINI_TEXT_MODEL}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    headers = {"x-goog-api-key": settings.GEMINI_API_KEY}
    resp = httpx.post(endpoint, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    text = _extract_text_from_llm_response(resp.json())
    if not text:
        raise RuntimeError("Gemini response did not contain any text")
    return text


def _call_openrouter_llm(system: str, user: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    settings = _settings()
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if settings.OPENROUTER_REFERRER:
        headers["HTTP-Referer"] = settings.OPENROUTER_REFERRER
    if settings.OPENROUTER_TITLE:
        headers["X-Title"] = settings.OPENROUTER_TITLE

    payload = {
        "model": model or settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    @retry_with_backoff(
        max_retries=3,
        initial_backoff=2.0,
        status_codes=[429, 500, 502, 503, 504],
        exceptions=(httpx.HTTPStatusError, httpx.TimeoutException),
        logger_name="agents",
    )
    def _do_post():
        resp = httpx.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp

    resp = _do_post()
    text = _extract_text_from_llm_response(resp.json())
    if not text:
        raise RuntimeError("OpenRouter response did not contain any text")
    return text


def _call_local_llm(system: str, user: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    """Call a local OpenAI-compatible LLM (LM Studio) and return text output."""
    settings = _settings()
    base = settings.LM_STUDIO_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"
    headers = {}
    if settings.LM_STUDIO_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LM_STUDIO_API_KEY}"

    payload = {
        "model": model or settings.LM_STUDIO_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    @retry_with_backoff(
        max_retries=2,
        initial_backoff=1.0,
        status_codes=[429, 500, 502, 503, 504],
        exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
        logger_name="agents",
    )
    def _do_post():
        resp = httpx.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp

    resp = _do_post()
    text = _extract_text_from_llm_response(resp.json())
    if text:
        return text
    raise RuntimeError("LM Studio response did not contain any text")


def _call_llm(system: str, user: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    """Unified LLM caller that dispatches to the configured provider."""
    settings = _settings()
    provider = settings.LLM_PROVIDER.lower()
    logger = _logger()

    try:
        if provider == "openrouter":
            return _call_openrouter_llm(system, user, model=model, temperature=temperature, max_tokens=max_tokens)
        elif provider == "gemini":
            return _call_gemini_text(system, user, model=model or settings.GEMINI_TEXT_MODEL, temperature=temperature, max_tokens=max_tokens)
        elif provider == "lmstudio":
            return _call_local_llm(system, user, model=model, temperature=temperature, max_tokens=max_tokens)
        else:
            logger.warning("Unknown LLM_PROVIDER '%s'; falling back to LM Studio", provider)
            return _call_local_llm(system, user, model=model, temperature=temperature, max_tokens=max_tokens)
    except Exception as exc:
        logger.error("LLM call failed for provider %s: %s", provider, exc)
        # Final fallback to Gemini if not already using it
        if provider != "gemini" and settings.GEMINI_API_KEY:
            logger.info("Falling back to Gemini text model...")
            return _call_gemini_text(system, user, model=settings.GEMINI_TEXT_MODEL, temperature=temperature, max_tokens=max_tokens)
        raise


def _repair_json(text: str) -> str:
    """Best-effort attempt to repair common LLM JSON artifacts (like unclosed brackets)."""
    text = text.strip()
    if not text:
        return text

    # Handle truncated JSON by closing open braces/brackets
    stack = []
    in_string = False
    escape = False

    for i, char in enumerate(text):
        if char == '"' and not escape:
            in_string = not in_string
        elif not in_string:
            if char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char == "}":
                if stack and stack[-1] == "}":
                    stack.pop()
            elif char == "]":
                if stack and stack[-1] == "]":
                    stack.pop()
        
        if char == "\\" and not escape:
            escape = True
        else:
            escape = False

    # If we are inside a string, close it first
    if in_string:
        text += '"'

    # Close remaining brackets in reverse order
    while stack:
        text += stack.pop()

    return text


def _extract_json(text: str) -> str:
    """Robustly extract JSON content from a potentially markdown-wrapped string."""
    text = text.strip()
    # Try to find content inside triple backticks
    code_block_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()
    else:
        # If no backticks, find the first occurrence of { or [ and the last occurrence of } or ]
        # We look for the outermost structure.
        first_brace = text.find("{")
        first_bracket = text.find("[")
        
        start = -1
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            start = first_brace
            end = text.rfind("}")
        elif first_bracket != -1:
            start = first_bracket
            end = text.rfind("]")
            
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1].strip()
        elif start != -1:
            # Maybe it's truncated? Just take everything from the start
            text = text[start:].strip()

    return _repair_json(text)


def run_researcher(search_query: Optional[str] = None, out_path: str = "output/successful_ads.json") -> str:
    """Run the Apify Meta Ads actor and write results to `out_path`.

    Returns the path to the saved JSON file.
    """
    logger = _logger()
    logger.info("Researcher: starting Apify actor (query=%s)", search_query)
    path = run_meta_ads_actor(search_query=search_query, out_path=out_path)
    logger.info("Researcher: saved ads to %s", path)
    return path


def run_strategist(ads_path: str = "output/successful_ads.json", out_path: str = "output/marketing_strategy.json", sample_size: int = 10) -> str:
    """Analyze scraped ads and produce a marketing strategy JSON file.

    This function samples the first `sample_size` ads to keep prompts small.
    """
    logger = _logger()
    logger.info("Strategist: loading ads from %s", ads_path)
    with open(ads_path, "r", encoding="utf-8") as f:
        ads = json.load(f)

    if isinstance(ads, dict):
        # some Apify dataset exports use { items: [...] }
        ads_list = ads.get("items") or ads.get("results") or []
    else:
        ads_list = ads

    sample = ads_list[:sample_size] if isinstance(ads_list, list) else ads_list

    prompt = (
        "You are a marketing strategist. Extract the core marketing angles, hooks, and pain points "
        "from the following ads sample and return a strict JSON object with keys: `angles`, `hooks`, `pain_points`. "
        "Each `angle` should be an object with `title`, `description`, and `examples` (list). Only output valid JSON.\n\n"
        f"Ads sample:\n{json.dumps(sample, ensure_ascii=False)}"
    )

    system = "You are a helpful marketing analyst."
    logger.info("Strategist: sending prompt to LLM (sample size=%d)", sample_size)
    resp_text = _call_llm(system, prompt)
    cleaned_json = _extract_json(resp_text)

    try:
        parsed = json.loads(cleaned_json)
        log_json(logger, "Strategist: parsed analysis", parsed)
    except Exception:
        logger.warning("Strategist: LLM did not return valid JSON; saving raw output")
        parsed = {"raw_output": resp_text}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    logger.info("Strategist: saved marketing strategy to %s", out_path)
    return out_path


def run_copywriter(marketing_strategy_path: str = "output/marketing_strategy.json", source_text: Optional[str] = None, out_path: str = "output/script.json", duration_seconds: int = 60) -> str:
    """Generate a strict-JSON script for the Remotion pipeline.

    The output MUST be a JSON array of scenes: [{"scene":1,"narration":"...","image_prompt":"..."},...]
    """
    logger = _logger()
    logger.info("Copywriter: loading marketing strategy from %s", marketing_strategy_path)
    try:
        with open(marketing_strategy_path, "r", encoding="utf-8") as f:
            strategy = json.load(f)
    except Exception:
        strategy = {}

    if source_text is None:
        logger.info("Copywriter: loading source text from Google Drive")
        try:
            source_text = fetch_doc_text()
        except Exception as exc:
            logger.warning("Copywriter: Google Drive source unavailable; continuing without it: %s", exc)
            source_text = ""

    prompt = (
        "You are a professional video copywriter. Using the marketing strategy below and the source text, "
        "write a highly converting 60-second video script. Output must be a JSON array of scenes with keys: `scene` (int), `narration` (string), and `image_prompt` (string). "
        "Return ONLY the JSON array—no explanation, markdown, or commentary.\n\n"
        f"Marketing strategy:\n{json.dumps(strategy, ensure_ascii=False)}\n\nSource text:\n{(source_text or '')}\n\nTarget duration_seconds: {duration_seconds}"
    )

    system = "You are a concise scriptwriter for short marketing videos."
    resp = _call_llm(system, prompt, max_tokens=2048)
    cleaned_json = _extract_json(resp)

    # try to parse and validate
    try:
        arr = json.loads(cleaned_json)
        scenes = validate_scene_list(arr)
        log_json(logger, "Copywriter: validated scenes", scenes)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        logger.info("Copywriter: wrote validated script to %s", out_path)
        return out_path
    except ValidationError as ve:
        logger.exception("Copywriter: validation failed: %s", ve)
        # save raw response for inspection
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(resp)
        raise
    except Exception as e:
        logger.exception("Copywriter: failed to parse LLM output: %s", e)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(resp)
        raise


def run_designer(
    script_path: str = "output/script.json",
    design_path: str = "output/video_design.json",
    code_path: str = "remotion-app/src/VideoGenerated.tsx",
) -> str:
    """Generate a video design spec and optional Remotion TSX via LLM."""
    logger = _logger()
    logger.info("Designer: loading script from %s", script_path)
    with open(script_path, "r", encoding="utf-8") as handle:
        script = json.load(handle)

    prompt = (
        "You are a professional video/infographic designer specializing in modern, dynamic motion ads. "
        "Your task is to create a visually stunning design specification for an advertisement video.\n\n"
        
        "DESIGN REQUIREMENTS:\n"
        "1. Generate a design object with these properties:\n"
        "   - bg_color: Dark or vibrant background (hex color) matching brand aesthetic\n"
        "   - accent_color: Primary action/highlight color (hex) that pops\n"
        "   - text_color: High contrast text color for readability (usually light)\n"
        "   - secondary_color: Supporting accent for depth (hex)\n"
        "   - layout: One of: 'fullscreen', 'split', 'picture-in-picture', 'minimalist'\n"
        "   - animation_style: One of: 'subtle' (corporate), 'dynamic' (energetic), 'bold' (aggressive)\n"
        "   - floating_elements: true (enables animated background elements), false for clean look\n"
        "   - show_badge: true to show scene badges, false for minimal\n"
        "   - text_position: 'bottom', 'center', or 'top' for narration placement\n"
        "   - element_scale: 1.0-2.0, controls size of floating visual elements\n"
        "   - blur_strength: 0-15, background blur intensity\n"
        "   - audio_gain: 0.5-3.0, audio volume (default 1.4)\n\n"
        
        "2. DESIGN STRATEGY - Be Intentional:\n"
        "   - For tech/business ads: Use blues, purples, minimal floating elements, dynamic animation\n"
        "   - For lifestyle/products: Use vibrant accents, bold animations, floating elements enabled\n"
        "   - For educational: Use secondary colors sparingly, centered text, subtle animations\n"
        "   - Match colors to script themes (e.g., green for eco, red for urgency, blue for trust)\n\n"
        
        "3. INFOGRAPHIC ELEMENTS (handled by template):\n"
        "   - Floating animated circles and shapes in background\n"
        "   - Scene transition badges with accent color\n"
        "   - Automatic text layering with professional typography\n"
        "   - Gradient backgrounds and modern shadows\n"
        "   - Your design props control the visual expression\n\n"
        
        "RETURN FORMAT - STRICT JSON ONLY:\n"
        "{\n"
        "  \"design\": {\n"
        "    \"bg_color\": \"#0f172a\",\n"
        "    \"accent_color\": \"#3b82f6\",\n"
        "    \"text_color\": \"#f8fafc\",\n"
        "    \"secondary_color\": \"#1e293b\",\n"
        "    \"layout\": \"fullscreen\",\n"
        "    \"animation_style\": \"dynamic\",\n"
        "    \"floating_elements\": true,\n"
        "    \"show_badge\": true,\n"
        "    \"text_position\": \"bottom\",\n"
        "    \"element_scale\": 1.2,\n"
        "    \"blur_strength\": 8,\n"
        "    \"audio_gain\": 1.4,\n"
        "    \"design_name\": \"Descriptive name\",\n"
        "    \"design_rationale\": \"Why these choices match the content\"\n"
        "  }\n"
        "}\n\n"
        
        "Do NOT include tsx_lines. Focus only on the design spec.\n"
        "Make colors, animations, and layout cohesive and professional.\n"
        "Ensure accent colors have strong contrast with background.\n\n"
        
        f"SCRIPT TO DESIGN FOR:\n{json.dumps(script, ensure_ascii=False)}"
    )

    system = (
        "You are a professional motion graphics designer. "
        "Output ONLY valid JSON with a 'design' key containing the design specification. "
        "No commentary, no markdown, no code blocks. Just pure JSON."
    )
    resp = _call_llm(system, prompt, max_tokens=2048)
    cleaned_json = _extract_json(resp)

    payload: Any
    try:
        payload = json.loads(cleaned_json)
    except Exception:
        logger.warning("Designer: LLM did not return valid JSON; saving raw output")
        payload = {"design": {"raw_output": resp}}

    design = payload.get("design") if isinstance(payload, dict) else None
    if not isinstance(design, dict):
        design = {"raw_output": resp}

    with open(design_path, "w", encoding="utf-8") as handle:
        json.dump(design, handle, ensure_ascii=False, indent=2)
    logger.info("Designer: wrote design spec to %s", design_path)
    log_json(logger, "Designer: design spec", design)

    tsx_lines = payload.get("tsx_lines") if isinstance(payload, dict) else None
    if isinstance(tsx_lines, list) and all(isinstance(line, str) for line in tsx_lines):
        code = "\n".join(tsx_lines).rstrip() + "\n"
        code_file = Path(code_path)
        code_file.parent.mkdir(parents=True, exist_ok=True)
        code_file.write_text(code, encoding="utf-8")
        logger.info("Designer: wrote video code to %s", code_file)
    else:
        logger.info("Designer: focusing on design spec; video uses VideoEnhanced template")

    return design_path


def run_director(script_path: str = "output/script.json", assets_dir: str = "output/assets", remotion_props_path: str = "output/remotion_props.json") -> str:
    return build_remotion_props(script_path=script_path, assets_dir=assets_dir, remotion_props_path=remotion_props_path)


def _add_render_args(
    parser: argparse.ArgumentParser,
    *,
    include_render_flag: bool,
    suppress_defaults: bool,
) -> None:
    def _default(value: Any) -> Any:
        return argparse.SUPPRESS if suppress_defaults else value

    if include_render_flag:
        parser.add_argument(
            "--render",
            action="store_true",
            default=_default(False),
            help="Render a Remotion video after props are created",
        )
    parser.add_argument("--props", default=_default("output/remotion_props.json"), help="Path to the Remotion props JSON")
    parser.add_argument("--assets-dir", default=_default("output/assets"), help="Directory for generated image/audio assets")
    parser.add_argument("--design", default=_default(None), help="Path to LLM video design JSON")
    parser.add_argument("--remotion-app", default=_default(None), help="Remotion app directory (default: config)")
    parser.add_argument("--remotion-entry", default=_default(None), help="Remotion entry point (default: config)")
    parser.add_argument("--composition", default=_default(None), help="Remotion composition id (default: config)")
    parser.add_argument("--output", default=_default(None), help="Output video path (default: remotion-app/out/video.mp4)")


def _get_cli_value(args: argparse.Namespace, name: str, fallback: Any) -> Any:
    return getattr(args, name, fallback)


def _cli():
    parser = argparse.ArgumentParser(description="Agent scaffolds: researcher, strategist, copywriter, director")
    _add_render_args(parser, include_render_flag=True, suppress_defaults=False)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("researcher")
    sub.add_parser("strategist")
    sub.add_parser("copywriter")
    director_parser = sub.add_parser("director")
    _add_render_args(director_parser, include_render_flag=True, suppress_defaults=True)
    designer_parser = sub.add_parser("designer")
    designer_parser.add_argument("--script", default="script.json", help="Path to the validated script JSON")
    designer_parser.add_argument("--design", default="video_design.json", help="Output path for video design JSON")
    designer_parser.add_argument(
        "--video-code",
        default="remotion-app/src/VideoGenerated.tsx",
        help="Output path for LLM-generated Remotion TSX",
    )
    render_parser = sub.add_parser("render")
    _add_render_args(render_parser, include_render_flag=False, suppress_defaults=True)
    all_parser = sub.add_parser("all")
    _add_render_args(all_parser, include_render_flag=True, suppress_defaults=True)

    args = parser.parse_args()
    if args.command == "researcher":
        run_researcher()
    elif args.command == "strategist":
        run_strategist()
    elif args.command == "copywriter":
        run_copywriter()
    elif args.command == "director":
        props_path = run_director(
            assets_dir=_get_cli_value(args, "assets_dir", "output/assets"),
            remotion_props_path=_get_cli_value(args, "props", "output/remotion_props.json"),
        )
        if _get_cli_value(args, "render", False):
            render_video(
                remotion_props_path=props_path,
                design_path=_get_cli_value(args, "design", None),
                remotion_app_dir=_get_cli_value(args, "remotion_app", None),
                entry_point=_get_cli_value(args, "remotion_entry", None),
                composition_id=_get_cli_value(args, "composition", None),
                output_path=_get_cli_value(args, "output", None),
            )
    elif args.command == "designer":
        run_designer(
            script_path=_get_cli_value(args, "script", "output/script.json"),
            design_path=_get_cli_value(args, "design", "output/video_design.json"),
            code_path=_get_cli_value(args, "video_code", "remotion-app/src/VideoGenerated.tsx"),
        )
    elif args.command == "render":
        render_video(
            remotion_props_path=_get_cli_value(args, "props", "output/remotion_props.json"),
            design_path=_get_cli_value(args, "design", None),
            remotion_app_dir=_get_cli_value(args, "remotion_app", None),
            entry_point=_get_cli_value(args, "remotion_entry", None),
            composition_id=_get_cli_value(args, "composition", None),
            output_path=_get_cli_value(args, "output", None),
        )
    elif args.command == "all":
        ads = run_researcher()
        strat = run_strategist(ads_path=ads)
        script = run_copywriter(marketing_strategy_path=strat)
        props_path = run_director(
            script_path=script,
            assets_dir=_get_cli_value(args, "assets_dir", "output/assets"),
            remotion_props_path=_get_cli_value(args, "props", "output/remotion_props.json"),
        )
        if _get_cli_value(args, "render", False):
            render_video(
                remotion_props_path=props_path,
                design_path=_get_cli_value(args, "design", None),
                remotion_app_dir=_get_cli_value(args, "remotion_app", None),
                entry_point=_get_cli_value(args, "remotion_entry", None),
                composition_id=_get_cli_value(args, "composition", None),
                output_path=_get_cli_value(args, "output", None),
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
