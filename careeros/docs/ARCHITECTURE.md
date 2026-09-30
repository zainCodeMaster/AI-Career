# CareerOS AI - System Architecture

## Overview

CareerOS AI is built as a layered, modular system with clear separation of concerns. The architecture is designed for:

- **Single-user initial deployment** with multi-user SaaS architecture built-in
- **Observable operations** with comprehensive logging and audit trails
- **Secure integrations** with external services (Gmail, GitHub, job sources)
- **Autonomous but human-controlled** AI workflows
- **Extensible** provider and adapter patterns

---

## High-Level Architecture

```
                         CAREEROS AI SYSTEM
                              │
                ┌─────────────┴─────────────┐
                │                           │
             React                      FastAPI
          TypeScript UI                  Backend
       (Vite + Tailwind)            (Python Async)
                │                           │
                │                    ┌──────┴──────┐
                │                    │             │
                │              Application       LangGraph
                │              Services          Agents
                │                    │             │
                │                    └──────┬──────┘
                │                           │
                └───────────────────────────┤
                                            │
                                      Supabase
                          ┌───────────────┼───────────────┐
                          │               │               │
                     PostgreSQL         pgvector       Storage
                     (Primary DB)     (Embeddings)     (Files)
                          │               │
                          └───────────────┘
                                │
                          Redis Cache
                                │
                    ┌───────────┼───────────┐
                    │           │           │
               Sessions      Jobs       Messages
                    │           │           │
                    └───────────┼───────────┘
                                │
                    Background Processing
                    (Celery / RQ Workers)
                                │
                ┌───────────────┼───────────────┐
                │               │               │
           Job Discovery   Email Sync      Embeddings
           User Notification Browser Automation


                    External Integrations
                │
        ┌───────┼───────┬────────┬─────────┐
        │       │       │        │         │
      Gmail  GitHub  LinkedIn  Job APIs  Playwright
      (OAuth) (OAuth) (Content) (REST)   (Browser)
```

---

## Component Layers

### 1. Frontend Layer

**Technology**: React + TypeScript + Vite + Tailwind CSS

**Responsibilities**:
- User interface and interactions
- Form management and validation
- State management (Zustand stores)
- API communication (TanStack Query)
- Client-side routing
- Authentication flow (OAuth handling)

**Key Features**:
- Real-time notifications
- Dashboard with career metrics
- Application tracking UI
- Email management interface
- Resume builder and editor
- Interview preparation tools
- GitHub/portfolio viewer
- Settings and preferences

**Constraints**:
- No business logic in components
- No direct database access
- No API keys or secrets stored
- Type-safe throughout (TypeScript)

---

### 2. API Layer (FastAPI)

**Technology**: FastAPI + Pydantic + SQLAlchemy

**Responsibilities**:
- HTTP request handling
- Request validation
- Response serialization
- Authentication and authorization
- Rate limiting
- CORS handling
- Error handling and sanitization

**Endpoints** (Proposed):
```
/api/v1/auth/
  POST   /login
  POST   /signup
  POST   /logout
  POST   /refresh
  GET    /me
  POST   /oauth/{provider}

/api/v1/profile/
  GET    /
  PUT    /
  GET    /career-dna

/api/v1/career/
  GET    /education
  POST   /education
  GET    /experience
  POST   /experience
  GET    /skills
  POST   /skills
  GET    /projects
  POST   /projects
  # ... more career data endpoints

/api/v1/documents/
  POST   /upload
  GET    /{id}
  DELETE /{id}
  POST   /{id}/process

/api/v1/jobs/
  GET    /           # List discovered jobs
  GET    /{id}       # Get job details
  GET    /radar      # Get job radar config
  PUT    /radar      # Update radar
  POST   /discover   # Trigger discovery

/api/v1/matches/
  GET    /           # List job matches
  GET    /{job_id}   # Detailed match analysis

/api/v1/resumes/
  GET    /           # List resumes
  POST   /           # Create resume
  GET    /{id}       # Get resume
  PUT    /{id}       # Update resume
  DELETE /{id}       # Delete resume
  GET    /{id}/sections       # List sections
  POST   /{id}/sections       # Create section
  PUT    /sections/{id}       # Update section
  DELETE /sections/{id}       # Delete section
  GET    /{id}/versions       # List versions
  POST   /ats/analyze         # ATS analysis
  POST   /tailor              # Tailor resume for job
  POST   /{id}/import/text    # Import resume from text
  POST   /{id}/import/file    # Import resume from file
  POST   /build-from-profile  # Build resume from career profile

/api/v1/applications/
  GET    /           # List applications
  POST   /           # Create application
  PUT    /{id}       # Update status
  GET    /{id}/history

/api/v1/emails/
  GET    /           # List emails
  GET    /{id}       # Get email details
  POST   /{id}/reply-draft
  POST   /{id}/reply # Send reply

/api/v1/interviews/
  GET    /           # List interviews
  POST   /           # Create interview
  GET    /{id}/prep  # Get preparation

/api/v1/github/
  GET    /user
  GET    /repos
  POST   /sync

/api/v1/linkedin/
  GET    /profile
  POST   /content-draft

/api/v1/portfolio/
  GET    /
  GET    /{id}

/api/v1/analytics/
  GET    /dashboard
  GET    /applications
  GET    /conversions

/api/v1/assistant/
  POST   /query      # Process natural language requests
  POST   /action     # Execute assistant actions
```

