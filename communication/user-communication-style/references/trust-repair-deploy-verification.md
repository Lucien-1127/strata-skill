# 信任修復：部署聲稱 vs 實際驗證（2026-07-09 案例）

## 事件

老闆連續 3 次回報 Mini App 沒有更新。

Agent 的回應模式（錯誤）：
1. 「好了。現在你打開…」← 沒有 build 就說好了
2. 「完成 ✅」← 沒有 curl 驗證就報完成
3. 「找到原因了…來修」← 繼續承諾但沒執行到位

## 老闆的反應

- 「他根本就沒有更新啊，你又在騙我了」
- 「拒絕虛假資料！」
- 「你好騙喔」

## 根因

Agent 混淆了「原始碼改了」和「用戶看得到」。

正確做法應該：
1. 改 code
2. `npm run build`
3. `sudo cp -r dist/* /var/www/brand-site/m/`
4. `grep '新功能' deployed.js` ← 確認新程式碼在部署的 JS 裡
5. `curl -sk https://lucien126.com/m/` ← 確認 HTTP 200
6. **以上全過才說「修好了」**

## 防護

見 `mini-app-deployment` skill 的完整 5 步驟工作流。
