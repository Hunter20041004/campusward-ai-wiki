#!/usr/bin/env python3
"""Build the teaching site only from the reviewed Wiki and source registry."""
import json, html, hashlib, re
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def esc(t): return html.escape(str(t),quote=True)
def save(p,t): (ROOT/p).write_text(t)
def anchor(u,t): return f'<a href="{esc(u)}">{esc(t)}</a>'
def page(path,title,body,depth=0,extra=''):
 base='../'*depth
 nav=''.join(anchor(base+url,label) for url,label in [('index.html','教學 Wiki'),('slides/index.html','看簡報'),('workflow.html','流程與紀錄'),('sources/index.html','來源')])
 return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="用 Campusward 理解 AI 搜課、排課與檢查，附原始來源與實際製作紀錄"><title>{esc(title)}｜Campusward 教學</title><link rel="stylesheet" href="{base}assets/fonts.css"><link rel="stylesheet" href="{base}assets/site.css">{extra}</head><body><a class="skip-link" href="#main">跳到內容</a><header class="site-header"><a class="brand" href="{base}index.html">Campusward <small>教學 Wiki</small></a><nav class="site-nav" aria-label="主要導覽">{nav}</nav></header>{body}<footer class="site-footer">非政大官方服務 · 教材依固定版本文件整理 · AI 協助摘要、製作與核對，詳見<a href="{base}records/ai-assistance.md">協作紀錄</a></footer><script src="{base}assets/site.js" defer></script></body></html>'''

data=load('content.json'); sources=load('sources/registry.json')
by_source={s['id']:s for s in sources}; by_wiki={w['id']:w for w in data['wiki']}; by_claim={c['id']:c for c in data['claims']}
# Checks occur before slide generation; structural support is distinct from semantic review.
issues=[]
for c in data['claims']:
 for sid in c['sources']:
  if sid not in by_source: issues.append(f"{c['id']} unknown source {sid}")
for w in data['wiki']:
 for cid in w['claims']:
  if cid not in by_claim: issues.append(f"{w['id']} unknown claim {cid}")
 for rid in w['related']:
  if rid not in by_wiki: issues.append(f"unknown Wiki link {rid}")
for slide in data['slides']:
 supported=set()
 for wid in slide['wiki']:
  if wid not in by_wiki: issues.append(f"unknown Wiki {wid}")
  else: supported.update(by_wiki[wid]['claims'])
 for cid in slide['claims']:
  if cid not in supported: issues.append(f"{slide['id']} claim {cid} absent from cited Wiki")
if len(sources)<5: issues.append('less than five sources')
if not (ROOT/'records/semantic-review.json').exists(): issues.append('missing semantic review')
if issues: raise SystemExit('\n'.join(issues))

# Execute a small real Wiki query for each lesson; all Wiki pages are the search corpus.
queries={
 'start':['AI','排課'],'request':['入門','規則'],'search':['搜課','搜尋'],
 'proposal':['JSON','格式'],'rules':['檢查','規則'],'try-it':['衝堂','空堂'],
 'rag':['RAG','課綱'],'citations':['引用','查證'],'data':['隱私','金鑰'],
 'quiz':['檢查','官方'],'takeaway':['AI','限制']}
def query_wiki(terms):
 ranked=[]
 for w in data['wiki']:
  title=w['title']+' '+w['summary']+' '+' '.join(w['tags'])
  body=' '.join(p for section in w['sections'] for p in section['paragraphs'])
  score=sum(3*title.lower().count(t.lower())+body.lower().count(t.lower()) for t in terms)
  if score: ranked.append((score,w['id']))
 ranked.sort(key=lambda x:(-x[0],x[1]))
 return [{'wiki':wid,'score':score} for score,wid in ranked[:3]]
retrieval=[]
for slide in data['slides']:
 terms=queries[slide['id']]
 hits=query_wiki(terms)
 retrieval.append({'slide':slide['id'],'query':terms,'hits':hits,'used':slide['wiki'],'claims':slide['claims']})
 for wid in slide['wiki']:
  if wid not in [r['wiki'] for r in hits]:
   followup=[by_wiki[wid]['title']]
   results=query_wiki(followup)
   if wid not in [r['wiki'] for r in results]: raise SystemExit('Follow-up retrieval failed: '+wid)
   retrieval[-1].setdefault('followups',[]).append({'query':followup,'hits':results,'used':wid,'reason':'補查對應條目完整上下文，不只採前三名'})
save('records/retrieval.json',json.dumps(retrieval,ensure_ascii=False,indent=2)+'\n')

# Wiki is written before the deck shell. The deck reads this reviewed content.json.
for w in data['wiki']:
 sections=''.join('<section><h2>'+esc(s['title'])+'</h2>'+''.join('<p>'+esc(p)+'</p>' for p in s['paragraphs'])+'</section>' for s in w['sections'])
 evidence=''
 for cid in w['claims']:
  c=by_claim[cid]
  refs='、'.join(anchor('../sources/index.html#'+sid,sid+' '+by_source[sid]['title']) for sid in c['sources'])
  evidence+=f'<li id="{cid}"><strong>{cid}</strong> {esc(c["text"])}<br>{refs}<br><small>定位：{esc(c["locator"])}</small></li>'
 related=' · '.join(anchor(r+'.html',by_wiki[r]['title']) for r in w['related'])
 body=f'<main id="main" class="article"><h1>{esc(w["title"])}</h1><p>{esc(w["summary"])}</p>{sections}<section class="source-list"><h2>這一頁的依據</h2><ul>{evidence}</ul><p>來源編號能追到原文，這不是自動證明每句內容都正確，摘要仍需閱讀核對。</p></section><h2>接著看</h2><p>{related}</p></main>'
 save('wiki/'+w['id']+'.html',page('',w['title'],body,1))
entries=''.join(f'<article class="wiki-entry" data-search="{esc(w["title"]+" "+w["summary"]+" "+" ".join(w["tags"]))}"><h3>{anchor("wiki/"+w["id"]+".html",w["title"])}</h3><p>{esc(w["summary"])}</p></article>' for w in data['wiki'])
home=f'''<main id="main"><section class="hero"><div><h1>一句需求，怎麼變成一份課表</h1><p>用 Campusward 看懂 AI 搜課、排課與檢查，先知道誰負責什麼，再自己試一次。</p><div class="hero-actions"><a class="button primary" href="slides/index.html">開始看簡報</a><a href="#wiki">先逛 Wiki</a></div></div><div class="hero-preview"><h2>先找資料，再做判斷</h2><p>你說需求 → AI 整理方向<br>程式搜課 → AI 提出方案<br>規則檢查 → 回官方確認</p><p>11 頁教學 · 6 篇 Wiki · {len(sources)} 份來源<br>不用登入，也不用 API 金鑰</p></div></section><section id="wiki"><div class="section-heading"><h2>從這裡找答案</h2><p>每篇都能追到原始來源</p></div><div class="search-box"><label for="search-wiki">想看哪個部分？</label><input id="search-wiki" type="search" placeholder="試試：衝堂、RAG、金鑰"><p id="search-count" aria-live="polite"></p></div><div class="wiki-grid">{entries}</div></section><div class="link-row">{anchor('workflow.html','看看 Wiki 怎麼變成簡報')}{anchor('sources/index.html','全部來源與取得紀錄')}{anchor('BRIEF.md','先討論的方向')}</div><p class="notice">教材中的課程是固定教學示意，不連線 AI、不代表正式課程，Campusward 排好的方案也不等於正式選上。</p></main>'''
save('index.html',page('','AI 搜課、排課與檢查',home))
source_rows=''
for s in sources:
 notes=''.join('<li>'+esc(n)+'</li>' for n in s['notes'])
 caution=''.join('<li>'+esc(n)+'</li>' for n in s['cautions'])
 source_rows+=f'<section id="{s["id"]}"><h2>{esc(s["id"]+" "+s["title"])}</h2><p>{anchor(s["url"],"閱讀原文")} · {anchor(s["id"]+".md","來源札記")}</p><ul>{notes}</ul><details><summary>來源限制與取得證據</summary><ul>{caution}</ul><p>取得：{esc(s["retrieved_at"])}<br>HTTP {s.get("http_status")} · {s["bytes"]:,} bytes<br>SHA256：<code>{esc(s["sha256"])}</code></p></details></section>'
source_body=f'<main id="main" class="article"><h1>資料從哪裡來</h1><p>先 ingest（取得並整理）來源，再寫 Wiki，這次共 {len(sources)} 份，產品文件與程式固定同一版本，外部文件只公開摘要與網址。</p><p>不是把來源名稱列出來就算讀過，下載紀錄保留 HTTP、時間與內容雜湊（像檔案指紋），來源札記另外寫出哪些說法不能推論。</p><div class="link-row">{anchor("registry.json","來源清單 JSON")}{anchor("ingest-log.jsonl","真實取得紀錄")}</div>{source_rows}</main>'
save('sources/index.html',page('','來源與取得證據',source_body,1))
# Static fallback remains readable if JS fails or is disabled.
fallback=''.join('<section><h2>'+esc(s['title'])+'</h2><p>'+esc(s['lead'])+'</p>'+''.join('<p>'+esc(x)+'</p>' for x in s['body'])+'</section>' for s in data['slides'])
body=f'<main id="main"><div id="deck"><div id="slide-host" aria-live="off"><p>正在載入簡報，若沒有載入，請回 Wiki 觀看同一份教材。</p></div><noscript><div class="article">{fallback}</div></noscript></div></main><footer class="deck-controls" aria-label="簡報控制"><button id="prev" type="button">上一頁</button><span id="page-status" aria-live="polite"></span><button id="next" type="button">下一頁</button><button id="overview" type="button">全部展開</button></footer><script src="deck.js" defer></script>'
save('slides/index.html',page('','AI 搜課、排課與檢查簡報',body,1,'<link rel="stylesheet" href="deck.css">'))

review=load('records/semantic-review.json')
first=load('records/structural-first-run.json')
workflow=f'''<main id="main" class="article"><h1>Wiki 怎麼變成簡報</h1><p>先確認要教什麼，再把資料整理進 Wiki，投影片從 Wiki 取材，查不到依據就回去補，不把一般技術介紹直接寫成產品已經有的功能。</p>
<section><h2>先討論，後生成</h2><p>我選的主題是「用 Campusward 教 AI 搜課、排課與檢查」，確認對象是初學者、免登入、每頁附出處後，才開始整理來源和教材，這段討論留在 {anchor('BRIEF.md','方向紀錄')}。</p><p>LLM Wiki 在這裡是一份由 AI 協助整理、可以查詢和互相連結的知識庫，內容存在 content.json，建置後變成六篇 Wiki，這次沒有另外呼叫 Gemini API，模型協作發生在 Codex 對話中。</p></section>
<section><h2>這次實際走的流程</h2><ol class="workflow-steps"><li><strong>確認題目</strong>：先討論教學對象與範圍</li><li><strong>取得資料</strong>：下載來源，留下網址、時間與檔案指紋</li><li><strong>核對來源</strong>：規格回頭對程式，產品現況和一般概念分開</li><li><strong>整理 Wiki</strong>：條目、交叉連結、重點編號與來源定位</li><li><strong>查詢 Wiki</strong>：用關鍵詞找相關條目，再選用有依據的重點</li><li><strong>整理與檢查</strong>：AI 產生教學草稿，程式檢查引用關係，另外閱讀核對語意</li><li><strong>產生簡報並操作</strong>：輸出 HTML，試按換頁、換班、空堂日與小測驗</li></ol><p class="status">找不到依據 → 回到取得資料；說法太滿 → 回到來源核對與 Wiki；引用不完整 → 補查 Wiki 再檢查；畫面或操作有問題 → 修改網頁後重新操作。</p><p>每張投影片都會再查一次 Wiki，所以查詢和核對會重複，只有通過的版本才拿來輸出，這樣新增來源或頁面時，也能沿用同一條流程。</p></section>
<section><h2>這輪真的檢查了什麼</h2><table><thead><tr><th>節點</th><th>發現與處理</th><th>證據</th></tr></thead><tbody><tr><td>取得資料</td><td>Python 下載遇到本機 CA 憑證鏈問題，改用保留 HTTPS 驗證的 curl，最後 14 份來源都回 HTTP 200</td><td>{anchor('records/source-retrieval-issue.md','工具輸出與處理')}</td></tr><tr><td>原文核對</td><td>初稿把套用規則寫得太概括，讀 changeSet.ts 後改成「拒絕新造成或變嚴重的問題」，也把課綱搜尋定位改到真正的搜尋與索引檔</td><td>{anchor('records/semantic-review.json','修改前後，共 '+str(len(review['changes']))+' 個欄位')}</td></tr><tr><td>引用檢查</td><td>第一次建置未通過：最後一張提到規則檢查，卻漏連 validation Wiki，補上引用後再跑，沒有放寬檢查</td><td>{anchor('records/structural-first-run.json','第一次輸出與修正')}</td></tr><tr><td>再次建置</td><td>14 份來源、6 篇 Wiki、12 個重點、11 張投影片，引用關係檢查通過</td><td>{anchor('records/latest-build.json','實際建置結果')}</td></tr><tr><td>Wiki 查詢</td><td>逐頁保存查詢詞、命中條目、採用條目和補查，查到前三篇還不夠時再查完整條目</td><td>{anchor('records/retrieval.json','11 次逐頁查詢')}</td></tr></tbody></table><p>程式查的是編號和引用關係，不會自動證明每句話都受原文支持，語意仍要閱讀原始文件核對，網站操作紀錄另外保存，不把固定示意當成產品 AI 的實測。</p><p>{anchor('records/browser-check.json','瀏覽器實際操作結果')} · {anchor('records/checks.json','網頁與資料檢查')}</p></section>
<section><h2>反思與流程調整</h2><p>這次只有一輪，還不能說哪個節點長期最常錯，這輪最需要回頭修的是整理到引用核對這一段：知道程式有檢查，還不代表可以寫成所有問題都會被擋掉，最後一張也真的漏了 Wiki 出處。</p><p>所以我把「查到來源」和「讀到真正執行的程式」放在輸出 HTML 前，先改好 Wiki 再產生簡報，引用缺漏則直接擋下建置，畫面完成後仍保留操作測試，因為資料有依據和按鈕能用，是不同的檢查。</p><p>這輪的調整是把前置的來源核對寫進重用規則，建置也固定要求語意核對紀錄和完整引用，之後新增頁面就沿用同一個門檻，這不是改了 Campusward 產品的流程，而是改這份教材的製作流程。</p></section>
<section><h2>AI 協助</h2><p>AI 協助整理來源、Wiki、教材初稿與網頁程式，這次依原始文件修過套用規則和引用方式，完整說明在 {anchor('records/ai-assistance.md','AI 協作紀錄')}，所有課程互動都標成固定教學示意。</p></section></main>'''
save('workflow.html',page('','流程與實際檢查紀錄',workflow))

now=datetime.now(timezone.utc).isoformat()
summary={'at':now,'status':'PASS','sources':len(sources),'wiki_entries':len(data['wiki']),'claims':len(data['claims']),'slides':len(data['slides']),'retrieval_queries':len(retrieval),'source_snapshot':'5d0a4637d66392a3155a4f7a80b7b9eaebfc5b49','content_sha256':hashlib.sha256((ROOT/'content.json').read_bytes()).hexdigest(),'checks':['來源編號存在','條目引用存在','投影片重點在引用Wiki內','先有語意核對紀錄再建置'],'limits':'這些檢查驗證資料關係，不是自動逐句事實查證；本次未呼叫產品Gemini API'}
save('records/latest-build.json',json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'records/build-runs.jsonl').open('a') as f:f.write(json.dumps(summary,ensure_ascii=False)+'\n')
print(json.dumps(summary,ensure_ascii=False))
