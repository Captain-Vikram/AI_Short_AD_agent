"""Helpers for multi-source market research using Apify actors."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apify_client import ApifyClient
from config.settings import get_settings
from src.utils import get_logger, log_json

def run_multi_source_research(
    query: str,
    sources: List[str] = ["meta", "youtube", "x", "reddit"],
    out_path: str = "output/market_signals.json"
) -> str:
    """Run research across multiple social platforms and aggregate the 'signals'."""
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)
    token = settings.APIFY_API_TOKEN
    
    if not token:
        logger.error("APIFY_API_TOKEN not configured")
        return ""

    client = ApifyClient(token)
    results = {}
    
    # Mapping sources to potential Apify actors (placeholders for common ones)
    actor_map = {
        "meta": settings.APIFY_META_ADS_ACTOR_ID,
        "youtube": "apify/youtube-scraper",
        "x": "quacker/twitter-url-scraper", # Example X actor
        "reddit": "apify/reddit-scraper"
    }

    logger.info("MarketResearch: starting multi-source research for query: %s", query)
    
    for source in sources:
        actor_id = actor_map.get(source)
        if not actor_id:
            continue
            
        logger.info("MarketResearch: scraping %s (actor=%s)", source, actor_id)
        # In a real scenario, we'd customize the input for each actor
        # For now, we use a generic search-based input
        try:
            # This is a simplified example; each actor has its own input schema
            run_input = {"search": query, "maxItems": 10}
            if source == "meta":
                run_input = {
                    "searchQuery": query, 
                    "activeStatus": "active",
                    "maxConcurrency": 1
                }
                
            run = client.actor(actor_id).call(run_input=run_input, timeout_secs=300)
            dataset = client.dataset(run["defaultDatasetId"])
            items = dataset.list_items().items
            results[source] = items
            logger.info("MarketResearch: found %d items for %s", len(items), source)
        except Exception as e:
            logger.warning("MarketResearch: failed to scrape %s: %s", source, e)
            results[source] = []

    # Calculate "Source Weights" (Simplified: based on item count)
    total_items = sum(len(items) for items in results.values())
    weights = {}
    if total_items > 0:
        for source, items in results.items():
            weights[source] = round((len(items) / total_items) * 100)
    else:
        weights = {s: 0 for s in sources}

    # Format into "Market Signal" structure
    market_signal = {
        "source": "AgentMultiSourceResearch",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "query": query,
        "sources_weights": weights,
        "aggregated_data": results,
        "summary_prompt": f"This is an aggregated market signal for '{query}' across {', '.join(sources)}."
    }

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(market_signal, f, ensure_ascii=False, indent=2)

    logger.info("MarketResearch: saved aggregated signals to %s", out_path)
    return out_path

__all__ = ["run_multi_source_research"]