**Key Principles**:
- Request/response validation with Pydantic
- Proper HTTP status codes
- Consistent error format
- Pagination support
- Filtering and sorting
- Rate limiting headers

---

### 3. Application Services Layer

**Technology**: Python service classes

**Responsibilities**:
- Business logic orchestration
- Data validation and transformation
- Transaction management
- Cross-repository operations
- Service composition

**Examples**:
```python
ProfileService - Career profile management
DocumentService - Document ingestion and processing
JobDiscoveryService - Job source coordination
JobMatchingService - Scoring and ranking
ResumeService - Resume generation and optimization
ApplicationService - Application tracking
EmailService - Email operations
InterviewService - Interview management
GitHubService - GitHub integration
AnalyticsService - Metrics and reporting
```

**Constraints**:
- No direct HTTP handling
- No direct database queries (use repositories)
- No AI logic directly (delegate to agents)
- Testable in isolation

---

### 4. LangGraph Agents Layer

**Technology**: LangGraph + LangChain

**Responsibilities**:
- AI decision-making and orchestration
- Tool selection and sequencing
- Agentic workflows
- Memory management
- Structured output generation

**Agents**:
```
CareerBrainAgent - Profile understanding and retrieval
JobMatchingAgent - Job scoring and ranking
ResumeAgent - Resume tailoring and optimization
ApplicationAgent - Form filling and submission preparation
EmailClassificationAgent - Email categorization
EmailReplyAgent - Intelligent response generation
InterviewAgent - Interview question generation and evaluation
GitHubAnalysisAgent - Repository analysis
SkillGapAgent - Missing skills identification
CareerStrategyAgent - Strategic recommendations
```

**Key Principles**:
- Modular subgraph structure
- Tool registry integration
- Structured outputs validated with Pydantic
- Factuality checks before returning results
- Clear success/failure boundaries
- Human approval integration

---

### 5. Tools Layer

**Technology**: Pydantic + Tool Registry

**Responsibilities**:
- Encapsulate atomic operations
- Declare risk levels
- Handle tool execution
- Audit logging

**Tool Categories**:

**READ Tools** (Information retrieval):
- read_job
- read_email
- read_github_repo
- search_career_brain
- search_job_opportunities

**LOW_RISK_WRITE Tools** (Safe modifications):
- create_resume_draft
- create_email_draft
- create_application_record
- update_career_profile
- process_document

**HIGH_RISK_WRITE Tools** (Consequential changes):
- send_email
- submit_application
- publish_linkedin_content
- update_public_profile

**SENSITIVE Tools** (Explicit approval required):
- accept_offer
- reject_offer
- make_legal_declaration
- financial_commitment

---

### 6. Repository Layer (Data Access)

**Technology**: SQLAlchemy ORM

**Responsibilities**:
- Database queries
- Connection management
- Query optimization
- Data transformation

**Repositories**:
```python
UserRepository
ProfileRepository
EducationRepository
ExperienceRepository
SkillRepository
ProjectRepository
CertificationRepository
DocumentRepository
DocumentChunkRepository
EmbeddingRepository
JobRepository
JobMatchRepository
ApplicationRepository
EmailRepository
InterviewRepository
GitHubRepository
AnalyticsRepository
AuditLogRepository
```

**Constraints**:
- No business logic
- No direct HTTP access
- Query results normalized to models
- Support pagination and filtering

---

### 7. Database Layer

**Technology**: Supabase PostgreSQL + pgvector

