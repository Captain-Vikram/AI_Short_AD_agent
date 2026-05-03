"""Helpers for running Apify actors and retrieving their dataset output.

This helper prefers the `apify_client` SDK but will fall back to a REST
dataset fetch when necessary.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from config.settings import get_settings
from src.utils import get_logger, log_json, retry_with_backoff

try:
    from apify_client import ApifyClient
    HAVE_APIFY_CLIENT = True
except Exception:
    HAVE_APIFY_CLIENT = False


@retry_with_backoff(
    max_retries=3,
    initial_backoff=2.0,
    status_codes=[429, 500, 502, 503, 504],
    exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
    logger_name="apify",
)
def _fetch_dataset_via_rest(dataset_id: str, token: str) -> List[Dict[str, Any]]:
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json&clean=1&limit=10000"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with httpx.Client() as client:
        resp = client.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []


def _parse_apify_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds = seconds / 1000.0
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in (
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _item_start_datetime(item: Dict[str, Any]) -> Optional[datetime]:
    for key in ("startDate", "start_date", "adStartDate", "date", "createdAt", "created_at"):
        parsed = _parse_apify_datetime(item.get(key))
        if parsed is not None:
            return parsed
    return None


def _filter_recent_items(items: List[Dict[str, Any]], max_age_days: int) -> List[Dict[str, Any]]:
    if max_age_days <= 0:
        return items
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    filtered: List[Dict[str, Any]] = []
    for item in items:
        started = _item_start_datetime(item)
        if started is None or started >= cutoff:
            filtered.append(item)
    return filtered


def _as_language_list(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    langs = [part.strip() for part in value.split(",") if part.strip()]
    return langs or None


def run_meta_ads_actor(
    search_query: Optional[str] = None,
    max_age_days: Optional[int] = None,
    target_url: Optional[str] = None,
    country: Optional[str] = None,
    page_id: Optional[str] = None,
    ad_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    token: Optional[str] = None,
    out_path: str = "successful_ads.json",
    wait_for_finish: bool = True,
    poll_interval: int = 5,
    timeout: int = 600,
) -> str:
    """Run the configured Apify actor that scrapes Meta Ads and save JSON output.

    Returns the path to the saved JSON file.
    """
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)

    actor_id = actor_id or settings.APIFY_META_ADS_ACTOR_ID
    token = token or settings.APIFY_API_TOKEN
    if not actor_id:
        raise ValueError("APIFY_META_ADS_ACTOR_ID not configured")
    if not token:
        raise ValueError("APIFY_API_TOKEN not configured")

    logger.info("Apify: starting actor %s", actor_id)
    input_body: Dict[str, Any] = {
        "activeStatus": settings.APIFY_META_ADS_ACTIVE_STATUS,
        "adType": settings.APIFY_META_ADS_AD_TYPE,
        "mediaType": settings.APIFY_META_ADS_MEDIA_TYPE,
        "isTargetedCountry": bool(settings.APIFY_META_ADS_IS_TARGETED_COUNTRY),
        "sortMode": settings.APIFY_META_ADS_SORT_MODE,
        "sortDirection": settings.APIFY_META_ADS_SORT_DIRECTION,
        "maxConcurrency": int(settings.APIFY_META_ADS_MAX_CONCURRENCY),
        "requestHandlerTimeoutSecs": int(settings.APIFY_META_ADS_REQUEST_HANDLER_TIMEOUT_SECS),
    }

    resolved_target_url = target_url or settings.APIFY_META_ADS_TARGET_URL
    if resolved_target_url:
        input_body["targetUrl"] = resolved_target_url
    else:
        input_body["country"] = country or settings.APIFY_META_ADS_COUNTRY
        input_body["searchQuery"] = search_query or settings.APIFY_META_ADS_SEARCH_QUERY
        if page_id or settings.APIFY_META_ADS_PAGE_ID:
            input_body["pageId"] = page_id or settings.APIFY_META_ADS_PAGE_ID
        if ad_id or settings.APIFY_META_ADS_AD_ID:
            input_body["adId"] = ad_id or settings.APIFY_META_ADS_AD_ID

    content_languages = _as_language_list(settings.APIFY_META_ADS_CONTENT_LANGUAGES)
    if content_languages:
        input_body["contentLanguages"] = content_languages

    if settings.APIFY_META_ADS_PROXY_URL:
        input_body["proxyUrl"] = settings.APIFY_META_ADS_PROXY_URL

    log_json(logger, "Apify: run input", input_body)

    items: List[Dict[str, Any]] = []

    if HAVE_APIFY_CLIENT:
        client = ApifyClient(token)
        actor = client.actor(actor_id)
        try:
            # try the modern call signature
            run = actor.call(run_input=input_body)
        except TypeError:
            # some versions accept positional arg
            run = actor.call(input_body)

        # common shapes for dataset id
        dataset_id = run.get("defaultDatasetId") or (run.get("defaultDataset") or {}).get("id") or run.get("datasetId")

        if dataset_id:
            try:
                dataset = client.dataset(dataset_id)
                res = dataset.list_items()
                if isinstance(res, dict):
                    items = res.get("items", [])
                elif isinstance(res, list):
                    items = res
                else:
                    items = getattr(res, "items", []) or []
            except Exception:
                items = _fetch_dataset_via_rest(dataset_id, token)
        else:
            # If dataset_id was not returned, try to locate results via run id
            # (left as future improvement).
            items = []
    else:
        raise RuntimeError("apify-client package not installed; install it or add a REST fallback implementation")

    filtered_items = _filter_recent_items(items, int(max_age_days or settings.APIFY_META_ADS_MAX_AGE_DAYS))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(filtered_items, f, ensure_ascii=False, indent=2)

    logger.info("Apify: saved %d items to %s", len(filtered_items), out_path)
    return out_path


__all__ = ["run_meta_ads_actor"]
