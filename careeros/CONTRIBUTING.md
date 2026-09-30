# Contributing to CareerOS AI

Thank you for your interest in contributing to CareerOS AI! This document outlines our development philosophy, workflow, and standards.

---

## 🎯 Our Development Philosophy

Before contributing, understand our core principles:

1. **Inspect before modifying** - Understand existing code before changing
2. **Never blindly overwrite** - Preserve working functionality
3. **Never delete features without justification** - Refactor, don't destroy
4. **Treat external data as untrusted** - Job descriptions, emails, webhooks
5. **No fabrication** - Never invent career information
6. **Human approval for consequential actions** - Applications, emails, offers need approval
7. **Strong typing** - TypeScript, Pydantic everywhere
8. **Observable and auditable** - Structured logging, audit trails
9. **Modular architecture** - Easy to test, replace, extend
10. **Production-ready** - Security, error handling, testing from day one

---

## 🏗️ Development Workflow

### 1. Inspect

Before you start coding, understand the system:

```bash
# Read relevant documentation
cat docs/ARCHITECTURE.md
cat docs/API.md
cat docs/DATABASE.md

# Inspect the current code
git log --oneline -20
ls -la backend/app/
ls -la frontend/src/

# Run existing tests
cd backend && pytest tests/
cd ../frontend && npm test
```

**Questions to answer**:
- What does this code currently do?
- What tests exist?
- What's the error-free baseline?
- What am I changing and why?
- What could break?

### 2. Plan

Create a clear implementation plan:

```markdown
## Feature: Job Radar Configuration

### Requirements
- User can create custom job search profiles
- Each profile has filters (roles, skills, locations)
- Radar runs on schedule (daily/weekly)
- Results notify user

### Changes
- Backend: New API endpoint /api/v1/jobs/radar
- Database: New table job_radar_configs
- Frontend: New UI component JobRadarBuilder
- Tests: API tests, integration tests

### Dependencies
- None new

### Security
- User isolation enforced
- Rate limiting on discovery

### Timeline
- Phase 4 deliverable
```

### 3. Implement

Follow these guidelines:

**Backend (Python)**:
- Use async/await where appropriate
- Validate with Pydantic
- Write docstrings
- Log important operations
- Handle errors gracefully
- Use type hints

**Frontend (TypeScript)**:
- Use React hooks, no class components
- Type everything with TypeScript
- Use Zustand for state
- Use TanStack Query for API calls
- Write tests with React Testing Library
- Follow component structure guidelines

**Database (SQL)**:
- Use Alembic migrations
- Write migration docstring
- Index foreign keys
- Add timestamps (created_at, updated_at)
- Use soft deletion where appropriate
- Add comments for complex columns

### 4. Test

Every feature requires tests:

**Backend Tests**:
```python
# tests/test_job_radar.py
import pytest
from app.services.job_radar import JobRadarService

@pytest.fixture
def user(db_session):
    """Create test user"""
    return create_test_user(db_session)

def test_create_radar(user):
    """Test creating a job radar"""
    service = JobRadarService(db_session)
    radar = service.create(
        user_id=user.id,
        name="AI Engineer",
        filters={...}
    )
    assert radar.name == "AI Engineer"
    assert radar.user_id == user.id

def test_user_isolation(user1, user2):
    """Test that users can't see each other's radars"""
    # user1 creates radar
    # Verify user2 can't see it
```

**Frontend Tests**:
```typescript
// src/features/jobs/__tests__/JobRadarBuilder.test.tsx
import { render, screen } from '@testing-library/react';
import { JobRadarBuilder } from '../JobRadarBuilder';

describe('JobRadarBuilder', () => {
  it('renders the form', () => {
    render(<JobRadarBuilder />);
    expect(screen.getByLabelText('Radar Name')).toBeInTheDocument();
  });

  it('submits form with data', async () => {
    // Test form submission
  });
});
```

**Integration Tests**:
```bash
# Test the full workflow: API → Service → Database
pytest tests/integration/test_job_radar_workflow.py
```

### 5. Verify

Before submitting:

```bash
# Backend
cd backend
pytest tests/          # All tests pass
black app/            # Format code
pylint app/           # Check style
mypy app/             # Type check

# Frontend
cd ../frontend
npm test              # All tests pass
npm run lint          # ESLint passes
npm run type-check    # TypeScript passes
npm run format        # Prettier formatting
```

