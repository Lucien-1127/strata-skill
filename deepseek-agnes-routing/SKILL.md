---
name: deepseek-agnes-routing
description: "DeepSeek V4 + Agnes 多模型路由策略研究"
status: stable
---
# deepseek-agnes-routing

## 📖 Description

DeepSeek V4 + Agnes 多模型路由策略研究

---

# DeepSeek V4 + Agnes 路由策略

## 功用
DeepSeek V4 架構深度研究 + Agnes-DeepSeek 多模型路由策略參考。含 V4 Flash/Pro 差異、成本優化與路由建議。

## 核心發現
| 模型 | 參數 | 激活 | Context | 成本 |
|------|------|------|---------|------|
| V4 Pro | 1.6T | 49B | 1M | $0.435/M in |
| V4 Flash | 284B | 13B | 1M | $0.14/M in |

## 路由策略建議
- 簡單任務 → Agnes 2.0 Flash
- 複雜推理 → DeepSeek V4 Flash
- 最大品質 → DeepSeek V4 Pro
- 多模型投票 → 混合路由

## 來源
原檔: 知識庫/DeepSeek V4 深度研究 + Agnes DeepSeek 路由策略.md
