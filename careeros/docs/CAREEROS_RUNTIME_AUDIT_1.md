# CareerOS Runtime Audit (Fresh Run)

Date: 2026-10-31

## Repository baseline
- Branch: `main`
- Commit: `fca04a9cab570b669d228dd9d6b5f4e686bc1370`
- Working tree contained pre-existing modified and untracked files; those were preserved. Only confirmed audit-related fixes were added.

## Environment
- Backend executable: `careeros/backend/.venv/Scripts/python.exe`
- Backend Python: `3.13.2`
- Node.js: `v24.18.0`
- npm: `11.16.0`
- Dependency declarations were inspected at `careeros/backend/pyproject.toml`, `careeros/backend/requirements.txt`, and `careeros/frontend/package.json`.

## Gemini dependency finding
The backend imported `google.genai` but both dependency manifests declared the deprecated `google-generativeai` package and neither Gemini package was installed. The manifests were changed to `google-genai>=1.0,<2.0`, and `google-genai==1.75.0` was installed. Verified in the backend virtual environment with `from google import genai`.

## Backend startup
Command:

```powershell
cd careeros/backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The server started successfully and remained responsive.

Health check:

```text
GET http://127.0.0.1:8000/health
200 {"status":"ok","service":"CareerOS API","timestamp":1793428680.62996}
```

## Database and migrations
Alembic configuration loaded the SQLite implementation. Running:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

completed successfully. This was executed against the configured local database, not a production database.

## Frontend startup
Command:

```powershell
cd careeros/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

The server returned HTTP 200 and served the Vite application HTML.

## Frontend validation
- TypeScript check: passed.
- ESLint: passed after escaping JSX apostrophes in `NotFoundPage.tsx`.
- Production build: passed (`1967` modules transformed).
- Vitest: 4 test files and 4 tests passed.

## Runtime warnings
- Vite reports that its native config loader plan does not yet support the current `__dirname` usage in the Vite and Vitest configurations.
- Backend tests emit Starlette `httpx2` deprecation warnings and two SQLAlchemy transaction warnings. None are application runtime startup failures.
