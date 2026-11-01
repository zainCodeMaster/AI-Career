# CareerOS AI — API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** Bearer Token (JWT)

---

## 1. Authentication

All endpoints except `/auth/*`, `/health`, `/ready` require:
```
Authorization: Bearer <access_token>
```

### 1.1 Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 1.2 Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK` (same as register)

### 1.3 Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK` (new token pair)

### 1.4 Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00Z"
}
```

### 1.5 Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

**Response:** `204 No Content`

---

## 2. Career Profile

### 2.1 Get Profile
```http
GET /profile
Authorization: Bearer <token>
```

### 2.2 Create/Update Profile
```http
POST /profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "summary": "Experienced software engineer...",
  "location": "Lahore, Pakistan",
  "years_of_experience": 5,
  "preferred_job_title": "Senior Python Developer",
  "preferred_location": "Remote",
  "remote_preference": "remote_only",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "portfolio_url": "https://johndoe.dev"
}
```

**Response:** `200 OK` (Profile object)

### 2.3 Education
```http
GET    /education
POST   /education
PUT    /education/{id}
DELETE /education/{id}
```

**Education Object:**
```json
{
  "id": "uuid",
  "degree": "Bachelor of Science in Computer Science",
  "institution": "LUMS",
  "field_of_study": "Computer Science",
  "start_date": "2018-09-01",
  "end_date": "2022-06-15",
  "grade": "3.8/4.0",
  "description": "Relevant coursework..."
}
```

### 2.4 Experience
```http
GET    /experience
POST   /experience
PUT    /experience/{id}
DELETE /experience/{id}
```

**Experience Object:**
```json
{
  "id": "uuid",
  "title": "Senior Software Engineer",
  "company": "TechCorp",
  "location": "Lahore, Pakistan",
  "start_date": "2022-07-01",
  "end_date": null,
  "is_current": true,
  "description": "Led backend team...",
  "achievements": ["Scaled API to 1M req/day", "Reduced latency 40%"]
}
```

### 2.5 Skills
```http
GET    /skills
POST   /skills
PUT    /skills/{id}
DELETE /skills/{id}
```

**Skill Object:**
```json
{
  "id": "uuid",
  "name": "Python",
  "category": "Programming Language",
  "proficiency": "expert",
  "years_experience": 6
}
```

### 2.6 Certifications
```http
GET    /certifications
POST   /certifications
PUT    /certifications/{id}
DELETE /certifications/{id}
```

**Certification Object:**
```json
{
  "id": "uuid",
  "name": "AWS Solutions Architect",
  "issuer": "Amazon Web Services",
  "issue_date": "2023-03-15",
  "expiry_date": "2026-03-15",
  "credential_id": "AWS-SA-12345",
  "credential_url": "https://aws.amazon.com/verify/..."
}
```

---

## 3. Resume Management

### 3.1 List Resumes
```http
GET /resumes?page=1&page_size=20&status=draft&resume_type=base
Authorization: Bearer <token>
```

**Response:**
```json
{
  "items": [...],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "has_next": false,
  "has_prev": false
}
```

### 3.2 Create Resume
```http
POST /resumes
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Resume",
  "resume_type": "base",
  "status": "draft"
}
```

### 3.3 Get Resume
```http
GET /resumes/{id}
Authorization: Bearer <token>
```

### 3.4 Update Resume
```http
PUT /resumes/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "status": "ready"
}
```

### 3.5 Delete Resume
```http
DELETE /resumes/{id}
Authorization: Bearer <token>
```

### 3.6 Resume Sections
```http
GET    /resumes/{id}/sections
POST   /resumes/{id}/sections
PUT    /resumes/sections/{section_id}
DELETE /resumes/sections/{section_id}
```

**Section Object:**
```json
{
  "id": "uuid",
  "section_type": "experience",
  "section_title": "Work Experience",
  "content": "Senior Engineer at TechCorp...",
  "display_order": 1,
  "is_custom": false
}
```

### 3.7 Resume Versions
```http
GET /resumes/{id}/versions
```

### 3.8 ATS Analysis
```http
POST /resumes/ats/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "resume_id": "uuid",
  "job_id": "uuid"
}
```

**Response:**
```json
{
  "resume_id": "uuid",
  "job_id": "uuid",
  "overall_score": 85.5,
  "keyword_coverage": { "score": 90, "matched": 18, "total": 20, ... },
  "skill_alignment": { "score": 80, "matched": 12, "total": 15, ... },
  "matched_keywords": ["Python", "FastAPI", "PostgreSQL"],
  "missing_keywords": ["Kubernetes", "GraphQL"],
  "strengths": ["Strong keyword match", "Relevant experience"],
  "weaknesses": ["Missing cloud keywords"],
  "recommendations": ["Add Kubernetes experience", "Mention GraphQL"]
}
```

### 3.9 Resume Tailoring
```http
POST /resumes/tailor
Authorization: Bearer <token>
Content-Type: application/json