**Key Tables**:
```sql
-- User & Profile
users
user_sessions
profiles
career_preferences

-- Career Data
education
experiences
skills
projects
certifications
achievements
courses
languages
career_goals

-- Documents & Embeddings
documents
document_chunks
embeddings

-- Jobs
job_sources
jobs
job_source_records
job_matches
job_radar_configs

-- Applications
applications
application_documents
application_answers
application_events
application_communications

-- Email
email_accounts
email_messages
email_threads
email_classifications

-- Interviews
interviews
interview_questions
interview_sessions
interview_evaluations

-- Integrations
github_accounts
github_repositories
linkedin_profiles
linkedin_content

-- Analytics
career_metrics
conversion_metrics
skill_analytics

-- System
audit_logs
tool_runs
ai_runs
notifications
automation_tasks
```

---

### 8. Cache Layer

**Technology**: Redis

**Use Cases**:
- Session management
- Token blacklisting
- Job discovery results (temporary)
- Embedding cache
- Rate limiting counters
- User preferences cache

---

### 9. Background Processing

**Technology**: Celery/RQ + APScheduler

**Job Types**:
- Job discovery and normalization
- Email synchronization
- Embedding generation
- Document processing
- Scheduled briefings
- Notification delivery
- Periodic profile analysis
- Video rendering

---

### 10. External Integrations

**Gmail API**:
- OAuth flow
- Email fetching
- Email sending
- Label management

**GitHub API**:
- Repository analysis
- README parsing
- Language detection
- Activity monitoring

**LinkedIn**:
- Profile optimization suggestions
- Content generation
- Post scheduling (future)

**Job Sources**:
- LinkedIn Jobs
- Indeed
- Google Jobs
- Company career sites
- Remote boards
- Startup boards

**Playwright**:
- Form filling
- Document upload
- Page navigation
- Screenshot capture
- CAPTCHA detection

---

## Data Flow Examples

### Job Discovery Flow

```
User → Frontend
     ↓
Backend API (/jobs/discover)
     ↓
JobDiscoveryService
     ↓
LangGraph Job Discovery Agent
     ↓
Tool: Fetch from sources (LinkedIn, Indeed, etc.)
     ↓
Tool: Normalize job data
     ↓
Tool: Check for duplicates
     ↓
Store in PostgreSQL + Redis
     ↓
Background: Generate embeddings
     ↓
Return discovered jobs → Frontend
```

### Application Preparation Flow

```
User → Frontend (Select job)
     ↓
Backend API (/applications/prepare)
     ↓
ApplicationService
     ↓
LangGraph Resume Agent
  ├→ Retrieve job requirements
  ├→ Query Career Brain
  ├→ Select relevant experience
  ├→ Generate tailored resume
  └→ Analyze ATS compatibility
     ↓
Store resume version
     ↓
LangGraph Application Agent
  ├→ Extract application questions
  ├→ Generate answers based on career data
  ├→ Flag sensitive questions
  └→ Prepare form filling plan
     ↓
Return preparation package → Frontend
     ↓
User reviews and approves
     ↓
Backend: Execute browser automation (Playwright)
     ↓
Tool: Fill forms, upload documents
     ↓
Tool: Final verification
     ↓
Tool: Submit application (with HIGH_RISK approval)
     ↓
Store application record
     ↓
Notify user
```

### Email Processing Flow

```
Background Job: Sync Gmail
     ↓
Fetch new emails via Gmail API
     ↓
EmailClassificationAgent
  ├→ Classify message type
  ├→ Extract sender/company
  ├→ Link to application if possible
  └→ Flag required actions
     ↓
Store email record
     ↓
If action required:
  ├→ Notify user
  └→ Suggest response
     ↓
User triggers reply
     ↓
EmailReplyAgent
  ├→ Retrieve email context
  ├→ Retrieve application context
  ├→ Retrieve career brain facts
  ├→ Generate response options
  └→ Fact-check before presenting
     ↓
User reviews draft
     ↓
User approves
     ↓
Send email via Gmail API
     ↓
Log communication
```

---

## Security Architecture

### Authentication & Authorization

```
Frontend
  ↓
OAuth2 Login (Google/GitHub)
  ↓
FastAPI receives code
  ↓
Exchange code for tokens
  ↓
Create session in Redis
  ↓
Store tokens securely (HttpOnly cookies or secure storage)
  ↓
Frontend: Use session for API calls
  ↓
Backend: Validate session per request
  ↓
User-scoped database queries via RLS
```

### Permission Model

