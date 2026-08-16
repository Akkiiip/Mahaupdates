"""Fetch recruitment-related links from the official MIDC portal and sync to Supabase."""

import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL = "https://recruitment.midcindia.org/default_2023.aspx"
KEYWORDS = ("recruitment", "advertisement", "notification", "exam", "result", "merit", "selection", "waiting", "verification", "candidate", "corrigendum", "hall ticket", "भरती", "जाहिरात", "सुचना", "सूचना", "परीक्षा", "निकाल", "निवड", "प्रतिक्षा", "प्रतीक्षा", "पात्र", "उमेदवार", "पडताळणी", "प्रवेशपत्र", "मुलाखत")

def contains_marathi(text): return bool(re.search(r"[\u0900-\u097F]", text))
def clean_title(title): return re.sub(r"\s+", " ", title).strip()

def classify(title):
    title = title.lower()
    rules = [("Document Verification", ("document verification", "पडताळणी", "कागदपत्रे", "प्रमाणपत्रे")), ("Hall Ticket", ("hall ticket", "admit", "प्रवेशपत्र")), ("Waiting List", ("waiting", "प्रतिक्षा", "प्रतीक्षा")), ("Selection List", ("selection", "निवड")), ("Merit List", ("merit", "गुणवत्ता")), ("Result", ("result", "निकाल")), ("Corrigendum", ("corrigendum", "सुधारीत")), ("Advertisement", ("advertisement", "जाहिरात")), ("Notification", ("notification", "notice", "सुचना", "सूचना", "सुचनापत्र"))]
    return next((kind for kind, words in rules if any(word in title for word in words)), "Other")

def translate_common_marathi(title):
    translated = title
    for marathi, english in [("सरळसेवा भरती", "Direct Recruitment"), ("भरतीअंतर्गत", "under the recruitment"), ("भरती अंतर्गत", "under the recruitment"), ("अग्निशमन विभाग", "Fire Department"), ("कागदपत्रे", "documents"), ("प्रमाणपत्रे", "certificates"), ("पडताळणीबाबत", "regarding verification"), ("पडताळणी", "verification"), ("सुचनापत्र", "notice"), ("सूचनापत्र", "notice"), ("सुचना", "notice"), ("सूचना", "notice"), ("परीक्षा", "examination"), ("निकाल", "result"), ("प्रारुप", "provisional"), ("निवड यादी", "selection list"), ("निवड", "selection"), ("प्रतिक्षा यादी", "waiting list"), ("प्रतीक्षा यादी", "waiting list"), ("मुलाखतीकरीता", "for interview"), ("मुलाखत", "interview"), ("पात्र उमेदवार", "eligible candidates"), ("उमेदवारांची यादी", "list of candidates"), ("सुधारीत", "revised"), ("अंतर्गत", "under"), ("प्रवेशपत्र", "hall ticket"), ("विभागीय", "divisional"), ("पदाच्या", "for the post of"), ("पदाची", "for the post of"), ("पदासाठी", "for the post"), ("यादी", "list"), ("आवेदनपत्र", "application"), ("अभ्यासक्रमामध्ये", "in the syllabus"), ("अभ्यासक्रमामध्‍ये", "in the syllabus"), ("समावेश", "inclusion"), ("करणेबाबत", "regarding"), ("प्रसिद्ध", "publication"), ("प्रसिध्‍द", "publication"), ("गुणवत्ता यादी", "merit list"), ("गुण", "marks"), ("एकुण", "total"), ("एकूण", "total")]: translated = translated.replace(marathi, english)
    translated = re.sub(r"\bClick\s*(Here)?\b", "", translated, flags=re.I)
    return clean_title(translated)

def get_language_titles(title):
    title = clean_title(title)
    return (title, translate_common_marathi(title)) if contains_marathi(title) else ("", title)

def save_update(client, title, full_url):
    table = client.table("updates"); now = datetime.now(timezone.utc).isoformat(); title_marathi, title_english = get_language_titles(title)
    existing = table.select("id").eq("official_url", full_url).execute().data
    if existing:
        table.update({"title": title, "title_marathi": title_marathi, "title_english": title_english, "type": classify(title), "last_seen": now}).eq("official_url", full_url).execute(); return "EXISTING"
    table.insert({"source": "MIDC", "title": title, "title_marathi": title_marathi, "title_english": title_english, "type": classify(title), "advertisement_numbers": re.findall(r"\b\d{1,3}/\d{4}\b", title), "recruitment_title": title, "status": "pending", "official_url": full_url, "first_seen": now, "last_seen": now}).execute(); return "NEW"

def main():
    supabase_url = os.getenv("SUPABASE_URL"); supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key: print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set."); return
    supabase = create_client(supabase_url, supabase_key); response = requests.get(URL, timeout=30); response.raise_for_status(); soup = BeautifulSoup(response.text, "html.parser")
    seen = set(); inserted = updated = 0
    for link in soup.find_all("a", href=True):
        title = clean_title((link.find_parent("tr") or link).get_text(" ", strip=True)); full_url = urljoin(URL, link["href"]); searchable_text = f"{title} {link['href']}".lower()
        if full_url not in seen and any(word in searchable_text for word in KEYWORDS):
            seen.add(full_url); status = save_update(supabase, title, full_url); inserted += status == "NEW"; updated += status != "NEW"; title_marathi, title_english = get_language_titles(title); print(f"STATUS: {status}\nTYPE: {classify(title)}\nTITLE MARATHI: {title_marathi or 'Not available'}\nTITLE ENGLISH: {title_english or 'Not available'}\nURL: {full_url}\n")
    print(f"SUPABASE: inserted={inserted}, existing/updated={updated}")

if __name__ == "__main__": main()