{
  "base_resume_id": "uuid",
  "target_job_id": "uuid",
  "name": "Tailored for Senior Python Role"
}
```

**Response:** Tailored resume with ATS analysis and changes.

### 3.10 Import Resume (Text)
```http
POST /resumes/{id}/import/text
Authorization: Bearer <token>
Content-Type: application/json

{
  "resume_text": "John Doe\nSenior Engineer\nExperience: 6 years..."
}
```

### 3.11 Import Resume (File)
```http
POST /resumes/{id}/import/file
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf|docx|txt file, max 10MB>
```

### 3.12 Build from Profile
```http
POST /resumes/build-from-profile?name=My%20Resume
Authorization: Bearer <token>
```

### 3.13 Export Resume
```http
GET /resumes/{id}/export
Authorization: Bearer <token>
```
**Response:** Plain text file download.

---

## 4. Job Discovery

### 4.1 Search Jobs
```http
GET /jobs?keyword=python&city=lahore&remote=true&employment_type=full_time&page=1&page_size=20&sort=posted_desc
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `keyword` | string | Search in title, description, company |
| `title` | string | Exact title match |
| `company` | string | Company name |
| `city` | string | City name |
| `province` | string | Province/state |
| `country` | string | ISO country code (PK, US, etc.) |
| `remote` | boolean | true=remote only |
| `hybrid` | boolean | true=hybrid only |
| `onsite` | boolean | true=onsite only |
| `employment_type` | string | full_time, part_time, contract, internship |
| `internship` | boolean | true=internships only |
| `entry_level` | boolean | true=0-2 years experience |
| `min_salary` | number | Minimum salary |
| `max_salary` | number | Maximum salary |
| `industry` | string | Category/industry |
| `source` | string | Source ID filter |
| `sector` | string | government, private, remote, any |
| `posted_within_days` | integer | Posted within N days |
| `closing_within_days` | integer | Closing within N days |
| `is_active` | boolean | Default true |
| `is_pakistan` | boolean | Pakistan eligibility filter |
| `page` | integer | Page number (default 1) |
| `page_size` | integer | Items per page (default 20) |
| `sort` | string | posted_desc, posted_asc, closing_asc, salary_desc, salary_asc |

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

**JobSummary:**
```json
{
  "id": "uuid",
  "source": "remote_ok",
  "source_url": "https://remoteok.com/remote-jobs/12345",
  "title": "Senior Python Developer",
  "company_name": "RemoteCorp",
  "city": "Lahore",
  "province": "Punjab",
  "country": "PK",
  "is_remote": true,
  "is_pakistan_eligible": true,
  "eligibility": "eligible",
  "eligibility_reason": "Remote worldwide",
  "employment_type": "full_time",
  "workplace_type": "remote",
  "salary_min": 80000,
  "salary_max": 120000,
  "salary_currency": "USD",
  "experience_min": 5,
  "posted_at": "2026-01-15T10:00:00Z",
  "status": "active",
  "is_active": true
}
```

### 4.2 Get Job Detail
```http
GET /jobs/{id}
Authorization: Bearer <token>
```

**Response:** `JobDetail` (extends `JobSummary` with description, requirements, responsibilities, skills, department, education_requirements, eligibility details)

### 4.3 Save/Unsave Job
```http
POST   /jobs/{id}/save
DELETE /jobs/{id}/save
Authorization: Bearer <token>
Content-Type: application/json

{ "notes": "Interesting remote role" }
```

