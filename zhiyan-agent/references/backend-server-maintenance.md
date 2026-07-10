# 智研後端 API Server 維護指南

## 服務資訊

- **路徑**: `/opt/zhiyan-backend/server.py`
- **埠號**: 8001
- **啟動方式**: `python3 /opt/zhiyan-backend/server.py`
- **venv**: `/opt/zhiyan-backend/venv/`
- **資料庫**: `DATA_DIR / "zhiyan.db"`（SQLite，自動建表）

## 診斷流程（強度路由）

採用 L1/L2/L3 強度路由診斷法，適用於所有 API 路由故障場景。

### 1️⃣ 偵察〔L1〕— 機械執行，不做根因判斷

```bash
# 健康檢查
curl -s --max-time 5 http://127.0.0.1:8001/api/status

# 確認服務在線
ss -tlnp | grep 8001
ps aux | grep "zhiyan-backend/server"

# 讀取原始碼確認實際註冊路由
grep "@app\.\(get\|post\|put\|delete\)" /opt/zhiyan-backend/server.py
```

### 2️⃣ 假設〔L3〕— 窮盡可能性空間

列出候選根因，按機率排序，每項附驗證方法：

| 假設 | 驗證方式 |
|:-----|:---------|
| 路由不存在（前端路徑 ≠ 後端路徑） | 比對 `grep` 輸出與前端要求端點 |
| Middleware 阻擋 | 檢查 CORS、依賴注入（Depends） |
| 請求 schema 不匹配 | curl 送正確 payload，觀察錯誤訊息 |
| 服務跑的是舊版程式碼 | `cat /proc/PID/cmdline` 確認啟動路徑 |

### 3️⃣ 驗證〔L2〕— 最低成本確認

```bash
# 直接對候選端點送真實請求
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST \
  http://127.0.0.1:8001/api/疑難端點 \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}'
echo ""

# 對比實際路由
grep "疑難端點" /opt/zhiyan-backend/server.py || echo "路由不存在"
```

### 4️⃣ 修復〔L2〕— 最小 diff

**前端相容 alias 模式**（禁止變更既有端點）：

```python
@app.post("/api/frontend-path")  # 前端打的
async def some_alias(req: SomeRequest, user_id: str = Depends(get_current_user)):
    """Alias → /api/actual-path"""
    return await actual_handler(req, user_id)
```

- 零邏輯複製，純委派呼叫
- 既有路徑與 schema 完全不動
- **修復前必須備份**：`cp server.py server.py.bak.$(date +%s)`

### 5️⃣ 迴歸〔L1〕— 全端點驗證

```bash
# 全端點掃描（至少測 8 個）
curl ... /api/status         # 既有
curl ... /api/疑難端點        # 修復目標
curl ... /api/真實路由        # 既有對照
curl ... /api/providers       # 重要輔助
curl ... /api/search/status   # RAG
curl ... /api/chat/ask        # 核心
curl ... /api/chat/committee   # 委員會
curl ... /api/chat/history    # 資料庫
```

## 實際路由表（2026-07-09 確認）

| 路徑 | 方法 | 功用 |
|:-----|:----:|:-----|
| `/api/status` | GET | 健康檢查 |
| `/api/providers` | GET | 列出 provider |
| `/api/chat/ask` | POST | 聊天主路由（LLM+RAG） |
| `/api/chat` | POST | ← `chat` alias → `/api/chat/ask` |
| `/api/chat/committee` | POST | 多模型委員會 |
| `/api/committee/run` | POST | ← `committee` alias → `/api/chat/committee` |
| `/api/chat/stream` | POST | 串流聊天 |
| `/api/chat/history` | GET | 對話歷史 |
| `/api/chat/clear` | POST | 清除對話 |
| `/api/contract/templates` | GET | 合約範本列表 |
| `/api/contract/generate` | POST | 產生合約 |
| `/api/monitor/tracked` | GET | 追蹤法規列表 |
| `/api/monitor/track` | POST | 新增追蹤 |
| `/api/monitor/check` | POST | 檢查法規異動 |
| `/api/search/query` | GET | 法規全文搜尋 |
| `/api/search/laws` | GET | 法規搜尋 |
| `/api/search/status` | GET | RAG 狀態 |
| `/api/osint/investigate` | POST | OSINT 調查 |
| `/api/summary/generate` | POST | 文件摘要 |
| `/api/user/profile` | GET | 使用者資訊 |
| `/api/user/setup` | POST | 註冊 |
| `/api/mcp/tools` | GET | MCP 工具清單 |
| `/api/mcp/execute` | POST | MCP 工具執行 |
| `/` | GET | 前端靜態頁 |

## 常見故障

### 404：路由不存在

前端打的端點跟後端註冊的路徑不一致。症狀：`curl → HTTP 404`，但 `api/status` 正常。

**解法**：加 alias 路由（見修復模式），不改變既有端點。

### 502：LLM API 錯誤

後端串接的 LLM（DeepSeek/FreeLLM）回傳錯誤。檢查：
1. `FREELMAPI_API_KEY` 環境變數是否有效
2. FreeLLM 容器是否健康：`docker ps --filter name=freellm`
3. DeepSeek 餘額：`curl https://api.deepseek.com/v1/user/balance -H "Authorization: Bearer $KEY"`

### 504：請求逾時

LLM 呼叫超過 120s timeout。委員會模式 timeout 300s。長推論場景預期回應時間：
- DeepSeek: 5-15s
- FreeLLM auto: 1-10s  
- Committee (k=3): 15-45s

## Provider 路由

| provider 值 | 走哪條路 | LLM API |
|:------------|:---------|:---------|
| `deepseek`（預設） | `call_deepseek()` | `https://api.deepseek.com/v1` |
| `freellmapi` | `call_freellmapi(model="auto")` | `http://127.0.0.1:3001/v1` |
| `committee` | `call_freellmapi(model="fusion")` | `http://127.0.0.1:3001/v1` |
