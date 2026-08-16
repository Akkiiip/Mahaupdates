"""Fetch official MahaTransco career updates into MahaUpdate."""
import os,re
from datetime import datetime,timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client
URL="https://www.mahatransco.in/index.php/career/active/"
KEYWORDS=("recruit","apprentice","advt","advertisement","result","selection","waiting","wait list","document verification","exam","interview","candidate","shortlist","merit")
def clean(s): return re.sub(r"\s+"," ",s or "").strip()
def classify(t):
 t=t.lower()
 for name,words in [("Result",("result","marks")),("Waiting List",("waiting","wait list")),("Selection List",("selection list","select list")),("Document Verification",("document verification",)),("Interview",("interview",)),("Exam",("exam","online test")),("Advertisement",("advt","advertisement","recruitment","apprentice"))]:
  if any(w in t for w in words): return name
 return "Notification"
def main():
 su,sk=os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY")
 if not su or not sk: raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
 c=create_client(su,sk); r=requests.get(URL,timeout=30); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
 now=datetime.now(timezone.utc).isoformat(); seen=set(); added=0
 for row in soup.select("tr"):
  title=clean(row.get_text(" ",strip=True)); a=row.select_one("a[href]")
  if not a or not title: continue
  href=urljoin(URL,a.get("href")); blob=(title+" "+href).lower()
  if href in seen or not any(k in blob for k in KEYWORDS): continue
  if "mahatransco.in" not in href: continue
  seen.add(href); exists=c.table("updates").select("id").eq("official_url",href).execute().data
  p={"source":"MahaTransco","title":title,"title_english":title,"title_marathi":"","type":classify(title),"recruitment_title":title,"status":"pending","official_url":href,"first_seen":now,"last_seen":now}
  if exists:c.table("updates").update({"last_seen":now,"type":p["type"]}).eq("official_url",href).execute()
  else:c.table("updates").insert(p).execute(); added+=1
 print(f"MahaTransco sync complete: {added} new updates")
if __name__=="__main__":main()
