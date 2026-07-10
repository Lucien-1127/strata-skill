---
name: document-vector-search
description: Build vector search over a markdown documentation repo using ChromaDB + any OpenAI-compatible embedding API. Covers multi-backend support, smart chunking by Markdown headers, incremental index updates, and frontmatter metadata preservation.
status: stable
---

# Document Vector Search

Build a semantic vector search over a markdown documentation repository. Uses ChromaDB for local persistent storage and any OpenAI-compatible embedding API (FreeLLM, OpenAI, HuggingFace Inference API, etc.).

## When to Use

- User asks to build search over a local docs/ directory
- Need semantic (vector) search over markdown content
- Want incremental indexing that skips unchanged files
- Need both CLI-friendly text output and JSON pipe output

## Project Structure

```
project/
├── build_index.py       # Index builder
├── search.py            # Semantic search
├── config.yaml          # Shared config (public)
├── .env                 # API keys (gitignored, NOT in config.yaml)
├── .gitignore
├── requirements.txt
├── vector_store/        # ChromaDB data (auto-created)
└── README.md
```

## Config Design

**config.yaml** — store only non-secret settings:
```yaml
docs_path: /path/to/docs
api_base: http://localhost:3001/v1    # OpenAI-compatible endpoint
api_key: ""                           # Leave blank; set in .env or env vars
embedding_model: text-embedding-3-small
vector_store_path: ./vector_store/
top_k: 5
```

**.env** — secrets only (add to .gitignore):
```
# FREELMAPI_KEY=sk-xxx
# OPENAI_API_KEY=sk-xxx
# HUGGINGFACE_TOKEN=hf_xxx
```

## Multi-Backend Embedding

| Backend | config.yaml `api_base` | Dims | Key Source |
|---------|----------------------|------|-----------|
| **FreeLLM API** (local Docker) | `http://localhost:3001/v1` | 1536 | `FREELMAPI_KEY` env / .env |
| **OpenAI API** | `https://api.openai.com/v1` | 1536 | `OPENAI_API_KEY` env |
| **HuggingFace Inference API** | (use huggingface_hub) | 1024 | `HUGGINGFACE_TOKEN` env |

For HuggingFace, use `InferenceClient.feature_extraction()` instead of OpenAI client. bge-m3 requires prefixes:
- **Documents**: `"Represent this sentence for searching relevant passages: " + text`
- **Queries**: `"Represent this query for searching relevant passages: " + text`

## Smart Chunking (Markdown-Aware)

Chunk by Markdown headings (`#` / `##` / `###`) for semantic coherence:

1. Each heading starts a new chunk
2. Chunks too long (>500 tokens) split further by paragraph
3. Overlap (~50 tokens) between consecutive chunks
4. Track `current_heading` as context for each chunk
5. Enrich each chunk with document title + heading context

Use tiktoken (`cl100k_base`) for accurate token counting.

## Frontmatter Metadata

Parse YAML frontmatter with `python-frontmatter`:
```python
post = frontmatter.load(filepath)
title = post.metadata.get("title", Path(filepath).stem)
tags = post.metadata.get("tags", [])
```

Store as ChromaDB metadata (list values must be stringified):
```python
metadatas=[{
    "filepath": filepath,
    "relpath": relpath,
    "title": title,
    "tags": ", ".join(tags),
    "chunk_index": str(i),
    "total_chunks": str(len(chunks)),
}]
```

## Incremental Updates

Skip already-indexed, unchanged files using SHA256 hashes:

1. `compute_file_hash()` — SHA256 of full file content
2. Store in `.file_hashes.yaml` in vector_store/
3. Before processing each file, compare hash
4. On change: delete old chunks by `filepath` filter, re-add
5. On unchanged: skip

## OpenAI-Compatible Client

Use `openai` library with custom `base_url` for all backends:
```python
from openai import OpenAI
client = OpenAI(api_key=cfg["api_key"], base_url=cfg["api_base"])
response = client.embeddings.create(model=model, input=batch)
```

## Pitfalls

- **Secrets in config**: User WILL object if you put API keys in config.yaml. Use `.env` file or env vars.
- **ChromaDB list metadata**: ChromaDB doesn't support list values in metadata. Stringify with `", ".join(list)`.
- **Dimension mismatch**: If you switch embedding models, you MUST delete the old `vector_store/` and rebuild. ChromaDB won't warn you.
- **bge-m3 prefixes**: Document and query prefixes differ. Using the wrong prefix degrades search quality by 10-20%.
- **FreeLLM API model names**: Not all models support `/v1/embeddings`. `text-embedding-3-small` works; test first with a single curl.
- **Rate limits**: HuggingFace free tier has rate limits. Batch embeddings (8-16 per batch).
- **File not found**: ChromaDB `get_collection()` raises `ValueError` on missing collection, not a friendly message. Catch and guide user to run `build_index.py` first.

## CLI Design

```
# Build or update index
python build_index.py [-c config.yaml]

# Search
python search.py "query" [-k 10] [--json]

# Interactive mode (no query arg)
python search.py
```

JSON output for piping:
```json
[{"filepath": "...", "relpath": "...", "title": "...", "score": 0.89, "summary": "..."}]
```
