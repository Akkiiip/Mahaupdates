import os
from datetime import datetime

from flask import Flask, redirect, render_template_string, request, url_for
from supabase import create_client

app = Flask(__name__)

PAGE = '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MahaUpdate Admin</title><style>
body{margin:0;font-family:system-ui;background:#f5f7fa;color:#172033}.top{background:#0b1f3a;color:#fff;padding:18px 5%;display:flex;justify-content:space-between;align-items:center}.top a{color:#fff;text-decoration:none}.wrap{max-width:1100px;margin:auto;padding:28px 18px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.stat,.card{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:20px}.num{font-size:30px;font-weight:800;color:#0b1f3a}.cards{display:grid;gap:12px;margin-top:20px}.meta{font-size:12px;color:#667085;margin-bottom:8px}.actions{display:flex;gap:8px;margin-top:14px}.btn{border:0;border-radius:8px;padding:9px 13px;font-weight:700;cursor:pointer}.publish{background:#22c55e;color:white}.reject{background:#fee2e2;color:#b91c1c}.bell{position:relative;font-size:22px}.bubble{position:absolute;top:-8px;right:-11px;background:#ef4444;color:#fff;border-radius:20px;padding:2px 6px;font-size:11px}.empty{text-align:center;color:#667085;padding:45px}.toast{position:fixed;right:20px;bottom:20px;background:#0b1f3a;color:#fff;padding:16px 20px;border-radius:12px;box-shadow:0 10px 30px #0003;display:none}.toast.show{display:block}@media(max-width:650px){.stats{grid-template-columns:1fr}.top{padding:15px}.wrap{padding:18px 12px}}
</style></head><body><div class="top"><a href="{{ public_url }}">← Back to Website</a><strong>MahaUpdate Admin</strong><div class="bell">🔔{% if pending_count %}<span class="bubble">{{ pending_count }}</span>{% endif %}</div></div><main class="wrap"><h1>Notification Review Dashboard</h1><p>Review new government updates before publishing them publicly.</p><div class="stats"><div class="stat"><div class="num">{{ pending_count }}</div>Pending Review</div><div class="stat"><div class="num">{{ published_count }}</div>Published</div><div class="stat"><div class="num">{{ rejected_count }}</div>Rejected</div></div><h2>Pending Notifications</h2><section class="cards">{% for item in pending %}<article class="card"><div class="meta">{{ item.get('source','Government') }} · {{ item.get('type','Update') }} · {{ item.get('first_seen','') }}</div><h3>{{ item.get('title_english') or item.get('title') }}</h3>{% if item.get('title_marathi') %}<p>{{ item.get('title_marathi') }}</p>{% endif %}<div class="actions"><form method="post" action="{{ url_for('publish', update_id=item['id']) }}"><button class="btn publish">Publish</button></form><form method="post" action="{{ url_for('reject', update_id=item['id']) }}"><button class="btn reject">Reject</button></form></div></article>{% else %}<div class="card empty">No pending notifications. New updates found by your scrapers will appear here.</div>{% endfor %}</section></main><div id="toast" class="toast">🔔 You have {{ pending_count }} update{{ '' if pending_count == 1 else 's' }} waiting for review.</div><script>{% if pending_count %}setTimeout(()=>document.getElementById('toast').classList.add('show'),500);setTimeout(()=>document.getElementById('toast').classList.remove('show'),7000);{% endif %}</script></body></html>'''

def client():
    url=os.getenv('SUPABASE_URL'); key=os.getenv('SUPABASE_KEY')
    if not url or not key: raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set.')
    return create_client(url,key)

def rows(status):
    return client().table('updates').select('*').eq('status',status).order('first_seen',desc=True).execute().data or []

@app.get('/admin')
def admin():
    pending=rows('pending'); published=rows('published'); rejected=rows('rejected')
    return render_template_string(PAGE,pending=pending,pending_count=len(pending),published_count=len(published),rejected_count=len(rejected),public_url=os.getenv('PUBLIC_SITE_URL','http://127.0.0.1:5000/'))

@app.post('/admin/publish/<update_id>')
def publish(update_id):
    client().table('updates').update({'status':'published','published_at':datetime.utcnow().isoformat()}).eq('id',update_id).execute()
    return redirect(url_for('admin'))

@app.post('/admin/reject/<update_id>')
def reject(update_id):
    client().table('updates').update({'status':'rejected'}).eq('id',update_id).execute()
    return redirect(url_for('admin'))

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5001,debug=True)
