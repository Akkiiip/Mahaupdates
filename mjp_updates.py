import os
import re
import warnings
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from notification_validation import create_client
from notification_validation import clean_notification_title, is_valid_notification_title

warnings.filterwarnings("ignore", message="Unverified HTTPS request")
HEADERS = {"User-Agent": "Mozilla/5.0"}
BAD_TITLES = {
    "", "download", "view", "view all", "click here", "click", "pdf", "details",
    "read more", "more", "link", "here", "skip to content", "skip to main content",
    "skip navigation", "what are you looking for", "what are you looking for?",
    "search", "menu", "home", "main content",
}

def clean(value):
    return " ".join(str(value or "").split())

def normalized(value):
    return re.sub(r"[^\w\s]", "", clean(value).lower()).strip()

def valid_title(title):
    return is_valid_notification_title(title)

def title_for_link(anchor):
    """Use the notice cell/heading, never bare navigation link text."""
    direct = clean_notification_title(anchor.get_text(" ", strip=True))
    if valid_title(direct):
        return direct
    row = anchor.find_parent("tr")
    if row:
        candidates = [clean_notification_title(cell.get_text(" ", strip=True))
                      for cell in row.find_all(["th", "td"])]
        for candidate in candidates:
            candidate = re.sub(r"\b(?:download|view|click here|pdf|details)\b", "", candidate, flags=re.I).strip(" -:|")
            if valid_title(candidate):
                return candidate
    for parent in (anchor.find_parent("article"), anchor.find_parent("li"), anchor.find_parent("section")):
        if not parent:
            continue
        heading = parent.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if heading:
            candidate = clean_notification_title(heading.get_text(" ", strip=True))
            if valid_title(candidate):
                return candidate
    return ""

def get_supabase():
    url = os.getenv("SUPABASE_URL"); key = os.getenv("SUPABASE_KEY")
    if not url or not key: raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set.")
    return create_client(url, key)

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status(); return r
    except requests.exceptions.SSLError:
        r = requests.get(url, headers=HEADERS, timeout=30, verify=False); r.raise_for_status(); return r

def classify(title):
    t = (title or "").lower()
    if any(w in t for w in ("result", "merit", "selection list", "shortlist", "score")): return "Result"
    if any(w in t for w in ("admit card", "hall ticket", "call letter")): return "Hall Ticket"
    if any(w in t for w in ("advertisement", "recruitment", "vacancy", "vacancies", "employment notice")): return "Advertisement"
    if any(w in t for w in ("notification", "notice", "corrigendum", "circular")): return "Notification"
    return "Other"

def save_update(client, source, title, official_url):
    now = datetime.now(timezone.utc).isoformat()
    existing = client.table("updates").select("id").eq("official_url", official_url).limit(1).execute().data
    if existing:
        client.table("updates").update({"last_seen": now}).eq("official_url", official_url).execute(); return "EXISTING"
    client.table("updates").insert({"source":source,"title":title[:1000],"type":classify(title),"official_url":official_url,"first_seen":now,"last_seen":now}).execute(); return "NEW"

def run_scraper(source, start_url, keywords):
    client = get_supabase(); soup = BeautifulSoup(fetch(start_url).text, "html.parser")
    seen = set(); new = existing = errors = skipped = 0
    for a in soup.find_all("a", href=True):
        title = title_for_link(a); href = urljoin(start_url, a["href"])
        if not valid_title(title):
            skipped += 1; continue
        if href in seen or href.lower().startswith(("javascript:", "mailto:")): continue
        seen.add(href)
        if not any(k in (title + " " + href).lower() for k in keywords): continue
        try:
            if save_update(client, source, title, href) == "NEW": new += 1
            else: existing += 1
        except Exception as exc:
            errors += 1; print(f"INSERT ERROR: {title[:80]} -> {exc}")
    print(f"{source}: inserted={new}, existing/updated={existing}, skipped_junk={skipped}, insert_errors={errors}")

if __name__ == '__main__':
    run_scraper('Maharashtra Jeevan Pradhikaran', 'https://mjp.maharashtra.gov.in/employee/recruitment/', ('recruit', 'vacan', 'advert', 'notice', 'result', 'exam', 'भरती', 'जाहिरात'))
