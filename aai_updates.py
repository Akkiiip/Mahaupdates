"""Fetch official Airports Authority of India recruitment updates into MahaUpdate."""
import os
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from supabase import create_client
from seo_utils import clean, classify, seo_metadata

URL='https://www.aai.aero/en/careers/recruitment/Offical'

def main():
    c=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_KEY'])
    soup=BeautifulSoup(requests.get(URL,timeout=30).text,'html.parser')
    now=datetime.now(timezone.utc).isoformat(); added=0; seen=set()
    for row in soup.select('tr'):
        cells=row.find_all(['td','th'])
        if len(cells)<2: continue
        title=clean(cells[0].get_text(' ',strip=True))
        if not title or 'exam name' in title.lower(): continue
        links=[urljoin(URL,a['href']) for a in row.select('a[href]')]
        href=next((u for u in links if 'aai.aero' in u),URL)
        key=f'{title}|{href}'
        if key in seen: continue
        seen.add(key); typ=classify(title)
        payload={'source':'AAI','title':title,'title_english':title,'title_marathi':'','type':typ,'recruitment_title':title,'status':'pending','official_url':href,'first_seen':now,'last_seen':now,**seo_metadata('AAI',title,typ)}
        exists=c.table('updates').select('id').eq('official_url',href).eq('title',title).execute().data
        if exists: c.table('updates').update({'last_seen':now,'type':typ}).eq('official_url',href).eq('title',title).execute()
        else: c.table('updates').insert(payload).execute(); added+=1
    print(f'AAI sync complete: {added} new updates')
if __name__=='__main__': main()
