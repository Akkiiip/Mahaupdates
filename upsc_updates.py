"""Fetch official UPSC recruitment advertisements and active examination updates."""
import os
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from supabase import create_client
from seo_utils import clean, classify, seo_metadata

URLS=('https://www.upsc.gov.in/recruitment/recruitment-advertisement','https://www.upsc.gov.in/examinations/active-exams')

def main():
    c=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_KEY'])
    now=datetime.now(timezone.utc).isoformat(); added=0; seen=set()
    for URL in URLS:
        soup=BeautifulSoup(requests.get(URL,timeout=30).text,'html.parser')
        for a in soup.select('a[href]'):
            title=clean(a.get_text(' ',strip=True)); href=urljoin(URL,a['href'])
            if not title or len(title)<8 or 'upsc.gov.in' not in href: continue
            low=title.lower()
            if not any(k in low for k in ('advertisement','examination','result','notice','recruitment','interview','test','civil services','engineering services','defence','medical services','geo-scientist')): continue
            if href in seen: continue
            seen.add(href); typ=classify(title)
            payload={'source':'UPSC','title':title,'title_english':title,'title_marathi':'','type':typ,'recruitment_title':title,'status':'pending','official_url':href,'first_seen':now,'last_seen':now,**seo_metadata('UPSC',title,typ)}
            exists=c.table('updates').select('id').eq('official_url',href).execute().data
            if exists: c.table('updates').update({'last_seen':now,'type':typ}).eq('official_url',href).execute()
            else: c.table('updates').insert(payload).execute(); added+=1
    print(f'UPSC sync complete: {added} new updates')
if __name__=='__main__': main()
