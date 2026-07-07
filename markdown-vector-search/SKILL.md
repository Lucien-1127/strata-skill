---
name: markdown-vector-search
description: Build ChromaDB-based semantic vector search over a directory of Markdown files. Covers recursive scanning, frontmatter parsing, smart heading-based chunking, OpenAI-compatible embedding, incremental updates, and CLI search.
version: 1.0.0
---

# Markdown Vector Search (ChromaDB + Embedding API)

Build a local semantic search engine over a directory of `.md` files using ChromaDB and any OpenAI-compatible embedding API (FreeLLM API, OpenAI, HuggingFace Inference API, local sentence-transformers).

---

## Architecture

```
Step 1: build_index.py
  docs/*.md ──→ frontmatter parsing ──→ heading-based chunking (tiktoken)
       ↓
  OpenAI-compatible API ──→ embeddings (N dims, configurable)
       ↓
  ChromaDB PersistentClient ──→ vector_store/ (local SQLite)
       ↑
  SHA256 file hash ──→ incremental update (skip unchanged files)

Step 2: search.py
  query string ──→ embed ──→ ChromaDB query (cosine) ──→ top-k results
       ↓
  text output  or  --json output (for pipe/jq)
```

---

## Key Components

### 1. Chunking Strategy

Use tiktoken (cl100k_base) to split Markdown by headings:

```python
def smart_chunk(text, max_tokens=500, overlap=50):
    # Split on ##/### headers → each heading starts a new chunk
    # Keep heading context as metadata for each chunk
    # Overlap preserves context across chunk boundaries
```

- **Default**: 500 tokens per chunk, 50 token overlap
- Headings (`#`, `##`, `###`) are chunk boundaries
- Frontmatter (YAML between `---`) is parsed separately, NOT chunked

### 2. Frontmatter Handling

Use `python-frontmatter` library:

```python
import frontmatter
post = frontmatter.load(filepath)
title = post.metadata.get('title', Path(filepath).stem)
tags = post.metadata.get('tags', [])
content = post.content
```

Tags stored as comma-separated string in ChromaDB metadata (ChromaDB doesn't support list values).

### 3. Embedding API Configuration

OpenAI-compatible client (works with any provider):

```python
from openai import OpenAI
client = OpenAI(api_key=KEY, base_url=BASE_URL)  # e.g. http://localhost:3001/v1
response = client.embeddings.create(model=MODEL, input=texts)
```

### 4. ChromaDB Setup

```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./vector_store/",
    settings=Settings(anonymized_telemetry=False),
)
collection = client.get_or_create_collection(
    name="my_docs",
    metadata={"hnsw:space": "cosine"},
)
```

### 5. Incremental Updates

Track file changes via SHA256 hash (stored in YAML):

```python
def compute_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
```

### 6. Search

```python
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k,
    include=["documents", "metadatas", "distances"],
)
# score = 1 - distance  (cosine distance to similarity)
```

---

## Configuration Template (`config.yaml`)

```yaml
docs_path: /path/to/docs                # .md 文件根目錄
api_base: http://localhost:3001/v1       # OpenAI-compatible API
api_key: your-api-key                    # 或透過環境變數
embedding_model: text-embedding-3-small  # 模型名稱
vector_store_path: ./vector_store/       # ChromaDB 持久化路徑
top_k: 5                                 # 預設搜尋結果數
```

---

## Output Formats

### Default (text)

```
  [1] 📄 10_核心控制層/12_核心閘門_CORE_GATE_v1.1.0.md
       標題: 12_核心閘門_CORE_GATE_v1.1.0
       分數: 0.8876
       標籤: 法律/AI, 智研, 核心, 閘門
       摘要: ## 12_核心閘門_CORE_GATE_v1.1.0 ... ## 角色定位 ...
```

### JSON (`--json` flag)

```json
[{
  "filepath": "/path/to/file.md",
  "relpath": "subdir/file.md",
  "title": "Document Title",
  "tags": "tag1, tag2",
  "score": 0.8876,
  "chunk_index": 0,
  "total_chunks": 5,
  "summary": "First 100 chars..."
}]
```

---

## Providers Matrix

| Provider | API Base | Model Example | Dims | Cost | Notes |
|:---------|:---------|:-------------|:----:|:----:|:------|
| FreeLLM API (:3001) | `http://localhost:3001/v1` | `text-embedding-3-small` | 1536 | $0 | GitHub free routing |
| HuggingFace Inference | `https://api-inference.huggingface.co` | `BAAI/bge-m3` | 1024 | $0 | Needs token, rate-limited |
| OpenAI | `https://api.openai.com/v1` | `text-embedding-3-small` | 1536 | 💰 | $0.02/1M tokens |
| Local sentence-transformers | `http://localhost:8765/v1` | `all-MiniLM-L6-v2` | 384 | $0 | Needs CPU/GPU, ~80MB-2GB |

---

## Pitfalls

### ChromaDB Batch Write Lock

ChromaDB 1.5.9 PersistentClient can trigger Rust-level SQLite lock when doing per-file `collection.add()` in a loop. **Always batch all chunks into a single `collection.add()` call:**

```python
# ❌ May deadlock:
for filepath in files:
    collection.add(embeddings=..., ids=...)

# ✅ Safe:
all_embeddings, all_ids, all_metadatas = [], [], []
for filepath in files:
    all_embeddings.extend(file_embeddings)
    all_ids.extend(file_ids)
    all_metadatas.extend(file_metadatas)
collection.add(embeddings=all_embeddings, ids=all_ids, metadatas=all_metadatas)
```

### Dimension Mismatch

When switching embedding models, vector dimensions MUST match. If they don't, delete the old store and rebuild:

```bash
rm -rf vector_store/
python build_index.py
```

Common dimensions:
- text-embedding-3-small → 1536
- bge-m3 → 1024
- all-MiniLM-L6-v2 → 384
- text-embedding-3-large → 3072

### bge-m3 Prefix Convention

When using bge-m3 via HuggingFace Inference API, prefix text differently for indexing vs querying:

```python
# For documents (indexing):
prefixed = f"Represent this sentence for searching relevant passages: {text}"

# For queries (searching):
prefixed = f"Represent this query for searching relevant passages: {query}"
```

This is required by bge-m3's training and ignoring it degrades results significantly.

### Rate Limiting

Free APIs (HF Inference, FreeLLM GitHub route) have rate limits. Batch embedding calls (8-16 per batch) with retry logic.

```python
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    try:
        response = client.embeddings.create(model=model, input=batch)
    except Exception as e:
        time.sleep(5)  # backoff
        response = client.embeddings.create(model=model, input=batch)
```

### Large Directories

For 100+ `.md` files with 500+ total chunks, expect:
- FreeLLM API / HF API: ~2-5 minutes (network latency)
- Local sentence-transformers: ~1-2 minutes (CPU)
- OpenAI API: ~30 seconds

---

## Related Skills

- `local-embedder-mem0-setup` — Mem0 OSS memory provider setup (uses same embedder pattern)
- `zhiyan-agent` — zhiyan-legal system prompts (the docs this searches)
