# Stage 0 — Forensic Audit: CareerOS Phase 1–7 Frontend

## A. Route Inventory

| Route | Protected? | Page | Main Features | Data Source | Key Actions | Status |
|---|---|---|---|---|---|---|
| `/jobs` | No | `JobsPage` | Job list, search/filter, save/unsave, discovery trigger | `JobsApi.list()`, `JobsApi.saved()`, `JobsApi.sources()`, `JobsApi.triggerDiscovery()` | Search, filter, save, unsave, run discovery | Implemented |
| `/resumes` | No | `ResumesPage` | Resume list, create, delete, navigate to editor | `ResumesApi.list()`, `ResumesApi.create()`, `ResumesApi.delete()` | Create resume, delete resume, open editor | Implemented |
| `/resumes/:id` | No | `ResumeEditorPage` | Resume details, sections, ATS analysis, tailoring, versions | `ResumesApi.get()`, `ResumesApi.listSections()`, `ResumesApi.update()`, `ResumesApi.analyzeATS()`, `ResumesApi.tailor()`, `ResumesApi.listVersions()` | Edit details, add/remove sections, run ATS, tailor, view versions | Implemented |
| `/dashboard` | No | `CRMDashboardPage` | CRM stats, pipeline overview, analytics funnel | `CrmApi.getDashboardStats()`, `CrmApi.getPipeline()`, `CrmApi.getAnalytics()` | View stats, pipeline, analytics | Implemented |
| `/applications` | No | `ApplicationsPage` | Application list, search/filter, create new | `CrmApi.listApplications()`, `CrmApi.createApplication()` | Search, filter, create application | Implemented |
| `/applications/:id` | No | `ApplicationDetailPage` | Application detail, timeline, offer, recommendations, status transition | `CrmApi.getApplication()`, `CrmApi.getApplicationTimeline()`, `CrmApi.getApplicationOffer()`, `CrmApi.listRecommendations()`, `CrmApi.transitionApplication()` | View detail, transition status | Implemented |
| `/pipeline` | No | `PipelinePage` | Kanban-style pipeline columns, inline status transitions | `CrmApi.getPipeline()`, `CrmApi.transitionApplication()` | Move applications between stages | Implemented |
| `/profile` | Yes | `ProfilePage` | Career profile overview and editing | Profile API client | View and update profile | Implemented |
| `/career-brain` | Yes | `CareerBrainPage` | Career intelligence search/context | Career Brain API client | Search and inspect career context | Implemented |
| `/matches` | Yes | `MatchesPage` | Job match list | Matching API client | Browse matches | Implemented |
| `/matches/:jobId` | Yes | `MatchDetailPage` | Match detail and scoring context | Matching API client | Inspect a job match | Implemented |
| `/job-discovery` | Yes | `JobDiscoveryPage` | Discovery controls and source status | Jobs API client | Run discovery and inspect sources | Implemented |
| `/career-data` | Yes | `CareerDataPage` | Career data management | Career API client | Manage profile data | Implemented |
| `/crm` | Yes | `CRMWorkspacePage` | CRM workspace | CRM API client | Work with CRM records | Implemented |
| `/settings` | Yes | `SettingsPage` | User settings and account actions | Auth API client | Review account settings and log out | Implemented |
| `/login` | No | `LoginPage` | Login form | Auth API client | Authenticate | Implemented |
| `/register` | No | `RegisterPage` | Registration form | Auth API client | Create an account | Implemented |

**Route observations:**
- `/login` and `/register` are public routes; the application routes are wrapped by `RequireAuth`
- `AuthProvider` restores the token from `localStorage`, validates it with `/auth/me`, and clears invalid tokens
- `AppLayout` provides the shared sidebar, top bar, mobile navigation, and logout action
- No lazy loading — all pages are eagerly imported in `App.tsx`
- No 404/Not Found route
- Authenticated users are not redirected away from `/login` or `/register`
- Navigation is defined in the shared layout rather than directly in `App.tsx`

