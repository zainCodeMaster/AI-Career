# CareerOS Bugs and Fixes (Fresh Audit)

## Fixed issues

### P2 — Gemini dependency mismatch
- Files: `backend/pyproject.toml`, `backend/requirements.txt`, `backend/app/services/llm.py`
- Root cause: the implementation imports the maintained `google-genai` SDK, while both dependency manifests declared `google-generativeai` and neither package was installed.
- Impact: Gemini LLM initialization could fail even when a Gemini API key was configured.
- Fix: declare and install `google-genai>=1.0,<2.0`; verify `from google import genai` and provider imports.
- Regression evidence: SDK import and package version verified successfully.

### P2 — New York job country normalization mismatch
- Files: `backend/app/services/job_normalizer.py`, `backend/tests/test_jobs.py`
- Root cause: the normalization test expected blank country for a non-Pakistan job, while location parsing correctly and productively detected New York as the United States. Unknown locations also defaulted incorrectly to Pakistan.
- Impact: explicit international locations could be stored incorrectly, and unknown locations could be inferred as Pakistan without evidence.
- Fix: detect explicit countries such as US; store an empty country when no country can be inferred; update the stale test expectation to `US`.
- Regression evidence: all 57 `test_jobs.py` cases passed, including the corrected normalization case.

### P3 — Frontend lint failures
- File: `frontend/src/pages/NotFoundPage.tsx`
- Root cause: unescaped apostrophes in JSX text.
- Impact: configured frontend lint failed.
- Fix: escaped the apostrophes with JSX entities.
- Regression evidence: ESLint completed with no errors.

## Remaining high-priority validation gaps

- Live external job-source availability, real file uploads, browser E2E journeys, production database connectivity, paid/live Gemini calls, and true deployment runtime were not executed without credentials or approval.
- Existing full-suite runtime warnings should be tracked, but are not confirmed functional failures.
