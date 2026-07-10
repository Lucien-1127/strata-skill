---
name: api-route-diagnostics
description: FastAPI / 後端 API 路由層智慧診斷與修復 — 假設驅動診斷法，含強度路由與六步流程
status: stable
---

# API Route Diagnostics

## 📖 Description

對 FastAPI 服務執行路由層智慧診斷與修復：定位故障或設計缺陷 → 最小修改 → 驗證 → 回報。採用「假設驅動診斷法」（先驗證、後修改），搭配強度路由（L1/L2/L3）控制推理深度。

**When to load**: 用戶回報 API 端點 404/500/逾時、前端呼叫失敗、新部署後路由異常、或要求檢查 API 服務健康狀態。

---

## 強度路由

| 等級 | 適用步驟 | 行為 |
|:----:|:---------|:-----|
| **L1 快速** | 偵察、健康檢查、迴歸驗證 | 機械執行，直出結果，禁止推理鏈 |
| **L2 標準** | 單根因修復、diff 撰寫 | 標準推理 |
| **L3 深度** | 假設生成與排序、跨模組故障、確診失敗後重分析 | 完整推理，窮盡假設空間 |

**升級規則：**
- 同一根因驗證失敗 ≥2 次 → 強制升 L3
- L1 步驟中發現異常 → 停止，升 L2 後重判
- 禁止在 L1 做根因判斷
- 越級使用 L3 於機械步驟視為違規（浪費 token）

---

## 執行流程

### 1. 偵察〔L1〕

讀取目標服務的相關資料：

```bash
# 確認行程存活
ps aux | grep -E "uvicorn|fastapi|server.py" | grep -v grep

# 確認埠號監聽
ss -tlnp | grep <port>

# 對所有已知端點發起 curl 健康檢查
for endpoint in /api/status /api/health /api/chat /api/committee/run; do
    echo "GET $endpoint: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$PORT$endpoint)"
done

# 讀取行程正在執行的原始碼（確認是正確版本）
cat <project>/server.py | grep -n "@app\."
```

**輸出：** 實際註冊路由表（`@app.get/post/put` 列表）、已測試端點的 HTTP 狀態碼。

### 2. 假設〔L3〕

列出可能根因，按機率排序，每項附驗證方法。常見候選：

| # | 假設 | 驗證方法 |
|:-:|:-----|:---------|
| 1 | **路由不存在** — 前後端端點路徑不一致 | 比對 router decorator 與前端呼叫 URL |
| 2 | **FastAPI 載入順序問題** — middleware/static mount 蓋掉路由 | 檢查 CORS → routes → static 順序 |
| 3 | **請求 schema 不匹配** — Pydantic model 與 payload 不符 | curl 帶正確 payload 測試 |
| 4 | **舊行程殘留** — 磁碟 code 與執行中 code 不一致 | `/proc/<PID>/cmdline` 對比磁碟路徑 |
| 5 | **依賴注入錯誤** — Depends() 驗證失敗 | 檢查 get_current_user 等 dependency |

### 3. 驗證〔L2〕

逐一以最低成本手段確認根因：

```bash
# 檢查路由是否存在
grep "@app.post.*/api/chat" server.py     # → 不存在 = 404 根因
grep "@app.post.*/api/chat/ask" server.py  # → 存在但路徑不同

# 檢查 schema 是否匹配 payload
python3 -c "from pydantic import BaseModel; req = ChatRequest(message='test'); print('OK')"

# 檢查舊程序殘留
diff <(cat /opt/.../server.py) /proc/<PID>/cmdline
```

如果 curl 404 但 grep 找不到對應的 route decorator → **確定根因：路由不存在**。

### 4. 修復〔L2〕

最小 diff 修改，不動無關程式碼。

**常用模式 — alias 路由（前端相容層）：**

```python
# 在既有端點定義後方，新增 alias 路由委派到同一 handler
@app.post("/api/chat")
async def chat_alias(req: ChatRequest, user_id: str = Depends(get_current_user)):
    """Alias → /api/chat/ask"""
    return await chat_ask(req, user_id)
```

**修復原則：**
- ✅ 新增 alias 路由（委派呼叫，零邏輯複製）
- ✅ 修正 Pydantic model 欄位
- ✅ 補上缺少的 route decorator
- ❌ 禁止變更既有端點路徑（前端 zxFetch 統一層依賴此契約）
- ❌ 禁止變更既有端點的回應 schema
- ❌ 禁止修改無關的程式碼區塊
- ❌ 禁止未經步驟 3 驗證即修改

**修改前務必備份：**
```bash
cp server.py server.py.bak.$(date +%s)
```

### 5. 迴歸〔L1〕

重跑觸發測試 + 檢查其餘全部端點（含 90 秒長推論逾時場景）：

```bash
# 逐一測試每一個註冊端點
echo "=== 1/N GET /api/status ==="
curl -s --max-time 5 http://127.0.0.1:8001/api/status | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'status={d[\"status\"]}')"

echo "=== 2/N POST /api/chat (修復目標) ==="
curl -s --max-time 30 -X POST http://127.0.0.1:8001/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'

echo "=== 3/N POST /api/committee/run (修復目標) ==="
curl -s --max-time 60 -X POST http://127.0.0.1:8001/api/committee/run -H "Content-Type: application/json" -d '{"message":"test","k":1}'
```

**所有端點必須回 200** 才算過關。

### 6. 回報〔L1〕

Markdown 格式報告，包含：

```markdown
## 根因（一句話）
…
## 證據
…
## 修改 diff
…
## 驗證結果（指令 + 實際輸出）
…
## 風險與回滾指令
cp server.py.bak.<timestamp> server.py && systemctl restart <service>
## 強度統計
| 步驟 | 等級 | 耗用 |
|:----|:----:|:----:|
| 偵察 | L1 | 機械 |
| 假設 | L3 | 完整推理 |
| 驗證 | L2 | 標準 |
| 修復 | L2 | 標準 |
| 迴歸 | L1 | 機械 |
```

---

## 注意事項

- 如果 curl 修復目標端點回 200 但預期行為不符 → 可能是 schema 問題，不是路由問題
- 修改後服務沒生效 → 檢查是否 kill 到正確的舊行程（port 可能被舊 PID 佔著）
- .pyc cache 可能導致新 code 沒被載入 → `find <project> -name "*.pyc" -delete`
- 禁止在無法定位根因時進行臆測性修復 — 輸出「無法確診」+ 已排除假設清單

## Related Skills

- `project-architecture-audit` — 程式碼庫/專案架構深度審計（分析層面而非運行層面）
- `verification-before-completion` — 修改驗證與回歸測試
