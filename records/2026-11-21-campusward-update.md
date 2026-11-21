# 11 月 21 日教材更新

原作業引用公開 GitHub 的 [5d0a463](https://github.com/Hunter20041004/campusward-nccu/tree/5d0a4637d66392a3155a4f7a80b7b9eaebfc5b49)，這次核對 11 月 18 日的本機提交 `a81a0f8896c107b7848fa678eb0b9499f341e896`，新增的內容都標成本機版，14 份公開來源仍是原作業採用的資料。

## 核對到的差異

- 搜課順序看 `apps/web/src/ai/orb.ts` 的 `planWithAi`，公開版第一輪有變更就先回傳，新版本第一輪要求搜課就會接著查，第二輪才交回最後的方案
- 搜課條件看同一檔案的 `readQuery` 和 `aiSearch`，新版支援星期、時段、通識、學分和不要早八，簡報用固定例句解釋能辨識的條件
- 備用模型看 `planWithAi` 的 `ask`，遇到逾時、服務暫時無法使用或額度用完等狀況，可多送一次模型請求，排課仍最多兩輪
- 復原看 `apps/web/src/data/usePlanner.ts` 的 `applyAi`、`liveUndo` 與 `apps/web/src/components/AiPanel.tsx` 的回覆卡，最近一次已套用的 AI 修改，只在目前課表仍對應那次修改時可復原
- 衝堂判準看公開版 `packages/engine/src/ai/changeSet.ts` 的 `applyAiChangeSet`，會比較變更前後，這次補準簡報標題與結尾

## 執行結果

```text
npm test -- apps/web/src/ai/orb.test.ts apps/web/src/ai/gemini.test.ts apps/web/src/data/usePlanner.test.tsx apps/web/src/components/AiPanel.test.tsx
Test Files  4 passed (4)
     Tests  119 passed (119)
```

測試用模擬的模型回覆，先比對這次引用的程式與測試檔沒有偏離固定提交，再重跑搜尋、切換模型、回覆和復原，另用簡報上的「週五下午 2學分 通識 不要早八」跑了 5 筆模擬課程，只有符合全部條件的 1 筆被找出來。
