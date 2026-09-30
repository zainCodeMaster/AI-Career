# CareerOS Master Roadmap

Date: 2026-09-21

This roadmap is evidence-based against the current repository. A phase is
complete only when its backend, UI, persistence, authorization, tests, and
important user journey are verified together.

## Phase 1-7

| Phase | Domain | Status | Evidence and remaining work |
| --- | --- | --- | --- |
| 1 | Authentication and security foundation | PARTIAL | Registration, login, protected routes, password hashing, rate limiting, and server-side token invalidation are implemented. Refresh-token rotation, device/session management, and broader security integration tests remain. |
| 2 | Career profile and career data | COMPLETE | Profile, skills, education, experience, and certifications have authenticated CRUD flows and backend coverage. |
| 3 | Career Brain and Career DNA | PARTIAL | Indexing, search, and context retrieval are real and user-scoped. A first-class structured Career DNA model and presentation are not yet verified. |
| 4 | Job discovery | PARTIAL | Normalization, source registry, discovery history, filtering, saving, preferences, and source health exist. Live source reliability and operational monitoring need production verification. |
| 5 | AI job matching | PARTIAL | Match scoring, explanations, gaps, and match detail are connected to profile/job data. Resume-aware application preparation and broader frontend workflow tests remain. |
| 6 | Resume and document intelligence | PARTIAL | CRUD, sections, versions, import, profile build, ATS analysis, and tailoring exist. Secure export/download and complete document relationships are not fully surfaced. |
| 7 | Career CRM | PARTIAL | Applications, state transitions, pipeline, analytics, companies, contacts, interviews, follow-ups, offers, and activities have backend support. Several detail/edit/document flows remain incomplete in the UI. |

## Required post-Phase-7 work

### Phase 8 - Production hardening (IN PROGRESS)

- Use Alembic for production schema evolution; keep `create_all` limited to
  local development and tests.
- Add revocable authentication semantics and regression coverage. Refresh-token
  rotation and logout invalidation are now implemented at the backend API layer.
- Add request correlation IDs, structured error logging, readiness checks, and
  operationally useful failure visibility. Request IDs and `/ready` validation
  are now live.
- Expand frontend workflow tests beyond the current route smoke test.

### Phase 9 - End-to-end product completion (NEXT)

- Finish Career DNA as a structured, explainable user-facing representation.
- Complete resume export/download with content-type, size, and ownership
  enforcement.
- Surface CRM detail/edit flows for interviews, documents, offers, and
  rejections.
- Add authenticated browser journeys for the critical product loop:
  profile -> discovery -> match -> resume -> application -> follow-up.

### Phase 10 - SaaS release readiness (DEFERRED UNTIL JUSTIFIED)

- Add deployment/runbook validation, database backup/restore exercises,
  production observability integration, and privacy/compliance review.
- Add billing, notifications, or admin operations only after a concrete
  product/business requirement exists; they are not fabricated in this
  repository.

## Exit criteria

The roadmap can stop only when no phase is PARTIAL for a product-critical
workflow, the final matrix is backed by passing tests and browser evidence,
and deployment instructions describe a reproducible migration-first setup.

