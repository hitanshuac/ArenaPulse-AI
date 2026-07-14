---
name: rag-pipeline
description: "Instructs the agent to build production-grade RAG pipelines with structure-aware chunking, hybrid retrieval, cross-encoder reranking, and content-hash deduplication. Encodes the stale-cache anti-pattern and the 73% retrieval-failure root cause from 2026 industry analysis. TRIGGERS: 'build a RAG pipeline', 'retrieval augmented generation', 'vector search', 'document Q&A', 'build a knowledge base', 'semantic search over documents', 'chatbot with documents'."
---

# RAG Pipeline Skill

This skill instructs the IDE copilot to scaffold a production-grade Retrieval-Augmented Generation pipeline. It encodes the 2026 industry consensus that **73% of RAG failures are retrieval failures** (wrong context provided to the LLM), not generation failures.

> **Post-Mortem Origin:** This skill was created after the user experienced a critical RAG failure in the `Hybrid-AI-Router` project where the system returned identical answers regardless of input. Root cause: stale embedding cache + naive chunking + no similarity threshold. This skill encodes the exact fix for that failure as Rule #1.

---

## Anti-Patterns (MUST Avoid)

### 1. The "Stale Cache" Trap (USER'S EXACT FAILURE)
- **What happened:** The system cached embeddings and retrieval results. When the user changed the input query, the system returned the same cached context, producing identical answers.
- **Root cause:** No content hashing, no cache invalidation, no similarity threshold.
- **Rule:** EVERY chunk MUST store `content_hash`, `source_url`, and `ingested_at` as metadata. Cache invalidation MUST be provenance-scoped (invalidate only chunks from the changed source, not the entire index). Set a **minimum similarity threshold** (e.g., 0.7) below which retrieved chunks are DISCARDED rather than passed to the LLM.

### 2. Naive Fixed-Size Chunking
- **What it is:** Splitting all documents into fixed 500-character blocks regardless of document structure.
- **Rule:** Use **structure-aware chunking** that respects document boundaries (headings, paragraphs, tables). Use **parent-child chunking** where small child chunks are indexed for precise retrieval, but the larger parent chunk is passed to the LLM for context.

### 3. Vector-Only Retrieval (Missing Hybrid Search)
- **What it is:** Relying exclusively on dense vector embeddings for retrieval. High embedding scores often occur because documents share vocabulary, not because they answer the query.
- **Rule:** ALWAYS combine dense embeddings (vector search) with lexical search (BM25). Use **Reciprocal Rank Fusion (RRF)** to merge results from both.

### 4. No Reranking
- **What it is:** Passing the raw top-k results directly to the LLM without quality filtering.
- **Rule:** ALWAYS use a cross-encoder reranker on the top-k retrieved results to filter out "topically similar but factually irrelevant" chunks.

### 5. Treating All Queries Equally
- **What it is:** Using the same retrieval flow for simple fact-retrieval and complex multi-hop reasoning.
- **Rule:** Classify queries by type BEFORE retrieval. Simple factual queries use direct vector search. Complex synthesis queries use iterative retrieval (agentic RAG) where the model decides if it needs more context.

### 6. No Groundedness Check
- **What it is:** Generating answers without verifying they are supported by the retrieved context.
- **Rule:** Implement an inline hallucination guardrail that verifies the generated answer is strictly supported by the retrieved chunks. If not, return "I don't have enough information" rather than hallucinating.

---

## Scaffolding Instructions

When the user asks to build a RAG pipeline, follow this exact sequence:

### Step 1: Document Ingestion with Content Hashing
```python
import hashlib
from datetime import datetime

def ingest_document(doc_path: str, source_url: str) -> list[dict]:
    """Ingest a document with mandatory metadata for cache invalidation."""
    raw_text = load_document(doc_path)
    chunks = structure_aware_chunk(raw_text)

    processed = []
    for i, chunk in enumerate(chunks):
        content_hash = hashlib.sha256(chunk.encode()).hexdigest()
        processed.append({
            "content": chunk,
            "metadata": {
                "content_hash": content_hash,
                "source_url": source_url,
                "ingested_at": datetime.utcnow().isoformat(),
                "chunk_index": i,
                "parent_chunk": get_parent_context(chunks, i),
            }
        })
    return processed
```

