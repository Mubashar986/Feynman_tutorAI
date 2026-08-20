# Data Decision Records (DDR) Index

Status legend: `PENDING` (not started) · `IN_PROGRESS` · `PROPOSED` (generated, awaiting user acceptance) · `ACCEPTED` · `SUPERSEDED`

## What are DDRs?
Data Decision Records (DDRs) govern the platform's data strategy, including schemas, migrations, isolation paradigms, consistency guarantees, and graph models. They detail how data flows, is structured, stored, and retrieved. 

DDRs are created **just-in-time** when a specific problem space requires rigorous data modeling decisions. New rows are added as data decisions surface during development.

## Existing DDRs

| ID | Data Decision Title | Scope | PRD Reference | Status |
|---|---|---|---|---|
| DDR-001 | Schema Migration Protocol (Expand/Contract Zero-Downtime) | Database Migrations | NFR-Data | PENDING |
| DDR-002 | Multi-Tenant Student State Isolation Strategy | Data Security | NFR-006 | PENDING |
| DDR-003 | Vector Store Schema & Metadata Filtering Taxonomy | Search | FR-008 | PENDING |
| DDR-004 | Knowledge Graph Schema (Concept Nodes, Prerequisite & Misconception Edges) | Learning Graph | FR-013 | PENDING |
| DDR-005 | Immutable Append-Only Audit & Learning Event Log Stream | Auditing | FR-022 | PENDING |
| DDR-006 | Polyglot Consistency (Postgres ↔ Vector Store ↔ Cache) | Consistency | NFR-Data | PENDING |
