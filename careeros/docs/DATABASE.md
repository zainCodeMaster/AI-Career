# CareerOS AI - Database Design

This document outlines the database schema and design principles for CareerOS AI.

---

## Overview

CareerOS uses PostgreSQL (via Supabase) as its primary database. The schema is designed for:

- **Normalization** - Avoid data duplication
- **Scalability** - Support growth to multi-user SaaS
- **Auditability** - Track all changes
- **Performance** - Indexed queries
- **Security** - Row-level security (RLS)

---

## Database Schema (Phase 2+)

The complete schema will be implemented using Alembic migrations in later phases.

### Core Entity Groups

#### User & Authentication
```sql
users
├── id (PK)
├── email (UNIQUE)
├── password_hash
├── created_at
├── updated_at
└── deleted_at (soft delete)

user_sessions
├── id (PK)
├── user_id (FK)
├── token
├── expires_at
└── created_at
```

#### Career Profile
```sql
profiles
├── id (PK)
├── user_id (FK, UNIQUE)
├── headline
├── summary
├── years_experience
├── created_at
├── updated_at
└── deleted_at

education
├── id (PK)
├── user_id (FK)
├── school_name
├── degree
├── field_of_study
├── start_date
├── end_date
├── description
├── created_at
├── updated_at

experiences
├── id (PK)
├── user_id (FK)
├── company_name
├── title
├── employment_type
├── location
├── start_date
├── end_date
├── description
├── skills
├── created_at
├── updated_at

skills
├── id (PK)
├── user_id (FK)
├── name
├── proficiency (BEGINNER/INTERMEDIATE/ADVANCED/EXPERT)
├── years_experience
├── endorsements
├── created_at
├── updated_at
```

#### Projects & Portfolio
```sql
projects
├── id (PK)
├── user_id (FK)
├── title
├── description
├── url
├── github_url
├── technologies (JSON array)
├── start_date
├── end_date
├── featured (boolean)
├── created_at
├── updated_at

portfolio_items
├── id (PK)
├── user_id (FK)
├── project_id (FK)
├── type (PROJECT/ACHIEVEMENT/ARTICLE)
├── content_url
├── media_urls (JSON array)
├── description
├── created_at
├── updated_at

github_repositories
├── id (PK)
├── user_id (FK)
├── github_id
├── name
├── url
├── description
├── language
├── stars
├── forks
├── topics (JSON)
├── last_updated
├── synced_at
├── created_at
```

#### Documents & Knowledge Base
```sql
documents
├── id (PK)
├── user_id (FK)
├── title
├── file_url (Supabase Storage)
├── file_type (PDF/DOCX/TXT/etc)
├── size_bytes
├── processed (boolean)
├── created_at
├── updated_at
├── deleted_at

document_chunks
├── id (PK)
├── document_id (FK)
├── content (text)
├── chunk_index
├── metadata (JSON)
├── created_at

embeddings
├── id (PK)
├── chunk_id (FK)
├── embedding (pgvector)
├── model (text)
├── created_at
```

#### Jobs & Matching
```sql
job_sources
├── id (PK)
├── name (LinkedIn/Indeed/Google/etc)
├── api_key (encrypted)
├── config (JSON)
├── enabled (boolean)
├── created_at
├── updated_at

jobs
├── id (PK)
├── source_id (FK)
├── external_id
├── company_name
├── title
├── description
├── requirements (JSON)
├── preferred_requirements (JSON)
├── skills (JSON array)
├── location (JSON)
├── remote_type (ONSITE/HYBRID/REMOTE)
├── employment_type
├── salary_min
├── salary_max
├── currency
├── posted_at
├── discovered_at
├── application_url
├── original_url
├── status (ACTIVE/ARCHIVED/EXPIRED)
├── created_at
├── updated_at

job_matches
├── id (PK)
├── job_id (FK)
├── user_id (FK)
├── match_score (0-100)
├── explanation (text)
├── applied_at
├── created_at

job_radar_configs
├── id (PK)
├── user_id (FK)
├── name
├── filters (JSON)
├── target_roles (JSON)
├── keywords (JSON)
├── locations (JSON)
├── salary_min
├── salary_max
├── enabled (boolean)
├── last_run_at
├── created_at
├── updated_at
```

