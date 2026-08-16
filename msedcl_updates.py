"""Fetch MSEDCL recruitment and career updates into MahaUpdate."""
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL = "https://www.mahadiscom.in/en/recruitment-career-options/"
KEYWORDS = ("recruit", "advt", "advertisement", "result", "selection", "wait list", "waiting", "document verification", "corrigendum", "exam", "hall ticket", "candidate")

def clean(text): return re.sub(r"\s+", " ", text or "").strip()
def classify(title):
    t=title.lower()
    if "result" in t:return "Result"
    if "wait" in t:return "Waiting List"
    if "document verification" in t:return "Document Verification"
    if "corrigendum" in t:return "Corrigendum"
    if "exam" in t:return "Exam"
    if "advt" in t or "advertisement" in t:return "Advertisement"
    return "Notification"

def main():
    su=os.getenv("SUPABASE_URL"); sk=os.getenv("SUPABASE_KEY")
    if not su or not sk: raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
    client=create_client(su,sk)
    r=requests.get(URL,timeout=30); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
    now=datetime.now(timezone.utc).isoformat(); seen=set(); added=0
    for a in soup.select("a[href]"):
        title=clean(a.get_text(" ",strip=True)); href=urljoin(URL,a.get("href"))
        if not title or href in seen: continue
        blob=(title+" "+href).lower()
        if not any(k in blob for k in KEYWORDS): continue
        if "mahadiscom.in" not in href: continue
        seen.add(href)
        exists=client.table("updates").select("id").eq("official_url",href).execute().data
        payload={"source":"MSEDCL","title":title,"title_english":title,"title_marathi":"","type":classify(title),"recruitment_title":title,"status":"pending","official_url":href,"first_seen":now,"last_seen":now}
        if exists:
            client.table("updates").update({"last_seen":now,"type":payload["type"]}).eq("official_url",href).execute()
        else:
            client.table("updates").insert(payload).execute(); added+=1
    print(f"MSEDCL sync complete: {added} new updates")

if __name__=="__main__": main()
