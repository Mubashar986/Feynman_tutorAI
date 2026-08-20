# ADR-003: Vector Database Technology — Qdrant with Local Disk & Remote Adapter

## 1. Context & Problem Statement
The platform requires a high-performance vector and hybrid retrieval store for resource chunk indexing, syllabus grounding, and past-paper question search (PRD §11, §14.3, §27, FR-005, FR-008). Retrieval requires strict metadata payload filtering (filtering by `exam_template_id`, `subject_id`, `topic_id`, `is_authoritative`). Furthermore, the solution must avoid high cloud latency (e.g. Pinecone round-trips), avoid Windows native C++ compilation/DLL friction (e.g. native Windows `pgvector`), and provide seamless offline execution for local development and CI testing.

## 2. Decision
Adopt **Qdrant** as the primary vector store behind an abstracted `VectorStoreBase` protocol. Use Qdrant client's native **local disk persistence mode (`QdrantClient(path="./data/vector_db")`)** or **in-memory mode (`":memory:"`)** for development and unit testing on Windows, and **remote Qdrant server (`url="http://..."`)** for production deployments.

## 3. Evaluated Alternatives

### Option A: Qdrant (Local Disk / In-Memory + Remote Server) (Recommended)
* **Description:** Rust-based vector search engine with Python client supporting both embedded (in-process) and client-server modes.
* **Pros:** Zero-dependency Windows setup (no C++ compilers or external services required for dev), blazing fast HNSW search, rich payload filtering, hybrid dense + sparse search with Reciprocal Rank Fusion (RRF), identical API between local dev and cloud production.
* **Cons:** In local disk mode, only one process can write to the local directory at a time (mitigated by using server mode in multi-process production).
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 84/85.

### Option B: Pinecone (Cloud SaaS Only)
* **Description:** Fully managed cloud vector database.
* **Pros:** Zero local infrastructure management.
* **Cons:** Adds 150–350ms network latency to every RAG retrieval step, paid tier cost scaling, free tiers sleep indexes, невозможно to run offline unit tests in CI without live API keys.
* **Mandatory Gates:** Passes gates, but fails latency and vendor independence (PRD §3.2).
* **Score:** 52/85.

### Option C: Native Windows `pgvector`
* **Description:** PostgreSQL vector extension compiled directly on Windows host.
* **Pros:** Relational and vector data in single database engine.
* **Cons:** High installation friction on Windows native (requires C++ compilers or finding third-party pre-compiled DLLs matching exact Postgres version), creates developer onboarding blockers.
* **Mandatory Gates:** Passes gates, but creates high environment friction on Windows.
* **Score:** 56/85.

### Option D: ChromaDB
* **Description:** Lightweight Python vector database.
* **Pros:** Easy local setup.
* **Cons:** Past stability issues with SQLite versioning and HNSWlib builds on Windows; less mature hybrid search and payload filtering than Qdrant.
* **Mandatory Gates:** Passes gates.
* **Score:** 64/85.

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (Qdrant) | Option B (Pinecone) | Option C (pgvector Windows) | Option D (ChromaDB) |
| :--- | :--- | :--- | :--- | :--- |
| **PRD Alignment** | 5 (Matches §11, §27) | 3 (Vendor lock-in §3.2) | 4 (Good architecture) | 4 (Adequate) |
| **Performance & Latency**| 5 (Sub-5ms local/server) | 2 (150-350ms network hop)| 4 (Fast) | 3 (Adequate) |
| **Windows Ergonomics** | 5 (Pure Python pip install) | 4 (HTTP only) | 1 (C++ compile errors) | 3 (Occasional build issues) |
| **Hybrid Search & Filter**| 5 (Payload index + RRF) | 3 (Basic metadata filter) | 4 (SQL JOIN + pg_trgm) | 3 (Basic) |
| **Gate 1–10 Status** | **PASS (All 10)** | PASS | PASS | PASS |

## 5. Consequences & Implementation Blueprint
* `VectorStoreBase` protocol defined in `backend/app/core/vector_store.py`.
* `QdrantVectorStore` implementation handles collection creation, payload indexing, embedding upsert, and hybrid similarity search.
* In local dev, vector store files reside in `backend/data/vector_db/`.

```yaml
adr_id: ADR-003
title: "Vector Database Technology — Qdrant with Local Disk & Remote Adapter"
decision_level: "Infrastructure / AI Retrieval"
status: accepted
date: "2026-08-20"
depends_on: [ADR-000]
supersedes: []
gates:
  - id: 5
    result: pass
    evidence: "Enables fast, source-grounded retrieval before Socratic tutor generation"
  - id: 10
    result: pass
    evidence: "Abstracted behind VectorStoreBase, avoiding vendor lock-in"
recommended_option: "Option A: Qdrant (Local Disk / In-Memory + Remote Server)"
priority_tier_used_for_tiebreak: "Tier 5 (Maintainability / Extensibility & Windows Ergonomics)"
open_assumptions: []
```
