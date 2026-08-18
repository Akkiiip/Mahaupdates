"""Fetch official Railway Recruitment Control Board employment notices."""
import os
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from notification_validation import create_client
from seo_utils import clean, classify, seo_metadata

URL='https://www.rrcb.gov.in/Employment_notices.html'
KEYWORDS=('cen','technician','alp','ntpc','junior engineer','je','level-1','paramedical','rpf','ministerial','recruitment','employment')

def main():
    c=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_KEY'])
    soup=BeautifulSoup(requests.get(URL,timeout=30).text,'html.parser')
    now=datetime.now(timezone.utc).isoformat(); added=0; seen=set()
    for a in soup.select('a[href]'):
        title=clean(a.get_text(' ',strip=True)); href=urljoin(URL,a['href'])
        if not title or href in seen: continue
        if not any(k in title.lower() for k in KEYWORDS): continue
        if 'rrcb.gov.in' not in href: continue
        seen.add(href); typ=classify(title)
        payload={'source':'Railway RRB','title':title,'title_english':title,'title_marathi':'','type':typ,'recruitment_title':title,'status':'pending','official_url':href,'first_seen':now,'last_seen':now,**seo_metadata('Railway RRB',title,typ)}
        exists=c.table('updates').select('id').eq('official_url',href).execute().data
        if exists: c.table('updates').update({'last_seen':now,'type':typ}).eq('official_url',href).execute()
        else: c.table('updates').insert(payload).execute(); added+=1
    print(f'RRCB sync complete: {added} new updates')
if __name__=='__main__': main()
