# CareerOS AI — Testing Documentation

**Version:** 1.0  
**Date:** October 30, 2026

---

## 1. Test Strategy

### 1.1 Testing Pyramid

```
        /\
       /  \     E2E Tests (Playwright) - Critical user journeys
      /____\
     /      \   Integration Tests - API + DB + Services
    /________\
   /          \ Unit Tests - Pure functions, services, components
  /____________\
```

### 1.2 Test Categories

| Category | Tool | Scope | Count |
|----------|------|-------|-------|
| Backend Unit | pytest | Pure functions, validators | ~150 |
| Backend Integration | pytest + TestClient | API routes, DB, services | ~200 |
| Backend Security | pytest | Auth, authorization, input validation | ~50 |
| Frontend Unit | Vitest + Testing Library | Components, hooks | 4 |
| E2E | Playwright | Critical user flows | Configured |

---

## 2. Backend Testing

### 2.1 Running Tests

```bash
cd careeros/backend

# Run all tests
python -m pytest -q

# Run specific test file
python -m pytest tests/test_auth.py -q

# Run with coverage
python -m pytest --cov=app --cov-report=term-missing

# Run specific test class
python -m pytest tests/test_jobs.py::TestCrossUserIsolation -q
```

### 2.2 Test Structure

```
tests/
├── conftest.py              # Fixtures, test client, auth helpers
├── test_auth.py             # Registration, login, refresh, logout, me
├── test_career.py           # Profile, education, experience, skills, certs
├── test_career_brain.py     # Indexing, search, context, answer
├── test_crm_*.py            # CRM: applications, companies, contacts, etc.
├── test_jobs.py             # Job search, save, discovery, sources
├── test_matching.py         # Match engine, signals, ranking
├── test_resume_*.py         # Resume CRUD, sections, versions, ATS, tailor, import
├── test_sources.py          # Job source adapters
├── test_security_sources.py # Source security validation
└── test_scheduler.py        # APScheduler integration
```

### 2.3 Key Fixtures (conftest.py)

```python
@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient with test database."""

@pytest.fixture
def db_session() -> Session:
    """SQLAlchemy session with transaction rollback."""

@pytest.fixture
def auth_headers(client) -> dict:
    """Register + login, return Authorization header."""

@pytest.fixture
def test_user(db_session) -> User:
    """Create test user in database."""
```

### 2.4 Test Patterns

#### Authentication Flow Test
```python
def test_register_login_logout(client):
    # Register
    resp = client.post("/api/v1/auth/register", json={...})
    assert resp.status_code == 201
    
    # Login
    resp = client.post("/api/v1/auth/login", json={...})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    
    # Access protected route
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
```

#### Database Isolation Test
```python
def test_cross_user_isolation(client, db_session):
    # User A creates job
    # User B cannot access User A's job
    # Expect 404 (not 403)
```

#### Source Adapter Test
```python
def test_remote_ok_fetch():
    source = RemoteOKSource()
    # Mock HTTP response
    jobs = source.fetch(max_results=10)
    assert len(jobs) > 0
    assert all(j.eligibility in ("eligible", "ineligible", "unknown") for j in jobs)
```

---

## 3. Frontend Testing

### 3.1 Running Tests

```bash
cd careeros/frontend

# Run all tests
npm test -- --run

# Run with UI
npm test

# Run with coverage
npm test -- --coverage
```

### 3.2 Test Structure

```
src/__tests__/
├── app-routes.test.tsx        # Route protection, navigation
├── auth-flow.test.tsx         # Login/register form validation
├── career-data-flow.test.tsx  # Profile CRUD integration
└── career-data-page-isolated.test.tsx  # Page component unit test
```

### 3.3 Example Component Test

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginPage } from '../pages/LoginPage';

test('shows validation errors for empty fields', () => {
  render(<LoginPage />);
  fireEvent.click(screen.getByRole('button', { name: /login/i }));
  expect(screen.getByText(/email is required/i)).toBeInTheDocument();
});
```

---

## 4. Test Data Management

### 4.1 Test Database
- SQLite in-memory for unit tests
- Separate test database file for integration tests
- Automatic rollback via transaction fixtures

### 4.2 Mocking External Services
```python
# In tests/test_sources.py
with patch('app.services.sources.international.httpx.get') as mock_get:
    mock_get.return_value.json.return_value = MOCK_REMOTE_OK_RESPONSE
    jobs = RemoteOKSource().fetch(max_results=5)
```

### 4.3 Deterministic Test Data
- `StaticListSource` for offline job discovery testing
- `FailingSource` for error handling tests
- Mock LLM provider for Career Brain tests

---

## 4. Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Backend Services | 85% | ~80% |
| API Routes | 90% | ~85% |
| Frontend Components | 70% | ~40% |
| Overall | 80% | ~75% |

---

## 5. Continuous Integration

### 5.1 GitHub Actions (`.github/workflows/tests.yml`)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: careeros_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e careeros/backend[dev]
      - run: cd careeros/backend && python -m pytest -q
  
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd careeros/frontend && npm ci
      - run: cd careeros/frontend && npm run build
      - run: cd careeros/frontend && npm test -- --run
```

---

## 5. Manual Testing Checklist

### 5.1 Authentication
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Reject login with wrong password
- [ ] Access protected route with token
- [ ] Reject expired token
- [ ] Refresh token works
- [ ] Logout invalidates refresh token

### 5.2 Career Profile
- [ ] Create complete profile
- [ ] Add/edit/delete education
- [ ] Add/edit/delete experience
- [ ] Add/edit/delete skills
- [ ] Add/edit/delete certifications

### 5.3 Resume
- [ ] Create base resume
- [ ] Import from TXT/PDF/DOCX
- [ ] Run ATS analysis against job
- [ ] Tailor resume for specific job
- [ ] Export resume as text
- [ ] Version history works

### 5.4 Job Discovery
- [ ] Search jobs with filters
- [ ] Save/unsave jobs
- [ ] Run discovery (all sources)
- [ ] Run discovery (single source)
- [ ] View source health
- [ ] Check discovery history

### 5.5 Job Matching
- [ ] View match feed
- [ ] View match detail with explanations
- [ ] Verify matched/missing skills shown

### 5.6 Career Brain
- [ ] Index career data
- [ ] Semantic search returns relevant chunks
- [ ] AI answer generation (with API key)
- [ ] Fallback works without API key

### 5.7 CRM
- [ ] Create application from job
- [ ] Move through pipeline stages
- [ ] Add interview
- [ ] Add follow-up
- [ ] View dashboard analytics
- [ ] View pipeline Kanban

---

## 6. Performance Testing

### 6.1 API Benchmarks (Target)
| Endpoint | Target (p95) |
|----------|-------------|
| `/jobs` (20 items) | < 200ms |
| `/jobs/matches` (20 items) | < 500ms |
| `/career-brain/answer` | < 3000ms (with LLM) |
| `/resumes/ats/analyze` | < 1000ms |

### 6.2 Load Testing (Future)
```bash
# Using locust or k6
locust -f locustfile.py --host=http://localhost:8000
```