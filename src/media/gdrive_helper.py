"""Google Drive / Google Docs text extraction helper."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from config.settings import get_settings
from src.utils import get_logger, retry_with_backoff


@retry_with_backoff(max_retries=3)
def fetch_doc_text(file_id: Optional[str] = None, credentials_path: Optional[str] = None) -> str:
    """Fetch the plain text contents of a Google Doc from Drive.

    Requires a service account JSON path via `GOOGLE_APPLICATION_CREDENTIALS`.
    """
    settings = get_settings()
    logger = get_logger(__name__, log_file=settings.RUN_LOG_FILE)

    resolved_file_id = file_id or settings.GOOGLE_DRIVE_FILE_ID
    if not resolved_file_id:
        raise ValueError("GOOGLE_DRIVE_FILE_ID not configured")

    credentials_file = credentials_path or settings.GOOGLE_APPLICATION_CREDENTIALS
    if not credentials_file:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not configured")

    path = Path(credentials_file)
    if not path.exists():
        raise FileNotFoundError(f"Credentials file not found: {path}")

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except Exception as exc:  # pragma: no cover - runtime import
        raise RuntimeError("Google Drive dependencies are not installed") from exc

    scopes = [scope.strip() for scope in settings.GOOGLE_DRIVE_SCOPES.split(",") if scope.strip()]
    creds = Credentials.from_service_account_file(str(path), scopes=scopes)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    logger.info("Drive: fetching metadata for file_id=%s", resolved_file_id)
    metadata = service.files().get(fileId=resolved_file_id, fields="name,mimeType,description").execute()
    mime_type = metadata.get("mimeType", "")

    try:
        if "google-apps" in mime_type:
            logger.info("Drive: exporting Google Doc text for %s", metadata.get("name"))
            request = service.files().export_media(fileId=resolved_file_id, mimeType="text/plain")
        else:
            logger.info("Drive: downloading media for %s (%s)", metadata.get("name"), mime_type)
            request = service.files().get_media(fileId=resolved_file_id)
        
        content = request.execute()
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return str(content)
    except Exception as e:
        logger.warning("Drive: fetch failed for %s: %s", metadata.get("name"), e)
        return metadata.get("description") or ""


__all__ = ["fetch_doc_text"]