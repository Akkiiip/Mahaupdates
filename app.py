import os
from datetime import datetime, timezone
from urllib.parse import quote, unquote

from flask import Flask, render_template_string, request, redirect, url_for
from supabase import create_client

app = Flask(__name__)
UPDATES_PER_PAGE = 10

PAGE = """
<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ page_title }} | MahaUpdate</title><style>
:root{--navy:#0b1f3a;--navy-light:#173b68;--saffron:#f59e0b;--bg:#f5f7fa;--card:#fff;--text:#172033;--muted:#667085;--border:#e5e7eb;--green:#22c55e;--red:#dc2626}*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans Devanagari",sans-serif;background:var(--bg);color:var(--text)}header{background:var(--navy);color:#fff}.header-container{max-width:1180px;margin:auto;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none}.logo{width:34px;height:34px;border-radius:10px;background:var(--saffron)}.brand-name{font-size:19px;font-weight:800}.brand-tagline{font-size:11px;opacity:.75}nav{display:flex;gap:8px}nav a{color:#dbe5f4;text-decoration:none;padding:9px 11px;border-radius:8px;font-size:14px;font-weight:650}nav a:hover,nav a.active{background:#ffffff18;color:#fff}.mobile-menu-button{display:none;background:none;border:0;color:#fff;font-size:24px}.container{max-width:1100px;margin:auto;padding:28px 18px 40px}.hero{background:linear-gradient(135deg,var(--navy),var(--navy-light));color:#fff;border-radius:20px;padding:34px;margin-bottom:24px}.hero h1{margin:0 0 10px}.source-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:24px}.source-card,.update-card,.filter-panel,.empty,.ad-large,.admin-card{background:#fff;border:1px solid var(--border);border-radius:15px;padding:18px}.source-card{text-decoration:none;color:inherit}.filter-row{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:10px}input,select{height:46px;border:1px solid var(--border);border-radius:9px;padding:0 12px;font-size:14px;background:#fff}.button{display:inline-flex;justify-content:center;align-items:center;min-height:44px;padding:0 17px;border:0;border-radius:9px;background:var(--navy);color:#fff;text-decoration:none;font-size:14px;font-weight:700;cursor:pointer}.button:hover{background:var(--navy-light)}.clear-link{display:inline-flex;margin-top:12px;color:var(--muted);text-decoration:none;font-size:13px}.updates{display:grid;gap:13px}.update-top{display:flex;justify-content:space-between;gap:15px;margin-bottom:12px}.badges{display:flex;gap:7px;flex-wrap:wrap}.badge{padding:5px 9px;border-radius:20px;font-size:11px;font-weight:750}.badge-mpsc{background:#eaf1ff;color:#285da8}.badge-midc{background:#fff1dc;color:#a65b00}.badge-type{background:#f1f3f6;color:#586273}.date{font-size:12px;color:var(--muted);white-space:nowrap}.official-button{display:inline-flex;margin-top:14px;padding:10px 14px;border-radius:9px;background:var(--navy);color:#fff;text-decoration:none;font-weight:700}.pagination{display:flex;justify-content:center;gap:8px;margin-top:24px}.pagination a,.pagination span{min-width:38px;height:38px;display:grid;place-items:center;border-radius:8px;text-decoration:none;border:1px solid var(--border);background:#fff;color:var(--text)}.pagination .current{background:var(--navy);color:#fff}.ad-large{min-height:110px;text-align:center;color:var(--muted);display:grid;place-content:center;gap:6px}.ad-label{text-transform:uppercase;font-size:10px;letter-spacing:1px}.empty{text-align:center;color:var(--muted);padding:35px}.admin-link{font-size:12px;opacity:.8}.admin-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}.stat-number{font-size:30px;font-weight:800;color:var(--navy)}.admin-list{display:grid;gap:12px}.meta{font-size:12px;color:var(--muted)}.actions{display:flex;gap:8px;margin-top:14px}.publish{background:var(--green)}.reject{background:#fee2e2;color:#991b1b}.bell{position:relative;display:inline-flex;align-items:center;justify-content:center;font-size:22px;margin-left:10px}.bubble{position:absolute;top:-9px;right:-10px;background:var(--red);color:#fff;border-radius:20px;padding:2px 6px;font-size:10px;font-weight:800}.toast{position:fixed;right:20px;bottom:20px;background:var(--navy);color:#fff;padding:16px 20px;border-radius:12px;box-shadow:0 10px 30px #0003;display:none;z-index:20}.toast.show{display:block}footer{background:#fff;border-top:1px solid var(--border);text-align:center;padding:25px;color:var(--muted);font-size:12px}@media(max-width:750px){.header-container{padding:12px 15px}.mobile-menu-button{display:block}nav{display:none;position:absolute;top:68px;left:0;right:0;background:var(--navy);padding:12px 15px 18px;flex-direction:column;z-index:10}nav.open{display:flex}.container{padding:20px 12px 35px}.hero{padding:25px 20px}.hero h1{font-size:25px}.source-grid,.filter-row,.admin-stats{grid-template-columns:1fr}.update-top{flex-direction:column;gap:8px}.official-button{width:100%;justify-content:center}}
</style></head><body><header><div class="header-container"><a href="/" class="brand"><div class="logo"></div><div><div class="brand-name">MahaUpdate</div><div class="brand-tagline">Maharashtra Government Updates</div></div></a><button class="mobile-menu-button" onclick="toggleMenu()">☰</button><nav id="main-nav"><a href="/" class="{{ 'active' if active_page == 'home' }}">Home</a><a href="/updates" class="{{ 'active' if active_page == 'updates' }}">All Updates</a><a href="/mpsc" class="{{ 'active' if active_page == 'mpsc' }}">MPSC</a><a href="/midc" class="{{ 'active' if active_page == 'midc' }}">MIDC</a><a href="/about" class="{{ 'active' if active_page == 'about' }}">About</a></nav>{% if pending_count is defined %}<a class="bell" href="/admin" title="Pending updates">🔔{% if pending_count %}<span class="bubble">{{ pending_count }}</span>{% endif %}</a>{% endif %}</div></header><main class="container">
{% if page_type == 'admin' %}<h1>Notification Review Dashboard</h1><p>Review new government updates before publishing them publicly.</p><div class="admin-stats"><div class="admin-card"><div class="stat-number">{{ pending_count }}</div>Pending Review</div><div class="admin-card"><div class="stat-number">{{ published_count }}</div>Published</div><div class="admin-card"><div class="stat-number">{{ rejected_count }}</div>Rejected</div></div><h2>Pending Notifications</h2><section class="admin-list">{% for item in updates %}<article class="update-card"><div class="meta">{{ item.get('source','Government') }} · {{ item.get('type','Update') }} · {{ format_date(item.get('first_seen')) }}</div><h3>{{ item.get('title_english') or item.get('title') }}</h3>{% if item.get('title_marathi') %}<p>{{ item.get('title_marathi') }}</p>{% endif %}<div class="actions"><form method="post" action="{{ url_for('publish_update', update_id=item['id']) }}"><button class="button publish">Publish</button></form><form method="post" action="{{ url_for('reject_update', update_id=item['id']) }}"><button class="button reject">Reject</button></form></div></article>{% else %}<div class="empty"><h3>No pending notifications</h3><p>New updates found by your scrapers will appear here.</p></div>{% endfor %}</section><div id="toast" class="toast">🔔 You have {{ pending_count }} update{{ '' if pending_count == 1 else 's' }} waiting for review.</div>{% elif page_type == 'home' %}<section class="hero"><h1>Maharashtra Government Updates, Simplified.</h1><p>Stay updated with official notifications, results, answer keys, recruitment updates and important announcements.</p></section><div class="source-grid"><a href="/mpsc" class="source-card"><h3>MPSC</h3><p>Maharashtra Public Service Commission updates, results, answer keys and notifications.</p></a><a href="/midc" class="source-card"><h3>MIDC</h3><p>Maharashtra Industrial Development Corporation recruitment and official updates.</p></a></div>{% elif page_type == 'about' %}<section class="hero"><h1>About MahaUpdate</h1><p>MahaUpdate collects important notices from official Maharashtra government sources and links back to the original source.</p></section>{% else %}<div class="filter-panel">{% if show_filters %}<form class="filter-row" method="get"><input name="search" value="{{ search }}" placeholder="Search updates"><select name="source"><option value="">All sources</option>{% for source in sources %}<option value="{{ source }}" {% if source == selected_source %}selected{% endif %}>{{ source }}</option>{% endfor %}</select><select name="type"><option value="">All types</option>{% for item_type in types %}<option value="{{ item_type }}" {% if item_type == update_type %}selected{% endif %}>{{ item_type }}</option>{% endfor %}</select><button class="button">Search</button></form><a class="clear-link" href="{{ current_path }}">Clear filters</a>{% endif %}</div>{% if updates %}<section class="updates">{% for item in updates %}<article class="update-card"><div class="update-top"><div class="badges"><span class="badge badge-{{ item.get('source','').lower() }}">{{ item.get('source','Government') }}</span><span class="badge badge-type">{{ item.get('type','Update') }}</span></div><span class="date">{{ format_date(item.get('first_seen')) }}</span></div><h3>{{ item.get('title') }}</h3><a class="official-button" href="/go?url={{ quote(item.get('official_url','')) }}" target="_blank">View Official Update</a></article>{% if loop.index in [3,7] and loop.index < updates|length %}<div class="ad-large"><div class="ad-label">Advertisement</div><strong>Large Ad Space</strong><span>Advertisement will appear here</span></div>{% endif %}{% endfor %}</section>{% else %}<div class="empty"><h3>No updates found</h3><p>Try changing your search or filters.</p></div>{% endif %}{% if total_pages > 1 %}<div class="pagination">{% if page > 1 %}<a href="{{ pagination_url(page - 1) }}">←</a>{% endif %}{% for number in range(1,total_pages+1) %}{% if number == page %}<span class="current">{{ number }}</span>{% else %}<a href="{{ pagination_url(number) }}">{{ number }}</a>{% endif %}{% endfor %}{% if page < total_pages %}<a href="{{ pagination_url(page + 1) }}">→</a>{% endif %}</div>{% endif %}{% endif %}</main><footer><strong>MahaUpdate</strong><br>Latest updates from official Maharashtra government sources.</footer><script>function toggleMenu(){document.getElementById('main-nav').classList.toggle('open')}{% if page_type == 'admin' and pending_count %}setTimeout(()=>document.getElementById('toast').classList.add('show'),500);setTimeout(()=>document.getElementById('toast').classList.remove('show'),7000);{% endif %}</script></body></html>
"""

