"""Fetch Maharashtra PWD recruitment notices into MahaUpdate pending review."""
import os
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from notification_validation import create_client

URL = "https://pwd.maharashtra.gov.in/en/notice-category/recruitments/"
SOURCE = "PWD"

def classify(title):
    text = title.lower()
    for kind, words in {
        "Result": ("result", "selected", "selection"),
        "Merit List": ("merit",),
        "Advertisement": ("advertisement", "recruitment"),
        "Hall Ticket": ("hall ticket", "admit"),
        "Corrigendum": ("corrigendum", "revised"),
        "Notification": ("notice", "notification"),
    }.items():
        if any(word in text for word in words): return kind
    return "Recruitment Update"

def main():
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    soup = BeautifulSoup(requests.get(URL, timeout=30).text, "html.parser")
    seen = set(); new = 0
    for row in soup.select("tr"):
        text = " ".join(row.stripped_strings)
        link = row.find("a", href=True)
        if not text or not link: continue
        official_url = urljoin(URL, link["href"])
        if official_url in seen: continue
        seen.add(official_url)
        existing = client.table("updates").select("id").eq("official_url", official_url).execute().data
        if existing: continue
        now = datetime.now(timezone.utc).isoformat()
        client.table("updates").insert({"source":SOURCE,"title":text,"title_english":text,"type":classify(text),"recruitment_title":text,"status":"pending","official_url":official_url,"first_seen":now,"last_seen":now}).execute()
        new += 1
    print(f"PWD: {new} new updates added to pending review")

if __name__ == "__main__": main()