### 4.4 List Saved Jobs
```http
GET /jobs/saved
Authorization: Bearer <token>
```

### 4.5 Run Discovery
```http
POST /jobs/_discovery/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "source_id": "remote_ok",
  "max_results": 100,
  "timeout": 30.0
}
```
Omit `source_id` to run all enabled sources.

**Response:**
```json
{
  "sources_attempted": 5,
  "sources_succeeded": 4,
  "sources_failed": 1,
  "jobs_found": 245,
  "jobs_created": 180,
  "jobs_updated": 45,
  "jobs_skipped": 20,
  "jobs_expired": 5,
  "error_count": 1
}
```

### 4.6 List Sources
```http
GET /sources
Authorization: Bearer <token>
```

### 4.7 Source Health
```http
GET /sources/health
Authorization: Bearer <token>
```

### 4.8 Source Detail
```http
GET /sources/{source_id}
Authorization: Bearer <token>
```

### 4.9 Discovery History
```http
GET /jobs/discovery/runs?page=1&page_size=20&source_id=remote_ok&status=success
Authorization: Bearer <token>
```

### 4.10 Job Preferences
```http
GET    /job-preferences
PUT    /job-preferences
Authorization: Bearer <token>
```

---

## 5. Job Matching

### 5.1 Get Match Feed
```http
GET /jobs/matches?page=1&page_size=20&min_score=50
Authorization: Bearer <token>
```

**Response:**
```json
{
  "items": [
    {
      "match": { ... },
      "job": { ... }
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "profile_completeness": "full"
}
```

### 5.2 Get Match Detail
```http
GET /jobs/{job_id}/match
Authorization: Bearer <token>
```

**MatchResult:**
```json
{
  "job_id": "uuid",
  "overall_score": 87.3,
  "breakdown": {
    "skills": 92.0,
    "experience": 85.0,
    "education": 90.0,
    "location": 95.0,
    "preferences": 80.0,
    "semantic": 88.0,
    "role_title": 75.0
  },
  "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "missing_skills": ["Kubernetes", "GraphQL"],
  "matched_requirements": ["5+ years Python", "FastAPI experience"],
  "missing_requirements": ["Kubernetes", "GraphQL"],
  "qualification_match": true,
  "experience_match": true,
  "location_match": true,
  "explanation": [
    "Matched 4 skills: Python, FastAPI, PostgreSQL, Docker.",
    "Missing required skill(s): Kubernetes, GraphQL.",
    "Experience: 6 years meets 5-year requirement.",
    "Education: Bachelor's meets requirement.",
    "Location: Remote worldwide matches preference.",
    "Preferences: Full-time matches preference.",
    "Semantic similarity: 0.88 (high relevance).",
    "Role match: Senior Python Developer aligns with target roles."
  ],
  "profile_completeness": "full",
  "generated_at": "2026-01-15T10:30:00Z"
}
```

---

## 6. Career Brain

### 6.1 Index Career Data
```http
POST /career-brain/index
Authorization: Bearer <token>
```

**Response:**
```json
{
  "documents_processed": 6,
  "chunks_created": 42,
  "embeddings_created": 42,
  "embeddings_reused": 0,
  "embedding_model": "local-hash-384"
}
```

### 6.2 Semantic Search
```http
POST /career-brain/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "Python machine learning experience",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "Python machine learning experience",
  "results": [
    {
      "id": "uuid",
      "source_type": "experience",
      "source_id": "uuid",
      "title": "Senior ML Engineer",
      "content": "Built ML pipelines using Python, scikit-learn...",
      "score": 0.92
    }
  ]
}
```

### 6.3 Build RAG Context
```http
POST /career-brain/context
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "Python machine learning experience",
  "top_k": 5
}
```

**Response:** `ContextResponse` with formatted context string.

### 6.4 Generate AI Answer
```http
POST /career-brain/answer
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What Python ML experience do I have?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What Python ML experience do I have?",
  "answer": "Based on your career profile, you have 3 years of Python ML experience...",
  "sources": [
    { "id": "uuid", "source_type": "experience", "title": "Senior ML Engineer", "score": 0.92 }
  ],
  "model": "gemini-1.5-flash",
  "confidence": "high",
  "warning": null
}
```