## B. Feature and Page Inventory

### Implemented and Working
- **Jobs listing** (`/jobs`) — search, filter by keyword/city/remote/internship, save/unsave, source list, discovery trigger
- **Resume list** (`/resumes`) — create, delete, navigate to editor
- **Resume editor** (`/resumes/:id`) — edit name/status/JSON, manage sections, ATS analysis, tailoring, version history
- **CRM Dashboard** (`/dashboard`) — stats cards, pipeline stages, analytics funnel
- **Applications list** (`/applications`) — search, filter by status/priority, create application
- **Application detail** (`/applications/:id`) — full detail view, timeline, offer, recommendations, status transition form
- **Pipeline** (`/pipeline`) — kanban columns with inline status transitions

### Implemented but Incomplete / Frontend-Only
- **Authentication** — backend has full auth (register/login/me), but frontend has NO login page, NO logout, NO token management UI. Token is read from localStorage but never set by frontend code.
- **Career Profile** — frontend pages exist, but the depth of CRUD coverage for skills, education, experience, and certifications requires further verification
- **Career Brain** — frontend page exists for the backend index/search/context endpoints
- **Job Matching** — frontend pages exist for match listing and detail; saved-match workflow coverage requires further verification
- **Saved Jobs detail** — backend has saved jobs list, but NO dedicated frontend page
- **Job Preferences** — backend has preferences endpoints, but NO frontend page
- **Sources health** — backend has `/sources/health`, but NO frontend page
- **Company CRUD** — backend has full company CRUD, but NO dedicated frontend page (only referenced in application detail)
- **Contact CRUD** — backend has full contact CRUD, but NO dedicated frontend page
- **Interview CRUD** — backend has full interview CRUD, but NO dedicated frontend page
- **Follow-up CRUD** — backend has full follow-up CRUD, but NO dedicated frontend page
- **Offer CRUD** — backend has full offer CRUD, but only read in application detail
- **Rejection CRUD** — backend has full rejection CRUD, but only read in application detail
- **Recommendation CRUD** — backend has full recommendation CRUD, but only read in application detail
- **Application Documents** — backend has document CRUD, but NO frontend page
- **Resume import from file** — backend has `/resumes/{id}/import/file`, but NO frontend UI
- **Resume build from profile** — backend has `/resumes/build-from-profile`, but NO frontend UI
- **Resume version creation** — backend has versioning, but NO frontend UI to create versions
- **Settings** — frontend settings page exists; backend account-preference coverage requires further verification

### Documented but Not Implemented
- Dedicated Saved Jobs page
- Company, Contact, Interview, Follow-up, Document, Offer, Rejection, and Recommendation management pages
- Resume import-from-file UI
- Resume build-from-profile UI
- Resume version creation UI

### Future Phase and Out of Scope
- Phase 8+: Browser Agent, Career Email, Interview Agent, GitHub/LinkedIn, Portfolio, Video Studio, Skill Gap, Analytics expansion

## C. API and Workflow Map

### Authentication
- **USER ACTION**: Submit login or registration form; log out from the shared app shell
- **ROUTE/PAGE**: `/login`, `/register`, authenticated routes
- **COMPONENT**: `LoginPage`, `RegisterPage`, `AuthContext`, `RequireAuth`, `AppLayout`
- **CLIENT VALIDATION**: Required form fields and page-level error messages
- **STATE/MUTATION**: `AuthContext` owns the current user and loading state
- **HTTP**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- **REQUEST**: JSON credentials/profile; bearer token on `/me`
- **RESPONSE**: `UserResponse` and `TokenResponse`
- **CACHE/INVALIDATION**: Token stored in `localStorage`; invalid tokens are removed during initialization
- **SUCCESS UI**: Navigate to the requested page after login/register
- **ERROR UI**: Inline form error
- **Notes**: Authentication and route protection are implemented. The remaining gap is authenticated-route handling for unknown paths.