def get_supabase():
    url=os.getenv('SUPABASE_URL'); key=os.getenv('SUPABASE_KEY')
    if not url or not key: raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set.')
    return create_client(url,key)

def get_all_updates(published_only=True):
    query=get_supabase().table('updates').select('*').order('first_seen',desc=True)
    if published_only: query=query.eq('status','published')
    return query.execute().data or []

def get_status_rows(status):
    return get_supabase().table('updates').select('*').eq('status',status).order('first_seen',desc=True).execute().data or []

def pending_count():
    return len(get_status_rows('pending'))

def format_date(value):
    if not value:return ''
    try:
        date=datetime.fromisoformat(str(value).replace('Z','+00:00')); now=datetime.now(date.tzinfo or timezone.utc); diff=(now.date()-date.date()).days
        return 'Today' if diff==0 else 'Yesterday' if diff==1 else date.strftime('%d %b %Y')
    except Exception:return str(value)[:10]

def get_page_number():
    try:return max(1,int(request.args.get('page',1)))
    except (ValueError,TypeError):return 1

def filter_updates(updates,fixed_source=None):
    search=request.args.get('search','').strip(); selected_source=request.args.get('source',''); update_type=request.args.get('type','')
    filtered=[]
    for update in updates:
        if fixed_source and update.get('source')!=fixed_source:continue
        if not fixed_source and selected_source and update.get('source')!=selected_source:continue
        if update_type and update.get('type')!=update_type:continue
        haystack=' '.join(str(update.get(k,'')) for k in ('title','title_english','title_marathi')).lower()
        if search and search.lower() not in haystack:continue
        filtered.append(update)
    return filtered,search,selected_source,update_type

