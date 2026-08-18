"""Fetch Maharashtra Police recruitment updates and store/update them in Supabase."""
import os, re, sys
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "https://www.mahapolice.gov.in/police-recruitment"
KEYWORDS = ("भरती","recruitment","selection","निवड","waiting","प्रतीक्षा","merit","गुण","result","निकाल","hall ticket","प्रवेशपत्र","answer","उत्तर","verification","पडताळणी","exam","परीक्षा")
GENERIC = {"download","view","click here","click","pdf","details",""}

def clean(value):
    return re.sub(r"\s+", " ", (value or "").replace("\u200b","")).strip()

def meaningful(text):
    return bool(clean(text)) and clean(text).lower() not in GENERIC

def classify(title):
    text=title.lower()
    rules=[
      ("Document Verification",("verification","पडताळणी")),
      ("Hall Ticket",("hall ticket","admit","प्रवेशपत्र")),
      ("Answer Key",("answer key","उत्तरतालिका","उत्तर तालिका")),
      ("Waiting List",("waiting","प्रतीक्षा","प्रतिक्षा")),
      ("Selection List",("selection","निवड")),
      ("Merit List",("merit","गुणवत्ता")),
      ("Result",("result","निकाल","गुणपत्रक")),
      ("Advertisement",("advertisement","जाहिरात")),
      ("Exam",("exam","परीक्षा","मैदानी चाचणी")),
    ]
    return next((k for k,w in rules if any(x in text for x in w)),"Recruitment Update")

def find_title_for_anchor(anchor):
    for name in ("article","li","tr","section","div"):
        parent=anchor.find_parent(name)
        if not parent: continue
        for h in parent.find_all(["h1","h2","h3","h4","h5","h6"]):
            text=clean(h.get_text(" ",strip=True))
            if meaningful(text): return text
        if parent.name=="tr":
            for cell in parent.find_all(["td","th"]):
                text=clean(re.sub(r"\b(?:Download|View)\b","",cell.get_text(" ",strip=True),flags=re.I))
                if meaningful(text): return text
    for el in anchor.find_all_previous(["h1","h2","h3","h4","h5","h6"]):
        text=clean(el.get_text(" ",strip=True))
        if meaningful(text): return text
    return ""

def candidate_links(soup):
    best={}
    for a in soup.find_all("a",href=True):
        label=clean(a.get_text(" ",strip=True)).lower()
        if label not in ("download","view"): continue
        href=urljoin(URL,a["href"])
        if not href.startswith(("http://","https://")): continue
        title=find_title_for_anchor(a)
        if not meaningful(title): continue
        if not any(k.lower() in f"{title} {href}".lower() for k in KEYWORDS): continue
        priority=0 if label=="download" else 1
        key=clean(title).lower()
        if key not in best or priority<best[key][2]: best[key]=(title,href,priority)
    return [(t,u) for t,u,_ in best.values()]

def main():
    su=os.getenv("SUPABASE_URL"); sk=os.getenv("SUPABASE_KEY")
    if not su or not sk:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set."); return
    client=create_client(su,sk)
    r=requests.get(URL,timeout=(10,45),headers={"User-Agent":"Mozilla/5.0 MahaUpdate/1.0"})
    r.raise_for_status()
    items=candidate_links(BeautifulSoup(r.text,"html.parser"))
    print(f"Maharashtra Police: notices found={len(items)}")
    inserted=updated=0; now=datetime.now(timezone.utc).isoformat()
    for title,href in items:
        existing=client.table("updates").select("id").eq("official_url",href).execute().data
        payload={"source":"Maharashtra Police","title":title,
          "title_marathi":title if re.search(r"[\u0900-\u097F]",title) else "",
          "title_english":title if not re.search(r"[\u0900-\u097F]",title) else "",
          "type":classify(title),"recruitment_title":title,"official_url":href,"last_seen":now}
        if existing:
            client.table("updates").update(payload).eq("official_url",href).execute(); updated+=1
        else:
            payload.update({"status":"pending","first_seen":now,"advertisement_numbers":[]})
            client.table("updates").insert(payload).execute(); inserted+=1
    print(f"Maharashtra Police: inserted={inserted}, existing/updated={updated}")

if __name__=="__main__":
    main()
