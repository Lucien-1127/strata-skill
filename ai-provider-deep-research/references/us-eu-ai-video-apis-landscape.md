# US/EU AI Video Generation API Landscape (2026-07-09)

Comprehensive research on 6 major Western AI video generation platforms:
**Runway (Gen-4.5), Pika (2.5), Luma AI (Ray 2), Haiper, Stability AI (SVD/SV3D), OpenAI Sora**

## Key Findings

### Most Developer-Friendly APIs
1. **Luma AI (Ray 2)** — Best docs (ReadMe, LLMs.txt), official Python/JS SDKs, RESTful API
2. **Runway (Gen-4.5)** — High quality, public API, but Zendesk-hosted docs
3. **Pika (2.5)** — Public API at pika.art/api, reasonable pricing $8/mo (annual)

### API Availability
- **Public API**: Runway, Pika, Luma, Stability AI
- **Beta/Partner Only**: OpenAI Sora (ChatGPT Plus/Pro only), Haiper (business deals only)

### Pricing (lowest monthly entry)
| Platform | Min $/mo | Max duration | Best quality |
|----------|---------|-------------|-------------|
| Runway | $12/yr | 15s @ 4K | Gen-4.5 |
| Pika | $8/yr | 15s @ 1080p | Pika 2.5 |
| Luma | $29.99 | 5s @ 4K | Ray 2 |
| Stability | $20 | 4s @ 576p | SVD/SV3D |
| OpenAI Sora | $20 (Plus) | 120s @ 4K | Sora 2.0 |

### Quality Rankings
- **Realism**: Sora > Runway ≈ Luma > Pika > Haiper > Stability
- **Motion Coherence**: Sora > Runway > Luma > Pika > Haiper > Stability
- **Character Consistency**: Runway ≈ Pika ≈ Sora > Luma > Haiper > Stability
- **Longest Generation**: Sora (120s) >> Runway/Pika (15s) > Haiper (10s)

### Technical Architecture
All major players now use **Diffusion Transformer (DiT)** variants:
- OpenAI: Original DiT paper authors (Sora = world model)
- Runway: Improved DiT with reference image support
- Luma: DiT + Concepts camera system
- Pika: Video DiT + Frame Control
- Stability: 3D-UNet + Temporal Attention (legacy approach, open-source)

### Notable Users/Clients
- **Runway**: Lionsgate, Nike, Adidas, VOGUE, CBS, 50M+ creators
- **Pika**: Warner Music, Universal Music, Nike, P&G, 3M+ Discord
- **Luma**: Hollywood directors, Zaha Hadid Architects, Epic Games
- **Haiper**: BBC, ITV (European media focus)
- **Stability**: MIT, Stanford, Oxford, global research community
- **Sora**: Tyler Perry, WPP, BuzzFeed, Shutterstock

### 2025-2026 Milestones
- **Runway**: Gen-4.5, Veo 3.1 integration, 4K output, Reference Images
- **Pika**: 2.5 model, Frame Control, Sound generation, 15s gens
- **Luma**: Ray 2 → Ray 2 Flash, Photon API, 4K Upscale, Camera Concepts
- **Haiper**: 2.0 model, Repose, Re-dress
- **Stability**: SV3D launch, company restructuring, slowed video investment
- **Sora**: 2.0 (120s, video editing, multi-character consistency)

### Data Sources
- [runwayml.com/pricing](https://runwayml.com/pricing) — JSON-LD embedded pricing
- [pika.art/pricing](https://pika.art/pricing) — Client-rendered pricing table
- [docs.lumalabs.ai](https://docs.lumalabs.ai) — LLMs.txt structured docs, video-generation.md
- [docs.lumalabs.ai/llms.txt](https://docs.lumalabs.ai/llms.txt) — Complete API index
- [stability.ai/brand-studio-plans](https://stability.ai/brand-studio-plans)
- [openai.com/sora](https://openai.com/sora)
- Full report: `/home/ysga1/ai-video-api-research.md`