### Jobs Discovery
- **USER ACTION**: Navigate to `/jobs`
- **ROUTE/PAGE**: `/jobs` → `JobsPage`
- **COMPONENT**: `JobsPage` — search form, job cards, save/unsave buttons, discovery trigger
- **CLIENT VALIDATION**: None (raw inputs)
- **STATE/MUTATION**: `useState` + manual `fetch`
- **HTTP**: `GET /api/v1/jobs?keyword=&city=&remote=&internship=&page=&page_size=`
- **REQUEST**: Query params
- **RESPONSE**: `JobListResponse { items: JobSummary[], total, page, page_size }`
- **CACHE/INVALIDATION**: None (manual refetch)
- **SUCCESS UI**: Job cards with title, company, location, salary, save button
- **ERROR UI**: Red error banner
- **Notes**: Mixed fetching pattern — `JobsPage` uses raw `useEffect`/`useState` while CRM pages use React Query

### Resume Creation
- **USER ACTION**: Click "Create" in `ResumesPage`
- **ROUTE/PAGE**: `/resumes` → `ResumesPage`
- **COMPONENT**: Inline form in `ResumesPage`
- **CLIENT VALIDATION**: `if (!name.trim()) return`
- **STATE/MUTATION**: `useState` + manual `fetch`
- **HTTP**: `POST /api/v1/resumes` with `{ name }`
- **REQUEST**: JSON body
- **RESPONSE**: `ResumeDetail`
- **CACHE/INVALIDATION**: None (navigates away)
- **SUCCESS UI**: Navigate to `/resumes/{id}`
- **ERROR UI**: Red error banner

### ATS Analysis
- **USER ACTION**: Enter job ID, click "Analyze" in `ResumeEditorPage`
- **ROUTE/PAGE**: `/resumes/:id` → `ResumeEditorPage` (ATS tab)
- **COMPONENT**: ATS tab with job ID input and analyze button
- **CLIENT VALIDATION**: `if (!id || !atsJobId) return`
- **STATE/MUTATION**: `useState` + manual `fetch`
- **HTTP**: `POST /api/v1/resumes/ats/analyze` with `{ resume_id, job_id }`
- **REQUEST**: JSON body
- **RESPONSE**: `ATSAnalysisResponse`
- **CACHE/INVALIDATION**: None
- **SUCCESS UI**: Score, breakdown, keywords, skills, recommendations
- **ERROR UI**: Red error banner

### Application Creation
- **USER ACTION**: Click "New Application", fill form, submit
- **ROUTE/PAGE**: `/applications` → `ApplicationsPage`
- **COMPONENT**: Expandable form with name and company fields
- **CLIENT VALIDATION**: HTML5 `required` on name field
- **STATE/MUTATION**: React Query `useMutation`
- **HTTP**: `POST /api/v1/applications` with `{ name, notes, priority, source }`
- **REQUEST**: JSON body
- **RESPONSE**: `ApplicationResponse`
- **CACHE/INVALIDATION**: `queryClient.invalidateQueries({ queryKey: ['crm'] })`
- **SUCCESS UI**: Form collapses, list refreshes
- **ERROR UI**: Inline error text

### Application Status Transition
- **USER ACTION**: Select new status, click "Transition" in `ApplicationDetailPage` or `PipelinePage`
- **ROUTE/PAGE**: `/applications/:id` or `/pipeline`
- **COMPONENT**: Status select + reason input + submit button
- **CLIENT VALIDATION**: `if (!transitionTo) return`
- **STATE/MUTATION**: React Query `useMutation`
- **HTTP**: `POST /api/v1/applications/{id}/transitions` with `{ to_status, reason }`
- **REQUEST**: JSON body
- **RESPONSE**: `ApplicationTransitionResponse`
- **CACHE/INVALIDATION**: `queryClient.invalidateQueries({ queryKey: ['crm'] })`
- **SUCCESS UI**: Success message, form resets
- **ERROR UI**: Red error text

