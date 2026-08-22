# ADR-011: Server-Side Authentication Provider, JWT Strategy & RBAC Architecture

* **Status:** PROPOSED (Awaiting User Acceptance)
* **Date:** 2026-08-23
* **PRD Reference:** PRD §5.2, §27, FR-021, NFR-005, Non-Negotiable Constraint #6
* **Architectural Domain:** Authentication, Authorization & Multi-Tenant Isolation
* **Author:** Backend Lead

---

## 1. What is the Decision?

This record decides the server-side authentication architecture, token serialization strategy, password hashing mechanism, and role-based access control (RBAC) implementation for the AI Adaptive Exam Learning Platform.

### Out of Scope:
- Social OAuth / SSO providers (deferred to enterprise phase).
- WebAuthn / Passkeys (Phase 3).

---

## 2. Why do we need this decision?

1. **Non-Negotiable Product Constraint #6**: Role-based access must be enforced strictly server-side (PRD FR-021, NFR-005). Client-side checks alone are never trusted.
2. **Student State Isolation (Constraint #2)**: Every database transaction and learning session must be strictly partitioned by `student_id` extracted from a cryptographically verified token.
3. **Stateless Scalability**: The backend must support concurrent requests across FastAPI workers without session-state bottlenecks or persistent DB reads on every static asset request.
4. **Zero Dependency Drift**: Replacing legacy unmaintained libraries (`passlib` last released 2020) with active, audited cryptographic libraries (`PyJWT`, `bcrypt`).

---

## 3. Candidate Approaches Evaluated

### Option 1: FastAPI Native OAuth2 Bearer + `PyJWT` + `bcrypt` (RECOMMENDED)
* **Description**: Custom stateless JWT authentication using standard RFC 7519 HMAC-SHA256 tokens (`PyJWT`) paired with direct `bcrypt` password hashing executed in thread pools.
* **How it works**:
  - Registration hashes password via `bcrypt.hashpw()` with random salt cost $\ge 12$.
  - Login returns a signed JWT `access_token` (15-minute TTL) containing `sub` (user_id), `role`, and `exp`, plus a secure `refresh_token` (7-day TTL).
  - FastAPI dependency `get_current_user()` and `require_role(["instructor", "admin"])` validates signature and enforces server-side RBAC on every protected route.
* **Pros**: Standard, stateless, zero vendor lock-in, OWASP compliant, highly performant on Windows and Linux.
* **Cons**: Requires managing token invalidation (via short TTL or Redis blocklist if needed).
* **Gate 6 (Server-Side RBAC)**: PASS (Enforced via FastAPI `Depends()`).

### Option 2: Python Standard Library Only (`hmac` + `hashlib.scrypt`)
* **Description**: Use standard library `hashlib.scrypt` for password hashing and custom signed JSON tokens using `hmac.digest`.
* **How it works**: Uses zero third-party dependencies.
* **Pros**: 0 pip installations.
* **Cons**: Reinventing standard JWT parsing, lacks standard RFC 7519 ecosystem tooling, harder for frontend libraries to decode claims cleanly.
* **Gate 6**: PASS.

### Option 3: Third-Party Managed Auth (Auth0 / Supabase / Clerk)
* **Description**: Delegate all authentication and user persistence to an external cloud auth provider.
* **Pros**: Out-of-the-box UI and multi-factor auth.
* **Cons**: Introduces external SaaS dependency, recurring cost, breaks offline local development guarantee, conflicts with PRD multi-tenant data isolation.
* **Gate 6**: PASS.

### Option 4: Legacy `passlib[bcrypt]` + `python-jose`
* **Description**: Traditional FastAPI tutorial auth stack.
* **Cons**: `passlib` is unmaintained (last release 2020), incompatible with bcrypt 4.0+ without monkey-patching, `python-jose` has unaddressed CVEs.
* **Gate 6**: PASS.

---

## 4. 17 Quality Controls Evaluation Matrix

| Quality Control | Option 1 (FastAPI + PyJWT + bcrypt) | Option 2 (Pure Stdlib) | Option 3 (Managed SaaS) | Option 4 (passlib + python-jose) |
| :--- | :---: | :---: | :---: | :---: |
| 1. PRD Alignment | **5** (Exact match to FR-021) | 3 | 3 | 3 |
| 2. Correctness | **5** (RFC 7519 standard) | 3 | 4 | 2 (bcrypt 4.0 incompatibilities) |
| 3. Security | **5** (OWASP bcrypt salt + HS256) | 4 | 5 | 2 (Outdated deps) |
| 4. Privacy | **5** (Self-hosted user DB) | 5 | 2 (Cloud PII leakage) | 5 |
| 5. Maintainability | **5** (Active audited packages) | 3 | 4 | 1 (Dead packages) |
| 6. Scalability | **5** (Stateless JWT verification) | 5 | 4 (Rate limits) | 4 |
| 7. Performance | **5** (Fast C-extensions) | 4 | 2 (External HTTP calls) | 4 |
| 8. Reliability | **5** (Zero external downtime risk) | 5 | 3 (Third-party outages) | 3 |
| 9. Data Integrity | **5** (Foreign keys in SQLModel) | 5 | 3 (SaaS sync drift) | 4 |
| 10. Explainability | **5** (Standard claim inspection) | 3 | 2 | 4 |
| 11. Auditability | **5** (User ID in all audit logs) | 5 | 3 | 4 |
| 12. Extensibility | **5** (Easy to add MFA/OAuth later) | 2 | 4 | 2 |
| 13. AI Safety | **5** (Clean student state scoping) | 5 | 5 | 5 |
| 14. MVP Fit | **5** (Fast setup, zero cost) | 3 | 3 | 2 |
| 15. Cost | **5** ($0.00 infrastructure cost) | 5 | 1 ($/MAU pricing) | 5 |
| 16. Implementation Effort | **4** (Simple modular auth service) | 2 | 4 | 3 |
| 17. Risk | **5** (Lowest architectural risk) | 3 | 3 | 1 (CVE risk) |
| **Total Score** | **83 / 85 (97.6%)** | 63 / 85 | 55 / 85 | 50 / 85 |

---

## 5. Mandatory Gates Verification

| Gate # | Rule | Option 1 Verification | Result |
| :---: | :--- | :--- | :---: |
| **Gate 2** | Student state isolated per student | `get_current_user` extracts `user_id` from token claims | ✅ **PASS** |
| **Gate 6** | Role-based access enforced server-side | `require_role(["instructor", "admin"])` route dependencies | ✅ **PASS** |
| **Gate 10** | Provider-specific logic isolated | Auth logic lives strictly in `backend/app/auth/` | ✅ **PASS** |

---

## 6. Implementation Blueprint

1. **Dependencies**: `pyjwt>=2.8.0`, `bcrypt>=4.1.0`.
2. **User Models (`backend/app/auth/models.py`)**:
   - `UserRole(str, Enum)`: `STUDENT = "student"`, `INSTRUCTOR = "instructor"`, `ADMIN = "admin"`.
   - `User(SQLModel, table=True)`: `id`, `email` (unique index), `hashed_password`, `full_name`, `role`, `is_active`, `created_at`, `updated_at`.
3. **Security Utilities (`backend/app/auth/security.py`)**:
   - `hash_password(password: str) -> str`
   - `verify_password(plain_password: str, hashed_password: str) -> bool`
   - `create_access_token(user_id: str, role: str, expires_delta: timedelta) -> str`
   - `decode_token(token: str) -> TokenPayload`
4. **Route Dependencies (`backend/app/auth/dependencies.py`)**:
   - `get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)) -> User`
   - `require_role(allowed_roles: List[UserRole])`
5. **API Endpoints (`backend/app/auth/router.py`)**:
   - `POST /api/v1/auth/register`: Creates new user with hashed password.
   - `POST /api/v1/auth/login`: Verifies password and returns `{ access_token, token_type: "bearer", user }`.
   - `GET /api/v1/auth/me`: Returns current authenticated user profile.