---

## 7. CRM (Application Management)

### 7.1 Applications

```http
GET    /applications?page=1&page_size=20&status=applied
GET    /applications/{id}
POST   /applications
PATCH  /applications/{id}
DELETE /applications/{id}
POST   /applications/{id}/transitions
GET    /applications/{id}/timeline
```

**ApplicationCreate:**
```json
{
  "name": "Senior Python at RemoteCorp",
  "job_id": "uuid",
  "company_id": "uuid",
  "priority": "high",
  "source": "manual",
  "notes": "Applied via company website",
  "deadline_at": "2026-02-15T23:59:00Z"
}
```

**ApplicationResponse:**
```json
{
  "id": "uuid",
  "name": "Senior Python at RemoteCorp",
  "status": "applied",
  "priority": "high",
  "source": "manual",
  "job": { "id": "uuid", "title": "Senior Python Developer", "company_name": "RemoteCorp" },
  "company": { "id": "uuid", "name": "RemoteCorp", "domain": "remotecorp.com" },
  "applied_at": "2026-01-15T10:00:00Z",
  "activities": [...],
  "interviews": [...],
  "follow_ups": [...]
}
```

### 7.2 State Transitions
```http
POST /applications/{id}/transitions
Authorization: Bearer <token>
Content-Type: application/json

{
  "to_status": "interview",
  "reason": "Phone screen scheduled",
  "metadata": { "interview_type": "phone" }
}
```

**Valid Transitions:**
```
saved → ready_to_apply → applied → application_viewed → screening → interview → technical_interview → final_interview → offer → accepted
                                                      ↘ rejected (from any state)
                                                      ↘ withdrawn (from any state)
                                                      ↘ on_hold (from any state)
```

### 7.3 Dashboard Stats
```http
GET /crm/dashboard
Authorization: Bearer <token>
```

### 7.4 Pipeline
```http
GET /crm/pipeline
Authorization: Bearer <token>
```

### 7.5 Analytics
```http
GET /crm/analytics
Authorization: Bearer <token>
```

### 7.4 Companies
```http
GET    /companies
POST   /companies
PATCH  /companies/{id}
DELETE /companies/{id}
```

### 7.5 Contacts
```http
GET    /contacts
POST   /contacts
PATCH  /contacts/{id}
DELETE /contacts/{id}
```

### 7.6 Interviews
```http
GET    /interviews?application_id=uuid
POST   /interviews
PATCH  /interviews/{id}
DELETE /interviews/{id}
```

### 7.7 Follow-ups
```http
GET    /follow-ups?application_id=uuid
POST   /follow-ups
PATCH  /follow-ups/{id}
DELETE /follow-ups/{id}
POST   /follow-ups/{id}/complete
```

---

## 8. Error Responses

### 8.1 Standard Error Format
```json
{
  "detail": "Error description"
}
```

### 8.2 Validation Error (422)
```json
{
  "detail": "Invalid request data"
}
```

### 8.3 HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## 9. Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/register` | 60/min/IP |
| `/auth/login` | 60/min/IP |
| `/auth/refresh` | 60/min/IP |
| All other | 120/min/user |

---

## 10. Example Complete Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123","full_name":"John Doe"}'

# 2. Login (save access_token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'

# 3. Create profile
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"summary":"...","location":"Lahore","years_of_experience":5}'

# 4. Add skills
curl -X POST http://localhost:8000/api/v1/skills \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Python","category":"Programming Language","proficiency":"expert","years_experience":6}'

# 5. Build resume from profile
curl -X POST "http://localhost:8000/api/v1/resumes/build-from-profile?name=My%20Resume" \
  -H "Authorization: Bearer <token>"

# 6. Run job discovery
curl -X POST http://localhost:8000/api/v1/jobs/_discovery/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'

# 7. Search jobs
curl "http://localhost:8000/api/v1/jobs?keyword=python&remote=true" \
  -H "Authorization: Bearer <token>"

# 8. Get matches
curl "http://localhost:8000/api/v1/jobs/matches" \
  -H "Authorization: Bearer <token>"

# 9. Track application
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Applied to RemoteCorp","job_id":"<job_id>","priority":"high"}'
```