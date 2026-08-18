"""Fetch National Health Mission Maharashtra recruitment notices into pending review."""

import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from notification_validation import create_client

URL = "https://nhm.maharashtra.gov.in/en/notice-category/recruitments/"
KEYWORDS = ("recruit", "advertisement", "interview", "eligible", "selection", "result", "vacancy", "post")


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def classify(title):
    text = title.lower()
    if "interview" in text: return "Interview"
    if "eligible" in text: return "Eligible Candidates"
    if "result" in text: return "Result"
    if "selection" in text: return "Selection List"
    if "advertisement" in text or "recruit" in text: return "Advertisement"
    return "Recruitment Update"


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
    now = datetime.now(timezone.utc).isoformat()
    seen = set(); inserted = updated = 0

    for anchor in soup.find_all("a", href=True):
        row = anchor.find_parent("tr") or anchor.find_parent(["article", "li", "div"])
        title = clean((row or anchor).get_text(" ", strip=True))
        href = urljoin(URL, anchor["href"])
        searchable = f"{title} {href}".lower()
        if not title or href in seen or not any(word in searchable for word in KEYWORDS):
            continue
        if not href.startswith(("http://", "https://")):
            continue
        seen.add(href)
        existing = client.table("updates").select("id").eq("official_url", href).execute().data
        payload = {
            "source": "NHM Maharashtra",
            "title": title,
            "title_english": title,
            "title_marathi": "",
            "type": classify(title),
            "recruitment_title": title,
            "official_url": href,
            "last_seen": now,
        }
        if existing:
            client.table("updates").update(payload).eq("official_url", href).execute(); updated += 1
        else:
            payload.update({"status": "pending", "first_seen": now, "advertisement_numbers": []})
            client.table("updates").insert(payload).execute(); inserted += 1

    print(f"NHM Maharashtra: inserted={inserted}, existing/updated={updated}")


if __name__ == "__main__":
    main()