def paginate(items,page):
    total=len(items); pages=max(1,(total+UPDATES_PER_PAGE-1)//UPDATES_PER_PAGE); page=min(page,pages); start=(page-1)*UPDATES_PER_PAGE
    return items[start:start+UPDATES_PER_PAGE],total,pages,page

def render_page(page_type,page_title,active_page,fixed_source=None,home=False,show_filters=True):
    try: all_updates=get_all_updates()
    except Exception as error:return f'<h2>MahaUpdate Error</h2><p>{error}</p>',500
    sources=sorted({x.get('source') for x in all_updates if x.get('source')}); types=sorted({x.get('type') for x in all_updates if x.get('type')})
    if home: filtered=all_updates[:10]; search=selected_source=update_type=''
    else: filtered,search,selected_source,update_type=filter_updates(all_updates,fixed_source)
    updates,total,total_pages,page=paginate(filtered,get_page_number())
    if home: total_pages=1; page=1
    def pagination_url(number):
        params=[]
        if search:params.append('search='+quote(search))
        if selected_source and not fixed_source:params.append('source='+quote(selected_source))
        if update_type:params.append('type='+quote(update_type))
        params.append('page='+str(number)); return request.path+'?'+'&'.join(params)
    return render_template_string(PAGE,page_type=page_type,page_title=page_title,active_page=active_page,show_filters=show_filters,updates=updates,total_updates=total,total_pages=total_pages,page=page,sources=sources,types=types,search=search,selected_source=selected_source,update_type=update_type,current_path=request.path,pagination_url=pagination_url,format_date=format_date,quote=quote,pending_count=pending_count())

@app.route('/')
def home():return render_page('home','MahaUpdate','home',home=True,show_filters=False)
@app.route('/updates')
def updates_page():return render_page('updates','All Updates','updates')
@app.route('/mpsc')
def mpsc_page():return render_page('mpsc','MPSC Updates','mpsc',fixed_source='MPSC')
@app.route('/midc')
def midc_page():return render_page('midc','MIDC Updates','midc',fixed_source='MIDC')
@app.route('/about')
def about_page():return render_page('about','About','about',show_filters=False)
@app.route('/admin')
def admin_page():
    pending=get_status_rows('pending'); published=get_status_rows('published'); rejected=get_status_rows('rejected')
    return render_template_string(PAGE,page_type='admin',page_title='Admin',active_page='',show_filters=False,updates=pending,pending_count=len(pending),published_count=len(published),rejected_count=len(rejected),format_date=format_date)
@app.post('/admin/publish/<update_id>')
def publish_update(update_id):
    get_supabase().table('updates').update({'status':'published','published_at':datetime.now(timezone.utc).isoformat()}).eq('id',update_id).execute(); return redirect(url_for('admin_page'))
@app.post('/admin/reject/<update_id>')
def reject_update(update_id):
    get_supabase().table('updates').update({'status':'rejected'}).eq('id',update_id).execute(); return redirect(url_for('admin_page'))
@app.route('/go')
def go_to_official():
    url=unquote(request.args.get('url',''))
    return redirect(url) if url.startswith(('http://','https://')) else redirect('/updates')

if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=False)
