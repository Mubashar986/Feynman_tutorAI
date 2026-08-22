# ADR-018: RAG Document Chunking, Heading Hierarchy & Formula Preservation Strategy

**Status:** PROPOSED  
**Date:** 2026-08-23  
**Deciders:** Principal Architect & AI/RAG Engineer  
**PRD Reference:** PRD §27 (RAG Chunking/Embedding Parameters), §5.3, §14.3, FR-005, FR-008, NFR-005

---

## 1. What is the Decision?

This decision defines the text chunking algorithms, window sizes, overlap ratios, heading hierarchy preservation, and LaTeX mathematical formula protections used to segment curriculum documents (textbooks, PDFs, syllabus notes) for vector embedding and grounded RAG retrieval.
- **In Scope:** Chunking strategy, target chunk token size, overlap percentage, metadata schema per chunk, heading breadcrumbs, LaTeX formula atomic preservation, and document status state machine.
- **Out of Scope:** Vector database indexing (ADR-003) and embedding vector generation models (ADR-007).

---

## 2. Why do we need this decision?

In an adaptive STEM learning platform (Physics, Calculus, Chemistry), naive text chunking destroys pedagogical context:
1. **Mathematical Formula Fracture:** If a chunk split occurs in the middle of a LaTeX equation (e.g. splitting `$R = \frac{u^2 \sin(2\theta)}{g}$`), the equation becomes unparseable and mathematically incorrect.
2. **Context Loss (Lost Subsections):** If a paragraph describing *"Terminal Velocity"* is chunked without retaining its parent header (*"Chapter 2: Forces in Fluids"*), semantic search fails to associate it with fluid mechanics.
3. **Chunk Size Drift:** Too small chunks (<128 tokens) lack sufficient context for Feynman explanations; too large chunks (>1500 tokens) dilute semantic similarity and exceed embedding vector density limits.

---

## 3. Candidate Approaches Evaluated

### Option 1: Hierarchical Recursive Character Splitter with Heading Breadcrumbs & LaTeX Protection (Recommended)
- **Architecture:** Splits hierarchically on markdown headers (`#`, `##`, `###`), double newlines (`\n\n`), single newlines (`\n`), and spaces, while treating LaTeX math blocks (`$$...$$`, `\(...\)`) as atomic indivisible units.
- **Parameters:** Target chunk size = **512 tokens (~2000 chars)**; Overlap = **15% (~75 tokens / 300 chars)**.
- **Metadata:** Each chunk stores `heading_hierarchy` (e.g., `["Mechanics", "Kinematics", "Projectile Motion"]`), `chunk_index`, `page_number`, `token_count`, and parent `topic_id`.
- **Pros:** Preserves mathematical integrity, maintains semantic hierarchy, optimal for dense vector search and grounded citations.
- **Cons:** Slightly more complex tokenizer and regex parsing.

### Option 2: Fixed-Size Character Window with Zero Overlap
- **Architecture:** Slices text every 1000 characters regardless of word or sentence boundaries.
- **Pros:** Trivial 2-line implementation.
- **Cons:** Splits words in half, breaks LaTeX formulas, causes massive hallucination in RAG answers. Disqualified.

### Option 3: Sentence-Only Chunking
- **Architecture:** Chunks text strictly by single sentences.
- **Pros:** Grammatically clean.
- **Cons:** Individual sentences lack sufficient context to explain complex derivations, leading to high token overhead and weak vector retrieval.

### Option 4: LLM-Assisted Semantic Chunking
- **Architecture:** Calls an LLM to read each document page and output semantic chunk boundaries.
- **Pros:** Highly contextual.
- **Cons:** Expensive ($0.02/page), slow (seconds per document), and vulnerable to rate limits and nondeterministic chunk outputs.

---

## 4. Evaluation Matrix (17 Quality Controls & 10 Gates)

| Quality Control / Gate | Option 1 (Recursive + LaTeX) | Option 2 (Fixed) | Option 3 (Sentence) | Option 4 (LLM Chunking) |
|:---|:---:|:---:|:---:|:---:|
| **1. PRD Alignment (FR-005, FR-008)** | 5/5 | 1/5 | 3/5 | 4/5 |
| **2. LaTeX Formula Integrity** | 5/5 | 1/5 | 2/5 | 4/5 |
| **3. Grounded Retrieval Accuracy** | 5/5 | 2/5 | 3/5 | 4/5 |
| **4. Ingestion Latency & Cost** | 5/5 | 5/5 | 4/5 | 1/5 |
| **5. Determinism & Testability** | 5/5 | 5/5 | 4/5 | 2/5 |
| **10 Mandatory Product Gates** | **PASS** | FAIL | **PASS** | FAIL |

---

## 5. Concrete Decision & Implementation Blueprint

**Decision:** Adopt **Option 1 (Hierarchical Recursive Character Splitter with Heading Breadcrumbs & LaTeX Protection)**.
- **Target Chunk Size:** 512 tokens (~2048 characters).
- **Chunk Overlap:** 75 tokens (~300 characters, ~15%).
- **Relational Tables:**
  - `Document`: Tracks uploaded file metadata, SHA-256 hash, size, status (`PENDING`, `PROCESSING`, `CHUNKED`, `INDEXED`, `FAILED`), and associated `exam_template_id` / `topic_id`.
  - `DocumentChunk`: Tracks chunk text, clean text, `chunk_index`, `page_number`, `token_count`, `heading_breadcrumbs`, and `topic_id`.
- **Location:** `backend/app/rag/` (`chunker.py`, `models.py`, `service.py`, `router.py`).
