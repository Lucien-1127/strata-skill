---
name: hermes-multi-skill-arch
description: "Hermes 多技能架構部署指南"
---
# hermes-multi-skill-arch

## 📖 Description

Hermes 多技能架構部署指南

---

# 🤖 Hermes 多技能架構部署指南

## 功用
Hermes Agent 多技能架構的完整部署指南，採用「1 個多感知基礎系統提示詞 + 多個專用 SKILL.md」的分層架構。

## 五層決策模型
```
層 1 — 輸入分類 (Intent Classification)
層 2 — 技能加載 (Skill Loading)
層 3 — 多信號驗證 (Multi-Signal Validation)
層 4 — 域內執行 (Domain Execution)
層 5 — 結果持久化 (Result Persistence)
```

## 技能路由矩陣
| 技能 | 信心閾值 | 成本上限 | 延遲目標 |
|------|---------|---------|---------|
| Trading | 92% | $0.20/次 | <2.5s |
| DevOps | 85% | $0.15/次 | <5s |
| FileOps | 80% | $0.10/次 | <10s |
| SkillDev | 88% | $0.25/次 | <30s |

## 來源
原檔: 知識庫/🔧代理管理/🤖 Hermes多技能架構部署指南.md
