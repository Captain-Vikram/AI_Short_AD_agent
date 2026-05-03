"""Advanced web discovery and reasoning-based research engine."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from apify_client import ApifyClient
from config.settings import get_settings
from src.utils import get_logger

def discover_market_leads(query: str) -> List[Dict[str, Any]]:
    """Use Google Search to find current 'leads' and trending topics."""
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    token = settings.APIFY_API_TOKEN
    
    if not token:
        logger.error("WebExplorer: APIFY_API_TOKEN not configured")
        return []

    client = ApifyClient(token)
    logger.info("WebExplorer: performing discovery search for: %s", query)
    
    try:
        # Use Apify's Google Search Scraper
        run_input = {
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": 10,
            "customAttributes": {"type": "discovery"}
        }
        # In a real scenario, we'd use 'apify/google-search-scraper'
        # For this demonstration, we'll simulate the response if the actor isn't ready
        run = client.actor("apify/google-search-scraper").call(run_input=run_input, timeout_secs=120)
        dataset = client.dataset(run["defaultDatasetId"])
        return dataset.list_items().items
    except Exception as e:
        logger.warning("WebExplorer: discovery search failed: %s", e)
        return []

def extract_entities_and_topics(discovery_results: List[Dict[str, Any]], llm_caller: Any) -> Dict[str, Any]:
    """Use an LLM to analyze search results and suggest deep-dive targets."""
    if not discovery_results:
        return {"tickers": [], "influencers": [], "platforms": ["meta", "youtube", "x"]}

    # Prepare a condensed version of the search results for the LLM
    snippets = []
    for item in discovery_results:
        for result in item.get("organicResults", []):
            snippets.append({
                "title": result.get("title"),
                "description": result.get("description"),
                "url": result.get("url")
            })

    prompt = (
        "You are an Advanced Market Intelligence Researcher. Analyze the following web search results "
        "and extract specific 'entities' that warrant a deep-dive investigation.\n\n"
        
        "YOUR TASK:\n"
        "1. TICKERS: Identify specific stock tickers or crypto symbols mentioned.\n"
        "2. INFLUENCERS: Identify specific experts or accounts people are talking about.\n"
        "3. HOT TOPICS: What are the specific sub-topics or pain points?\n"
        "4. TARGET PLATFORMS: Based on the results, which platforms (X, YouTube, Reddit, Meta) seem most relevant?\n\n"
        
        f"WEB SEARCH SNIPPETS:\n{json.dumps(snippets[:20], ensure_ascii=False)}\n\n"
        "OUTPUT FORMAT: Return a strict JSON object with keys: `tickers`, `influencers`, `topics`, `platforms`."
    )

    system = "You are a world-class investigative researcher. You find the signal in the noise."
    try:
        # We pass the llm_caller function from agents.py
        resp = llm_caller(system, prompt)
        # Assuming _extract_json is available or we do simple cleanup
        import re
        json_match = re.search(r"({.*})", resp, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
    except Exception:
        pass
        
    return {"tickers": [], "influencers": [], "topics": [], "platforms": ["meta", "youtube", "x"]}

__all__ = ["discover_market_leads", "extract_entities_and_topics"]
