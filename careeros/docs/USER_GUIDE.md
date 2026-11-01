# CareerOS AI — User Guide

**Version:** 1.0  
**Date:** October 30, 2026

---

## 1. Getting Started

### 1.1 What is CareerOS AI?
CareerOS AI is your personal AI-powered Career Operating System. It helps you:
- Build a comprehensive career profile
- Manage resumes with ATS optimization
- Discover jobs from multiple sources
- Get AI-powered job matching and career advice
- Track applications through a professional CRM

### 1.2 First Login
1. Open CareerOS in your browser
2. Click **"Register"** to create an account
3. Fill in your email, password, and full name
4. You'll be redirected to the Dashboard

---

## 2. Career Profile

### 2.1 Complete Your Profile
Navigate to **Career Profile** from the sidebar. Fill in:

| Section | Purpose |
|---------|---------|
| **Summary** | Your professional elevator pitch |
| **Location** | Current city, country |
| **Experience** | Years of professional experience |
| **Target Role** | The job title you're targeting |
| **Remote Preference** | Remote only / Hybrid / On-site / Any |
| **Links** | LinkedIn, GitHub, Portfolio |

### 2.2 Add Education
Click **Education** tab → **Add Education**:
- Degree, Institution, Field of Study
- Start/End dates, Grade/GPA
- Relevant coursework or honors

### 2.3 Add Experience
Click **Experience** tab → **Add Experience**:
- Job Title, Company, Location
- Start/End dates (check "Current" if applicable)
- Description of responsibilities
- Key achievements (bullet points)

### 2.4 Add Skills
Click **Skills** tab → **Add Skill**:
- Skill name (e.g., "Python", "Project Management")
- Category (Programming, Framework, Soft Skill, etc.)
- Proficiency: Beginner / Intermediate / Advanced / Expert
- Years of experience

### 2.5 Add Certifications
Click **Certifications** tab → **Add Certification**:
- Name, Issuer, Issue/Expiry dates
- Credential ID and verification URL

---

## 3. Resume Studio

### 3.1 Create a Base Resume
1. Go to **Resume Studio** → **New Resume**
2. Choose **"Build from Profile"** to auto-populate from your career data
3. Or create manually with custom sections

### 3.2 Import Existing Resume
1. Click **Import** → Choose file (PDF, DOCX, TXT)
2. Review parsed sections
3. Edit any misparsed content

### 3.3 Resume Sections
Each resume has ordered sections:
- **Header**: Name, contact, links
- **Summary**: Professional summary
- **Experience**: Work history
- **Education**: Degrees
- **Skills**: Technical and soft skills
- **Certifications**: Certificates
- **Projects**: Portfolio projects (custom)
- **Custom**: Any additional sections

Drag to reorder, click to edit, use trash icon to delete.

### 3.4 ATS Analysis
1. Open a resume → Click **"ATS Analysis"**
2. Select a job from your saved jobs
3. Get detailed scoring:
   - **Overall Score** (0-100)
   - **Keyword Coverage** - How many job keywords appear
   - **Skill Alignment** - Required vs optional skills
   - **Experience Match** - Years and relevance
   - **Education Match** - Degree requirements
   - **Missing Keywords** - What to add

### 3.5 Tailor Resume for a Job
1. From ATS Analysis or Job Detail → Click **"Tailor Resume"**
2. System creates a new version optimized for that job
3. Review changes: added keywords, reordered skills, emphasized experience
4. Save as new version

### 3.6 Version History
- Every tailor creates a new version
- View all versions: **Resume → Versions**
- Compare versions, revert if needed

### 3.7 Export
- **Export as Text**: Plain text for copy-paste
- **Copy to Clipboard**: Quick sharing

---

## 4. Job Discovery

### 4.1 Search Jobs
Go to **Jobs** page. Use filters:

| Filter | Description |
|--------|-------------|
| **Keyword** | Search title, description, company |
| **City** | Specific location (e.g., "Lahore") |
| **Workplace** | Remote / On-site / Any |
| **Employment Type** | Full-time, Part-time, Contract, Internship |
| **Pakistan Eligibility** | Eligible / Not Eligible / Unknown |

### 4.2 Understanding Eligibility Badges
| Badge | Meaning |
|-------|---------|
| 🟢 **Pakistan Eligible** | Worldwide remote or explicitly accepts PK |
| 🔴 **Not Eligible** | Restricted to US/UK/CA/EU only |
| ⚪ **Unknown** | Insufficient information |

### 4.3 Job Cards
Each job shows:
- Title, Company, Location
- Remote/On-site badge
- Employment type
- Salary range (if available)
- Source label
- **Save** button (bookmark)
- **View Original** → Opens source website

### 4.4 Job Details
Click a job to see:
- Full description
- Requirements & Responsibilities
- Skills required
- **Match Score** (if profile complete)
- **Apply** → Creates CRM application
- **Save** → Bookmark for later

### 4.5 Run Discovery
Click **"Run Discovery"** to fetch latest jobs from all configured sources:
- Remote OK (international remote)
- Himalayas (international remote)
- Rozee.pk, Mustakbil, BrightSpyre (Pakistan)
- Government portals (FPSC, PPSC, NTS, etc.)

> **Note:** Some sources are unverified HTML parsers. Results may vary.

### 4.6 Discovery Status
Go to **Job Discovery** page to see:
- Source health (Active/Degraded/Failed)
- Last run time
- Jobs discovered per source
- Run history with stats

---

## 5. Job Matching

