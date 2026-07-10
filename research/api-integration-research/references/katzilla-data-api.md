# Katzilla Data API

多來源資料 API 聚合平台，提供 FDA、SEC、Congress、USGS 等政府/公開資料。

## 基本資訊

- **官網**: https://katzilla.dev
- **WorkSpace**: https://katzilla.dev/workspace
- **文件**: https://katzilla.dev/docs
- **完整目錄**: https://katzilla.dev/data
- **SDK**: `npm install @katzilla/sdk` / `pip install katzilla`

## 方案

| 方案 | 限制 |
|---|---|
| Free | 1,000 requests/month, hard-capped, no card |

## API 端點

全部使用相同格式：`curl 'https://api.katzilla.dev/v1/{path}' -H 'x-api-key: YOUR_KEY'`

| 端點 | 說明 |
|---|---|
| `/v1/fda/recalls` | FDA 最近召回 |
| `/v1/sec/filings?ticker=AAPL` | SEC 申報文件 |
| `/v1/congress/bills?_limit=5` | 國會法案 |
| `/v1/usgs/earthquakes?magnitude=4` | USGS 地震資料 |
| `/agents` | 完整目錄 |

## Header 規則

- **header**: `x-api-key: YOUR_KEY`
- 不加 `Bearer` 前綴

## 帳號狀態

- 使用者: Lucien
- 註冊時間: ~2026-07-01
- 狀態: 未使用過任何 call

## 相關技能

- `api-integration-research` — 第三方 API 系統化研究
- `ai-provider-deep-research` — 多源深度研究
