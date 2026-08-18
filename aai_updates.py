"""
MAHAUPDATE AAI REPAIR + STRICT SCRAPER

Run once to:
1. Remove known AAI navigation/footer/pagination junk currently in Supabase.
2. Scrape only real AAI recruitment detail URLs.
3. Preserve genuine recruitment records.

Requirements:
    pip install requests beautifulsoup4 supabase
Environment:
    SUPABASE_URL
    SUPABASE_KEY
"""

import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from supabase import create_client


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

START_URL = "https://www.aai.aero/en/careers/recruitment"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

# Only these URL families represent actual recruitment detail content.
VALID_PATH_RE = re.compile(
    r"^/en/recruitment/"
    r"(?:release|press-note|syllabus|result)/\d+/?$",
    re.I,
)

GENERIC_TITLES = {
    "", "download", "view", "view all", "click here", "click",
    "read more", "more", "details", "pdf", "link", "here",
    "skip to content", "skip to main content", "home",
    "exam name", "recruitment dashboard",
}

DATE_ONLY_RE = re.compile(
    r"^(?:updated\s+on|last\s+updated\s+on)\s*[:\-]?\s*"
    r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$",
    re.I,
)

KEYWORDS = (
    "recruit", "vacan", "advert", "notice", "result",
    "exam", "career", "employment", "appointment",
    "selection", "junior", "senior", "manager",
    "assistant", "executive", "gate",
)


def clean(value):
    value = (value or "").replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set."
        )

    return create_client(url, key)


def fetch(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=(10, 45),
    )
    response.raise_for_status()
    return response


def is_real_recruitment_url(url):
    parsed = urlparse(url)

    if parsed.scheme != "https":
        return False

    if parsed.netloc.lower() != "www.aai.aero":
        return False

    return bool(VALID_PATH_RE.match(parsed.path))


def is_valid_title(title):
    title = clean(title)
    lower = title.lower()

    if not title:
        return False

    if lower in GENERIC_TITLES:
        return False

    if DATE_ONLY_RE.match(title):
        return False

    if len(title) < 12 or len(title) > 1000:
        return False

    return True


def find_title(anchor):
    """
    AAI recruitment cards contain multiple detail links for the same
    recruitment notice. Find the closest concise title in that card/row.
    """

    # Look in increasingly larger logical containers.
    for tag_name in ("tr", "article", "li", "section", "div"):
        container = anchor.find_parent(tag_name)

        if not container:
            continue

        candidates = []

        # Strongest candidates: headings.
        for element in container.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        ):
            text = clean(element.get_text(" ", strip=True))
            if is_valid_title(text):
                candidates.append(text)

        # Table cells and paragraphs are common on AAI pages.
        if not candidates:
            for element in container.find_all(["td", "th", "p"]):
                text = clean(element.get_text(" ", strip=True))

                if not is_valid_title(text):
                    continue

                if text.lower().startswith(
                    ("updated on", "last updated")
                ):
                    continue

                candidates.append(text)

        # Prefer a candidate containing recruitment-related words.
        unique = sorted(
            set(candidates),
            key=lambda value: (len(value), value.lower())
        )

        for candidate in unique:
            lower = candidate.lower()
            if any(word in lower for word in KEYWORDS):
                return candidate

        if unique:
            return unique[0]

    return ""


def classify(title, url):
    text = f"{title} {url}".lower()

    if "/result/" in url or any(
        word in text for word in ("result", "merit", "selection")
    ):
        return "Result"

    if "/syllabus/" in url or any(
        word in text for word in ("syllabus", "exam", "examination")
    ):
        return "Exam"

    if any(
        word in text for word in (
            "advertisement", "recruitment", "vacancy",
            "vacancies", "employment"
        )
    ):
        return "Advertisement"

    if "/press-note/" in url or "press note" in text:
        return "Notification"

    return "Recruitment Update"


