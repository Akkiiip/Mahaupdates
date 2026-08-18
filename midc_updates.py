"""Print and store recruitment-related links from the official MIDC portal."""

import os
import os
import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from supabase import create_client


URL = "https://recruitment.midcindia.org/default_2023.aspx"

KEYWORDS = (
    "recruitment",
    "advertisement",
    "notification",
    "exam",
    "result",
    "merit",
    "selection",
    "waiting",
    "verification",
    "candidate",
    "corrigendum",
    "भरती",
    "जाहिरात",
    "सुचना",
    "परीक्षा",
    "निकाल",
    "निवड",
    "प्रतिक्षा",
    "पात्र",
    "उमेदवार",
    "पडताळणी",
    "प्रवेशपत्र",
    "मुलाखत",
)


def classify(title):
    title = title.lower()

    rules = [
        (
            "Document Verification",
            ("document verification", "पडताळणी"),
        ),
        (
            "Hall Ticket",
            ("hall ticket", "admit", "प्रवेशपत्र"),
        ),
        (
            "Waiting List",
            ("waiting", "प्रतिक्षा"),
        ),
        (
            "Selection List",
            ("selection", "निवड"),
        ),
        (
            "Merit List",
            ("merit", "गुणवत्ता"),
        ),
        (
            "Result",
            ("result", "निकाल"),
        ),
        (
            "Corrigendum",
            ("corrigendum", "सुधारीत"),
        ),
        (
            "Advertisement",
            ("advertisement", "जाहिरात"),
        ),
        (
            "Notification",
            ("notification", "notice", "सुचना"),
        ),
    ]

    return next(
        (
            kind
            for kind, words in rules
            if any(word in title for word in words)
        ),
        "Other",
    )


def save_update(client, title, full_url):
    table = client.table("updates")

    now = datetime.now(timezone.utc).isoformat()

    if (
        table
        .select("id")
        .eq("official_url", full_url)
        .execute()
        .data
    ):
        (
            table
            .update(
                {
                    "last_seen": now
                }
            )
            .eq("official_url", full_url)
            .execute()
        )

        return "EXISTING"

    table.insert(
        {
            "source": "MIDC",
            "title": title,
            "type": classify(title),
            "advertisement_numbers": re.findall(
                r"\b\d{1,3}/\d{4}\b",
                title,
            ),
            "recruitment_title": title,
            "status": "pending",
            "official_url": full_url,
            "first_seen": now,
            "last_seen": now,
        }
    ).execute()

    return "NEW"


def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print(
            "ERROR: SUPABASE_URL and SUPABASE_KEY must be set."
        )
        return

    supabase = create_client(
        supabase_url,
        supabase_key,
    )

    response = requests.get(
        URL,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    seen = set()

    inserted = 0
    updated = 0

    for link in soup.find_all(
        "a",
        href=True,
    ):
        title = (
            link.find_parent("tr")
            or link
        ).get_text(
            " ",
            strip=True,
        )

        full_url = urljoin(
            URL,
            link["href"],
        )

        combined_text = (
            f"{title} {link['href']}"
        ).lower()

        if (
            full_url not in seen
            and any(
                word in combined_text
                for word in KEYWORDS
            )
        ):
            seen.add(full_url)

            status = save_update(
                supabase,
                title,
                full_url,
            )

            if status == "NEW":
                inserted += 1

            elif status == "EXISTING":
                updated += 1

            print(
                f"STATUS: {status}\n"
                f"TYPE: {classify(title)}\n"
                f"TITLE: {title}\n"
                f"URL: {full_url}\n"
            )

    print(
        f"SUPABASE: inserted={inserted}, "
        f"existing/updated={updated}"
    )


if __name__ == "__main__":
    main()