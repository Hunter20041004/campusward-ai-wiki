#!/usr/bin/env python3
import json,re,sys,hashlib
from pathlib import Path
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
errors=[];links=0;count=0
class Document(HTMLParser):
 def handle_starttag(self,tag,attrs):
  global links
  a=dict(attrs)
  for key in ('href','src'):
   if key not in a:continue
   u=a[key]; parts=urlsplit(u)
   if parts.scheme or u.startswith('//'):continue
   if not parts.path:continue
   target=(self.path.parent/unquote(parts.path)).resolve()
   links+=1
   if not target.is_relative_to(ROOT):errors.append('link outside project: '+u)
   elif not target.exists():errors.append(str(self.path.relative_to(ROOT))+': missing '+u)
   elif parts.fragment and target.suffix=='.html':
    if not re.search(r'''id=["']'''+re.escape(unquote(parts.fragment))+r'''["']''',target.read_text()):errors.append('missing anchor '+u)
  if tag=='img' and not a.get('alt'):errors.append('image missing alt')
for file in ROOT.rglob('*.html'):
 if 'raw' in file.parts:continue
 count+=1;t=file.read_text();parser=Document();parser.path=file;parser.feed(t)
 if '<html lang="zh-Hant">' not in t:errors.append('missing language '+str(file))
 if 'name="viewport"' not in t:errors.append('missing viewport '+str(file))
data=json.loads((ROOT/'content.json').read_text())
for w in data['wiki']:
 for s in w['sections']:
  for p in s['paragraphs']:
   if p.count('。')>1:errors.append('paragraph split with periods: '+w['id'])
for slide in data['slides']:
 for p in slide['body']:
  if p.count('。')>1:errors.append('paragraph split with periods: '+slide['id'])
registry=json.loads((ROOT/'sources/registry.json').read_text())
for source in registry:
 if source['http_status']!=200:errors.append('source HTTP failure '+source['id'])
 if not re.fullmatch('[0-9a-f]{64}',source['sha256']):errors.append('invalid hash '+source['id'])
 raw=ROOT/source['raw_path']
 if raw.exists() and hashlib.sha256(raw.read_bytes()).hexdigest()!=source['sha256']:errors.append('source hash mismatch '+source['id'])
for record in ('records/browser-check.json',):
 p=ROOT/record
 if p.exists() and json.loads(p.read_text()).get('status')!='PASS':errors.append('not passed '+record)
if '--strict' in sys.argv:
 for record in ('records/browser-check.json','records/published-check.json'):
  p=ROOT/record
  if not p.exists():errors.append('missing '+record)
  elif json.loads(p.read_text()).get('status')!='PASS':errors.append('not passed '+record)
summary={'at':datetime.now(timezone.utc).isoformat(),'status':'FAIL' if errors else 'PASS','html_pages':count,'local_links':links,'sources':len(registry),'checks':['本機檔案與錨點','來源HTTP與雜湊','段內句號','圖片替代文字'],'errors':errors,'limits':'連結存在與來源關係不等於內容正確，部署後另檢查公開網址與互動'}
(ROOT/'records/checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
sys.exit(bool(errors))
