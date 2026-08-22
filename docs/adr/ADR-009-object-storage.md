# ADR-009: Object Storage Provider Strategy for Document Ingestion

**Status:** PROPOSED  
**Date:** 2026-08-23  
**Deciders:** Principal Architect & Backend Lead  
**PRD Reference:** PRD §27 (Object Storage Provider), §5.3, FR-005, NFR-005 (Untrusted File Ingestion)

---

## 1. What is the Decision?

This decision establishes the storage architecture for uploaded source documents (textbooks, past papers, syllabus guides, PDF/Markdown/TXT files) in the AI-Powered Adaptive Exam Learning Platform.
- **In Scope:** File ingestion storage interface, local disk zero-setup development driver, S3/MinIO production storage adapter, content hashing (SHA-256), and file validation security boundaries.
- **Out of Scope:** Vector embedding storage (governed by ADR-003) and relational metadata storage (governed by ADR-001).

---

## 2. Why do we need this decision?

PRD §5.3 and FR-005 require students and instructors to upload curriculum documents to ground Feynman AI explanations and question generation. 
PRD Constraint #7 mandates: *"Uploaded files must be treated as untrusted input"*.
Without a standardized storage interface:
1. Local development would require setting up external AWS S3 buckets or local Docker MinIO instances, breaking the zero-setup local Windows development guarantee.
2. Hardcoding local filesystem paths would prevent cloud container deployments (Kubernetes, ECS) where local disk is ephemeral.
3. Raw file storage without content deduplication and SHA-256 hashing would lead to duplicate storage and race conditions.

---

## 3. Candidate Approaches Evaluated

### Option 1: Pluggable `StorageProvider` Protocol with Local Disk Driver (Default) + S3 Driver (Recommended)
- **Architecture:** Abstract `StorageProvider` class with `save_file()`, `get_file()`, `delete_file()`, and `get_file_path()`. Default implementation stores files in `data/uploads/` with sanitized SHA-256 filenames; environment variable `STORAGE_BACKEND=s3` switches to AWS S3/MinIO.
- **Pros:** Zero external dependencies for local dev, production-ready S3 adapter, clean test mockability.
- **Cons:** Requires implementing two lightweight driver classes.

### Option 2: Hardcoded Local Filesystem Storage Only
- **Architecture:** Save all files directly using `aiofiles` / `open()` to a fixed directory.
- **Pros:** Minimal lines of initial code.
- **Cons:** Fails immediately in multi-instance cloud deployments with ephemeral storage.

### Option 3: Mandatory Cloud AWS S3
- **Architecture:** Require AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`) for all development and testing.
- **Pros:** Cloud-native from day 1.
- **Cons:** Fails zero-setup developer prerequisite protocol.

### Option 4: Database BLOB Storage (PostgreSQL `BYTEA`)
- **Architecture:** Store raw binary file content directly in PostgreSQL/SQLite tables.
- **Pros:** Relational transactions include file data.
- **Cons:** Rapidly bloats database backups, degrades query performance, and exceeds SQLite in-memory limits.

---

## 4. Evaluation Matrix (17 Quality Controls & 10 Gates)

| Quality Control / Gate | Option 1 (Pluggable Local/S3) | Option 2 (Local Only) | Option 3 (Mandatory S3) | Option 4 (DB BLOB) |
|:---|:---:|:---:|:---:|:---:|
| **1. PRD Alignment (§5.3, §27)** | 5/5 | 3/5 | 4/5 | 2/5 |
| **2. Correctness & Isolation** | 5/5 | 3/5 | 5/5 | 4/5 |
| **3. Security & Untrusted Input (NFR-005)** | 5/5 | 3/5 | 5/5 | 3/5 |
| **4. Zero-Setup Local Dev Guarantee** | 5/5 | 5/5 | 1/5 | 4/5 |
| **5. Maintainability & Testability** | 5/5 | 3/5 | 2/5 | 3/5 |
| **6. Scalability & Cloud Readiness** | 5/5 | 1/5 | 5/5 | 1/5 |
| **10 Mandatory Product Gates** | **PASS** | FAIL | FAIL | **PASS** |

---

## 5. Concrete Decision & Implementation Blueprint

**Decision:** Adopt **Option 1 (Pluggable `StorageProvider` Protocol)**.
- **Driver 1 (`LocalStorageProvider`):** Default for development and test execution. Stores files under `data/uploads/` using UUID/hash prefixes with path traversal guards (`os.path.abspath` verification).
- **Driver 2 (`S3StorageProvider`):** Enabled when `STORAGE_BACKEND=s3`.
- **Location:** `backend/app/core/storage/`.
