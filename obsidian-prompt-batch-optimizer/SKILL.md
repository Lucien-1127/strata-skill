---
name: obsidian-prompt-batch-optimizer
description: "批量優化 Obsidian vault 內所有提示詞的腳本工具，保留 YAML frontmatter，使用 Hermes config 中的 DeepSeek API"
---
# obsidian-prompt-batch-optimizer

## 📖 Description

批量優化 Obsidian vault 內所有提示詞的腳本工具，保留 YAML frontmatter，使用 Hermes config 中的 DeepSeek API

---

---
name: obsidian-prompt-batch-optimizer
title: Obsidian Prompt Batch Optimizer
description: 批量優化 Obsidian vault 內所有提示詞的腳本工具，保留 YAML frontmatter，使用 Hermes config 中的 DeepSeek API
---

# Obsidian Prompt Batch Optimizer

批量讀取 Obsidian vault 內的提示詞檔案 → 用 DeepSeek 逐一優化 → 存回原檔（保留 YAML frontmatter），並自動備份原始檔案。

## 前置條件

- Hermes 配置了 DeepSeek provider（`~/.hermes/config.yaml` 中有 `custom_providers` 含 deepseek）
- `pip install openai pyyaml`

## 腳本位置

- 腳本：`<vault>/_scripts/batch_prompt_optimizer.py`
- 備份目錄：`<vault>/_optimized_backup/`
- 優化報告：`<vault>/_optimized_backup/優化報告.md`

## 處理範圍

自動收集以下目錄的 `.md` / `.txt` 檔案：
1. `copilot/system-prompts/` — Obsidian Copilot 系統提示詞
2. `copilot/copilot-custom-prompts/` — 自訂斜線指令
3. `copilot/copilot-模板/` — 模板
4. `知識庫/🔧提示詞庫/` — 精選可運行的提示詞（跳過純知識文件）

## 優化策略

- 保留 YAML frontmatter 不做修改
- 強化結構：角色、背景、目標、指令、約束、輸出格式
- 增加邊界約束（anti-jailbreak, 輸出可控, 準確性聲明）
- 使用繁體中文（台灣用語）

## 優化 API 參數

- Model: `deepseek-v4-flash`
- Temperature: 0.3
- Max tokens: 8000

## 執行方式

```bash
cd <vault>
python _scripts/batch_prompt_optimizer.py
```

## 還原方式

```bash
cd <vault>/_optimized_backup
for f in *.bak; do cp "$f" "../$f"; done
```
