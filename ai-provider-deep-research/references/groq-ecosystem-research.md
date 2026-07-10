# Groq Ecosystem Research — Reference Summary

**Source session**: 2026-07-07 deep research on Groq ecosystem  
**Method used**: Phase 1B terminal+urllib fallback (no web_search available)

## Key Data Points

### Groq LPU Architecture
- Custom Language Processing Unit (LPU) — purpose-built for inference, not GPUs
- Foundational unit: Tensor Streaming Processor (TSP) — 320 SIMD lanes, 144 instruction queues, 220 MiB on-chip SRAM
- Max system: 10,440 TSPs across 145 racks, ≤5 hops between any two TSPs
- On-chip SRAM bandwidth: 80 TB/s (vs GPU HBM ~8 TB/s)
- Current chip: 14nm process (announced path to 4nm)
- Four design principles: Software-first, Programmable Assembly Line, Deterministic Compute, On-chip Memory
- Deterministic execution → 0.22s TTFT with minimal variance, predictable latency

### GroqCloud API
- URL: `https://api.groq.com/openai/v1` — fully OpenAI compatible
- SDKs: Python (groq, ~609★), TypeScript (groq-typescript, ~257★)
- All generated with Stainless framework
- Highest throughput model: GPT OSS 20B at 1,000 t/s
- Supports: Text Gen, STT/TTS, OCR, Reasoning, Tool Use, MCP (Beta), LoRA, Structured Outputs, Prompt Caching

### Pricing (per 1M tokens)
| Model | Input | Output | Speed |
|:------|:-----:|:------:|:-----:|
| GPT OSS 20B | $0.075 | $0.30 | 1,000 t/s |
| Llama 3.1 8B | $0.05 | $0.08 | 560 t/s |
| GPT OSS 120B | $0.15 | $0.60 | 500 t/s |
| Llama 3.3 70B | $0.59 | $0.79 | 280 t/s |
| Qwen3 32B | $0.29 | $0.59 | 662 t/s |
| Llama 4 Scout | $0.11 | $0.34 | 594 t/s |
| Kimi K2 0905 | $1.00 | $3.00 | 200+ t/s |

### GitHub Ecosystem (41 public repos)
Top repos: groq-api-cookbook (1,384★), openbench (784★), groq-appgen (653★), groq-python (609★), groq-desktop-beta (397★)

### Stability
- 100% API uptime (Apr-Jul 2026) per status.groq.com
- Production vs Preview model tiers distinguished
- Active changelog with regular releases

### Key URLs for future research
- https://console.groq.com/docs — API documentation
- https://groq.com/the-groq-lpu-explained — LPU architecture
- https://codeconfessions.substack.com/p/groq-lpu-design — Deep technical analysis
- https://wow.groq.com/lpu-inference-engine — LPU inference engine
- https://status.groq.com — Service status
- https://github.com/groq — Official GitHub organization
