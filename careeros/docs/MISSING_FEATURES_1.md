# CareerOS Missing Features and Verification Gaps

This report separates source code presence from fresh runtime evidence.

## Not established by fresh evidence

### Browser automation
- Playwright/browser journeys for registration, login, logout, profile CRUD, uploads, CRM, navigation, responsive behavior, and accessibility were not executed.

### Live integrations
- Live Gemini generation and Career Brain answers require credentials and API usage and were not performed.
- Live Remote OK, Himalayas, government, private-board, company, and international source retrieval was not performed without internet/API approval.
- Gmail, GitHub, LinkedIn, Indeed, browser-assisted applications, and media integrations are not presented as tested unless their live implementation and execution are verified separately.

### End-to-end workflows
- Resume PDF/DOCX upload through the real UI.
- Complete job discovery-to-save journey with real or controlled source records.
- Career Brain ingestion through UI, retrieval, answer, and source citations.
- Scheduler restart persistence through an actual service restart.
- Notification and global-search UI journeys with real backend data.

### Production readiness
- Supabase/PostgreSQL production connectivity was not verified.
- Production secrets, HTTPS, backup/restore, monitoring, observability, disaster recovery, scaling, and deployment health checks remain unverified.
- Row-level security and database constraints require targeted production-equivalent verification.

## Known documented roadmap items
README statuses pending for browser-agent application automation, Gmail, GitHub/LinkedIn integrations, portfolio/content generation, video studio, skill-gap analysis, full analytics, and production hardening. These must remain pending until implementation and live tests are available.
