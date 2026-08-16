"""Fetch Maharashtra Jeevan Pradhikaran recruitment links into pending review."""
import os
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL = "https://mjp.maharashtra.gov.in/employee/recruitment/"
SOURCE = "MJP"
KEYWORDS = ("recruitment","advertisement","application","corrigendum","exam","hall ticket","result","selection","merit","भरती","जाहिरात","परीक्षा","प्रवेशपत्र","निकाल")

def classify(title):
    t=title.lower()
    if "hall" in t or "प्रवेशपत्र" in title:return "Hall Ticket"
    if "result" in t or "निकाल" in title:return "Result"
    if "merit" in t:return "Merit List"
    if "corrigendum" in t or "शुद्धिपत्रक" in title:return "Corrigendum"
    if "advertisement" in t or "जाहिरात" in title:return "Advertisement"
    return "Recruitment Update"

def main():
    client=create_client(os.environ["SUPABASE_URL"],os.environ["SUPABASE_KEY"])
    soup=BeautifulSoup(requests.get(URL,timeout=30).text,"html.parser")
    added=0; seen=set()
    for a in soup.find_all("a",href=True):
        title=" ".join(a.stripped_strings)
        if not title or not any(k in (title+" "+a["href"]).lower() for k in KEYWORDS): continue
        official_url=urljoin(URL,a["href"])
        if official_url in seen:continue
        seen.add(official_url)
        if client.table("updates").select("id").eq("official_url",official_url).execute().data:continue
        now=datetime.now(timezone.utc).isoformat()
        client.table("updates").insert({"source":SOURCE,"title":title,"title_marathi":title if any('\u0900'<=c<='\u097f' for c in title) else "","title_english":title if not any('\u0900'<=c<='\u097f' for c in title) else "","type":classify(title),"recruitment_title":title,"status":"pending","official_url":official_url,"first_seen":now,"last_seen":now}).execute();added+=1
    print(f"MJP: {added} new updates added to pending review")
if __name__=="__main__":main()
