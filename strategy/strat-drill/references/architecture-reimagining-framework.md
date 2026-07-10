# Architecture Reimagining Framework

> 來源: 使用者提供的架構重構提示詞（2026-07-09）
> 用途: 在修改任何系統架構前，先執行架構重構分析，而非假設現有架構正確

## 必須執行的分析維度

### 1. Architecture Gap Analysis
- 是否缺少重要模組？
- 是否有重複功能？
- 是否存在過度設計？
- 是否存在可抽象化的部分？

### 2. Multi-Dimensional Exploration

至少從以下維度思考（可自行增加）：

| 維度 | 關注點 |
|:-----|:--------|
| Architecture | 整體結構是否合理 |
| Workflow | 流程是否直線、有無 pipeline/queue |
| Decision | 決策層是否存在，路由判斷方式 |
| Validation | 輸入驗證、型別安全、rate limiting |
| Recovery | 崩潰復原、rollback、backup |
| Knowledge | 領域知識是否集中 |
| Context | 前後端資料理解是否一致 |
| Memory | Token/Session 儲存方式、XSS 風險 |
| Tool Integration | CLI 工具、health check、backup script |
| Output Contract | API response 格式是否統一 |
| User Experience | 載入狀態、錯誤處理、離線支援 |
| Maintainability | 單一職責原則、檔案大小 |
| Extensibility | 新增功能需要修改幾處 |
| Performance | Connection pooling、caching |
| Token Efficiency | JWT payload 大小 |
| Cross-Model Compatibility | 是否支援多後端版本 |

### 3. Alternative Architecture Generation

至少提出三種不同架構：

| Type | 特性 |
|:-----|:------|
| **A. Minimal** | 最精簡，與現狀最接近 |
| **B. Balanced** | 推薦，兼顧品質與開發成本 |
| **C. Advanced** | 最高品質，全容器化 + 監控 |

每種架構分析：
- 優點 / 缺點
- 適用情境
- Token 成本
- 維護成本
- 擴充能力

### 4. Enhancement Suggestions

主動提出「還可以增加什麼」，不等使用者說：
- 新模組、新流程、新驗證
- 新 Decision Policy、新 Workflow
- 新 Plugin、新工具整合
- 新 Output Strategy

### 5. Pattern Matching

比對已知最佳設計模式（如 Single Responsibility、Strategy、Repository、Circuit Breaker、Health Endpoint、Graceful Degradation）。

若有更好的 Pattern，提出替代方案。

### 6. Future Compatibility

若未來 GPT/Claude/Gemini/MCP 接入，目前架構是否仍適用？

若不適用，提出新的抽象層設計。

### 7. Innovation Review

最終回答：目前架構是：
- □ 只是優化？
- □ 還是重新定義？

若只是優化，必須再提出至少一個突破性方案。

## 輸出格式

```
Architecture Review
Gap Report
Alternative Architectures
Enhancement Suggestions
Final Recommendation
```

## 實戰案例

2026-07-09 對 Hermes Proxy Console 的架構重構發現：
- **Gap**: 後端單點故障（無 systemd）、無資料庫持久層（JSON 取代 SQLite 交易）、前端直接打後端無 API Gateway、靜態站與 SPA 混雜造成 nginx 邏輯複雜
- **Recommendation**: 短期加 systemd unit + rate limiting + 統一 API response 格式；中期重寫後端為 FastAPI；長期容器化 + Prometheus 監控
