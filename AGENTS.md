# Campusward 教學 Wiki 的延伸規則

目的：用搜課排課情境讓初學者分辨 AI 的建議和程式的檢查，維持免登入的 HTML 教材。

- 原始來源先進 sources/registry.json，紀錄網址、取得時間和 SHA256；外部全文只在本機 sources/raw/，不公開整份版權文件
- content.json 的 claims 要寫來源編號與定位，Wiki 條目要引用 claims，投影片只能從 Wiki 取材；一般官方文件不可直接當作 Campusward 已實作的證據；補充尚未公開的本機版本時可用 `record` 引用核對紀錄，須標明固定版本、實作位置和測試方式，和公開來源分開
- 修改來源後重跑 ingest 與建置；規格和程式不同時，以本次固定版本的實作為主並註明差異
- 先在 records/ 留討論範圍，再生成 Wiki；不捏造討論、使用經驗、模型呼叫或失敗紀錄
- 教學示意固定標明不連線 AI、不代表正式課程，不加入 API 金鑰、登入或正式選課功能
- wiki/ 是可重建的 HTML，內容改 content.json；slides/ 的互動改 JavaScript；assets/ 放共用樣式
- 文字採繁體中文台灣用語，直接簡短，段內用逗號等接續，真正結束才用句號，保留 AI 協助說明
- 驗證：python3 scripts/build.py、python3 scripts/check.py；瀏覽器驗證用 node scripts/verify.cjs，需要本機 Playwright 套件，必須是配套 Chromium 和獨立測試資料，關閉自己建立的測試程序
