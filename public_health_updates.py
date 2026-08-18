"""Fetch Maharashtra Public Health Department recruitment advertisements into pending review."""
import os
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL="https://phd.maharashtra.gov.in/en/document-category/advertisement/"
SOURCE="Public Health Department"

def classify(title):
    t=title.lower()
    if "corrigendum" in t:return "Corrigendum"
    if "result" in t:return "Result"
    if "merit" in t:return "Merit List"
    if "advertisement" in t or "recruitment" in t:return "Advertisement"
    return "Recruitment Update"

def main():
    client=create_client(os.environ["SUPABASE_URL"],os.environ["SUPABASE_KEY"])
    soup=BeautifulSoup(requests.get(URL,timeout=30).text,"html.parser")
    added=0;seen=set()
    for row in soup.select("tr"):
        cells=list(row.stripped_strings);link=row.find("a",href=True)
        if not cells or not link:continue
        title=cells[0];official_url=urljoin(URL,link["href"])
        if official_url in seen:continue
        seen.add(official_url)
        if client.table("updates").select("id").eq("official_url",official_url).execute().data:continue
        now=datetime.now(timezone.utc).isoformat()
        client.table("updates").insert({"source":SOURCE,"title":title,"title_english":title,"type":classify(title),"recruitment_title":title,"status":"pending","official_url":official_url,"first_seen":now,"last_seen":now}).execute();added+=1
    print(f"Public Health Department: {added} new updates added to pending review")
if __name__=="__main__":main()
