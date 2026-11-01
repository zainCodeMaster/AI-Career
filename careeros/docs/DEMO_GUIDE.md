# CareerOS AI — Demo Guide

**Version:** 1.0  
**Date:** October 30, 2026  
**Duration:** ~15-20 minutes

---

## 1. Demo Overview

This guide walks through a complete end-to-end demonstration of CareerOS AI for FYP evaluation. The demo showcases all core features in a logical user journey.

### 1.1 Demo Scenario
**Persona:** *Sarah Ahmed* — Senior Software Engineer (6 years exp), based in Lahore, Pakistan. Looking for remote Senior Python/ML roles at international companies.

### 1.2 Prerequisites
- CareerOS running locally (see INSTALLATION.md)
- Optional: `GEMINI_API_KEY` in `.env` for AI features
- Sample resume file (PDF/DOCX) for import demo

---

## 2. Demo Script

### 🎬 Scene 1: Onboarding & Profile Setup (3 min)

**Goal:** Show complete profile creation

1. **Register/Login**
   - Open http://localhost:5173
   - Click "Register" → sarah.ahmed@example.com / password123
   - Auto-login, land on Dashboard

2. **Complete Career Profile**
   - Navigate: **Sidebar → Career Profile**
   - Fill Summary: *"Senior Software Engineer with 6 years building scalable Python applications. Expert in ML pipelines, FastAPI, PostgreSQL. Seeking remote Senior/Lead roles."*
   - Location: *Lahore, Pakistan*
   - Experience: *6 years*
   - Target Role: *Senior Python Engineer / ML Engineer*
   - Remote Preference: *Remote Only*
   - Add LinkedIn/GitHub URLs

3. **Add Education**
   - Tab: **Education** → **Add**
   - BS Computer Science, LUMS, 2016-2020, CGPA 3.8

4. **Add Experience**
   - Tab: **Experience** → **Add**
   - *Senior Software Engineer @ DataTech (2022-Present)*
   - *Software Engineer @ StartupXYZ (2019-2022)*
   - Add 2-3 achievements per role

5. **Add Skills** (Critical for matching!)
   - Python (Expert, 6 yrs), FastAPI (Expert, 4 yrs), PostgreSQL (Advanced, 5 yrs)
   - Machine Learning (Advanced, 3 yrs), Docker (Advanced, 3 yrs), AWS (Intermediate, 2 yrs)
   - Kubernetes (Intermediate, 1 yr), GraphQL (Beginner, 6 mo)

6. **Add Certification**
   - AWS Solutions Architect Associate, 2023

**✅ Checkpoint:** Profile shows "Complete" with all sections filled.

---

### 🎬 Scene 2: Resume Studio (3 min)

**Goal:** Show resume creation, ATS analysis, and tailoring

1. **Build from Profile**
   - Navigate: **Resume Studio** → **New Resume** → "Build from Profile"
   - Name: *"Sarah Ahmed - Senior Python Engineer"*
   - Review auto-generated sections

2. **Import Resume** (Optional)
   - Click **Import** → Upload sample PDF
   - Show parsed sections, edit if needed

3. **ATS Analysis**
   - Go to **Jobs** → Save a relevant job (e.g., "Senior Python Engineer - Remote")
   - Open Resume → **ATS Analysis** → Select saved job
   - Show: Overall score, keyword coverage, missing keywords
   - **Target: Score > 80**

4. **Tailor Resume**
   - From ATS Analysis → **"Tailor Resume"**
   - Name: *"Tailored - Senior Python at RemoteCorp"*
   - Show: Added keywords, reordered skills, emphasized ML experience
   - **Version History** shows both versions

---

### 🎬 Scene 3: Job Discovery & Matching (4 min)

**Goal:** Show multi-source discovery and AI matching

1. **Run Discovery**
   - Go to **Jobs** → Click **"Run Discovery"**
   - Wait for completion (~10-15 seconds)
   - Show toast: *"Discovery: 5/6 sources ok; 180 new jobs..."*

2. **Search & Filter**
   - Keyword: *"Python"*
   - Workplace: *Remote only*
   - Pakistan Eligibility: *Eligible*
   - Show: Filtered results with eligibility badges

3. **Job Cards & Details**
   - Hover card → Shows eligibility reason on hover
   - Click job → Full details
   - Point out: **Match Score** badge, **Save** button, **View Original**

4. **Match Feed**
   - Navigate: **Job Matches**
   - Show ranked list with scores
   - Click top match → **Match Detail**
   - Walk through breakdown:
     - Skills: 92% (Python, FastAPI, PostgreSQL matched)
     - Missing: Kubernetes, GraphQL
     - Explanation in plain English

---

### 🎬 Scene 4: Career Brain AI (3 min)

**Goal:** Show RAG-powered career assistant

> **Requires:** `GEMINI_API_KEY` in `.env` for full demo. Without it, shows deterministic fallback.

1. **Index Career Data**
   - Navigate: **Career Brain** → **"Index My Career Data"**
   - Wait for completion: *"6 documents, 42 chunks indexed"*

2. **Semantic Search**
   - Query: *"Python machine learning pipelines"*
   - Show results with relevance scores

3. **AI Answer Generation**
   - Click **"Ask Career Brain"**
   - Ask: *"What Python ML experience do I have?"*
   - Show: Answer with source citations, confidence level

4. **More Questions**
   - *"What skills am I missing for a Senior ML Engineer role?"*
   - *"Summarize my leadership experience"*
   - *"Which remote companies match my profile?"*

> **Without API Key:** Shows retrieved context with warning: *"AI answer generation not configured..."*

