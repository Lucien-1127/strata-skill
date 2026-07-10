# 實戰記錄：zhiyan-backend 路由 404 診斷（2026-07-09）

## 情境

已知端點清單：`/api/chat`、`/api/status`、`/api/committee/run`
實際結果：`/api/status` ✅ 200，`/api/chat` ❌ 404，`/api/committee/run` ❌ 404

## 診斷步驟

1. **偵察**：讀取 `/opt/zhiyan-backend/server.py` 全部 1168 行
2. **發現**：實際路由註冊為 `/api/chat/ask` 與 `/api/chat/committee`，不是前端預期的 `/api/chat` 與 `/api/committee/run`
3. **根因**：路由命名不一致（缺少 alias）
4. **修復**：新增 2 條 alias 路由，委派到既有 handler

## 修復 diff

```python
@app.post("/api/chat")
async def chat_alias(req: ChatRequest, user_id: str = Depends(get_current_user)):
    """Alias → /api/chat/ask"""
    return await chat_ask(req, user_id)

@app.post("/api/committee/run")
async def committee_alias(req: CommitteeRequest, user_id: str = Depends(get_current_user)):
    """Alias → /api/chat/committee"""
    return await chat_committee(req, user_id)
```

## 迴歸結果

8/8 端點全 ✅（含 2 條 alias + 6 條既有路由）

## 教訓

- FastAPI 中 route decorator 的路徑是唯一註冊來源，不存在的路徑就是 404
- alias 路由是最小成本解法（不動既有 handler，不變 schema）
- 備份指令：`cp server.py server.py.bak.$(date +%s)`
- 回滾指令：`cp server.py.bak.<TIMESTAMP> server.py && \`pkill -f "zhiyan-backend" && /opt/zhiyan-backend/venv/bin/python3 /opt/zhiyan-backend/server.py\``
