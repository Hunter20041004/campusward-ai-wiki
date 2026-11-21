/* Run only with Playwright's bundled Chromium and an isolated temporary profile. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const cp = require('node:child_process');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const root=path.resolve(__dirname,'..');
  const base=process.env.VERIFY_URL || 'http://localhost:4180/';
  const evidenceDir=process.env.VERIFY_EVIDENCE_DIR || path.join(root,'assets');
  fs.mkdirSync(evidenceDir,{recursive:true});
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'campusward-wiki-test-'));
  const executable=chromium.executablePath();
  assert(executable.includes('/ms-playwright/'), 'Use bundled test Chromium');
  assert(!executable.includes('/Applications/Google Chrome.app/'), 'Never use daily Chrome');
  const results=[];const consoleErrors=[];let browserPid;let context;let result;
  const record=(name,detail)=>results.push({name,status:'PASS',detail});
  try {
    context=await chromium.launchPersistentContext(profile,{executablePath:executable,headless:true,viewport:{width:1366,height:1150},reducedMotion:'reduce'});
    const lines=cp.execFileSync('ps',['-axo','pid=,command='],{encoding:'utf8'}).split('\n');
    const line=lines.find(x=>x.includes('--user-data-dir='+profile)&&!x.includes('--type='));
    assert(line && line.includes(executable),'Actual process must match test executable and profile');
    browserPid=Number(line.trim().split(/\s/)[0]);
    console.log(JSON.stringify({isolation:{executable,profile,pid:browserPid,actual_process:line.trim()}}));
    const page=await context.newPage();
    page.on('pageerror',e=>consoleErrors.push(e.message));
    await page.goto(base,{waitUntil:'networkidle'});
    await page.locator('#search-count').waitFor();
    await page.keyboard.press('Tab');await page.locator('.skip-link').focus();await page.locator('.skip-link').hover();
    assert.equal(await page.locator('.skip-link').evaluate(e=>getComputedStyle(e).color),'rgb(255, 255, 255)');
    assert.equal(await page.locator('.skip-link').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(35, 50, 74)');
    record('鍵盤跳轉對比','focus與hover仍為白字深底，對比12.9:1');
    await page.locator('#search-wiki').focus();
    assert.match(await page.locator('#search-count').textContent(),/6 \/ 6/);
    await page.locator('#search-wiki').fill('RAG');
    assert.equal(await page.locator('.wiki-entry:visible').count(),1);
    await page.locator('#search-wiki').fill('完全查不到的教材');
    assert.match(await page.locator('#search-count').textContent(),/找不到/);
    await page.locator('#search-wiki').fill('');
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'evidence-wiki.png'),fullPage:true});
    record('Wiki 搜尋','6篇；RAG命中1篇；查無結果提示；清除恢復');
    await page.goto(new URL('slides/',base).href,{waitUntil:'networkidle'});
    await page.locator('.slide:visible').waitFor();
    assert.equal(await page.locator('.slide').count(),11);
    assert.equal(await page.locator('#prev').isDisabled(),true);
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'evidence-slides.png'),fullPage:true});
    await page.locator('#next').click(); assert.equal(new URL(page.url()).hash,'#request');
    await page.keyboard.press('End');assert.equal(new URL(page.url()).hash,'#takeaway');
    assert.equal(await page.locator('#next').isDisabled(),true);
    await page.keyboard.press('Home');assert.equal(new URL(page.url()).hash,'#start');
    record('換頁與網址','上一頁/下一頁、Home/End與hash定位符合頁面');
    await page.goto(new URL('slides/#search',base).href,{waitUntil:'networkidle'});
    const searchSlide=page.locator('.slide:visible');
    assert.match(await searchSlide.textContent(),/第一輪沒有提出變更/);
    assert.match(await searchSlide.textContent(),/11 月 18 日本機版/);
    assert.match(await searchSlide.textContent(),/週五下午 2學分 通識 不要早八/);
    const searchWiki=await searchSlide.locator('a[href$="wiki/search.html"]').getAttribute('href');
    await page.goto(new URL(searchWiki,page.url()).href,{waitUntil:'networkidle'});
    const updateEvidence=page.locator('#C13 a');
    assert.match(await updateEvidence.textContent(),/本機新版核對紀錄/);
    const evidenceUrl=new URL(await updateEvidence.getAttribute('href'),page.url());
    const evidence=await page.request.get(evidenceUrl.href);
    assert.equal(evidence.status(),200);
    assert.match(await evidence.text(),/119 passed/);
    await page.goto(new URL('slides/#rules',base).href,{waitUntil:'networkidle'});
    const rulesSlide=page.locator('.slide:visible');
    assert.match(await rulesSlide.textContent(),/新造成的衝堂會被擋下/);
    assert.match(await rulesSlide.textContent(),/最近一次已套用的 AI 修改/);
    record('版本標註與證據','公開版搜課、本機版範例、衝堂與復原皆可讀，Wiki 連結可取得更新紀錄');
    await page.goto(new URL('slides/#try-it',base).href,{waitUntil:'networkidle'});
    await page.locator('#check-plan').click();
    assert.match(await page.locator('#demo-result').textContent(),/拒絕：兩門課衝堂/);
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'evidence-conflict.png'),fullPage:true});
    await page.locator('#demo-section').selectOption('B2');
    await page.locator('#check-plan').click();
    assert.match(await page.locator('#demo-result').textContent(),/可排入示意課表/);
    await page.locator('#demo-free-day').check();
    await page.locator('#check-plan').click();
    assert.match(await page.locator('#demo-result').textContent(),/拒絕：佔用保留的空堂日/);
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'evidence-free-day.png'),fullPage:true});
    record('固定示意三種結果','B1衝堂拒絕；B2通過；B2加週三空堂拒絕');
    await page.goto(new URL('slides/#quiz',base).href,{waitUntil:'networkidle'});
    await page.locator('.quiz-choice').nth(0).click();
    assert.match(await page.locator('.quiz-feedback').textContent(),/再想一下/);
    await page.locator('.quiz-choice').nth(1).click();
    assert.match(await page.locator('.quiz-feedback').textContent(),/答對了/);
    record('小測驗','錯誤與正確選項都顯示原因');
    await page.locator('#overview').click();assert.equal(await page.locator('.slide:visible').count(),11);
    await page.locator('#overview').click();assert.equal(await page.locator('.slide:visible').count(),1);
    await page.emulateMedia({media:'print'});assert.equal(await page.locator('.slide:visible').count(),11);
    await page.emulateMedia({media:'screen'});
    record('展開與列印','全部展開11頁；回單頁1頁；列印11頁');
    await page.setViewportSize({width:390,height:844});
    const ids=['start','request','search','proposal','rules','try-it','rag','citations','data','quiz','takeaway'];
    for(const id of ids){
      await page.goto(new URL('slides/#'+id,base).href,{waitUntil:'networkidle'});
      assert.equal(await page.locator('.slide:visible').getAttribute('id'),id);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Mobile slide overflow '+id);
    }
    await page.goto(new URL('slides/#try-it',base).href,{waitUntil:'networkidle'});
    await page.locator('#demo-section').selectOption('B2');await page.locator('#demo-free-day').check();await page.locator('#check-plan').click();
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'evidence-mobile.png'),fullPage:true});
    record('手機11頁','390px無橫向溢出，示意仍可操作');
    await page.goto(new URL('workflow.html',base).href,{waitUntil:'networkidle'});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Workflow overflow');
    assert.match(await page.locator('#november-update').textContent(),/11 月 21 日教材更新/);
    const originalBuild=await page.request.get(new URL('records/2026-11-17/latest-build.json',base).href);
    assert.equal(originalBuild.status(),200);
    assert.equal((await originalBuild.json()).claims,12);
    record('原作業紀錄','11 月 17 日建置紀錄保留原本 12 個重點');
    await page.setViewportSize({width:1366,height:1150});
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'evidence-workflow.png'),fullPage:true});
    assert.deepEqual(consoleErrors,[]);record('網頁執行','沒有未處理的JavaScript錯誤');
    if(process.env.VERIFY_HOLD==='1'){ console.log('ISOLATION_HOLD'); await new Promise(r=>setTimeout(r,15000)); }
    result={at:new Date().toISOString(),status:'PASS',target:base,checks:results,isolation:{executable,profile,pid:browserPid},limits:'只實測本教材的固定互動與呈現，不代表已呼叫或測試原產品的Gemini服務'};
  }catch(e){result={at:new Date().toISOString(),status:'FAIL',target:base,checks:results,error:e.stack};process.exitCode=1;}
  finally{
    if(context)await context.close();
    let alive=false;try{process.kill(browserPid,0);alive=true;}catch{}
    if(alive){await new Promise(r=>setTimeout(r,500));try{process.kill(browserPid,0);alive=true;}catch{alive=false;}}
    result.cleanup={test_browser_exited:!alive,profile_removed:false};
    const privateDir=path.join(root,'records/private');fs.mkdirSync(privateDir,{recursive:true});
    fs.writeFileSync(path.join(privateDir,'isolation-runtime.json'),JSON.stringify(result.isolation||{},null,2));
    if(result.isolation){result.isolation.executable=result.isolation.executable.replace(os.homedir(),'~');result.isolation.profile=path.basename(result.isolation.profile);}

    fs.rmSync(profile,{recursive:true,force:true});result.cleanup.profile_removed=!fs.existsSync(profile);
    if(alive){result.status='FAIL';process.exitCode=1;}
    const dest=process.env.VERIFY_URL?'published-check.json':'browser-check.json';
    fs.writeFileSync(path.join(root,'records',dest),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result,null,2));
  }
})();
