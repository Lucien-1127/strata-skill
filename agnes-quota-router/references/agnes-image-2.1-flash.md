# 🎨 Agnes Image 2.1 Flash — 官方 API 參考文件
# 來源: https://wiki.agnes-ai.com/llms.txt
# 模型: agnes-image-2.1-flash
# 端點: POST https://apihub.agnes-ai.com/v1/images/generations

## 文生圖 (必填: model, prompt, size)
- model: agnes-image-2.1-flash
- prompt: 自然語言描述 (建議 8 維度結構: 主體/場景/風格/光影/色彩/構圖/鏡頭/品質)
- size: 例如 1024x768
- response_format: 放在 extra_body 內 (不可在頂層!)
- URL 輸出: extra_body.response_format = "url" → data[0].url
- Base64 輸出: return_base64 = true (頂層) → data[0].b64_json

## 圖生圖 (必填: model, prompt, size, image)
- image: 在 extra_body.image 陣列中，元素為公開 URL 或 Data URI Base64
- 不需要 tags: ["img2img"]
- 構圖保留: 在 prompt 中明確寫「保留原始構圖」
- 同時指定「要改什麼」與「要保留什麼」
- 圖生圖 Base64: extra_body.response_format = "b64_json"

## 常見錯誤
- ❌ response_format 放頂層 → 錯誤
- ❌ 圖生圖傳遞 tags → 錯誤
- ❌ 輸入圖像 URL 不可公開訪問 → 建議 Data URI Base64
- ⏱ 超時建議: 60-360s

## 定價
- 原價: $0.003/張
- 當前: $0/張 (免費)

## 提示詞結構建議
[主體] + [場景/環境] + [風格] + [光照] + [構圖] + [質量要求]
