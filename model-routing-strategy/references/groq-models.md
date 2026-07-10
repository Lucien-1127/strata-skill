# Groq 模型參考 — 2026-07-07

> 研究來源：Groq Console Docs、OpenAI GPT-OSS GitHub、Groq 官方部落格、Hacker News、Dev.to
> All models: 131,072 context window, **no Vision support**

## ⚠️ 重要更正：Function Calling 狀態

~~Groq API 層級未啟用 Function Calling~~ → **Groq 官方文件顯示 Tool Use / Function Calling = ✅ 正式支援**（2026-07確認）。FreeLLM API catalog metadata 可能標記錯誤。如果 FreeLLM 路由時說不支援，請直接檢查 Groq API 而非依賴 catalog 旗標。

## LPU 架構要點

| 面向 | 數據 |
|:-----|:------|
| 推理速度 | GPT-OSS 20B 達 1000 T/s，比 GPU 方案快 3-18x |
| 首字延遲 (TTFT) | 0.22 秒，變異極小 |
| 確定性 | 完全確定性（編譯器靜態調度），每次執行結果與時間完全一致 |
| 記憶體頻寬 | 80 TB/s SRAM（vs GPU HBM 約 8 TB/s） |
| 能源效率 | 比 GPU 高 10 倍 |
| SLA | 🟢 **100%** 可用率（2026年4-7月） |
| API 相容 | 完全 OpenAI 相容，零遷移成本 |

## 模型一覽

| 模型 | 參數 | 速度 | Max Completion | Input $/1M | Output $/1M | FREE TPD |
|:-----|:-----|:----:|:-------------:|:----------:|:-----------:|:--------:|
| **llama-3.1-8b-instant** | 8B | 560 T/s | 131,072 | $0.05 | $0.08 | 500K ⭐ |
| **openai/gpt-oss-20b** | 21B MoE (3.6B active) | 1000 T/s ⚡ | 65,536 | $0.075 | $0.30 | 200K |
| **openai/gpt-oss-120b** | 117B MoE (5.1B active) | 500 T/s | 65,536 | $0.15 | $0.60 | 200K |
| **groq/compound** | Multi-model router | 450 T/s | 8,192 | varies | varies | 70K TPM |
| **groq/compound-mini** | Multi-model router | 450 T/s | 8,192 | varies | varies | 70K TPM |
| **llama-3.3-70b-versatile** | 70B | 280 T/s 🐢 | 32,768 | $0.59 | $0.79 | 100K |
| **openai/gpt-oss-safeguard-20b** | 21B (safety) | 1000 T/s | 65,536 | $0.075 | $0.30 | 200K |

## FREE 層限額（全部 30 RPM 共享）

| 模型 | RPM | RPD | TPM | TPD |
|:-----|:---:|:---:|:---:|:---:|
| groq/compound | 30 | 250 | 70K | — |
| groq/compound-mini | 30 | 250 | 70K | — |
| llama-3.1-8b-instant | 30 | 14.4K | 6K | 500K |
| llama-3.3-70b-versatile | 30 | 1K | 12K | 100K |
| gpt-oss-120b | 30 | 1K | 8K | 200K |
| gpt-oss-20b / safeguard | 30 | 1K | 8K | 200K |

## DEV 層限額 ($5/月)

| 模型 | RPM | RPD | TPM |
|:-----|:---:|:---:|:---:|
| groq/compound | 200 | 20K | 200K |
| llama-3.1-8b-instant | 1K | 500K | 250K |
| llama-3.3-70b-versatile | 1K | 500K | 300K ⭐ |
| gpt-oss-120b | 1K | 500K | 250K |
| gpt-oss-20b | 1K | 500K | 250K |

## 任務推薦

| 任務 | 🥇 首選 | 理由 |
|:-----|:--------|:------|
| 簡單對話/大量批次 | llama-3.1-8b-instant | 最便宜, 最快 560 T/s, TPD 500K |
| 低延遲場景 | gpt-oss-20b | 1000 T/s, $0.075/$0.30 |
| 高品質推理 | gpt-oss-120b | 117B MoE, CoT, reasoning effort |
| 複雜推理/程式碼 | gpt-oss-120b | 能力最強, 原生 function calling |
| 即時網路資訊 | groq/compound | 內建 Web Search + Code Execution |
| 安全審查 | gpt-oss-safeguard-20b | 安全專用 |
| DEV 層主力 | llama-3.3-70b + gpt-oss-120b | TPM 升級後 CP 值最高 |

## 注意事項

- ✅ **Function Calling 已支援**（Groq API 層級正式開放，非 FreeLLM catalog 標記的 false）
- ❌ **無 Vision 支援**（所有 Groq 託管模型均不支援圖片輸入）
- groq/compound 有額外工具費：Basic Web Search $5/1K req, Advanced $8/1K req, Code Execution $0.18/hr, Visit Website $1/1K req
- FREE 層 30 RPM 為**全部模型共享**，非各模型獨立
- llama-3.3-70b TPD 僅 100K，做主力會很快被限
- Groq 狀態頁：status.groq.com（2026年4-7月 100% uptime）
- Groq 另有 `ai.groq.com` 提供免 API key 的對話介面（GroqChat）
- GitHub 生態：官方 41 個儲存庫，groq-api-cookbook (1,384★)、openbench (784★) 最活躍
- 定價頁面：groq.com/pricing（console.groq.com/docs/pricing 曾回傳 404）
