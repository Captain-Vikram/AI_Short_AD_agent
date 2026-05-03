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
        "You are a Senior Marketing Strategist and Ad Psychologist. Analyze the following successful ads and extract a deep 'Why/How/What' framework for each unique pattern identified.\n\n"
        
        "YOUR TASK:\n"
        "1. THE 'WHY' (Psychological Triggers): Identify the core human desires being targeted (e.g., Fear of Missing Out, Desire for Status, Need for Security). Explain the psychological mechanism at play.\n"
        "2. THE 'HOW' (Structure & Pacing): Analyze the hook structure, the visual narrative style (e.g., UGC, cinematic, direct response), and the pacing of the information.\n"
        "3. THE 'WHAT' (The Offer): Identify the specific product/service, the unique value proposition (UVP), and the call to action (CTA).\n\n"
        
        "OUTPUT FORMAT: Return a strict JSON object with these keys:\n"
        "- `market_insights`: Broad trends across all ads.\n"
        "- `winning_patterns`: A list of objects, each containing:\n"
        "  - `pattern_name`: A descriptive name.\n"
        "  - `psychology`: The 'Why'.\n"
        "  - `structure`: The 'How'.\n"
        "  - `offer_details`: The 'What'.\n"
        "  - `ad_examples`: Short summaries of ads that fit this pattern.\n"
        "- `angles`: Core marketing angles derived from the ads.\n"
        "- `hooks`: A list of the most effective hook types found.\n"
        "- `pain_points`: Specific customer pain points addressed.\n\n"
        
        f"Ads sample:\n{json.dumps(sample, ensure_ascii=False)}\n\n"
        "Only output valid JSON."
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


def run_copywriter(marketing_strategy_path: str = "output/marketing_strategy.json", market_data_path: Optional[str] = None, out_path: str = "output/script.json", duration_seconds: int = 60) -> str:
    """Generate a high-converting, psychology-driven video script.
    
    This agent uses advanced direct-response marketing techniques (AIDA, PAS)
    to create professional content that avoids 'AI slop'.
    """
    logger = _logger()
    logger.info("Copywriter: loading marketing strategy from %s", marketing_strategy_path)
    try:
        with open(marketing_strategy_path, "r", encoding="utf-8") as f:
            strategy = json.load(f)
    except Exception:
        strategy = {}

    market_data = {}
    if market_data_path and os.path.exists(market_data_path):
        logger.info("Copywriter: loading market data from %s", market_data_path)
        try:
            with open(market_data_path, "r", encoding="utf-8") as f:
                market_data = json.load(f)
        except Exception as exc:
            logger.warning("Copywriter: failed to load market data: %s", exc)

    prompt = (
        "You are a Top 1% Direct-Response Copywriter and Creative Director for high-budget social media ads. "
        "Your task is to write a script that is indistinguishable from a human expert and engineered for MAXIMUM retention.\n\n"
        
        "PHASE 1: THE PATTERN INTERRUPT (Scene 1)\n"
        "- Open with a 'Great Lead'. Start mid-action or with a counter-intuitive question that shatters the user's scroll.\n"
        "- DO NOT start with 'Are you tired of...' or 'Introducing...'.\n"
        "- Example: 'Most people think X is the secret to Y. They are dead wrong.'\n\n"
        
        "PHASE 2: THE ADRENALINE LOOP (Scenes 2-4)\n"
        "- Use 'The Open Loop' technique. Imply a payoff that only comes at the end.\n"
        "- Use short, punchy sentences (3-5 words) followed by one longer, rhythmic explanation.\n"
        "- Focus on high-status language. Avoid generic 'Unleash' or 'Empower' slop.\n\n"
        
        "PHASE 3: CINEMATIC DIRECTION (Image Prompts)\n"
        "- Prompts must be MASTERPIECES. Use art-house terminology.\n"
        "- Keywords: 'Anamorphic flares', 'Kodak Portra 400 aesthetic', 'Negative space', 'Tonal contrast', 'Cyberpunk noir lighting'.\n"
        "- Each prompt must describe a SPECIFIC moment of motion (e.g., 'Particles suspended in a beam of light', 'Slow-motion droplets on cold steel').\n\n"
        
        "TECHNICAL CONSTRAINTS:\n"
        "- Total narration: 140-160 words (high energy).\n"
        "- Structure: Exactly 6 scenes.\n"
        "- Output: Strict JSON array `[{\"scene\": 1, \"narration\": \"...\", \"image_prompt\": \"...\"}, ...]`.\n\n"
        
        f"MARKETING STRATEGY (Proven Patterns):\n{json.dumps(strategy, ensure_ascii=False)}\n\n"
        f"CURRENT MARKET DATA (The 'Signal'):\n{json.dumps(market_data, ensure_ascii=False)}\n\n"
        "BANNED WORDS: Unlock, unleash, discover, empower, revolutionary, game-changer, in today's world, meet [Product Name].\n\n"
        "CORE REQUIREMENT: You MUST combine the winning patterns from the strategy with the current market signals. "
        "If the market data contains specific prices, tickers, or trends, weave them naturally into the narrative to make the ad feel 'LIVE' and 'URGENT'.\n\n"
        "Return ONLY the JSON array."
    )

    system = "You are a world-class creative director and copywriter. You produce professional, cinematic marketing scripts."
    resp = _call_llm(system, prompt, max_tokens=3000)
    cleaned_json = _extract_json(resp)

    try:
        arr = json.loads(cleaned_json)
        scenes = validate_scene_list(arr)
        log_json(logger, "Copywriter: validated professional script", scenes)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        return out_path
    except Exception as e:
        logger.exception("Copywriter: failed to generate professional script: %s", e)
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


