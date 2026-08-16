"""Fetch official Maharashtra DMA What's New recruitment/career notices."""
import os,re
from datetime import datetime,timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from seo_utils import clean,classify,seo_metadata
URL='https://mahadma.maharashtra.gov.in/en/home33/'
KEYWORDS=('recruit','selection','waiting','engineer','appointment','exam','result','advertisement','vacancy','group')
def main():
 su=os.getenv('SUPABASE_URL'); sk=os.getenv('SUPABASE_KEY')
 if not su or not sk:raise RuntimeError('SUPABASE_URL and SUPABASE_KEY are required')
 c=create_client(su,sk); s=BeautifulSoup(requests.get(URL,timeout=30).text,'html.parser'); now=datetime.now(timezone.utc).isoformat(); seen=set(); added=0
 for a in s.select('a[href]'):
  title=clean(a.get_text(' ',strip=True)); href=urljoin(URL,a['href']); blob=(title+' '+href).lower()
  if not title or href in seen or not any(k in blob for k in KEYWORDS) or 'mahadma.maharashtra.gov.in' not in href:continue
  seen.add(href); typ=classify(title); payload={'source':'DMA Maharashtra','title':title,'title_english':title,'title_marathi':'','type':typ,'recruitment_title':title,'status':'pending','official_url':href,'first_seen':now,'last_seen':now,**seo_metadata('DMA Maharashtra',title,typ)}
  exists=c.table('updates').select('id').eq('official_url',href).execute().data
  if exists:c.table('updates').update({'last_seen':now,'type':typ}).eq('official_url',href).execute()
  else:c.table('updates').insert(payload).execute();added+=1
 print(f'DMA sync complete: {added} new updates')
if __name__=='__main__':main()
