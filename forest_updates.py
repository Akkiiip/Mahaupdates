"""Fetch official Maharashtra Forest Department recruitment notices into MahaUpdate."""
import os,re
from datetime import datetime,timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from notification_validation import create_client
URL="https://mahaforest.gov.in/index.php/fieldoffice/News/index/RlBzMW8rMWFWdjVRWXc9PQ%3D%3D/Ri8wb3Z1dEFTZnhTWlZNPQ%3D%3D/en"
KEYWORDS=("recruitment","recruit","advertisement","appointment","veterinary officer","junior research fellow","selection","waiting","result","exam","interview")
def clean(s):return re.sub(r"\s+"," ",s or "").strip()
def classify(t):
 t=t.lower()
 if "result" in t:return "Result"
 if "waiting" in t:return "Waiting List"
 if "selection" in t:return "Selection List"
 if "interview" in t:return "Interview"
 if "exam" in t:return "Exam"
 if "advertisement" in t or "recruit" in t:return "Advertisement"
 return "Notification"
def main():
 su,sk=os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY")
 if not su or not sk:raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
 c=create_client(su,sk); r=requests.get(URL,timeout=30);r.raise_for_status();soup=BeautifulSoup(r.text,"html.parser")
 now=datetime.now(timezone.utc).isoformat();seen=set();added=0
 for row in soup.select("tr"):
  title=clean(row.get_text(" ",strip=True));a=row.select_one("a[href]")
  if not a or not title:continue
  href=urljoin(URL,a.get("href"));blob=(title+" "+href).lower()
  if href in seen or not any(k in blob for k in KEYWORDS):continue
  if "mahaforest.gov.in" not in href:continue
  seen.add(href);exists=c.table("updates").select("id").eq("official_url",href).execute().data
  p={"source":"Maharashtra Forest Department","title":title,"title_english":title,"title_marathi":"","type":classify(title),"recruitment_title":title,"status":"pending","official_url":href,"first_seen":now,"last_seen":now}
  if exists:c.table("updates").update({"last_seen":now,"type":p["type"]}).eq("official_url",href).execute()
  else:c.table("updates").insert(p).execute();added+=1
 print(f"Forest sync complete: {added} new updates")
if __name__=="__main__":main()