### 5.1 Match Feed
Go to **Job Matches** to see ranked jobs:
- **Overall Score** (0-100)
- **Breakdown**: Skills, Experience, Education, Location, Preferences, Semantic, Role
- **Matched Skills** / **Missing Skills**
- **Explanation** in plain English

### 5.2 Match Detail
Click a match for detailed breakdown:
- Side-by-side comparison
- Specific missing requirements
- Recommendations for improvement

### 5.3 How Matching Works
The engine evaluates 7 signals:

| Signal | Weight | What It Checks |
|--------|--------|----------------|
| **Skills** | 30% | Required/optional skill overlap |
| **Experience** | 15% | Years vs job requirement |
| **Education** | 10% | Degree level match |
| **Location** | 15% | City/province/remote preference |
| **Preferences** | 15% | Employment type, salary, sector |
| **Semantic** | 10% | Career Brain vector similarity |
| **Role/Title** | 5% | Title keyword overlap |

> **Note:** Missing data is treated neutrally (not penalized).

---

## 6. Career Brain (AI Assistant)

### 6.1 What It Does
Career Brain indexes your profile, experience, education, skills, and resumes to answer career questions with citations.

### 6.2 Setup
1. Go to **Career Brain** → Click **"Index My Career Data"**
2. Wait for indexing to complete
3. Now you can ask questions!

### 6.3 Ask Questions
Examples:
- *"What Python ML experience do I have?"*
- *"Which jobs match my profile best?"*
- *"What skills am I missing for a Senior DevOps role?"*
- *"Summarize my leadership experience"*

### 6.4 Understanding Answers
Each answer shows:
- **Answer** — AI-generated response
- **Sources** — Citations from your data
- **Confidence** — High / Medium / Low
- **Warning** — If AI unavailable or low context

> **Without Gemini API Key:** Shows retrieved context only (deterministic fallback).

---

## 7. Application CRM

### 7.1 Create Application
From **Job Detail** → Click **"Track Application"**:
- Auto-fills job title, company
- Set priority: Low / Medium / High / Urgent
- Add deadline, notes

### 7.2 Pipeline Stages
Drag applications through stages:
```
Saved → Ready to Apply → Applied → Screening → Interview → Technical Interview → Final Interview → Offer → Accepted
                                                                    ↘ Rejected (any stage)
                                                                    ↘ Withdrawn
                                                                    ↘ On Hold
```

### 7.3 Application Detail
Click an application to manage:
- **Timeline** — All activities, status changes
- **Interviews** — Schedule, prepare, record outcomes
- **Follow-ups** — Set reminders, mark complete
- **Documents** — Attach resume, cover letter
- **Contacts** — Link recruiters, hiring managers
- **Offers/Rejections** — Record details

### 7.4 Dashboard Analytics
Go to **CRM Dashboard** for:
- **Stats Cards**: Total, Active, Interviews, Offers, Response Rate
- **Pipeline** — Count per stage
- **Funnel** — Conversion rates between stages
- **Upcoming** — Interviews, follow-ups due

### 7.5 CRM Workspace
Go to **CRM Workspace** for:
- **Companies** — Track target companies
- **Contacts** — Manage recruiter relationships
- **Interviews** — Calendar view
- **Follow-ups** — All pending reminders

---

## 8. Settings

### 8.1 Job Preferences
Go to **Settings** → **Job Preferences**:
- Target roles
- Preferred cities/provinces
- Remote preference
- Employment types
- Experience level
- Minimum salary
- Sector preference

### 8.2 AI Configuration
- **Gemini API Key** — Enter for AI features
- **Model** — gemini-1.5-flash / gemini-1.5-pro
- **Temperature** — Creativity (0.0-1.0)

### 8.3 Notifications
- Email notifications (future)
- In-app reminders for follow-ups, interviews

### 8.4 Security
- Change password
- View active sessions
- Enable 2FA (future)

---

## 9. Tips & Best Practices

### 9.1 Profile Completeness
- **Complete profile = Better matches**
- Add at least: 5 skills, 2 experiences, 1 education
- Keep profile updated

### 9.2 Resume Strategy
- **Base resume**: Complete, well-structured
- **Tailored versions**: One per job application
- **ATS score > 80**: Good target
- **Update monthly**: Add new achievements

### 9.3 Job Search
- **Run discovery weekly** for fresh listings
- **Filter by Pakistan Eligibility** to avoid wasted applications
- **Save interesting jobs** before applying
- **Check match scores** before applying

### 9.4 Application Tracking
- **Create application immediately** when you apply
- **Set follow-up reminders** (3-5 business days)
- **Log all interviews** with prep notes
- **Record outcomes** for learning

### 9.4 Career Brain
- **Re-index after profile updates**
- **Ask specific questions** for better answers
- **Use citations** to verify information

---

## 10. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Global Search |
| `⌘/` | Help |
| `Esc` | Close modal/dropdown |
| `Tab` | Navigate form fields |

---

## 11. Troubleshooting

| Problem | Solution |
|---------|----------|
| No jobs found | Run discovery, check filters, verify eligibility |
| Low match scores | Complete profile, add more skills, tailor resume |
| Career Brain not answering | Add Gemini API key, re-index data |
| Resume import failed | Try TXT format, check file size < 10MB |
| Discovery fails | Check source health, some sources may be down |

---

## 12. Privacy & Data

- **Your data stays local** (SQLite) or on your PostgreSQL
- **No data shared** with third parties except configured APIs
- **Gemini API** only receives your query + relevant context
- **Delete account** from Settings → removes all data

---

## 13. Support

- **Documentation:** `docs/` folder
- **API Reference:** http://localhost:8000/docs
- **Issues:** https://github.com/zainCodeMaster/AI-Career/issues