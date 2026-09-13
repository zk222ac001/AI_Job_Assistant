from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings

@dataclass(slots=True)
class GmailMessage:
    message_id: str
    thread_id: str | None
    sender: str
    subject: str
    snippet: str
    received_at: datetime | None

class GmailMonitor:
    """Read-only Gmail REST client using an OAuth access token supplied by the operator."""
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gmail_access_token:
            raise ValueError("GMAIL_ACCESS_TOKEN is not configured")
        self.user_id = settings.gmail_user_id
        self.query = settings.gmail_monitor_query
        self.headers = {"Authorization": f"Bearer {settings.gmail_access_token}"}
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
        self.timeout = settings.email_provider_timeout_seconds

    async def fetch_recent(self, max_messages: int) -> list[GmailMessage]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            listing = await client.get(f"{self.base_url}/users/{self.user_id}/messages", params={"q": self.query, "maxResults": max_messages})
            listing.raise_for_status()
            refs = listing.json().get("messages", [])
            messages = []
            for ref in refs:
                response = await client.get(f"{self.base_url}/users/{self.user_id}/messages/{ref['id']}", params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]})
                response.raise_for_status()
                messages.append(self._convert(response.json()))
            return messages

    @staticmethod
    def _convert(payload: dict[str, object]) -> GmailMessage:
        headers = {str(item.get("name", "")).lower(): str(item.get("value", "")) for item in (payload.get("payload") or {}).get("headers", [])}
        received_at = None
        internal_date = payload.get("internalDate")
        if internal_date:
            try:
                received_at = datetime.fromtimestamp(int(str(internal_date)) / 1000, tz=timezone.utc)
            except (ValueError, TypeError):
                received_at = None
        return GmailMessage(message_id=str(payload.get("id")), thread_id=str(payload.get("threadId")) if payload.get("threadId") else None, sender=headers.get("from", "unknown"), subject=headers.get("subject", ""), snippet=str(payload.get("snippet") or ""), received_at=received_at)
