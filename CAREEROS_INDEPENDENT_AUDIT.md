# CareerOS AI — Independent Source Audit & Final Work Plan

**Snapshot reviewed:** `CareerOS-Current.zip` uploaded 30 October 2026  
**Review type:** Static source inspection, Python syntax compilation, test/build attempts, review of the supplied login screenshots, and current official API/SDK/Node documentation.  
**Important boundary:** This is the ZIP snapshot, not a live connection to the user's Windows machine or a deployed CareerOS service. `.env`, `.venv`, `node_modules`, local databases and credentials were excluded. No source files in the user's original project were changed.

## 1. Executive verdict

CareerOS is a broad full-stack FYP prototype, but the uploaded snapshot does **not** justify describing the product as a verified real-time, autonomous, fully AI-powered career operating system. There are multiple strong modules, but key pathways have code-level integration defects.

The highest-risk issues are:

1. Automatic scheduled job discovery currently skips every scheduled run because one boolean is used both for scheduler-started state and the active-run lock.
2. Remote OK and Himalayas adapters are registered in Python, but the database source registry does not seed either source, all seeded sources default disabled, and there is no source enable/configuration API or UI.
3. The Himalayas adapter does not map the current official API response contract, does not paginate, requests more than the official 20-job page cap, and misses the canonical application link and stable `guid`.
4. Pakistan eligibility is represented by both a boolean and a three-state string; the frontend collapses `unknown` into `false`, the backend defaults unfiltered job results to the boolean `true`, and source adapters default uncertain remote listings to eligible.
5. A new Alembic migration adds `jobs.eligibility` even though the earlier Phase 4 migration already created that column. A clean migration path is therefore likely to fail on a duplicate column.
6. Gemini code uses the deprecated `google-generativeai` SDK and the shut-down `gemini-1.5-flash` default. The Career Brain answer endpoint is not called by the frontend page.
7. Multiple visible UI controls are inert or misleading (global search, notifications, theme handling, invalid sidebar routes); the visual redesign is not consistent across all screens.

**Bottom line:** Fix the core data, migrations, scheduler, AI wiring, and source provisioning before adding more features. Building all future SaaS modules now would add breadth while the main job-discovery and AI journeys remain unreliable.

## 2. Checks actually performed

| Check | Result | What this does / does not prove |
|---|---|---|
| ZIP extraction and source inventory | Completed; 567 files extracted | Snapshot is readable; generated artifacts are also present |
| Backend Python syntax | `python -m compileall -q backend/app backend/migrations backend/tests` passed | Syntax only; not import/runtime correctness |
| Backend pytest | Blocked at collection: `ModuleNotFoundError: No module named 'jose'` | No test pass/fail total can be reported from this environment |
| Python dependency installation | Blocked: container DNS/network could not reach PyPI | Could not install `backend` requirements for a full test run |
| Frontend dependencies | `npm ci` timed out | Frontend tests/build were not run |
| Frontend Node runtime in this audit container | Node 22.16.0 | Lockfile includes `jsdom` requiring Node `^22.22.2 || ^24.15.0` and `undici` requiring `>=22.19.0`; this container is too old for those locked packages |
| Python unit/integration tests | Not verified | Do not rely on the historical 493/500+ test claims as a fresh run |
| Browser/E2E | Not run | ZIP does not include a running service or browser installation |
| Live Gemini | Not run | No API key was included, as expected |
| Live job API HTTP calls | Not run from the app | Official current API docs were checked; connector behaviour in the live runtime remains unverified |
| Database migration | Not executed | Duplicate-column issue found by static revision/model inspection; test it only on a disposable database |
| UI review | Two login screenshots reviewed | Only login visual treatment can be assessed; not the entire application |

The user previously reported Node 24.18.0 on the Windows development machine; this version satisfies the checked Node package engine ranges, but the install/build still needs to be run locally with that actual runtime.

## 3. Verified P0 defects — fix before FYP demonstration

### P0.1 Scheduler never runs discovery (code-level defect)

**Evidence:** `backend/app/services/scheduler.py`
- `start()` sets `self._running = True` after starting APScheduler (around lines 95–96).
- `_run_discovery()` immediately checks `if self._running: return` (around lines 110–115).
- Therefore, once the application starts the scheduler, its callback observes `_running == True` and exits without discovering jobs.
- The same flag is also set/reset around an individual run, so it conflates “scheduler is alive” with “job run is in progress”.