```
Tool Risk Level → Default Behavior
├── READ → Automatic execution
├── LOW_RISK_WRITE → Automatic execution (safe)
├── HIGH_RISK_WRITE → User approval required
└── SENSITIVE → Explicit human intervention

Agent Output → Validation
├── Schema validation (Pydantic)
├── Factuality check
├── External content sanitization
└── Audit logging
```

### Data Isolation

```
Every resource has:
├── user_id (ownership)
├── created_at (audit trail)
├── updated_at (change tracking)
└── created_by / updated_by (attribution)

Database RLS enforces:
├── Users can only see their own data
├── No cross-user queries
├── All queries filtered by user context
```

---

## Observability Architecture

### Logging

```
Structured JSON logging throughout:
├── API request/response logs
├── Service operation logs
├── Agent execution logs
├── Tool execution logs
├── Database query logs (dev only)
├── External API calls
└── Audit events (user actions)

Log levels:
├── DEBUG: Development details
├── INFO: Normal operations
├── WARNING: Potential issues
├── ERROR: Failures requiring attention
└── CRITICAL: System-level issues
```

### Tracing

```
Every request has:
├── Request ID (unique, propagated)
└── Trace context (for distributed tracing)

Agent runs tracked with:
├── Agent run ID
├── Step-by-step execution
└── Tool invocation IDs
```

### Metrics

```
Application metrics:
├── Request latency
├── Error rates
├── AI token usage
├── Cache hit rates
├── Database query times
└── Background job success rates

Business metrics:
├── Jobs discovered
├── Applications created
├── Email interactions
├── Interview preparations
└── Conversion rates
```

---

## Deployment Architecture

### Development Environment

```
Frontend:
  npm run dev → Vite dev server (localhost:5173)

Backend:
  uvicorn main:app --reload → FastAPI (localhost:8000)

Database:
  Supabase (cloud) or local PostgreSQL

Cache:
  Redis (local or cloud)

Background Jobs:
  Celery worker (local)
```

### Production Environment

```
Frontend:
  React SPA → Vercel/Netlify/S3 + CloudFront

Backend:
  FastAPI → Docker → Cloud Run/ECS/Railway

Database:
  Supabase PostgreSQL (managed)

Cache:
  Redis Cloud or AWS ElastiCache

Background Jobs:
  Celery on separate workers

Monitoring:
  Sentry, DataDog, or similar
```

---

## Future Evolution

### Multi-User SaaS

```
Current (Single User):
users[1]
  ↓
profiles[1]
  ↓
applications[many]

Future (Multi-Tenant):
organizations[many]
  ├→ users[many]
  ├→ profiles[many]
  └→ subscriptions[1]

Data model:
├── organization_id in all tables
├── RLS enforcing org isolation
├── Usage-based billing
├── Team management
└── Advanced analytics
```

### Provider Flexibility

```
Current:
LLM Requests → Gemini Provider

Future:
LLM Requests
  ├→ Provider Router
  ├→ Gemini Provider
  ├→ OpenAI Provider
  ├→ Anthropic Provider
  └→ Local Provider
```

---

## Performance Considerations

### Caching Strategy

- **Career Brain**: Embed career data at login, cache in memory
- **Job Matches**: Cache for 1 hour
- **API Responses**: Cache public data appropriately
- **Embeddings**: Cache computed embeddings

### Database Optimization

- Indexes on frequently queried columns
- Denormalization where necessary
- Partitioning for large tables (future)
- Connection pooling

### API Response Times

- Aim for <200ms for read operations
- Aim for <500ms for processing operations
- Use background jobs for heavy processing
- Return partial results with async completion

---

## Testing Architecture

### Unit Tests

- Individual functions/methods
- Mock external dependencies
- Use pytest fixtures

### Integration Tests

- Service layer interactions
- Database operations
- API endpoint behavior

### E2E Tests

- Full user workflows
- Browser automation testing
- External API mocking

### AI Tests

- Golden test cases for agents
- Factuality validation
- Prompt injection detection
- Job matching evaluation

---

## Development Workflow

1. **Inspect** existing code and architecture
2. **Plan** changes with clear requirements
3. **Implement** feature following conventions
4. **Test** at all levels (unit, integration, E2E)
5. **Verify** no regressions
6. **Review** for security, performance, style
7. **Document** changes and impact
8. **Deploy** following release process

---

**This architecture is designed to scale from personal use to a production SaaS platform while maintaining security, observability, and maintainability throughout.**
