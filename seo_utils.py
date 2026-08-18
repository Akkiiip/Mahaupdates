"""Shared SEO metadata helpers for MahaUpdate official notices."""
import re
from datetime import datetime

TYPE_TERMS={
 'Recruitment':['Recruitment','Bharti','भरती'], 'Advertisement':['Recruitment Advertisement','Bharti Advertisement','भरती जाहिरात'],
 'Result':['Result','निकाल'], 'Hall Ticket':['Hall Ticket','Admit Card','प्रवेशपत्र'], 'Answer Key':['Answer Key','उत्तरतालिका'],
 'Merit List':['Merit List','गुणवत्ता यादी'], 'Waiting List':['Waiting List','प्रतीक्षा यादी'],
 'Document Verification':['Document Verification','कागदपत्र पडताळणी'], 'Corrigendum':['Corrigendum','शुद्धीपत्रक'], 'Exam':['Exam','परीक्षा'], 'Notification':['Notification','अधिसूचना']}

def clean(text): return re.sub(r'\s+',' ',text or '').strip()
def classify(title):
 t=(title or '').lower()
 if 'answer key' in t:return 'Answer Key'
 if 'hall ticket' in t or 'admit card' in t:return 'Hall Ticket'
 if 'merit' in t:return 'Merit List'
 if 'wait' in t:return 'Waiting List'
 if 'document verification' in t:return 'Document Verification'
 if 'result' in t:return 'Result'
 if 'corrig' in t:return 'Corrigendum'
 if 'exam' in t:return 'Exam'
 if any(x in t for x in ('recruit','bharti','भरती')):return 'Recruitment'
 if any(x in t for x in ('advertisement','advt','vacancy')):return 'Advertisement'
 return 'Notification'

def seo_metadata(source,title,item_type=None,year=None):
 title=clean(title); item_type=item_type or classify(title); year=str(year or datetime.now().year)
 terms=TYPE_TERMS.get(item_type,[item_type]); keywords=[]
 for x in [source,title,item_type,year,'Maharashtra','Maharashtra Government','Maharashtra Govt Jobs',*terms]:
  x=clean(str(x))
  if x and x.lower() not in {k.lower() for k in keywords}:keywords.append(x)
 keywords=keywords[:14]
 seo_title=clean(f'{title} | {source} {item_type} {year} | MahaUpdate')
 description=clean(f'Official {source} {item_type} update: {title}. Check eligibility, dates, result and official notification on MahaUpdate. महाराष्ट्र सरकारी अपडेट आणि भरती माहिती.')
 return {'seo_title':seo_title[:160],'seo_description':description[:300],'seo_keywords':', '.join(keywords)}
