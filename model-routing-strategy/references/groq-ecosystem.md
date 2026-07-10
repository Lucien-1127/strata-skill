# Groq 生態研究摘要

## 來源
- https://groq.com | https://console.groq.com/docs | https://status.groq.com
- https://github.com/groq (41 repos) | https://github.com/groq/groq-api-cookbook (1384★)
- https://codeconfessions.substack.com/p/groq-lpu-design (LPU 架構深度剖析)

## LPU 架構核心

| 面向 | Groq LPU | NVIDIA GPU |
|:-----|:---------|:-----------|
| 晶片類型 | TSP (Tensor Streaming Processor) | CUDA 核心 |
| 記憶體架構 | SRAM 220 MiB/TSP, 80 TB/s 頻寬 | HBM, ~8 TB/s |
| 調度方式 | 編譯器靜態調度（完全確定性） | 硬體動態調度（非確定性） |
| 首字延遲 | 0.22 秒，低變異 | 波動大 |
| 速度 | Llama 3.1 8B: 560 t/s, GPT-OSS 20B: 1000 t/s | 通常 100-300 t/s |
| 能源效率 | 比 GPU 高 10x | 基準線 |
| 製程 | 14nm（第一代） | 4nm/5nm |

## 可用模型（Production）

| 模型 | 速度 | Input $/1M | Output $/1M | Context | FREE TPD |
|:-----|:----:|:----------:|:-----------:|:-------:|:--------:|
| llama-3.1-8b-instant | 560 t/s | $0.05 | $0.08 | 131K | 500K |
| openai/gpt-oss-20b | 1000 t/s | $0.075 | $0.30 | 131K | 200K |
| openai/gpt-oss-120b | 500 t/s | $0.15 | $0.60 | 131K | 200K |
| llama-3.3-70b-versatile | 280 t/s | $0.59 | $0.79 | 131K | 100K |
| groq/compound | 450 t/s | 依用量 | 依用量 | 131K | 70K TPM |

## 免費 Tier Rate Limits

| 模型 | RPM | TPM | TPD |
|:-----|:---:|:---:|:---:|
| 全模型共享 | 30 | — | — |
| llama-3.1-8b-instant | 30 | 6K | 500K |
| openai/gpt-oss-120b | 30 | 8K | 200K |
| llama-3.3-70b-versatile | 30 | 12K | 100K |
| groq/compound | 30 | 70K | 無 TPD 限制 |

## 關鍵限制
- ❌ Groq API 支援 Function Calling（官方文件標示 ✅），但 FreeLLM catalog 標記為 ❌（metadata 過時）
- ❌ 無 Vision / 多模態支援
- ❌ FREE 層全模型共享 30 RPM
- ✅ API 完全 OpenAI 相容（零遷移成本）
- ✅ 100% 運行時間 (2026-04 ~ 2026-07)

## 選用建議

| 任務 | 首選 | 理由 |
|:-----|:------|:------|
| 大量日常任務 | llama-3.1-8b-instant | 最便宜、最快(560)、最高FREE TPD(500K) |
| 低延遲場景 | openai/gpt-oss-20b | 1000 t/s 最快 |
| 複雜推理/程式碼 | openai/gpt-oss-120b | 120B MoE、function calling、可調 reasoning |
| 最高品質推理 | llama-3.3-70b-versatile | 70B 但 FREE TPD 僅 100K（謹慎用） |
| 代理/Web Search | groq/compound | 內建 Web Search + Code Execution |

## 路由策略建議（現狀 vs 建議）

| 現狀 | 問題 | 建議 |
|:-----|:------|:------|
| NVIDIA Nemotron 120B 10.9M tokens | Worker 全滿、503 頻繁 | 改用 Groq GPT-OSS-120B |
| Groq 6 把金鑰 > 95% 閒置 | 放著養蚊子 | 排入路由優先順位 |
| llama-3.3-70b 只用 1,995 tokens | 100K TPD 配額幾乎全新 | 設為複雜推理專用 |