### Step 2: Structure-Aware Chunking (NOT Fixed-Size)
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def structure_aware_chunk(text: str, max_chunk_size: int = 1000) -> list[str]:
    """Chunk by document structure first, then by size as fallback."""
    # First pass: split by structure (headings, sections)
    headers_to_split_on = [
        ("#", "heading_1"),
        ("##", "heading_2"),
        ("###", "heading_3"),
    ]
    structural_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    structural_chunks = structural_splitter.split_text(text)

    # Second pass: if any chunk exceeds max size, split recursively
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=200,  # 20% overlap to preserve context
    )
    final_chunks = []
    for chunk in structural_chunks:
        if len(chunk.page_content) > max_chunk_size:
            final_chunks.extend(size_splitter.split_text(chunk.page_content))
        else:
            final_chunks.append(chunk.page_content)
    return final_chunks
```

### Step 3: Hybrid Retrieval (Dense + BM25 + RRF)
```python
def hybrid_retrieve(query: str, top_k: int = 10) -> list[dict]:
    """Combine vector search and BM25 with Reciprocal Rank Fusion."""
    # Dense retrieval (vector search)
    vector_results = vector_store.similarity_search_with_score(
        query, k=top_k
    )
    # Filter by minimum similarity threshold
    SIMILARITY_THRESHOLD = 0.7
    vector_results = [
        (doc, score) for doc, score in vector_results
        if score >= SIMILARITY_THRESHOLD
    ]

    # Lexical retrieval (BM25)
    bm25_results = bm25_retriever.get_relevant_documents(query)[:top_k]

    # Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(vector_results, bm25_results, k=60)
    return fused[:top_k]
```

### Step 4: Cross-Encoder Reranking
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, documents: list[dict], top_n: int = 5) -> list[dict]:
    """Rerank retrieved documents using a cross-encoder."""
    pairs = [(query, doc["content"]) for doc in documents]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(documents, scores), key=lambda x: x[1], reverse=True
    )
    return [doc for doc, score in ranked[:top_n]]
```

### Step 5: Deduplication on Ingestion
```python
def deduplicate_chunks(new_chunks: list[dict], existing_hashes: set) -> list[dict]:
    """Remove near-duplicate chunks before inserting into the vector store."""
    unique = []
    for chunk in new_chunks:
        if chunk["metadata"]["content_hash"] not in existing_hashes:
            unique.append(chunk)
            existing_hashes.add(chunk["metadata"]["content_hash"])
    return unique
```

### Step 6: Groundedness Guardrail
```python
def check_groundedness(answer: str, context_chunks: list[str]) -> bool:
    """Verify the answer is supported by the retrieved context."""
    prompt = f"""Given the following context, determine if the answer is fully supported.
    Context: {' '.join(context_chunks)}
    Answer: {answer}
    Return ONLY 'grounded' or 'ungrounded'."""

    result = model.invoke(prompt)
    return "grounded" in result.content.lower()
```

---

## Vector Store Selection Guide

| Use Case | Recommended Store | Why |
|:---|:---|:---|
| Local development / prototyping | ChromaDB | Zero config, in-memory option |
| Production with SQL stack | pgvector (PostgreSQL) | Runs alongside existing DB |
| High-scale production | Pinecone / Weaviate | Managed, auto-scaling |
| Free tier / hackathons | ChromaDB or FAISS | No API costs |

---

## Required Dependencies
```
langchain-core>=0.3.0
langchain-text-splitters>=0.3.0
chromadb>=0.5.0  # or pgvector
sentence-transformers>=3.0.0  # for reranking
```

## Reference Implementations
- `Marker-Inc-Korea/AutoRAG` — RAG evaluation and optimization framework (4,853★)
- `NicholasGoh/fastapi-mcp-langgraph-template` — Full-stack with pgvector RAG (548★)
