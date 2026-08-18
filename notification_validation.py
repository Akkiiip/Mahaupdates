"""Central validation for titles stored in the MahaUpdate ``updates`` table."""
from __future__ import annotations

import re
import unicodedata


EXACT_JUNK_TITLES = frozenset({
    "", "download", "view", "view all", "pdf", "click", "click here",
    "read more", "more", "details", "link", "here", "home", "menu", "search",
    "back", "next", "previous", "skip to content", "skip to main content",
    "skip navigation", "main content", "accessibility", "accessibility options",
    "what are you looking for", "what are you looking for?",
})

_NAVIGATION_RE = re.compile(
    r"^(?:skip(?:\s+to)?\s+(?:main\s+)?content|skip\s+navigation|"
    r"go\s+to\s+(?:main\s+)?content|(?:open|close)\s+(?:menu|search)|"
    r"(?:site\s+)?search|navigation|breadcrumb|toggle\s+menu|"
    r"accessibility(?:\s+options)?)$",
    re.IGNORECASE,
)


def clean_notification_title(value: object) -> str:
    """Normalize Unicode, invisible spaces, whitespace, and display punctuation."""
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", text).strip()


def normalized_notification_title(value: object) -> str:
    text = clean_notification_title(value).casefold()
    return re.sub(r"[^\w\s]", "", text).strip()


_NORMALIZED_JUNK = frozenset(normalized_notification_title(item) for item in EXACT_JUNK_TITLES)


def is_valid_notification_title(value: object) -> bool:
    """Return False only for clear UI/navigation text; legitimate short notices pass."""
    title = clean_notification_title(value)
    normalized = normalized_notification_title(title)
    if not normalized or normalized in _NORMALIZED_JUNK or _NAVIGATION_RE.fullmatch(normalized):
        return False
    # One-character labels and bare punctuation are UI artifacts.  Do not impose a
    # word-count rule: concise legitimate notices such as "Result" remain valid.
    return any(char.isalnum() for char in title) and len(normalized) >= 2


class _NoopInsert:
    """Mimics a Supabase query response when a rejected record is skipped."""
    data = []
    count = 0

    def execute(self):
        return self


class _ValidatedTable:
    def __init__(self, table, name):
        self._table = table
        self._name = name

    def insert(self, payload, *args, **kwargs):
        if self._name == "updates":
            title = payload.get("title") if isinstance(payload, dict) else None
            if not is_valid_notification_title(title):
                print(f"SKIPPED INVALID NOTIFICATION: {clean_notification_title(title)!r}")
                return _NoopInsert()
            payload = dict(payload)
            payload["title"] = clean_notification_title(title)
        return self._table.insert(payload, *args, **kwargs)

    def update(self, payload, *args, **kwargs):
        if self._name == "updates" and isinstance(payload, dict) and "title" in payload:
            if not is_valid_notification_title(payload["title"]):
                print(f"SKIPPED INVALID NOTIFICATION UPDATE: {clean_notification_title(payload['title'])!r}")
                return _NoopInsert()
            payload = dict(payload)
            payload["title"] = clean_notification_title(payload["title"])
        return self._table.update(payload, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._table, name)


class ValidatedSupabaseClient:
    def __init__(self, client):
        self._client = client

    def table(self, name):
        return _ValidatedTable(self._client.table(name), name)

    def __getattr__(self, name):
        return getattr(self._client, name)


def validated_create_client(factory):
    def create_client(*args, **kwargs):
        return ValidatedSupabaseClient(factory(*args, **kwargs))
    return create_client


# Scrapers import this factory explicitly, making validation independent of
# Python's optional sitecustomize loading behavior.
from supabase import create_client as _supabase_create_client
create_client = validated_create_client(_supabase_create_client)