#### Applications
```sql
applications
├── id (PK)
├── user_id (FK)
├── job_id (FK)
├── status (NEW/SHORTLISTED/PREPARING/READY/APPLIED/etc)
├── resume_id (FK)
├── cover_letter_id (FK)
├── applied_at
├── created_at
├── updated_at

application_documents
├── id (PK)
├── application_id (FK)
├── document_type (RESUME/COVER_LETTER/PORTFOLIO/etc)
├── file_url (Supabase Storage)
├── created_at

application_answers
├── id (PK)
├── application_id (FK)
├── question_text
├── answer_text
├── generated (boolean)
├── user_approved (boolean)
├── created_at
├── updated_at

application_events
├── id (PK)
├── application_id (FK)
├── event_type (STATUS_CHANGE/EMAIL_RECEIVED/etc)
├── description
├── metadata (JSON)
├── created_at
```

#### Resumes
```sql
resumes
├── id (PK, UUID)
├── user_id (FK → users.id, CASCADE delete)
├── name (VARCHAR 255)
├── resume_type (VARCHAR 32)
│   └── Enum: base | tailored | imported
├── status (VARCHAR 32)
│   └── Enum: draft | ready | archived
├── target_job_id (FK → jobs.id, SET NULL)
├── parent_resume_id (FK → resumes.id, SET NULL)
│   └── Self-referential: parent resume for versioning
├── version_number (INTEGER, default 1)
├── structured_data (JSON)
│   └── Parsed resume content: summary, skills, experience, education, projects, certifications, achievements, custom_sections
├── source_file_name (VARCHAR 255, nullable)
├── source_file_type (VARCHAR 50, nullable)
│   └── pdf | docx | txt
├── import_metadata (JSON, nullable)
├── ats_score (INTEGER, nullable)
├── ats_breakdown (JSON, nullable)
├── ats_analyzed_at (TIMESTAMPTZ, nullable)
├── ats_analyzed_for_job_id (FK → jobs.id, SET NULL)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

resume_sections
├── id (PK, UUID)
├── resume_id (FK → resumes.id, CASCADE delete)
├── section_type (VARCHAR 50)
│   └── summary | skills | experience | education | projects | certifications | custom
├── section_title (VARCHAR 255, nullable)
├── content (TEXT)
├── display_order (INTEGER, default 0)
├── is_custom (BOOLEAN, default false)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

**Resume Relationships:**
- `resumes.user_id` → `users.id` (owner)
- `resumes.target_job_id` → `jobs.id` (target job for tailored resumes)
- `resumes.parent_resume_id` → `resumes.id` (version tree parent)
- `resume_sections.resume_id` → `resumes.id` (sections belong to a resume)

**Resume Indexes:**
- `ix_resumes_user_type` on `(user_id, resume_type)`
- `ix_resumes_status` on `(status)`
- `ix_resumes_resume_type` on `(resume_type)`
- `ix_resumes_target_job` on `(target_job_id)`
- `ix_resumes_parent` on `(parent_resume_id)`
- `ix_resumes_ats_analyzed` on `(ats_analyzed_for_job_id)`
- `uq_resume_user_name_version` unique constraint on `(user_id, name, version_number)`

**Resume Section Indexes:**
- `ix_resume_sections_resume_type` on `(resume_id, section_type)`
- `ix_resume_sections_order` on `(resume_id, display_order)`
- `ix_resume_sections_section_type` on `(section_type)`

#### Email Integration
```sql
email_accounts
├── id (PK)
├── user_id (FK)
├── email
├── provider (GMAIL/OUTLOOK)
├── access_token (encrypted)
├── refresh_token (encrypted)
├── synced_at
├── created_at
├── updated_at

email_messages
├── id (PK)
├── user_id (FK)
├── email_account_id (FK)
├── external_id (Gmail ID)
├── from_address
├── to_address
├── subject
├── body
├── html_body
├── received_at
├── classification (RECRUITER/INTERVIEW/OFFER/etc)
├── application_id (FK)
├── processed (boolean)
├── created_at

