"""Fetch official MAHAGENCO career and exam updates into MahaUpdate."""
import os,re
from datetime import datetime,timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client
URL="https://www.mahagenco.in/career-advertisement"
KEYWORDS=("recruit","advt","advertisement","result","selection","waiting","corrigendum","exam","notification","candidate","interview")
def clean(s):return re.sub(r"\s+"," ",s or "").strip()
def classify(t):
 t=t.lower()
 if "result" in t:return "Result"
 if "waiting" in t:return "Waiting List"
 if "selection" in t:return "Selection List"
 if "corrigendum" in t:return "Corrigendum"
 if "exam" in t:return "Exam"
 if "interview" in t:return "Interview"
 if "advt" in t or "advertisement" in t or "recruit" in t:return "Advertisement"
 return "Notification"
def main():
 su,sk=os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY")
 if not su or not sk:raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
 c=create_client(su,sk); r=requests.get(URL,timeout=30); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
 now=datetime.now(timezone.utc).isoformat(); seen=set(); added=0
 for a in soup.select("a[href]"):
  title=clean(a.get_text(" ",strip=True)); href=urljoin(URL,a.get("href")); blob=(title+" "+href).lower()
  if not title or href in seen or not any(k in blob for k in KEYWORDS):continue
  if "mahagenco.in" not in href:continue
  seen.add(href); exists=c.table("updates").select("id").eq("official_url",href).execute().data
  p={"source":"MAHAGENCO","title":title,"title_english":title,"title_marathi":"","type":classify(title),"recruitment_title":title,"status":"pending","official_url":href,"first_seen":now,"last_seen":now}
  if exists:c.table("updates").update({"last_seen":now,"type":p["type"]}).eq("official_url",href).execute()
  else:c.table("updates").insert(p).execute();added+=1
 print(f"MAHAGENCO sync complete: {added} new updates")
if __name__=="__main__":main()
