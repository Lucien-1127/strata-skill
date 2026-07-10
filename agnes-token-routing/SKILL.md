---
name: agnes-token-routing
description: "Agnes AI Token Plan 路由排程"
status: stable
---
# agnes-token-routing

## 📖 Description

Agnes AI Token Plan 路由排程

---

# Agnes AI Token Plan 路由排程

## 功用
Agnes AI Token Plan Starter（1500 req/5h）的路由排程策略，最大化 Token 使用效率。

## 核心策略
- 主要模型：agnes-2.0-flash
- 模型切換：agnes-1.5-flash（簡單任務）
- 圖像生成：agnes-image-2.1-flash
- 影片生成：agnes-video-v2.0
- 路由原則：低成本任務優先用 Agnes，複雜推理用 DeepSeek

## 來源
原檔: 知識庫/Agnes AI Token Plan 路由排程.md
