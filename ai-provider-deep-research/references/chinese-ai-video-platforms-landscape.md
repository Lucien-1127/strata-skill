# Chinese/Asian AI Video Generation Platform Landscape

> **Research date**: 2026-07-09
> **Method**: Direct HTML scraping via curl (browser tools unavailable), extracting embedded JSON config data from SPA pages

## Platform Quick Reference

| Platform | Developer | API | Best For |
|----------|-----------|-----|----------|
| Kling 可靈 | Kuaishou (快手) | ✅ Apply (min $2K/mo) | High-quality video gen |
| CogVideo | Zhipu AI (智譜) | ✅ Open REST API | Cheapest API + open-source |
| Vidu | Shengshu (生數) | ✅ API platform | Overall best for devs |
| Jimeng 即夢 | ByteDance (字節) | ❌ Web only | CapCut/TikTok ecosystem |
| TopView 混元 | Tencent (騰訊) | ✅ Tencent Cloud | HunyuanVideo open-source |
| Wan 萬相 | Alibaba (阿里) | ✅ Bailian platform | Long video (15s) + audio sync |

## Key Technical Trends (2025-2026)

1. **DiT (Diffusion Transformer)** is the universal architecture — all 6 platforms use it or its variants
2. **Audio-visual sync** is the 2025-2026 differentiator (Wan 2.6, Vidu S1)
3. **Reference-to-Video (R2V)** is becoming standard for character consistency
4. **Multi-shot narrative** (automatic multi-scene generation) is emerging (Wan 2.6 I2V)
5. **Open-source movement**: CogVideoX-2B, HunyuanVideo now open source
6. **Real-time streaming digital humans** are a China-native innovation (Vidu S1, 540P/25FPS)

## Taiwan (Traditional Chinese) Support Ranking

1. **Vidu** — best (multi-language site, 9 languages, no China phone required)
2. **Kling AI** — OK (English site available, no China phone required for web)
3. **Wan/CogVideo** — moderate (need China account)
4. **Jimeng/TopView** — poor (China phone + real-name auth required)

## API Fee Ranges (Approximate)

| Platform | Entry Level | Production Level |
|----------|------------|-----------------|
| Kling | ~$2K USD/month | ~$150K+/month |
| CogVideo | API credits, low | Negotiable |
| Vidu | Free credits + subscriptions | Credits-based |
| Wan (Aliyun) | Pay-per-call | Bulk discounts |
| TopView (Tencent) | Pay-per-call | Bulk discounts |
| Jimeng | Free + member web | No API |

## Web Scraping Notes for Chinese SPA Sites

Chinese AI platform sites are typically heavy SPAs built with React/Vue/Next.js. They embed massive configuration objects (i18n strings, pricing tiers, feature flags, model versions) inline in `<script>` tags as JavaScript variable assignments or JSON blobs. These can be extracted with:

```bash
# Extract embedded JSON config - Kling pattern
curl -s "https://klingai.com" | grep -oP "window\['kConf_ytech\.[^']+'\]=\K\{[^}]+(\{[^}]*\}[^}]*)*\}" | head -3

# Extract Next.js data - Vidu/Next.js pattern  
curl -s "https://platform.vidu.com" | grep -oP 'self\.__next_f\.push\(\[1,"\\[^"]+' | head -5

# Extract route data - Jimeng/Modern.js pattern
curl -s "https://jimeng.jianying.com" | grep -oP '_ROUTER_DATA\s*=\s*\K\{[^}]+(\{[^}]*\}[^}]*)*\}'

# Extract JSON-LD structured data (works on most sites)
curl -s "https://www.vidu.com" | grep -oP '<script type="application/ld\\+json">\K[^<]+'
```

## Full Report

Full structured analysis (10 sections, 6 platforms, Western comparison):
- File: `asia-ai-video-platforms-report.md` in session workspace
- Covers: API openness, model tech, features, pricing, Taiwan support, West vs China comparison
