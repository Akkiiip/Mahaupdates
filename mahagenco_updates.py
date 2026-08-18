"""Fetch official MAHAGENCO career and exam updates into MahaUpdate."""
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL = "https://www.mahagenco.in/career-advertisement"
KEYWORDS = (
    "recruit", "advt", "advertisement", "result", "selection",
    "waiting", "corrigendum", "exam", "notification", "candidate", "interview",
)
GENERIC_TITLES = {
    "", "download", "view", "view all", "click here", "click", "pdf",
    "details", "read more", "more", "link", "here",
}


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def meaningful(value):
    return clean(value).lower() not in GENERIC_TITLES


def classify(title):
    text = title.lower()
    if "result" in text:
        return "Result"
    if "waiting" in text:
        return "Waiting List"
    if "selection" in text:
        return "Selection List"
    if "corrigendum" in text:
        return "Corrigendum"
    if "exam" in text:
        return "Exam"
    if "interview" in text:
        return "Interview"
    if any(word in text for word in ("advt", "advertisement", "recruit")):
        return "Advertisement"
    return "Notification"


def contextual_title(anchor):
    """Return the notice text associated with a generic Download/View link."""
    direct = clean(anchor.get_text(" ", strip=True))
    if meaningful(direct):
        return direct

    # Tables are common on MAHAGENCO pages: use the other cells in the same row.
    row = anchor.find_parent("tr")
    if row:
        parts = []
        for cell in row.find_all(["th", "td"]):
            text = clean(cell.get_text(" ", strip=True))
            text = re.sub(r"\b(?:download|view|click here|pdf|details)\b", "", text, flags=re.I)
            text = clean(text)
            if meaningful(text):
                parts.append(text)
        if parts:
            return " - ".join(dict.fromkeys(parts))

    # Otherwise look for a meaningful heading/label in the nearest content block.
    for tag in ("li", "article", "section", "div"):
        parent = anchor.find_parent(tag)
        if not parent:
            continue
        for heading in parent.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = clean(heading.get_text(" ", strip=True))
            if meaningful(text):
                return text
        text = clean(parent.get_text(" ", strip=True))
        text = re.sub(r"\b(?:download|view|click here|pdf|details)\b", "", text, flags=re.I)
        text = clean(text)
        if meaningful(text) and len(text) <= 300:
            return text

    # Last resort: nearest preceding heading.
    for heading in anchor.find_all_previous(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = clean(heading.get_text(" ", strip=True))
        if meaningful(text):
            return text
    return ""


def main():
    su = os.getenv("SUPABASE_URL")
    sk = os.getenv("SUPABASE_KEY")
    if not su or not sk:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")

    client = create_client(su, sk)
    response = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 MahaUpdate/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    now = datetime.now(timezone.utc).isoformat()
    seen = set()
    added = updated = skipped_generic = 0

    for anchor in soup.select("a[href]"):
        href = urljoin(URL, anchor.get("href"))
        title = contextual_title(anchor)
        blob = f"{title} {href}".lower()

        if not title or href in seen or not any(keyword in blob for keyword in KEYWORDS):
            continue
        if "mahagenco.in" not in href:
            continue
        if not meaningful(title):
            skipped_generic += 1
            continue

        seen.add(href)
        existing = client.table("updates").select("id").eq("official_url", href).execute().data
        payload = {
            "source": "MAHAGENCO",
            "title": title,
            "title_english": title,
            "title_marathi": "",
            "type": classify(title),
            "recruitment_title": title,
            "status": "pending",
            "official_url": href,
            "first_seen": now,
            "last_seen": now,
        }
        if existing:
            client.table("updates").update({
                "title": title,
                "title_english": title,
                "recruitment_title": title,
                "type": payload["type"],
                "last_seen": now,
            }).eq("official_url", href).execute()
            updated += 1
        else:
            client.table("updates").insert(payload).execute()
            added += 1

    print(f"MAHAGENCO sync complete: {added} new, {updated} updated, {skipped_generic} generic links skipped")


if __name__ == "__main__":
    main()
