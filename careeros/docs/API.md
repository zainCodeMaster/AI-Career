# CareerOS AI - API Documentation

## Base URL

```
/api/v1
```

## Authentication

All endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Resumes

### List Resumes

```
GET /resumes
```

Query parameters:
- `page` (int, default: 1)
- `page_size` (int, default: 20)

Returns a paginated list of the authenticated user's resumes.

### Create Resume

```
POST /resumes
```

Request body:
```json
{
  "name": "Software Engineer Resume",
  "resume_type": "base"
}
```

`resume_type` is optional and defaults to `base`. Valid values: `base`, `tailored`, `imported`.

### Get Resume

```
GET /resumes/{resume_id}
```

Returns full resume details including sections, versions, and target job.

### Update Resume

```
PUT /resumes/{resume_id}
```

Request body (all fields optional):
```json
{
  "name": "Updated Resume Name",
  "status": "ready",
  "structured_data": { ... }
}
```

### Delete Resume

```
DELETE /resumes/{resume_id}
```

Returns `204 No Content` on success.

### Build Resume from Profile

```
POST /resumes/build-from-profile?name=My Resume
```

Generates a base resume from the user's verified Career Profile data.

---

## Resume Sections

### List Sections

```
GET /resumes/{resume_id}/sections
```

Returns all sections for a resume, ordered by `display_order`.

### Create Section

```
POST /resumes/{resume_id}/sections
```

Request body:
```json
{
  "section_type": "skills",
  "section_title": "Technical Skills",
  "content": "Python, Django, PostgreSQL",
  "display_order": 0,
  "is_custom": false
}
```

### Update Section

```
PUT /resumes/sections/{section_id}
```

Request body (all fields optional):
```json
{
  "section_type": "skills",
  "section_title": "Updated Title",
  "content": "Updated content",
  "display_order": 1,
  "is_custom": true
}
```

### Delete Section

```
DELETE /resumes/sections/{section_id}
```

Returns `204 No Content` on success.

---

## Resume Versions

### List Versions

```
GET /resumes/{resume_id}/versions
```

Returns all versions of a resume, including the resume itself and child versions.

---

## ATS Analysis

### Analyze Resume ATS

```
POST /resumes/ats/analyze
```

Request body:
```json
{
  "resume_id": "uuid",
  "job_id": "uuid"
}
```

Returns deterministic ATS analysis including:
- `overall_score` (0-100)
- `breakdown` (section scores)
- `matched_keywords`, `missing_keywords`
- `matched_skills`, `missing_skills`
- `matched_requirements`, `missing_requirements`
- `recommendations`

Scoring is deterministic and does not use LLM calls.

---

## Resume Tailoring

### Tailor Resume for Job

```
POST /resumes/tailor
```

Request body:
```json
{
  "base_resume_id": "uuid",
  "target_job_id": "uuid",
  "name": "Tailored Resume Name"
}
```

Creates a new tailored resume based on the base resume and target job. The original resume is never modified. Returns the tailored resume, ATS analysis, match results, and change log.

---

## Resume Import

### Import Resume from Text

```
POST /resumes/{resume_id}/import/text
```

Request body:
```json
{
  "resume_text": "Plain text resume content..."
}
```

`resume_text` is limited to 50,000 characters. Returns the updated resume with parsed structured data.

### Import Resume from File

```
POST /resumes/{resume_id}/import/file
```

Upload a resume file (PDF, DOCX, or TXT). Returns the updated resume with parsed structured data.

---

## Response Schemas

### ResumeResponse

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "Software Engineer Resume",
  "resume_type": "base",
  "status": "draft",
  "target_job_id": "uuid",
  "version_number": 1,
  "structured_data": { ... },
  "ats_score": 75,
  "ats_breakdown": { ... },
  "created_at": "2026-09-10T...",
  "updated_at": "2026-09-10T..."
}
```

### ResumeSectionResponse

```json
{
  "id": "uuid",
  "resume_id": "uuid",
  "section_type": "skills",
  "section_title": "Technical Skills",
  "content": "Python, Django",
  "display_order": 0,
  "is_custom": false,
  "created_at": "2026-09-10T...",
  "updated_at": "2026-09-10T..."
}
```

### ATSAnalysisResponse

```json
{
  "resume_id": "uuid",
  "job_id": "uuid",
  "overall_score": 75,
  "breakdown": {
    "keyword_coverage": 80,
    "skill_alignment": 70,
    "structure_score": 90
  },
  "matched_keywords": ["python", "django"],
  "missing_keywords": ["kubernetes"],
  "matched_skills": ["python", "postgresql"],
  "missing_skills": ["docker"],
  "matched_requirements": ["5+ years experience"],
  "missing_requirements": ["AWS certification"],
  "recommendations": ["Consider adding Docker experience"],
  "analyzed_at": "2026-09-10T..."
}
```

### TailorResponse

```json
{
  "tailored_resume_id": "uuid",
  "base_resume_id": "uuid",
  "target_job_id": "uuid",
  "tailoring_changes": [ ... ],
  "ats_analysis": { ... },
  "matched_requirements": [ ... ],
  "missing_requirements": [ ... ],
  "recommendations": [ ... ],
  "created_at": "2026-09-10T..."
}
```

---

## Error Responses

All errors return a standard format:

```json
{
  "detail": "Error message"
}
```

Common status codes:
- `400` — Invalid request data
- `401` — Authentication required
- `403` — Insufficient permissions
- `404` — Resource not found
- `422` — Validation error
- `500` — Internal server error