email_threads
├── id (PK)
├── user_id (FK)
├── messages (array of message IDs)
├── application_id (FK)
├── created_at
```

#### Interviews
```sql
interviews
├── id (PK)
├── user_id (FK)
├── application_id (FK)
├── company_name
├── position_title
├── interview_type (PHONE/TECHNICAL/BEHAVIORAL/etc)
├── scheduled_at
├── duration_minutes
├── timezone
├── interviewer_name
├── meeting_url
├── preparation_notes
├── created_at
├── updated_at

interview_questions
├── id (PK)
├── interview_id (FK)
├── question_text
├── category (TECHNICAL/BEHAVIORAL/etc)
├── difficulty (EASY/MEDIUM/HARD)
├── created_at

interview_sessions
├── id (PK)
├── interview_id (FK)
├── session_type (MOCK/REAL)
├── notes
├── evaluation (JSON)
├── recorded_at
└── created_at
```

#### Analytics & Audit
```sql
audit_logs
├── id (PK)
├── user_id (FK)
├── action (APPLICATION_SUBMITTED/EMAIL_SENT/etc)
├── resource_type
├── resource_id
├── details (JSON)
├── status (SUCCESS/FAILED)
├── ip_address
├── user_agent
├── timestamp
└── created_at

tool_runs
├── id (PK)
├── ai_run_id (FK)
├── tool_name
├── input (JSON)
├── output (JSON)
├── error (text)
├── duration_ms
├── tokens_used
├── cost
└── created_at

ai_runs
├── id (PK)
├── user_id (FK)
├── agent_name
├── request (JSON)
├── response (JSON)
├── error (text)
├── tokens_used
├── cost
└── created_at

notifications
├── id (PK)
├── user_id (FK)
├── type (JOB_MATCH/INTERVIEW/EMAIL/etc)
├── title
├── message
├── data (JSON)
├── read (boolean)
├── created_at
```

---

## Indexing Strategy

```sql
-- User isolation
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at DESC);
CREATE UNIQUE INDEX idx_job_user_unique ON job_matches(job_id, user_id);

-- Foreign key indexes
CREATE INDEX idx_email_messages_application ON email_messages(application_id);
CREATE INDEX idx_interview_application ON interviews(application_id);

-- Search optimization
CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_applications_status ON applications(status);

-- pgvector similarity search
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);

-- Audit trail
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action, timestamp DESC);
```

---

## Row-Level Security (RLS)

All user-scoped tables will have RLS policies:

```sql
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own applications"
  ON applications
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can only create their own applications"
  ON applications
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can only update their own applications"
  ON applications
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

---

## Migrations

Database changes are managed with Alembic:

```bash
# Create migration
alembic revision --autogenerate -m "Add job matching tables"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

Migrations will be created in Phase 2+ as schema is finalized.

---

## Encryption & Sensitive Data

Sensitive fields (OAuth tokens, passwords) are encrypted:

```python
# Using SQLAlchemy with encryption
from sqlalchemy_utils import EncryptedType
from cryptography.fernet import Fernet

class EmailAccount(Base):
    access_token = Column(
        EncryptedType(String, settings.encryption_key),
        nullable=False
    )
    refresh_token = Column(
        EncryptedType(String, settings.encryption_key),
        nullable=False
    )
```

---

## Backup & Recovery

- **Backup frequency**: Daily (Supabase managed)
- **Retention**: 30 days
- **Point-in-time recovery**: Supported
- **Testing**: Monthly backup restore test

---

## Performance Considerations

- **Connection pooling**: Using SQLAlchemy pool
- **Query optimization**: Eager loading with joinedload
- **Caching**: Redis for frequently accessed data
- **Partitioning**: Consider for email_messages and audit_logs tables
- **Archive strategy**: Move old data to cold storage after 1 year

---

## Data Retention Policy

| Data Type | Retention | Deletion |
|-----------|-----------|----------|
| User accounts | Until deleted | Hard/soft delete after 90 days |
| Applications | Until user deletes | Hard delete after 2 years |
| Emails | Until user deletes | Hard delete after 1 year |
| Audit logs | Permanent | Archive after 1 year |
| Embeddings | Until deleted | Recalculate on document update |
| Sessions | 30 days | Automatic expiration |

---

**Database schema will be finalized and implemented in Phase 2 - Career Profile.**