### Pipeline Move
- **USER ACTION**: Select target status from dropdown in pipeline card
- **ROUTE/PAGE**: `/pipeline` → `PipelinePage`
- **COMPONENT**: Inline select per application card
- **CLIENT VALIDATION**: `if (target && target !== app.status)`
- **STATE/MUTATION**: React Query `useMutation`
- **HTTP**: `POST /api/v1/applications/{id}/transitions` with `{ to_status }`
- **REQUEST**: JSON body
- **RESPONSE**: `ApplicationTransitionResponse`
- **CACHE/INVALIDATION**: `queryClient.invalidateQueries({ queryKey: ['crm'] })`
- **SUCCESS UI**: Card refreshes in new column
- **ERROR UI**: Global error banner

## D. CRUD and State-Machine Matrix

### Application CRUD
| Operation | Frontend | Backend Endpoint | Notes |
|---|---|---|---|
| Create | `CrmApi.createApplication()` | `POST /applications` | Creates with name, notes as notes, priority, source |
| Read (list) | `CrmApi.listApplications()` | `GET /applications` | Supports filtering by status, priority, search |
| Read (detail) | `CrmApi.getApplication()` | `GET /applications/{id}` | Returns full object with relationships |
| Update | `CrmApi.updateApplication()` | `PATCH /applications/{id}` | Used for PATCH updates (NOT for status) |
| Delete | `CrmApi.deleteApplication()` | `DELETE /applications/{id}` | Cascade deletes related entities |
| Transition | `CrmApi.transitionApplication()` | `POST /applications/{id}/transitions` | Dedicated state-machine endpoint |

### Application State Machine
- **Valid states**: `saved`, `ready_to_apply`, `applied`, `application_viewed`, `screening`, `interview`, `technical_interview`, `final_interview`, `offer`, `accepted`, `rejected`, `withdrawn`, `expired`, `on_hold`
- **Transition endpoint**: `POST /applications/{id}/transitions` with `{ to_status, reason?, metadata? }`
- **Direct PATCH of status**: BLOCKED by backend — returns 400 error
- **Allowed transitions**: Defined in `ApplicationStateMachine._ALLOWED_TRANSITIONS`
- **Terminal states**: `accepted`, `rejected`, `withdrawn`, `expired`
- **Reason required from**: `rejected`, `withdrawn`, `expired`, `accepted`, `offer`
- **Frontend compliance**: `ApplicationDetailPage` and `PipelinePage` use `transitionApplication()` — correct. `ApplicationUpdate` type includes `status` field but it's not used in the UI for transitions.

### Resume CRUD
| Operation | Frontend | Backend Endpoint | Notes |
|---|---|---|---|
| Create | `ResumesApi.create()` | `POST /resumes` | Creates base resume |
| Read (list) | `ResumesApi.list()` | `GET /resumes` | Supports pagination, status/type filters |
| Read (detail) | `ResumesApi.get()` | `GET /resumes/{id}` | Returns full detail with sections, versions |
| Update | `ResumesApi.update()` | `PUT /resumes/{id}` | Updates name, status, structured_data |
| Delete | `ResumesApi.delete()` | `DELETE /resumes/{id}` | Cascade deletes sections |
| Section CRUD | `ResumesApi.createSection()`, `updateSection()`, `deleteSection()` | `POST/PUT/DELETE /resumes/sections/{id}` | Section management |
| Versions | `ResumesApi.listVersions()` | `GET /resumes/{id}/versions` | Read-only version list |
| ATS | `ResumesApi.analyzeATS()` | `POST /resumes/ats/analyze` | ATS analysis |
| Tailor | `ResumesApi.tailor()` | `POST /resumes/tailor` | Creates tailored version |