def run_director_review(script_path: str = "output/script.json", out_path: str = "output/directed_script.json") -> str:
    """The Director reviews the script to ensure cinematic cohesion and visual flow.
    
    This agent takes the raw copy and adds 'Director's Notes', refines image prompts
    for visual continuity, and ensures the 'Pattern Interrupt' is strong.
    """
    logger = _logger()
    logger.info("Director: Reviewing script for cinematic quality: %s", script_path)
    
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    prompt = (
        "You are a World-Class Film Director. You have been handed a script by a copywriter. "
        "Your job is to elevate this into a cinematic masterpiece. You must ensure VISUAL CONTINUITY "
        "and emotional impact across all scenes.\n\n"
        
        "DIRECTOR'S TASKS:\n"
        "1. VISUAL METAPHOR: Enhance the `image_prompt` of each scene. Ensure they aren't just literal but METAPHORICAL. "
        "   If the script is about 'growth', don't just show a plant; show 'time-lapse shadows moving across an oak floor as a sprout breaks through'.\n"
        "2. CINEMATIC CONTINUITY: If a character or setting is established in Scene 1, ensure the following prompts use "
        "   consistent keywords (e.g., 'The same high-tech laboratory', 'The same woman with neon-blue hair').\n"
        "3. PACING: Adjust the narration if it feels too long for a single scene. Break it into 'beats'.\n"
        "4. CAMERA LANGUAGE: Add specific camera directions: 'Dutch angle', 'Slow dolly zoom', 'Rack focus'.\n\n"
        
        "OUTPUT REQUIREMENT:\n"
        "Return a JSON array of the same length. Keep the keys `scene`, `narration`, and `image_prompt`. "
        "Update the `image_prompt` with your cinematic refinements.\n\n"
        
        f"RAW SCRIPT:\n{json.dumps(script, ensure_ascii=False)}\n\n"
        "Return ONLY the JSON array. No preamble."
    )

    system = "You are an elite film director and visual storyteller. You think in frames, lighting, and movement."
    resp = _call_llm(system, prompt, max_tokens=3000)
    cleaned_json = _extract_json(resp)

    try:
        directed_scenes = json.loads(cleaned_json)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(directed_scenes, f, ensure_ascii=False, indent=2)
        logger.info("Director: Script elevated and saved to %s", out_path)
        return out_path
    except Exception as e:
        logger.exception("Director: Failed to refine script: %s", e)
        # Fallback to original script if refinement fails
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        return out_path


def run_director(script_path: str = "output/script.json", assets_dir: str = "output/assets", remotion_props_path: str = "output/remotion_props.json") -> str:
    # First, let the Director review and elevate the script
    directed_script_path = "output/directed_script.json"
    final_script_path = run_director_review(script_path, directed_script_path)
    
    # Then proceed with asset generation using the elevated script
    return build_remotion_props(script_path=final_script_path, assets_dir=assets_dir, remotion_props_path=remotion_props_path)


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


from src.media.market_research import run_multi_source_research
from src.media.web_explorer import discover_market_leads, extract_entities_and_topics

