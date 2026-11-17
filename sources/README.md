# 來源與取得紀錄

產品資料固定在 `5d0a4637d66392a3155a4f7a80b7b9eaebfc5b49`，每份原文的網址、取得時間、大小與 SHA-256（像檔案指紋）在 [registry.json](registry.json)，短札記是 S1–S14，公開版本只保留來源與摘要，下載原文放在已排除提交的 `raw/`。

從作業目錄執行 `python3 scripts/ingest.py` 會重新取得全部來源，確認 HTTPS、HTTP 200 與預期內容後更新清單；`python3 scripts/ingest.py --verify-only` 只核對本機檔案的大小和指紋，不連網。

本次先用 Python 3.14 的 urllib 下載，實際出現 `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`，代表本機憑證鏈缺少；改用系統 curl 後下載成功，沒有關掉 HTTPS 憑證驗證，也沒有使用 Gemini 金鑰或呼叫模型。

後來增加五份程式來源和 RAG 原論文，補上套用、復原與課綱檢索的證據，最後共 14 份，其中 11 份是產品公開資料、2 份是官方文件、1 份是研究論文，執行結果見 [last-ingest-output.txt](last-ingest-output.txt)，歷次成功紀錄見 [ingest-log.jsonl](ingest-log.jsonl)，憑證錯誤的完整重現輸出見 [retrieval-errors.txt](retrieval-errors.txt)。

核對時最需要分清：S2 是規格；S9 實作只擋下新造成或變嚴重的問題；S5 過濾引用課號不等於查證回答；S6 沒有傳 JSON Schema；S10–S13 顯示使用本機文字檢索，不能說一定有向量資料庫；備案與復原資料的程式證據不等於本次操作過原網站。