### 6. Review

Create a pull request and request review:

```markdown
## PR Description

### What
- Implemented job radar configuration UI and API
- Users can create custom job discovery filters
- Radar triggers based on schedule

### Why
- Core feature in Phase 4
- Allows personalized job discovery
- Foundation for job matching

### Changes
- Backend: 3 new API endpoints
- Frontend: New JobRadarBuilder component
- Database: 1 new table with indexes
- Tests: 15 unit + 5 integration tests

### Testing
- All new code has tests
- Existing tests pass
- Manual verification: [screenshots]

### Security
- User isolation validated
- Input validation with Pydantic
- Rate limiting added

### Performance
- Database queries optimized
- API response time: <200ms
```

### 7. Deploy

After review and approval:

```bash
git checkout main
git pull
git checkout -b release/feature-name
# Version bumping, changelog update
git commit -m "Release: job radar feature v1.0"
git tag v1.0.0
git push origin main --tags
```

---

## 📋 Code Standards

### Python (Backend)

**Style**:
```python
# Use async for I/O operations
async def get_jobs():
    jobs = await db.query(Job)
    return jobs

# Use Pydantic for validation
class JobRadarRequest(BaseModel):
    name: str
    filters: JobFilters
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v

# Write docstrings
def create_resume(job_id: int, user_id: int) -> Resume:
    """
    Create a job-specific resume.
    
    Args:
        job_id: ID of the target job
        user_id: ID of the user
        
    Returns:
        Generated Resume object
        
    Raises:
        JobNotFound: If job doesn't exist
        UserNotFound: If user doesn't exist
    """
```

**Testing**:
```python
# Use descriptive test names
def test_resume_generation_with_matching_skills_produces_higher_score():
    """Clear what's being tested"""

# Use fixtures for shared setup
@pytest.fixture
def user_with_profile(db_session):
    user = create_test_user(db_session)
    create_test_profile(db_session, user)
    return user

# Test one behavior per test
def test_matching_skills_increases_score(user_with_profile):
    # Setup
    job = create_test_job(skills=['Python', 'FastAPI'])
    
    # Action
    score = calculate_match_score(user_with_profile, job)
    
    # Assert
    assert score > 80
```

### TypeScript (Frontend)

**Style**:
```typescript
// Use type-safe components
interface JobRadarProps {
  onSave: (radar: JobRadarConfig) => Promise<void>;
  initialData?: JobRadarConfig;
}

export const JobRadarBuilder: React.FC<JobRadarProps> = ({
  onSave,
  initialData,
}) => {
  // Implementation
};

// Use hooks for state
const [filters, setFilters] = useState<JobFilters>(
  initialData?.filters ?? DEFAULT_FILTERS
);

// Use TanStack Query for server state
const { mutate: saveRadar } = useMutation({
  mutationFn: (data: JobRadarConfig) => api.saveRadar(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['radars'] });
  },
});
```

**Testing**:
```typescript
describe('JobRadarBuilder', () => {
  it('should load initial data', () => {
    const initialData = { name: 'AI', filters: {} };
    render(<JobRadarBuilder initialData={initialData} />);
    expect(screen.getByDisplayValue('AI')).toBeInTheDocument();
  });

  it('should call onSave when form is submitted', async () => {
    const onSave = vi.fn();
    render(<JobRadarBuilder onSave={onSave} />);
    
    await userEvent.click(screen.getByText('Save'));
    expect(onSave).toHaveBeenCalled();
  });
});
```

### Database Migrations

**Alembic Format**:
```python
# backend/migrations/versions/001_create_job_radars.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    """Create job_radar_configs table"""
    op.create_table(
        'job_radar_configs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('filters', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_job_radar_user', 'job_radar_configs', ['user_id'])

def downgrade():
    """Drop job_radar_configs table"""
    op.drop_table('job_radar_configs')
```

---

## 📚 Documentation Standards

Every feature should have documentation:

### README Updates

- Add to main README.md if user-facing
- Include feature description and usage

### Architecture Updates

- Update docs/ARCHITECTURE.md if changing system design
- Update data flow diagrams
- Document new components

### API Documentation

- Add endpoint to docs/API.md
- Include request/response examples
- Document error cases
- Document authentication requirements

### Code Comments

- Explain WHY, not WHAT
- Comment complex algorithms
- Explain non-obvious design decisions