**Impact:** The scheduled hourly discovery path is not operational. A green scheduler startup log would be misleading because the callback self-skips.

**Fix:** Use two separate states/locks, e.g. `_scheduler_started` and `_run_in_progress` (prefer a thread lock for the latter). The scheduled callback should check only the in-progress lock. Add a test that starts the scheduler with a short interval, waits for the callback, and asserts `discover_all_enabled()` is invoked exactly once. Also expose last run/next run health.

### P0.2 Source connectors are not provisioned or enableable from the product

**Evidence:**
- `backend/app/services/job_sources.py:225-250` registers `remote_ok` and `himalayas` in `SOURCE_REGISTRY`.
- `backend/migrations/versions/c3d4e5f6a7b8_add_phase4_job_discovery.py:169-208` seeds government/private/unsupported/company sources only; it does **not** seed `remote_ok` or `himalayas`.
- The same migration inserts all listed sources with `enabled=0`.
- `backend/app/services/job_discovery.py:370-381` only runs rows where `enabled IS TRUE AND is_active IS TRUE`.
- `backend/app/api/routes/jobs.py:396-456` exposes only GET source-list/health/detail endpoints. There are no POST/PATCH/PUT/DELETE source-management endpoints.
- `JobDiscoveryRun.source_id` has a foreign key to `job_sources.id` (`backend/app/db/models/jobs.py:192-202`). A manual `source_id=remote_ok` request cannot safely work until the source record exists.

**Impact:** The presence of connector classes does not mean users can discover jobs from those connectors. On a clean database, the two international sources are not registered in the DB; existing seeded sources are disabled; and the UI/API has no way to enable them.

**Fix:** Add idempotent source provisioning/seeding for Remote OK and Himalayas; keep unsupported sources disabled; add a protected operator/admin source-management endpoint/UI or a documented, validated environment configuration mechanism; add tests for a clean DB proving sources exist, are intentionally enabled, are executed, persist jobs and appear in source health. Do not enable arbitrary scraping sources by default.

### P0.3 Himalayas parser does not match current official API schema

**Evidence:** `backend/app/services/sources/international.py:187-286`:
- Requests `limit=max_results` (default 200), while the official endpoint permits a maximum of 20 per page.
- Does not use `nextCursor`; it reads only the first page.
- Reads `company.name`, but official payload uses `companyName`.
- Reads `employment_type`, but official field is `employmentType`.
- Reads `salary_min/max`, `salary_currency`, but official fields are `minSalary`, `maxSalary`, `currency`.
- Reads `published_at/created_at`, but official field is `pubDate`.
- Reads `url/apply_url` and `id`, but official fields include `applicationLink` and stable `guid`.
- Does not map `locationRestrictions`, `timezoneRestrictions`, or `expiryDate`.
- Its eligibility helper defaults unclear records to `eligible`.

**Impact:** Company/title/pay/date/application URL/expiry/eligibility can be dropped or misclassified. `source_job_id` can become empty or unstable if `id` and `url` are absent, damaging deduplication.

**Fix:** Map the documented schema exactly; use `guid`; preserve `applicationLink` unchanged for Apply; preserve and visibly link the Himalayas source listing; use cursor pagination with `limit <= 20`; map restrictions and expiry; do not infer worldwide eligibility from missing restrictions; remove closed/expired jobs; add fixture tests from the official response shape.

