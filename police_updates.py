"""Fetch Maharashtra Police recruitment updates and send new items to Supabase pending review."""

import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL = "https://www.mahapolice.gov.in/police-recruitment"
KEYWORDS = (
    "भरती", "recruitment", "selection", "निवड", "waiting", "प्रतीक्षा",
    "merit", "गुण", "result", "निकाल", "hall ticket", "प्रवेशपत्र",
    "answer", "उत्तर", "verification", "पडताळणी", "exam", "परीक्षा"
)


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def classify(title):
    text = title.lower()
    rules = [
        ("Document Verification", ("verification", "पडताळणी")),
        ("Hall Ticket", ("hall ticket", "admit", "प्रवेशपत्र")),
        ("Answer Key", ("answer key", "उत्तरतालिका", "उत्तर तालिका")),
        ("Waiting List", ("waiting", "प्रतीक्षा", "प्रतिक्षा")),
        ("Selection List", ("selection", "निवड")),
        ("Merit List", ("merit", "गुणवत्ता")),
        ("Result", ("result", "निकाल", "गुणपत्रक")),
        ("Advertisement", ("advertisement", "जाहिरात")),
        ("Exam", ("exam", "परीक्षा", "मैदानी चाचणी")),
    ]
    return next((kind for kind, words in rules if any(word in text for word in words)), "Recruitment Update")


def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set.")
        return

    client = create_client(supabase_url, supabase_key)
    response = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 MahaUpdate/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    seen = set()
    inserted = updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for anchor in soup.find_all("a", href=True):
        parent = anchor.find_parent(["article", "li", "tr", "div"])
        title = clean((parent or anchor).get_text(" ", strip=True))
        href = urljoin(URL, anchor["href"])
        searchable = f"{title} {href}".lower()

        if not title or href in seen or not any(keyword.lower() in searchable for keyword in KEYWORDS):
            continue
        if not href.startswith(("http://", "https://")):
            continue

        seen.add(href)
        existing = client.table("updates").select("id").eq("official_url", href).execute().data
        payload = {
            "source": "Maharashtra Police",
            "title": title,
            "title_marathi": title if re.search(r"[\u0900-\u097F]", title) else "",
            "title_english": title if not re.search(r"[\u0900-\u097F]", title) else "",
            "type": classify(title),
            "recruitment_title": title,
            "official_url": href,
            "last_seen": now,
        }
        if existing:
            client.table("updates").update(payload).eq("official_url", href).execute()
            updated += 1
        else:
            payload.update({"status": "pending", "first_seen": now, "advertisement_numbers": []})
            client.table("updates").insert(payload).execute()
            inserted += 1

    print(f"Maharashtra Police: inserted={inserted}, existing/updated={updated}")


if __name__ == "__main__":
    main()
