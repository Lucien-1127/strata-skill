---
name: url-cleaner
description: "自動清除網址中的追蹤參數"
status: stable
---
# url-cleaner

## 📖 Description

自動清除網址中的追蹤參數

---

# 🧹 網址自動清除器

## 觸發條件
用戶貼了一串長網址時自動觸發。

## 功用
清除網址中的 UTM 追蹤參數、多餘 query string，還原為乾淨的短網址。

## 規則
- 移除 utm_source/utm_medium/utm_campaign 等
- 移除 fbclid/gclid/ref 等追蹤參數
- 保留必要參數（如 ?v= video id）
- 輸出乾淨網址

## 來源
原檔: copilot-custom-prompts/🧹 網址自動清除器.md
