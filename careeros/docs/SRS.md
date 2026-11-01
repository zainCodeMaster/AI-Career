# CareerOS AI — Software Requirements Specification (SRS)

**Version:** 1.0  
**Date:** October 30, 2026  
**Status:** Final FYP Submission

---

## 1. Introduction

### 1.1 Purpose
CareerOS AI is a comprehensive, AI-powered Career Operating System designed to help job seekers—particularly those based in Pakistan—manage their complete career journey from profile creation through job discovery, application tracking, and interview preparation.

### 1.2 Scope
The system provides:
- Professional career profile management (education, experience, skills, certifications)
- Resume upload, parsing, ATS analysis, and job-specific tailoring
- Multi-source job discovery with evidence-based Pakistan eligibility classification
- AI-powered job matching with explainable scoring
- Application CRM with Kanban pipeline, timeline, and analytics
- Career Brain RAG system for contextual career advice
- Interview preparation and skill gap analysis

### 1.3 Definitions
| Term | Definition |
|------|------------|
| ATS | Applicant Tracking System |
| RAG | Retrieval-Augmented Generation |
| CRM | Customer Relationship Management (here: Application CRM) |
| FYP | Final Year Project |
| LLM | Large Language Model |
| PK | Pakistan |

### 1.4 User Classes
- **Job Seeker**: Primary user managing their career profile, applications, and job search
- **System Administrator**: Manages job sources, system configuration (future)

### 1.5 Constraints
- SQLite for development; PostgreSQL + pgvector for production
- No unauthorized scraping of LinkedIn, Indeed, Google Jobs
- Gemini API key required for AI features (optional; graceful fallback)
- Pakistan-first design for eligibility logic

---

## 2. Functional Requirements

### 2.1 Authentication & User Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AUTH-01 | User registration with email/password | P0 |
| FR-AUTH-02 | JWT-based login with access/refresh tokens | P0 |
| FR-AUTH-03 | Token refresh and logout | P0 |
| FR-AUTH-04 | Protected routes with authentication guard | P0 |

### 2.2 Career Profile Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-PROF-01 | CRUD for career profile (summary, location, preferences) | P0 |
| FR-PROF-02 | Education records (degree, institution, dates, GPA) | P0 |
| FR-PROF-03 | Work experience (role, company, dates, achievements) | P0 |
| FR-PROF-04 | Skills with proficiency levels and years of experience | P0 |
| FR-PROF-05 | Certifications with issuer and dates | P0 |
| FR-PROF-06 | Profile completeness score (0-100) based on completed sections | P1 |

### 2.3 Resume Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RES-01 | Create/edit/delete resumes with sections | P0 |
| FR-RES-02 | Import from TXT, PDF, DOCX with text extraction | P0 |
| FR-RES-03 | Build base resume from career profile data | P0 |
| FR-RES-04 | ATS analysis against job (keyword, skills, experience) | P0 |
| FR-RES-05 | Job-specific resume tailoring with version history | P0 |
| FR-RES-06 | Export as plain text | P0 |
| FR-RES-07 | Cover letter generation grounded in verified career data | P1 |

### 2.3 Resume Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RES-01 | Create/edit/delete resumes with sections | P0 |
| FR-RES-02 | Import from TXT, PDF, DOCX with text extraction | P0 |
| FR-RES-03 | Build base resume from career profile data | P0 |
| FR-RES-04 | ATS analysis against job (keyword, skills, experience) | P0 |
| FR-RES-05 | Job-specific resume tailoring with version history | P0 |
| FR-RES-06 | Export as plain text | P0 |

### 2.4 Job Discovery
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-JOB-01 | Search/filter jobs by keyword, location, workplace type | P0 |
| FR-JOB-02 | Save/unsave jobs with notes | P0 |
| FR-JOB-03 | Run multi-source discovery (manual + scheduled) | P0 |
| FR-JOB-04 | View source health and discovery history | P0 |
| FR-JOB-05 | Evidence-based Pakistan eligibility (eligible/ineligible/unknown) | P0 |
| FR-JOB-06 | International remote sources: Remote OK, Himalayas | P1 |

