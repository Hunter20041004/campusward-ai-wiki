# Campusward 教學 Wiki

用 Campusward 教 AI 搜課、排課與檢查，給第一次接觸的人看，先整理 Wiki，再產生 11 頁 HTML 簡報，全部免登入、免金鑰。

- [教學 Wiki](https://hunter20041004.github.io/campusward-ai-wiki/)
- [HTML 簡報](https://hunter20041004.github.io/campusward-ai-wiki/slides/)
- [流程與真實紀錄](https://hunter20041004.github.io/campusward-ai-wiki/workflow.html)
- [來源](https://hunter20041004.github.io/campusward-ai-wiki/sources/)

## 重跑

這是新的教學專案，沒有既有測試套件，這次新增來源驗證、引用關係、連結與互動檢查，原 Campusward 產品未修改。

```sh
python3 scripts/ingest.py
python3 scripts/build.py
python3 -m http.server 4180
```

另一個終端執行：

```sh
node scripts/verify.cjs
python3 scripts/check.py
```

瀏覽器測試需 Playwright 套件與配套 Chromium，預設可指定 `PLAYWRIGHT_MODULE`，不使用日常 Chrome 或其資料夾，結束會關閉並刪除本次獨立測試資料。

`content.json` 是 Wiki 和簡報的來源，新增內容時讀 AGENTS.md，來源需先進 registry，投影片引用的重點必須存在於對應 Wiki；sources/raw/ 只有本機下載全文，不上傳公開 Repository。

## AI 協助

Codex 協助來源摘要、Wiki、簡報、程式和測試，使用者決定主題與教學方向，固定互動示意不連線 AI、不代表正式課程，也沒有正式選課功能，協作範圍記在 records/ai-assistance.md。

Outfit / Noto Sans TC 字體依 SIL Open Font License 隨站提供，授權在 assets/fonts/；來源原文各依原網站授權，本教材僅公開短摘要、連結和來源定位。