def run_market_intelligence(query: str, out_path: str = "output/market_signals.json") -> str:
    """Run an advanced Recursive Research Loop: Discovery -> Reasoning -> Deep-Dive -> Distillation."""
    logger = _logger()
    logger.info("Market Intelligence: initiating RECURSIVE loop for: %s", query)
    
    # 1. DISCOVERY PHASE: Broad web search
    discovery_results = discover_market_leads(query)
    
    # 2. REASONING PHASE: LLM identifies entities and deep-dive targets
    intelligence_map = extract_entities_and_topics(discovery_results, _call_llm)
    logger.info("Market Intelligence: reasoning complete. Found entities: %s", intelligence_map)
    
    # 3. DEEP-DIVE PHASE: Targeted social research based on discovered entities
    # We combine the original query with discovered tickers and influencers
    deep_dive_queries = [query]
    if intelligence_map.get("tickers"):
        deep_dive_queries.extend(intelligence_map["tickers"][:3])
    if intelligence_map.get("influencers"):
        deep_dive_queries.extend(intelligence_map["influencers"][:2])
        
    combined_results = {}
    platforms = intelligence_map.get("platforms", ["meta", "youtube", "x", "reddit"])
    
    for dq in deep_dive_queries:
        logger.info("Market Intelligence: deep-diving into entity: %s", dq)
        raw_path = run_multi_source_research(dq, sources=platforms, out_path=f"output/raw_{dq.replace(' ', '_')}.json")
        if raw_path and os.path.exists(raw_path):
            with open(raw_path, "r", encoding="utf-8") as f:
                combined_results[dq] = json.load(f)

    # 4. DISTILLATION PHASE: LLM synthesizes all intelligence into the final Market Signal
    prompt = (
        "You are an Elite Intelligence Officer and Market Analyst. You have just completed a recursive web investigation. "
        "Your task is to synthesize the following diverse data points into a MASTER Market Signal report.\n\n"
        
        "THE INVESTIGATION SCOPE:\n"
        f"- Primary Subject: {query}\n"
        f"- Discovered Entities: {json.dumps(intelligence_map.get('tickers', []), ensure_ascii=False)}\n"
        f"- Expert Leads: {json.dumps(intelligence_map.get('influencers', []), ensure_ascii=False)}\n\n"
        
        "RAW INTELLIGENCE DATA:\n"
        f"{json.dumps(combined_results, ensure_ascii=False)[:12000]}\n\n"
        
        "REQUIRED FIELDS in JSON (Matches example1.json spec):\n"
        "- `ticker`: Primary asset ticker.\n"
        "- `title`: Urgent headline.\n"
        "- `direction`: 'LONG' or 'SHORT'.\n"
        "- `confidence_level`: 1-100.\n"
        "- `sources_weights`: Weighted importance of research channels.\n"
        "- `Wisdom of Professional Traders`: Deep synthesis of expert sentiment.\n"
        "- `Key Insights`: High-level strategic takeaways.\n"
        "- `Trading Recommendation`: Specific tactical execution plan.\n\n"
        
        "Only output valid JSON."
    )

    system = "You are a master of synthesis. You turn disparate web clues into actionable market intelligence."
    logger.info("Market Intelligence: distilling final report")
    resp = _call_llm(system, prompt, max_tokens=3000)
    cleaned_json = _extract_json(resp)

    try:
        parsed = json.loads(cleaned_json)
        # Add metadata about the recursive search
        parsed["_metadata"] = {
            "search_depth": "recursive",
            "entities_discovered": intelligence_map,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        logger.info("Market Intelligence: MASTER signal saved to %s", out_path)
        return out_path
    except Exception as e:
        logger.error("Market Intelligence: distillation failed: %s", e)
        # Fallback to the first deep-dive result if synthesis fails
        return out_path if os.path.exists(out_path) else ""

def _cli():
    parser = argparse.ArgumentParser(description="Agent scaffolds: researcher, strategist, copywriter, director")
    _add_render_args(parser, include_render_flag=True, suppress_defaults=False)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("researcher")
    intel_parser = sub.add_parser("market-intel")
    intel_parser.add_argument("--query", default="trading", help="Market topic to research")

    sub.add_parser("strategist")
    copy_parser = sub.add_parser("copywriter")
    copy_parser.add_argument("--strategy", default="output/marketing_strategy.json", help="Path to marketing strategy")
    copy_parser.add_argument("--market-data", help="Path to market signal JSON (e.g. scripts/example1.json)")
    
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
    all_parser.add_argument("--query", help="Query for researcher/market-intel")
    all_parser.add_argument("--multi-source", action="store_true", help="Use multi-source market intelligence")
    all_parser.add_argument("--market-data", help="Path to pre-existing market signal JSON")
    _add_render_args(all_parser, include_render_flag=True, suppress_defaults=True)

    args = parser.parse_args()
    if args.command == "researcher":
        run_researcher(search_query=_get_cli_value(args, "query", None))
    elif args.command == "market-intel":
        run_market_intelligence(query=_get_cli_value(args, "query", "trading"))
    elif args.command == "strategist":
        run_strategist()
    elif args.command == "copywriter":
        run_copywriter(
            marketing_strategy_path=_get_cli_value(args, "strategy", "output/marketing_strategy.json"),
            market_data_path=_get_cli_value(args, "market_data", None)
        )
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
        query = _get_cli_value(args, "query", None)
        ads = run_researcher(search_query=query)
        strat = run_strategist(ads_path=ads)
        
        market_data_path = _get_cli_value(args, "market_data", None)
        if _get_cli_value(args, "multi_source", False):
            market_data_path = run_market_intelligence(query=query or "trading")
            
        script = run_copywriter(
            marketing_strategy_path=strat,
            market_data_path=market_data_path
        )
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