### Company CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| Create | `POST /companies` | |
| Read (list) | `GET /companies` | |
| Read (detail) | `GET /companies/{id}` | |
| Update | `PATCH /companies/{id}` | |
| Delete | `DELETE /companies/{id}` | |
| Merge | `POST /companies/{id}/merge` | |

### Contact CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| Create | `POST /contacts` | |
| Read (list) | `GET /contacts` | |
| Read (detail) | `GET /contacts/{id}` | |
| Update | `PATCH /contacts/{id}` | |
| Delete | `DELETE /contacts/{id}` | |

### Interview CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| Create | `POST /interviews` | |
| Read (list) | `GET /interviews` | |
| Read (detail) | `GET /interviews/{id}` | |
| Update | `PATCH /interviews/{id}` | |
| Delete | `DELETE /interviews/{id}` | |

### Follow-up CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| Create | `POST /follow-ups` | |
| Read (list) | `GET /follow-ups` | |
| Read (detail) | `GET /follow-ups/{id}` | |
| Update | `PATCH /follow-ups/{id}` | |
| Delete | `DELETE /follow-ups/{id}` | |
| Complete | `POST /follow-ups/{id}/complete` | |

### Offer CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| Upsert | `PUT /applications/{id}/offer` | |
| Read | `GET /applications/{id}/offer` | |

### Rejection CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| Create | `POST /rejections` | (via application endpoint) |
| Read | `GET /applications/{id}/rejection` | |
| Delete | `DELETE /rejections/{id}` | |

### Recommendation CRUD (backend only, no frontend)
| Operation | Endpoint | Notes |
|---|---|---|
| List | `GET /recommendations` | |
| Regenerate | `POST /applications/{id}/recommendations` | |

## E. UI State Inventory

### JobsPage
- Initial loading: `Loading…` text
- Background refresh: None (manual refetch only)
- Empty: Gray card with "No jobs found" message
- Partial data: N/A
- Error: Red banner with error message
- Retry: "Search" button
- Offline/network: Same as error
- Validation error: None
- Submitting: N/A
- Success: N/A
- Disabled: N/A
- Not found: N/A

### ResumesPage
- Initial loading: `Loading…` text
- Background refresh: None
- Empty: Gray card with "No resumes yet" message
- Partial data: N/A
- Error: Red banner
- Retry: Page reload
- Validation: Manual `if (!name.trim()) return`
- Submitting: N/A
- Success: Navigate to editor
- Disabled: N/A

### ResumeEditorPage
- Initial loading: `Loading resume…` text
- Background refresh: None
- Empty: Sections show "No sections yet"
- Partial data: N/A
- Error: Red banner or "Resume not found"
- Retry: Page reload
- Validation: `JSON.parse(rawJson)` can throw
- Submitting: `Saving…` / `Analyzing…` / `Tailoring…` button text
- Success: `alert("Saved")` — uses browser alert
- Disabled: Buttons disabled during mutations

### CRMDashboardPage
- Initial loading: `Loading CRM dashboard…` text
- Background refresh: None
- Empty: N/A (stats always have values, possibly zero)
- Partial data: N/A
- Error: Red error text
- Retry: Page reload
- Submitting: N/A
- Success: N/A

### ApplicationsPage
- Initial loading: `Loading…` text
- Background refresh: None
- Empty: Gray card with "No applications yet" message
- Partial data: N/A
- Error: Red banner or inline error
- Retry: "Refresh" button
- Validation: HTML5 `required` on name
- Submitting: N/A (mutation pending not shown on button)
- Success: Form collapses
- Disabled: N/A

### ApplicationDetailPage
- Initial loading: `Loading application…` text
- Background refresh: None
- Empty/Not found: "Application not found" gray text
- Partial data: N/A
- Error: Red error text
- Retry: Page reload
- Validation: `if (!transitionTo) return`
- Submitting: `Transitioning…` button text
- Success: Green success message
- Disabled: Button disabled during mutation

