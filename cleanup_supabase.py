"""
MahaUpdate database cleanup.
Creates a local JSON backup of affected records before changing Supabase.

Rules:
- DELETE generic/navigation/accessibility records accidentally scraped as updates.
- DELETE social-media/share URLs.
- DELETE obvious homepage/portal records detected from generic titles.
- DELETE date-only AAI titles such as "Updated on 24-07-2026".
- DELETE suspiciously long titles likely containing page boilerplate.

This script only affects explicitly matched bad records.
"""

import os
import re
import json
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

from dotenv import load_dotenv
from supabase import create_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_KEY is missing.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

GENERIC_TITLES = {
    "", "download", "view", "view all", "click here", "click", "read more",
    "more", "details", "pdf", "link", "here",
    "skip to content", "skip to main content", "skip navigation",
    "what are you looking for", "what are you looking for?",
    "search", "menu", "home", "back", "next", "previous",
    "accessibility", "accessibility options", "main content",
}

SOCIAL_DOMAINS = {
    "facebook.com", "www.facebook.com", "x.com", "www.x.com",
    "twitter.com", "www.twitter.com", "linkedin.com", "www.linkedin.com",
    "instagram.com", "www.instagram.com", "youtube.com", "www.youtube.com",
}

DATE_ONLY_PATTERNS = [
    re.compile(r"^updated\s+on\s*[:\-]?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$", re.I),
    re.compile(r"^last\s+updated\s+on\s*[:\-]?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$", re.I),
]


def fetch_all():
    rows = []
    start = 0
    batch_size = 1000
    while True:
        result = supabase.table("updates").select("*").range(start, start + batch_size - 1).execute()
        batch = result.data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        start += batch_size
    return rows


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalized(value):
    # Ignore punctuation differences so "What are you looking for?" and
    # "What are you looking for" are treated as the same junk title.
    return re.sub(r"[^\w\s]", "", clean(value).lower()).strip()


def get_domain(url):
    try:
        return urlparse(str(url or "")).netloc.lower()
    except Exception:
        return ""


def is_social_url(url):
    domain = get_domain(url)
    return domain in SOCIAL_DOMAINS or any(domain.endswith("." + d) for d in SOCIAL_DOMAINS)


def is_date_only_title(title):
    title = clean(title)
    return any(pattern.match(title) for pattern in DATE_ONLY_PATTERNS)


def is_navigation_title(title):
    title_norm = normalized(title)
    generic_norms = {normalized(item) for item in GENERIC_TITLES}
    if title_norm in generic_norms:
        return True
    # Common accessibility/navigation phrases that may gain punctuation or spaces.
    return any(
        phrase in title_norm
        for phrase in (
            "skip to main content", "skip to content", "skip navigation",
            "what are you looking for", "accessibility options",
        )
    )


def find_bad_records(rows):
    bad = []
    for row in rows:
        title = clean(row.get("title"))
        title_norm = normalized(title)
        url = str(row.get("official_url") or "")
        source = clean(row.get("source"))
        reason = None

        if is_navigation_title(title):
            reason = f"generic_or_navigation_title:{title_norm or 'empty'}"
        elif is_social_url(url):
            reason = "social_media_url"
        elif is_date_only_title(title):
            reason = "date_only_title"
        elif len(title) > 500:
            reason = f"suspiciously_long_title:{len(title)}"
        elif source == "DMER Maharashtra" and title_norm in {
            normalized("बॉण्ड सर्व्हिस पोर्टल"), normalized("अर्ज करण्यासाठी येथे क्लिक करा")
        }:
            reason = "portal_navigation"

        if reason:
            item = dict(row)
            item["_cleanup_reason"] = reason
            bad.append(item)
    return bad


def backup_records(records):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mahaupdate_cleanup_backup_{timestamp}.json"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": records,
    }
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, default=str)
    return filename


def delete_records(records):
    deleted = 0
    failed = []
    for row in records:
        row_id = row.get("id")
        try:
            supabase.table("updates").delete().eq("id", row_id).execute()
            deleted += 1
            print(f"DELETED | {row_id} | {row.get('_cleanup_reason')} | {clean(row.get('title'))[:100]}")
        except Exception as exc:
            failed.append({"id": row_id, "error": str(exc), "title": row.get("title")})
            print(f"FAILED | {row_id} | {exc}")
    return deleted, failed


def main():
    print("=" * 70)
    print("MAHAUPDATE DATABASE CLEANUP")
    print("=" * 70)
    rows = fetch_all()
    print(f"Current records: {len(rows)}")
    bad = find_bad_records(rows)
    print(f"\nBad records matched: {len(bad)}")
    if not bad:
        print("No records matched the cleanup rules.")
        return
    from collections import Counter
    reasons = Counter(item["_cleanup_reason"] for item in bad)
    print("\nMATCHED BY RULE")
    for reason, count in reasons.most_common():
        print(f"{reason}: {count}")
    backup_file = backup_records(bad)
    print(f"\nBACKUP CREATED: {backup_file}")
    print("Starting cleanup...\n")
    deleted, failed = delete_records(bad)
    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)
    print(f"Matched: {len(bad)}")
    print(f"Deleted: {deleted}")
    print(f"Failed: {len(failed)}")
    print(f"Backup: {backup_file}")


if __name__ == "__main__":
    main()