def save_update(client, title, official_url):
    now = datetime.now(timezone.utc).isoformat()

    existing = (
        client.table("updates")
        .select("id")
        .eq("official_url", official_url)
        .limit(1)
        .execute()
        .data
    )

    payload = {
        "source": "AAI",
        "title": title[:1000],
        "type": classify(title, official_url),
        "official_url": official_url,
        "last_seen": now,
    }

    if existing:
        client.table("updates").update(payload).eq(
            "official_url", official_url
        ).execute()
        return "EXISTING"

    payload["first_seen"] = now
    client.table("updates").insert(payload).execute()
    return "NEW"


def is_bad_existing_aai_record(row):
    """
    Remove only obvious navigation/footer/pagination records.
    Real recruitment detail URLs are never removed by this rule.
    """
    url = clean(row.get("official_url", ""))
    title = clean(row.get("title", ""))
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Preserve all genuine recruitment detail records.
    if is_real_recruitment_url(url):
        return False

    bad_titles = {
        "exam name",
        "recruitment dashboard",
        "careers media medical grievances lost & found shg application cpp portal",
    }

    if title.lower() in bad_titles:
        return True

    # These were inserted by the broad previous version and are not
    # individual recruitment notices.
    if parsed.netloc.lower() != "www.aai.aero":
        return True

    if path in {
        "/en/careers/recruitment",
        "/en/careers/aai-career",
        "/en/media/press-releases",
        "/en/media/latest-news",
        "/en/media/press-clippings",
        "/en/media/photogallery",
        "/en/contact-us",
        "/en/feedback",
        "/en/sitemap",
        "/en/privacy-policy",
        "/en/disclaimer",
        "/en/terms-and-conditions",
        "/en/faqs",
    }:
        return True

    if path.startswith("/en/important-links/"):
        return True

    if path.startswith("/en/aai-mediation-policy"):
        return True

    if path.startswith("/en/annuity"):
        return True

    if path.startswith("/en/node/add/"):
        return True

    # Sorting and pagination URLs are navigation, not notices.
    if parsed.query or "page=" in url.lower():
        return True

    return False


def cleanup_bad_aai(client):
    rows = (
        client.table("updates")
        .select("id,title,official_url")
        .eq("source", "AAI")
        .execute()
        .data
    )

    bad_rows = [
        row for row in rows
        if is_bad_existing_aai_record(row)
    ]

    print(
        f"AAI cleanup: total={len(rows)}, "
        f"bad_navigation_records={len(bad_rows)}"
    )

    deleted = failed = 0

    for row in bad_rows:
        try:
            client.table("updates").delete().eq(
                "id", row["id"]
            ).execute()

            deleted += 1
            print(
                f"DELETED | {row['id']} | "
                f"{clean(row.get('title', ''))[:100]}"
            )

        except Exception as exc:
            failed += 1
            print(
                f"DELETE FAILED | {row['id']} | {exc}"
            )

    print(
        f"AAI cleanup complete: "
        f"deleted={deleted}, failed={failed}"
    )

    return deleted, failed


def scrape_aai(client):
    response = fetch(START_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    seen = set()
    inserted = existing = skipped = errors = 0

    for anchor in soup.find_all("a", href=True):
        url = urljoin(START_URL, anchor["href"])

        if url in seen:
            continue

        seen.add(url)

        if not is_real_recruitment_url(url):
            skipped += 1
            continue

        title = find_title(anchor)

        if not is_valid_title(title):
            skipped += 1
            continue

        try:
            status = save_update(client, title, url)

            if status == "NEW":
                inserted += 1
                print(f"NEW      | {title[:180]}")
            else:
                existing += 1

        except Exception as exc:
            errors += 1
            print(
                f"ERROR | {title[:100]} | {exc}"
            )

    print(
        f"\nAAI: inserted={inserted}, "
        f"existing/updated={existing}, "
        f"skipped={skipped}, errors={errors}"
    )


def main():
    print("=" * 70)
    print("MAHAUPDATE AAI REPAIR + STRICT SCRAPER")
    print("=" * 70)

    client = get_supabase()

    cleanup_bad_aai(client)

    print("\nStarting strict AAI scrape...\n")
    scrape_aai(client)


if __name__ == "__main__":
    main()