### PipelinePage
- Initial loading: `Loading pipeline…` text
- Background refresh: None
- Empty: "No applications" per column
- Partial data: N/A
- Error: Red banner
- Retry: Page reload
- Submitting: Select disabled during transition
- Success: Card moves to new column
- Disabled: Select disabled per card during transition

## F. Design-System Assessment

### Current Typography
- No typography scale defined
- Headings: `text-2xl font-bold` (pages), `text-xl font-bold` (subsections), `text-lg font-semibold` (cards)
- Body: Default Tailwind text
- Muted: `text-gray-500`, `text-gray-400`, `text-xs text-gray-400`
- No font family customization — uses system font stack via Tailwind default

### Current Colors
- Tailwind config extends only 5 colors:
  - `primary: '#0066cc'` (blue)
  - `secondary: '#666666'` (gray)
  - `success: '#00cc66'` (green)
  - `warning: '#ffcc00'` (yellow)
  - `error: '#cc0000'` (red)
- Status badges: `bg-blue-100 text-blue-800` (single blue for all statuses)
- No semantic color tokens for backgrounds, borders, focus rings, info, neutral
- No dark mode

### Spacing
- Page padding: `p-6` (24px)
- Card padding: `p-4` (16px)
- Section gaps: `mb-6`, `mb-4`, `gap-3`, `gap-4`
- No spacing scale or density variants