**Current source rules:** Himalayas allows displaying listings on an app/site operated by the integrator, but requires the unchanged `applicationLink` for Apply, visible source credit/link, and removal of expired jobs; its API cache refreshes daily, while its MCP server is the documented live-search option. [Himalayas API documentation](https://himalayas.app/api) and [Remote Jobs API reference](https://himalayas.app/docs/remote-jobs-api).

### P0.4 Eligibility is not truly three-state end-to-end

**Evidence:**
- `backend/app/services/job_normalizer.py:133-165`: `RawJob.is_pakistan_eligible` defaults to `True`; `eligibility` is a separate optional string.
- `job_normalizer.py:378-393`: `country` is derived from the boolean (`PK` if true) while the `eligibility` string is saved independently.
- `backend/app/db/models/jobs.py:125-130,154-162`: both boolean and string columns exist, with the boolean defaulting to true.
- `backend/app/api/routes/jobs.py:152-155`: if no `is_pakistan` filter is provided, backend adds `is_pakistan_eligible IS TRUE`; “Any” therefore does not mean any.
- `frontend/src/pages/JobsPage.tsx:34-42`: `eligible` sends true, while both `ineligible` and `unknown` send false. Unknown cannot be filtered separately.
- Both Remote OK and Himalayas helper methods return eligible by default when no restriction is detected (`international.py:139-169` and `288-318`).

**Impact:** The platform can falsely label a remote opportunity as Pakistan-eligible, and user filters do not match their labels.

**Fix:** Make `eligibility` a canonical enum (`eligible`, `ineligible`, `unknown`) and use it consistently in source parsing, persistence, search filters, matching, recommendations, and UI. Keep applicant eligibility separate from job's actual country/location. Backfill unknown conservatively. “Any” should omit the eligibility filter; “Unknown” must query only unknown. Add tests for explicit Pakistan, worldwide, USA-only, APAC/time zone, sponsorship, no restriction metadata, and contradictory requirements.

### P0.5 Alembic migration tries to add a column already created

**Evidence:**
- `backend/migrations/versions/c3d4e5f6a7b8_add_phase4_job_discovery.py:84` already creates `jobs.eligibility` as `Text`.
- `backend/migrations/versions/add_eligibility_columns_to_jobs.py:14-24` is later in the migration chain and attempts `op.add_column("jobs", sa.Column("eligibility", sa.String(32), nullable=True))` again, then adds `eligibility_reason`.
- `backend/migrations/env.py:86-109` reads `sqlalchemy.url` from Alembic config, while runtime engine uses `settings.database_url` in `backend/app/db/database.py:13-19`; `backend/alembic.ini` hardcodes a relative SQLite URL.

**Impact:** A clean Alembic upgrade is expected to fail on duplicate column `eligibility`; production Alembic can target the wrong database URL if not configured externally.

**Fix:** Reconcile migration history. The follow-up revision should only add genuinely missing fields, migrate column type safely if needed, and derive DB URL from the validated settings (or explicit Alembic env override). Add disposable fresh-SQLite and PostgreSQL migration tests. Do not run the uncorrected migration on the user's main database.

### P0.6 Gemini implementation is not live-ready and can mask errors as valid answers

**Evidence:**
- `backend/app/services/llm.py:54-82` defaults to `gemini-1.5-flash` and imports `google.generativeai`.
- `backend/app/core/config.py:67-72` repeats the same model default and legacy settings.
- The factory (`llm.py:210-220`) calls `GeminiProvider()` without passing the Pydantic setting's API key/model in the explicit `llm_provider == "gemini"` branch; in auto mode it passes the key but not the configured model/temperature/token limit.
- `llm.py:124-130` converts exceptions into response text such as `Generation failed: ...`; the caller in `career_brain.py:281-299` treats that string as an answer and can return `warning=None`.
- `llm.py:132-170` returns an empty default Pydantic schema on provider/parse failure, which can look like a successful empty result.
- Grep across backend confirms `get_llm_provider()` is called only by `CareerBrainAnswerGenerator`; resume parser/ATS/tailoring are documented deterministic logic and are not connected to Gemini.

**Impact:** The main default model is shut down, the Python SDK is deprecated, config values are not consistently passed, and provider failures can be mislabeled as AI responses. Resume analysis and cover letter claims in the delivery report overstate what code connects to Gemini.

**Current official facts:** Google lists `google-genai` as the recommended maintained SDK and says legacy `google-generativeai` libraries were deprecated on 30 Nov 2025. Google release notes say Gemini 1.5 models, including `gemini-1.5-flash`, shut down 29 Sep 2025. [Google Gemini API libraries](https://ai.google.dev/gemini-api/docs/libraries), [migration guide](https://ai.google.dev/gemini-api/docs/migrate), and [release notes](https://ai.google.dev/gemini-api/docs/changelog).

**Fix:** Migrate to `google-genai`; select a supported model from Google's current model list; pass API key/model/temperature/token limits through one configuration path; use typed provider failures; never return error strings as successful answers or `schema()` as successful generation; add tests for success, missing key, timeout, rate-limit, malformed output and provider error. Keep mock mode explicit and visibly marked as mock.

### P0.7 Career Brain's real answer endpoint is not connected to the screen

**Evidence:**
- Backend `POST /career-brain/answer` exists in `backend/app/api/routes/career_brain.py:143-189`.
- `frontend/src/api/careerBrain.ts:43-58` exposes `search`, `context`, `index` only; no `answer()` method or answer DTO.
- `frontend/src/pages/CareerBrainPage.tsx:18-64,73-102` calls search/context/index only and renders retrieved chunks/context, not generated AI answer.

**Impact:** Even if Gemini is correctly configured, the normal Career Brain screen cannot invoke the answer endpoint.

**Fix:** Add typed frontend answer client and chat UI, loading/error state, provider/model status, confidence/warnings, and cited source chunks. Add full frontend/API contract tests.

## 4. P1 — important functional and UX gaps

### P1.1 Workplace filter is wired incorrectly

`frontend/src/pages/JobsPage.tsx:180-188` represents “On-site only” as `remote=false`. Backend `jobs.py:156-161` only applies the remote filter when true and on-site filter when `onsite=true`. Therefore selecting on-site sends no effective workplace filter. Send `onsite=true` (or implement an explicit workplace_type filter) and support hybrid explicitly.

### P1.2 Inert or misleading top-bar controls

- `frontend/src/components/layout/TopBar.tsx:92-133`: global-search modal input has no controlled state, submit handler or navigation/search action.
- `TopBar.tsx:147-155`: notifications button has no click handler; unread red dot is hardcoded; no notification API/centre exists.
- `TopBar.tsx:44-60` has its own theme state; `AppLayout.tsx:27-36` mutates DOM during render and always adds `dark` class. Theme persistence/switching can conflict.

**Fix:** Implement global job/company search (or rename/remove the UI); build a real notifications model/API/centre or remove the fake indicator; centralize theme state and avoid DOM mutation during render.

### P1.3 Invalid sidebar routes and no 404 route

- `frontend/src/components/layout/Sidebar.tsx:53-60` links `/profile/education`, `/profile/experience`, `/profile/skills`, `/profile/certifications`.
- `frontend/src/App.tsx:31-49` defines only `/profile` and none of those nested routes.
- `App.tsx:51-53` has no catch-all not-found route.

Either build the four nested routes or remove them from navigation and route users to sections within `/profile`. Add protected/public 404 handling.

### P1.4 UI redesign not verified site-wide

Only `frontend/login-final.png` and `frontend/login-verified.png` are included. The final login screenshot has a dark marketing canvas and white login card; that is a reasonable composition, but it does not prove the dashboard/jobs/resume/Brain/CRM/settings screens were redesigned consistently. Source still contains legacy light utility styles in multiple pages. Run visual tests at desktop and mobile sizes and inspect each route. Do not infer every page is premium from the login screenshot.

### P1.5 Build emits generated JavaScript/declarations into `src`

- `frontend/package.json` build script is `tsc && vite build`.
- `frontend/tsconfig.json` has declarations/declaration maps/source maps enabled and no `noEmit` or separate `outDir`.
- The ZIP contains **144** `.js`, `.d.ts`, and `.map` artefacts under `frontend/src` (in addition to 100 `.ts/.tsx` source files).

**Fix:** Use `tsc --noEmit && vite build` or set `noEmit: true`; remove generated `.js/.d.ts/.map` from `src` and ensure future builds do not repopulate them.

### P1.6 CI uses Node 18 while Vite 8 requires newer Node

- `.github/workflows/tests.yml:63-68` configures Node 18.
- `frontend/package.json` has Vite `^8.2.2`.
- The lockfile shows Vite needs `^20.19.0 || >=22.12.0`; jsdom requires `^22.22.2 || ^24.15.0`; undici requires `>=22.19.0`.
- Official Vite docs specify Node 20.19+ or 22.12+. [Official Vite guide](https://vite.dev/guide/).

**Fix:** Update GitHub Actions to Node 24 (or an exactly supported Node 22.22+), update `engines`, and run clean `npm ci`, type-check, lint, tests and build. Do not leave CI on Node 18.

### P1.7 `package-lock.json` is ignored

Root `.gitignore` includes `package-lock.json`. The uploaded ZIP contains a lockfile, but the actual Git tracking state cannot be verified because `.git` was excluded. Make sure `frontend/package-lock.json` is tracked and committed; `npm ci` and reproducible CI depend on it.

### P1.8 Resume tailoring and ATS are deterministic, not Gemini-generated

`backend/app/services/resume/resume_parser.py` and `ats_analyzer.py` explicitly describe deterministic/rule-based logic; `resume_tailorer.py` reorders/suggests existing structured data and avoids inventing details. This can be a valid feature, but label it honestly. It is not proof of AI resume analysis or an LLM-generated cover letter. If LLM tailoring is desired, add a distinct opt-in workflow with evidence-grounded constraints and human review.

### P1.9 Settings/source admin is incomplete

`SettingsPage.tsx` currently edits basic user/job preferences rather than being a genuine integration, AI, notification and security settings centre. Source API routes are read-only; there is no way for an operator to enable/disable or configure source records through the UI. Add an admin-only source health/configuration panel and safe settings forms, or remove controls that cannot do anything.

## 5. Other limitations and product gaps

| Area | Actual status in this snapshot | What is required |
|---|---|---|
| Career profile | CRUD foundation present | Verify end-to-end persistence and onboarding completeness |
| Job discovery | Engine, source registry and scheduler code present | Fix source registration/activation, scheduler, API mapping and freshness lifecycle |
| Job matching | Deterministic explainable scoring | Fix eligibility and calibrate score; label as estimate, not hiring probability |
| Career Brain | Hash-based retrieval + backend answer endpoint | Connect UI; use supported LLM; consider real embedding model/pgvector only after quality/cost tests |
| Resume parsing | Deterministic file parsing | Test malicious/malformed files and safe binary persistence |
| ATS analysis | Rule-based | Explain components; do not call LLM-based unless wired |
| Resume tailoring | Deterministic transformation | Add optional grounded LLM tailoring only if needed; preserve source facts |
| Cover letter | No proven Gemini-backed workflow from code search | Implement a separate generation workflow if claimed |
| CRM/application tracking | Broad CRUD/status/timeline | Verify user journey and make status updates/notes actually persist |
| Notifications | No notification entity/API/centre found | Build notification persistence, read state, preferences and delivery mechanism |
| Interview Coach | No complete working coach flow | Questions, practice session, answer feedback, rubric, history |
| GitHub portfolio | Not implemented | OAuth read-only scope, repo selection, explicit consent and evidence-based project analysis |
| Gmail intelligence | Not implemented | Google OAuth consent, inbox scope, classification, thread linking, draft-only replies by default |
| Browser apply agent | Not implemented | Site-specific permitted automation, approval before submit, audit logs and safe retries |
| Multi-tenant SaaS | Not implemented | Workspace/tenant ownership model, roles, isolation and migration plan |
| Billing | Not implemented | Payment gateway, subscription/plan enforcement, cancellation/refunds and webhook verification |
| Production operations | Not ready | Hosted PostgreSQL, migrations, backups/restore, monitoring, tracing, alerts, deployment, TLS/secrets |

## 6. “Real-time” — what CareerOS can realistically promise

“Real-time” has two different meanings and should not be conflated:

1. **Live application behaviour:** UI updates immediately after the user's own action; discovery run progress is streamed; application status/notification updates are pushed by SSE/WebSocket or refreshed promptly.
2. **Upstream job freshness:** external providers decide when their feeds refresh. CareerOS cannot make a provider publish a job instantly if its API is cached or updated daily.

Himalayas documents a daily-refreshed REST API and a separate MCP server for live search. Its documentation says there is no benefit to polling its cached API more frequently than daily. [Himalayas API documentation](https://himalayas.app/api) and [Remote Jobs API reference](https://himalayas.app/docs/remote-jobs-api). Remote OK documents a public JSON/RSS feed, attribution and link-back requirements; its API does not promise a strict real-time update SLA in the official FAQ. [Remote OK FAQ](https://remoteok.com/faq) and [Remote OK Terms](https://www.remoteok.com/legal).

**Recommended product behaviour:** show `Last checked`, `Last successful sync`, `Source freshness`, `Provider status`, and `Job closing/expired` state on every source/job. Use provider-compliant schedules, not aggressive polling. Use SSE/WebSockets for *CareerOS's own* sync progress and notification events. Never badge the entire aggregated marketplace “real-time” without a measured freshness definition.

## 7. Prioritised implementation plan

### Wave A — P0 reliability (must be done before presenting as working)

1. Fix migration duplication and make Alembic use the configured database URL safely.
2. Fix scheduler state lock and test a callback actually fires.
3. Seed Remote OK/Himalayas into `job_sources`; add a safe source enable/configure workflow; verify FK and database persistence.
4. Correct Himalayas contract/pagination/expiry/attribution/application link.
5. Make eligibility one canonical three-state field through parser → DB → API → filters → matching → UI.
6. Migrate Gemini SDK/model, correct factory config and provider error handling.
7. Wire `/career-brain/answer` to the frontend.
8. Fix on-site/hybrid filters.

### Wave B — P1 product usability and quality

9. Complete or remove inert global search/notifications/theme controls.
10. Repair invalid sidebar routes and add 404.
11. Stop TypeScript emitting generated outputs into source; clean generated files.
12. Update CI Node version; retain and track package lock.
13. Add a source-health/admin page with enable/disable, last sync, next sync, recent errors.
14. Verify resume/apply CRM end-to-end with real database persistence.
15. Add visual QA screenshots for every main route at desktop/mobile sizes.
16. Add security negative tests for cross-user IDs, refresh/logout replay, file upload validation and role/permission enforcement.

### Wave C — advanced career platform features

17. **Career Intelligence:** actual semantic embeddings, grounded RAG answer with citations, dedicated skill-gap endpoint and progress tracking.
18. **Interview Coach:** role/job-specific HR + technical questions, answer rubric, feedback, STAR coaching, saved practice sessions.
19. **Portfolio/GitHub Analyzer:** OAuth read-only integration, repo selection, README/commit/language analysis, evidence-based skills/projects; never infer employment claims from GitHub alone.
20. **Career Email Intelligence:** opt-in Gmail OAuth, classify application confirmations/interview/rejection/offers, link threads to applications, create draft responses (do not auto-send by default).
21. **Notification Centre:** persistent notifications, unread count, preferences, in-app events, optional email delivery.
22. **Career Agent:** approved multi-step planning/action workflow; preview, user approval, execution result, audit trail and retry-safe operations.
23. **Job source manager:** provider status, quotas, allowed refresh schedule, attribution policy, last successful sync, failure history and expiry checks.
24. **Near-real-time app updates:** SSE/WebSockets for sync progress, notification events and application changes; provider polling remains policy-bound.

### Wave D — real SaaS / production (not just code changes)

25. Multi-tenant workspace and role-based authorization.
26. Billing, subscription plans and usage metering.
27. Production PostgreSQL, migration/rollback policy and tested backup restoration.
28. Durable queues/workers (Redis/Celery/RQ or equivalent), idempotency, retry and dead-letter handling.
29. Observability: metrics, logs, traces, error reporting, job-source dashboards, alerts and uptime checks.
30. Privacy controls: consent, data export, deletion, retention, sensitive-file storage, encryption and access auditing.
31. Production hosting, domain, TLS, secrets manager, CI/CD and incident runbook.
32. Authorized partner/API agreements for platforms requiring permission; code cannot grant LinkedIn/Indeed/Gmail/GitHub OAuth approval or commercial content rights.

## 8. Acceptance criteria for saying “real-time, working CareerOS”

- Clean DB migrations pass on disposable SQLite and PostgreSQL test databases.
- Application boots with health/readiness both successful.
- Scheduler callback is observed executing; manual and scheduled discovery both create/update records.
- Remote OK/Himalayas are present, enabled intentionally, and their actual returned job records are persisted.
- Every listing retains source attribution, canonical original link, apply URL and timestamps; expired jobs are removed.
- Unknown eligibility remains unknown at every layer.
- Career Brain screen uses `/answer` and clearly labels real Gemini vs fallback/mock.
- Gemini uses a supported model and produces a real non-sensitive smoke-test response when a key is configured.
- Resume ATS/tailoring labels match their actual deterministic/AI implementation.
- All visible buttons work or are explicitly disabled/unavailable.
- Desktop and mobile visual QA is performed on each major route.
- Backend tests, frontend type-check/lint/tests/build and Playwright user journey pass from a clean installation.
- CI runs on supported Node and an isolated PostgreSQL service.
- No secrets, local DBs, compiled outputs or personal resumes are part of the submission ZIP/repository.

## 9. Final recommendation

Do **not** send Kilo a broad “build every future feature” prompt yet. First fix Wave A defects because they block core promises. Then implement Wave B. For Sunday FYP, a reliable discover → eligibility → match → resume → track workflow with accurate Gemini status is stronger than a half-built Gmail agent, GitHub analyser, browser automation and subscription system.

The future modules should be designed as a roadmap and then implemented in sequence. Gmail, GitHub OAuth, LinkedIn/Indeed partner access, production database/hosting, payments, and licensed job-data reuse require external credentials, user consent, provider approval or operational setup; they cannot truthfully be completed just by generating code inside Kilo.
