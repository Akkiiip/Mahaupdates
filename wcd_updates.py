"""Fetch active official Women and Child Development Maharashtra recruitment posts."""
import os
from datetime import datetime,timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from notification_validation import create_client
from seo_utils import clean,classify,seo_metadata
URL='https://wcdchrms.in/posts?district_id=39'
def main():
 su=os.getenv('SUPABASE_URL'); sk=os.getenv('SUPABASE_KEY')
 if not su or not sk:raise RuntimeError('SUPABASE_URL and SUPABASE_KEY are required')
 c=create_client(su,sk); s=BeautifulSoup(requests.get(URL,timeout=30).text,'html.parser'); now=datetime.now(timezone.utc).isoformat(); seen=set();added=0
 for a in s.select('a[href]'):
  title=clean(a.get_text(' ',strip=True)); href=urljoin(URL,a['href'])
  if not title or len(title)<3 or href in seen:continue
  if any(x in title.lower() for x in ('privacy','terms','apply','तपशील पहा','back','next')):continue
  if 'wcdchrms.in' not in href:continue
  if not any(x in href.lower() for x in ('post','job','vacan')):continue
  seen.add(href);typ='Recruitment';payload={'source':'Women and Child Development Maharashtra','title':title,'title_english':title,'title_marathi':title if any('\u0900'<=ch<='\u097f' for ch in title) else '','type':typ,'recruitment_title':title,'status':'pending','official_url':href,'first_seen':now,'last_seen':now,**seo_metadata('Women and Child Development Maharashtra',title,typ)}
  exists=c.table('updates').select('id').eq('official_url',href).execute().data
  if exists:c.table('updates').update({'last_seen':now}).eq('official_url',href).execute()
  else:c.table('updates').insert(payload).execute();added+=1
 print(f'WCD sync complete: {added} new updates')
if __name__=='__main__':main()
