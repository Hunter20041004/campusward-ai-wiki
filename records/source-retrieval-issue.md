# 取得來源時的憑證問題

日期：2026-11-17，這份紀錄依本次工具回傳整理，不是當時另存的機器日誌，也沒有倒填事件時間。

原操作是以本機 Python 3.14 的 `urllib.request.urlopen(u, timeout=45)`，下載固定版本的 [README 原文](https://raw.githubusercontent.com/Hunter20041004/campusward-nccu/5d0a4637d66392a3155a4f7a80b7b9eaebfc5b49/README.md)，第一份尚未取得就結束，工具回傳 exit code 1，錯誤原文節錄如下。

```text
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)

urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)>
```

問題是這次 Python 連線無法驗證憑證鏈，後來改用系統 curl 並保留 HTTPS 驗證，全部來源 HTTP 200，沒有略過憑證檢查；最終執行輸出在 [last-ingest-output.txt](../sources/last-ingest-output.txt)。

為了補留完整輸出，後來以相同網址再次執行 urllib，仍回傳同類錯誤，完整重現輸出在 [retrieval-errors.txt](../sources/retrieval-errors.txt)，那是後續重現的紀錄，不能當作最初執行的完整日誌；[ingest-log.jsonl](../sources/ingest-log.jsonl) 只記錄取得腳本實際完成的成功批次，沒有把這次問題倒填進去。