---

### 🎬 Scene 5: Application CRM (3 min)

**Goal:** Show end-to-end application tracking

1. **Create Application**
   - From **Job Detail** (top match) → **"Track Application"**
   - Name auto-filled: *"Senior Python Engineer at RemoteCorp"*
   - Priority: *High*, Deadline: *Next Friday*

2. **Pipeline Management**
   - Navigate: **Applications** → Kanban view
   - Drag: *Saved → Ready to Apply → Applied*
   - Show status badge updates

3. **Application Detail**
   - Click application → **Timeline** (auto-logs status changes)
   - **Add Interview**: Schedule, type (Technical), prep notes
   - **Add Follow-up**: "Check status with recruiter", due in 3 days
   - **Attach Documents**: Resume, Cover Letter

4. **Dashboard Analytics**
   - Navigate: **CRM Dashboard**
   - Show: Stats cards, Pipeline counts, Funnel conversion
   - Point out: *Response Rate, Interview Rate, Offer Rate*

---

### 🎬 Scene 6: Settings & Polish (1 min)

**Goal:** Show customization

1. **Job Preferences**
   - Settings → Job Preferences
   - Set target roles, cities, salary range

2. **AI Configuration**
   - Settings → AI Config
   - Show Gemini API Key field, model selection

3. **Theme Toggle**
   - TopBar → Sun/Moon icon
   - Show dark/light mode switch

---

## 3. Demo Data Setup

### 3.1 Sample Resume Content (for import demo)
```
SARAH AHMED
Senior Software Engineer
Lahore, Pakistan | +92-XXX-XXXXXXX | sarah.ahmed@email.com
LinkedIn: linkedin.com/in/sarahahmed | GitHub: github.com/sarahahmed

SUMMARY
Senior Software Engineer with 6 years building scalable Python applications.
Expert in ML pipelines, FastAPI, PostgreSQL. Seeking remote Senior/Lead roles.

EXPERIENCE
Senior Software Engineer | DataTech | 2022-Present
- Led team of 4 building ML-powered recommendation engine (Python, scikit-learn, TensorFlow)
- Reduced model training time 60% using distributed computing (Dask, Ray)
- Architected event-driven microservices with FastAPI, Kafka, PostgreSQL
- Mentored 2 junior engineers, established code review standards

Software Engineer | StartupXYZ | 2019-2022
- Built REST APIs with Flask/FastAPI serving 1M+ requests/day
- Implemented CI/CD pipelines (GitHub Actions, Docker, Kubernetes)
- Designed database schemas, optimized queries (PostgreSQL, Redis)

EDUCATION
BS Computer Science | LUMS | 2016-2020 | CGPA: 3.8/4.0

SKILLS
Python (Expert), FastAPI (Expert), PostgreSQL (Advanced), Machine Learning (Advanced)
Docker (Advanced), AWS (Intermediate), Kubernetes (Intermediate), GraphQL (Beginner)

CERTIFICATIONS
AWS Solutions Architect Associate | Amazon Web Services | 2023
```

### 3.2 Sample Job for Matching
Use the discovery system to find real jobs, or the StaticListSource in tests for deterministic demo data.

---

## 4. Key Talking Points for Evaluators

| Feature | Technical Highlight |
|---------|---------------------|
| **Multi-source Discovery** | Modular adapter pattern, 8+ sources, normalized schema, dedup via content hash |
| **Pakistan Eligibility** | Evidence-based classification (not default-true), 3-state logic with reasons |
| **Job Matching** | 7-signal weighted scoring, missing data handling, explainable breakdown |
| **Career Brain** | Deterministic chunking, hash embeddings (dev) / pgvector (prod), RAG with citations |
| **Resume ATS** | Rule-based keyword extraction, skill normalization, section-aware scoring |
| **Tailoring** | Versioned resumes, diff tracking, job-specific optimization |
| **CRM** | State machine with valid transitions, timeline, interviews, follow-ups |
| **Architecture** | Modular monolith, clear service boundaries, DI, audit logging |

---

## 5. Common Demo Issues & Fixes

| Issue | Quick Fix |
|-------|-----------|
| No jobs after discovery | Check source health page; some sources may be down |
| Low match scores | Ensure profile has 5+ skills, 2+ experiences |
| Career Brain not answering | Add `GEMINI_API_KEY` to `.env`, restart backend |
| Resume import fails | Use TXT format, keep file < 10MB |
| Dark mode not persisting | Check localStorage, clear cache |

---

## 6. Demo Checklist (Pre-Demo)

- [ ] Backend running on :8000
- [ ] Frontend running on :5173
- [ ] `GEMINI_API_KEY` in `.env` (for AI demo)
- [ ] Sample resume PDF ready
- [ ] Browser cache cleared
- [ ] Demo script printed
- [ ] Backup plan: screenshots/video if live demo fails

---

## 7. Demo Recording Tips

1. **Resolution:** 1920x1080 minimum
2. **Zoom:** 125% for readability
3. **Narrate:** Explain *what* and *why*, not just *how*
4. **Pace:** 2-3 seconds between actions
5. **Highlight:** Use mouse to point at key UI elements
5. **Timebox:** Keep each scene to allocated time

---

## 8. Fallback: Pre-recorded Demo

If live demo is risky, prepare a 5-minute video covering:
1. Profile setup (30s)
2. Resume ATS + Tailor (45s)
3. Discovery + Matching (60s)
4. Career Brain Q&A (45s)
5. CRM Pipeline (45s)
6. Dashboard Analytics (15s)

Upload to YouTube (unlisted) or include in submission package.