### Shape/Depth
- Border radius: `rounded` (default 4px) everywhere
- Shadows: `shadow-sm` on cards
- Borders: Default `border` (1px solid #e5e7eb)
- No radius variants (sm/md/lg)
- No shadow variants

### Form Controls
- Inputs: `rounded border p-2` — browser-default appearance
- Selects: Same as inputs
- Buttons: `rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700` (primary), `rounded border px-4 py-2 hover:bg-gray-100` (secondary)
- No custom checkbox/radio/switch styles
- No field wrapper component
- No inline error styling on inputs

### Tables/Lists
- No table component used
- Lists use `<ul className="space-y-3">` with `<li>` cards
- No responsive table patterns

### Icons
- No icon library installed or used
- Text-only UI

### Inconsistencies
- `JobsPage` uses raw `useEffect`/`useState`; CRM pages use React Query
- Some pages have `mx-auto max-w-6xl p-6` wrapper (`JobsPage`, `ResumesPage`, `ResumeEditorPage`), others don't (`CRMDashboardPage`, `ApplicationsPage`, `PipelinePage`, `ApplicationDetailPage`)
- Header patterns vary: some have flex justify-between, some don't
- Empty state styling is inconsistent
- Error styling is mostly consistent but varies in placement
- Loading text varies: "Loading…", "Loading resume…", "Loading application…", "Loading pipeline…", "Loading CRM dashboard…"
- Button text varies: "Save"/"Saved ✓", "Create"/"Cancel", "Search"/"Reset", "Analyze"/"Analyzing…"
- `ApplicationDetailPage` uses `h2` for section titles while others use `h3`

## G. Risk Register

### High-Risk Areas

| Risk | Severity | Description | Mitigation Status |
|---|---|---|---|
| **Authentication flow** | P1 | Login, registration, token restoration, logout, and `/auth/me` validation are implemented, but authenticated users can still manually visit the public auth pages. | PARTIALLY MITIGATED |
| **Unknown routes** | P1 | No 404/Not Found route exists, so an unknown URL renders an empty route tree. | NOT MITIGATED |
| **Mixed data-fetching patterns** | P1 | `JobsPage`, `ResumesPage`, `ResumeEditorPage` use raw `useEffect`/`useState`. CRM pages use React Query. Inconsistent caching, error handling, loading states. | Needs consolidation |
| **No component architecture** | P1 | All UI is inline in page components. No reusable Button, Input, Card, Badge, etc. High duplication, inconsistent styling. | Needs design system |
| **No form validation** | P1 | No Zod, no React Hook Form. Manual validation only. No inline error association. | Needs validation layer |
| **Application state machine** | P1 | Backend enforces transitions via dedicated endpoint. Frontend correctly uses `transitionApplication()`. But `ApplicationUpdate` type exposes `status` field which could be misused. | Backend protects; frontend needs cleanup |
| **No error normalization** | P2 | API errors throw raw `Error` with response text. No normalized error format, no user-friendly messages. | Needs improvement |
| **No optimistic updates** | P2 | All mutations wait for server response. No optimistic UI. | Low priority |
| **No offline support** | P2 | No service worker, no offline queue. | Low priority |
| **Compiled JS in repo** | P2 | `.js` and `.js.map` files alongside `.tsx` sources indicate build artifacts committed. | Cleanup needed |
| **Zustand installed but unused** | P2 | `zustand` in dependencies but never imported. Dead dependency. | Remove or use |
| **Zod installed but unused** | P2 | `zod` in dependencies but never imported. Dead dependency. | Remove or use |
| **@radix-ui installed but unused** | P2 | `@radix-ui/react-dialog` and `@radix-ui/react-slot` installed but never imported. | Remove or use |
| **ESLint config mismatch** | P2 | ESLint v10 expects `eslint.config.*` but project has `.eslintrc.json`. Lint command fails. | Fix config |
| **No responsive mobile nav** | P2 | Top nav has no mobile drawer. On mobile, links wrap or overflow. | Needs mobile nav |
| **No skip link / landmarks** | P2 | No skip link, no semantic landmarks beyond header. | Accessibility gap |
| **No focus management** | P2 | Dialogs, modals, and navigation transitions have no focus management. | Accessibility gap |
| **File upload not implemented** | P2 | Backend supports PDF/DOCX/TXT import, but no frontend UI exists. | Missing UI |
| **Resume version creation not implemented** | P2 | Backend supports versioning, but frontend has no UI to create versions. | Missing UI |
| **Career Profile not implemented** | P3 | Backend has full profile CRUD, but no frontend pages. | Missing UI |
| **Career Brain not implemented** | P3 | Backend has search/context endpoints, but no frontend page. | Missing UI |
| **Job Matching not implemented** | P3 | Backend has match endpoints, but no frontend page. | Missing UI |

## H. Baseline Evidence

### Frontend Checks
| Check | Command | Result |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | PASS — no errors |
| Build | `npx vite build` | PASS — built in 3.21s |
| Lint | `npx eslint . --ext ts,tsx --max-warnings 0` | FAIL — ESLint config mismatch (v10 expects `eslint.config.*`, project has `.eslintrc.json`) |
| Tests | `npx vitest run` | N/A — no project-specific test files exist (only `src/__tests__/setup.ts`) |

### Backend Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python -m pytest tests/ -q` | PASS — 471 tests passed, 0 failed |
| Baseline count | `pytest tests/ --collect-only` | 471 test functions across 24 test files |

### Known Baseline Issues
1. No 404/Not Found route exists
2. Authenticated users are not redirected away from the public auth pages
3. Frontend data-fetching patterns remain mixed between raw effects and React Query
4. No frontend test coverage exists beyond the route smoke test
5. No focus trap is implemented for the mobile navigation drawer

---

## Stage 0 Exit Gate

**Status: PASS with follow-up work**

The route inventory, feature inventory, API map, state-machine model, design assessment, and baseline results are complete enough to explain how the application works. However, several critical blockers must be addressed before redesign:

1. **Missing fallback routing** — Unknown paths do not render a Not Found page.
2. **Missing Phase 1–7 frontend for major features** — Career Profile, Career Brain, Job Matching, Saved Jobs, Companies, Contacts, Interviews, Follow-ups, and Documents remain incomplete despite having backend APIs.

These are not redesign issues — they are missing features that must be built, not styled. Authentication and route protection are now in place; the remaining implementation work is product coverage and fallback routing.

**Decision: PROCEED with the current redesign and prioritize a Not Found route, auth-page redirects, and the remaining feature pages.**