### 2.5 Job Matching
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-MAT-01 | Explainable match scoring (skills, experience, education, location, preferences, semantic, role) | P0 |
| FR-MAT-02 | Matched/missing skills and requirements breakdown | P0 |
| FR-MAT-03 | Personalized ranked job feed | P0 |
| FR-MAT-04 | Match detail page with explanations | P0 |

### 2.6 Career Brain (RAG)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CB-01 | Index user career data (profile, experience, education, skills, resumes) | P0 |
| FR-CB-02 | Semantic search over indexed career data | P0 |
| FR-CB-03 | Generate AI answers with source citations (when Gemini configured) | P1 |
| FR-CB-04 | Deterministic fallback when AI unavailable | P0 |

### 2.7 Application CRM
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CRM-01 | Kanban pipeline (saved → ready → applied → screening → interview → offer/rejected) | P0 |
| FR-CRM-02 | Application timeline with activities | P0 |
| FR-CRM-03 | Interview tracking (schedule, notes, outcomes) | P0 |
| FR-CRM-04 | Follow-up reminders | P0 |
| FR-CRM-05 | Dashboard analytics (stats, funnel, pipeline) | P0 |

### 2.9 Notifications
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-NOT-01 | In-app notifications for interview reminders | P1 |
| FR-NOT-02 | Follow-up reminders with due dates | P1 |
| FR-NOT-03 | Read/unread status and notification list | P1 |
| FR-NOT-04 | Mark as read and delete notifications | P1 |

### 2.10 AI Features (Gemini)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AI-01 | Resume analysis and improvement suggestions | P1 |
| FR-AI-02 | Cover letter generation | P1 |
| FR-AI-03 | Skill gap analysis against target roles | P1 |
| FR-AI-04 | Career roadmap generation | P1 |

---

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PERF-01 | API response time (p95) | < 500ms |
| NFR-PERF-02 | Frontend build size | < 500KB gzipped |
| NFR-SEC-01 | JWT tokens with rotation, bcrypt passwords | Compliant |
| NFR-SEC-02 | File upload validation (type, size, path traversal) | Compliant |
| NFR-SEC-03 | No secrets in logs or code | Compliant |
| NFR-REL-01 | Background job retries with exponential backoff | 3 retries |
| NFR-REL-02 | Graceful degradation when AI unavailable | Mock provider |
| NFR-USAB-01 | Responsive design (mobile, tablet, desktop) | Tailwind CSS |
| NFR-USAB-02 | Dark-first premium UI theme | Implemented |
| NFR-DATA-01 | SQLite dev / PostgreSQL prod with migrations | Alembic |

---

## 4. System Constraints

1. **Job Sources**: Only authorized sources used (Remote OK API, Himalayas API, public government pages). No LinkedIn/Indeed scraping.
2. **AI Provider**: Google Gemini (configurable). Mock provider when unconfigured.
3. **Database**: SQLite for development; PostgreSQL with pgvector for production.
4. **Deployment**: Docker + docker-compose for containerized deployment; supports Docker Compose for local dev and production.
5. **Eligibility Logic**: Defaults to UNKNOWN; requires evidence for ELIGIBLE/INELIGIBLE.

---

## 5. Acceptance Criteria

| Feature | Criteria |
|---------|----------|
| Auth | Register → login → access protected routes → logout works |
| Profile | Can create complete profile with all sections |
| Resume | Upload PDF → extract text → run ATS → tailor for job |
| Jobs | Search jobs → filter by Pakistan eligibility → save → view match |
| Matching | Match score > 0 with explainable breakdown |
| Career Brain | Index data → search → get AI answer (with key) or fallback |
| CRM | Create app → move through pipeline → track interview |
| UI | Dark theme, responsive, no layout shifts |

---

## 6. Future Enhancements (Post-FYP)

- Official LinkedIn/Indeed partnerships
- Browser automation for application submission
- Email integration (Gmail/Outlook)
- GitHub portfolio analysis
- Multi-tenant SaaS architecture
- Billing and subscription management