```python
# BAD: Comments state the obvious
x = x + 1  # increment x

# GOOD: Comments explain reasoning
# We use field-level encryption for PII per GDPR requirements
encrypted_salary = encrypt_field(salary, user_id)
```

---

## 🔐 Security Guidelines

When contributing security-related code:

1. **Never hardcode secrets**
   ```python
   # WRONG
   api_key = "sk-1234567890"
   
   # CORRECT
   api_key = os.getenv("GEMINI_API_KEY")
   if not api_key:
       raise ValueError("GEMINI_API_KEY not configured")
   ```

2. **Validate all external data**
   ```python
   # External job description is untrusted
   job_description = job_data['description']  # Could be malicious
   
   # Validate before use
   try:
       parsed = parse_job_description(job_description)
   except ValidationError:
       logger.warning(f"Invalid job description: {job_data['id']}")
       return None
   ```

3. **Use parameterized queries**
   ```python
   # WRONG: SQL injection risk
   query = f"SELECT * FROM jobs WHERE title = '{title}'"
   
   # CORRECT: SQLAlchemy prevents injection
   query = db.query(Job).filter(Job.title == title)
   ```

4. **Implement rate limiting**
   ```python
   # Protect expensive operations
   @app.post("/api/v1/jobs/discover")
   @rate_limit(per_minute=5)
   async def discover_jobs():
       # ...
   ```

5. **Audit consequential actions**
   ```python
   # Log when user submits an application
   await audit_log.record(
       user_id=user.id,
       action="APPLICATION_SUBMITTED",
       resource_id=application.id,
       details={"company": company_name}
   )
   ```

---

## 🚀 Performance Guidelines

- **Don't optimize prematurely**, but think about scalability
- **Measure before optimizing**, use profiling tools
- **Cache appropriately**, use Redis for frequently accessed data
- **Batch operations**, avoid N+1 queries
- **Index database columns**, especially foreign keys
- **Lazy load data**, load only what's needed

Example:
```python
# WRONG: N+1 queries - fetches user for every application
apps = db.query(Application).all()
for app in apps:
    user = db.query(User).filter(User.id == app.user_id).first()
    print(user.name)

# CORRECT: Uses eager loading
apps = db.query(Application).options(
    joinedload(Application.user)
).all()
for app in apps:
    print(app.user.name)  # No additional queries
```

---

## 🔄 Branching Strategy

- `main` - Production-ready code (latest release)
- `develop` - Integration branch for current phase
- `feature/description` - Feature branches (off develop)
- `bugfix/description` - Bug fix branches (off develop)
- `release/version` - Release preparation
- `hotfix/description` - Emergency production fixes (off main)

```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/job-radar

# Commit regularly
git commit -m "feat: add job radar model and service"
git commit -m "feat: add job radar API endpoints"
git commit -m "test: add comprehensive radar tests"

# Push to GitHub
git push origin feature/job-radar

# Create pull request, get review, merge
```

---

## 📝 Commit Message Format

Use conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `test` - Test changes
- `docs` - Documentation
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `chore` - Dependency updates, configuration

**Examples**:
```
feat(jobs): add job radar configuration API

- Create POST /api/v1/jobs/radar endpoint
- Validate radar filters with Pydantic
- Store in PostgreSQL with user isolation

Closes #123

---

fix(matching): correct skill matching algorithm

The previous algorithm didn't properly handle skill levels.
Now uses weighted scoring based on proficiency.

---

test(email): add comprehensive email classification tests

Added 20 test cases covering:
- Recruiter emails
- Interview invitations
- Offer emails
- Rejection emails

Closes #456
```

---

## 🆘 Getting Help

- **Architecture questions** → Read docs/ARCHITECTURE.md
- **API questions** → Read docs/API.md
- **Database questions** → Read docs/DATABASE.md
- **Code style** → Look at similar existing code
- **Stuck?** → Open an issue with context

---

## 📋 Checklist Before PR

- [ ] Code follows project style guide
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] No hardcoded secrets or credentials
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts with `develop`
- [ ] Performance impact considered
- [ ] Security impact considered
- [ ] Backwards compatibility maintained

---

## 🎓 Learning Resources

- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/concepts/)
- [React Best Practices](https://react.dev/learn)
- [SQLAlchemy Guide](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---

**Thank you for contributing to CareerOS AI!**
