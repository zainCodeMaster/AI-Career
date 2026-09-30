# CareerOS AI

## Autonomous AI Career & Job Operating System

CareerOS AI is a production-grade personal career operating system that intelligently discovers relevant job opportunities, evaluates applications, manages professional communication, improves career profiles, and continuously learns from outcomes.

This is **not** a chatbot demo, job scraper, or resume generator. It's a comprehensive career intelligence platform designed initially for personal use but architected for future SaaS scale.

---

## 🎯 Mission

Build an autonomous system that understands your complete career profile and continuously helps you:

- **Discover** relevant jobs from legitimate sources
- **Evaluate** opportunities against your career DNA
- **Prepare** tailored applications and interviews
- **Communicate** professionally via email and messaging
- **Improve** your professional presence and profiles
- **Learn** from application outcomes and market feedback
- **Plan** your career strategically based on data

---

## 🏗️ Project Status

**Current Phase**: Phase 6 - Resume Engine (Tailoring + ATS)

### Phase Timeline
- **Phase 0**: Architecture (✓ Complete)
- **Phase 1**: Foundation (React + FastAPI + Supabase) (✓ Complete)
- **Phase 2**: Career Profile (CRUD APIs) (✓ Complete)
- **Phase 3**: Career Brain (Embeddings + RAG) (✓ Complete)
- **Phase 4**: Job Discovery (Job sources) (✓ Complete)
- **Phase 5**: Job Matching (Scoring engine) (✓ Complete)
- **Phase 6**: Resume Engine (Tailoring + ATS) (✓ Complete)
- **Phase 7**: Application CRM (Tracking) (✓ Core Complete)
- **Phase 8**: Browser Agent (Playwright automation) (Pending)
- **Phase 9**: Career Email (Gmail + classification) (Pending)
- **Phase 10**: Interview Agent (Preparation) (Pending)
- **Phase 11**: GitHub + LinkedIn (Integration) (Pending)
- **Phase 12**: Portfolio + Content (Generation) (Pending)
- **Phase 13**: Project Video Studio (Media) (Pending)
- **Phase 14**: Skill Gap + Career Strategy (Analysis) (Pending)
- **Phase 15**: Analytics (Dashboards) (Pending)
- **Phase 16**: Production Hardening (Security + Deploy) (Pending)

---

## 💡 Core Concepts

### Career Brain
A persistent, RAG-enabled knowledge base that understands:
- Education, experience, skills (technical & soft)
- Projects, repositories, certifications
- Career goals, preferences, salary expectations
- Application history and outcomes

### Career DNA
A deep analysis of your professional profile:
- Skill classification (strong/proficient/developing/weak)
- Career track compatibility
- Market alignment
- Readiness assessment

### Job Radar
Continuous job discovery from legitimate sources:
- LinkedIn, Indeed, Google Jobs, company sites
- Remote boards, startup boards, internship platforms
- Normalized into universal job schema
- Deduplicated across sources
- Scored against your profile

### Application Intelligence
Autonomous but human-controlled workflow:
- Job-specific resume tailoring
- ATS compatibility analysis
- Intelligent form filling
- Application tracking
- Outcome analysis

### Career Email Agent
Classification, linking, and response:
- Recruiter outreach detection
- Interview invitation extraction
- Application linking
- Intelligent reply drafting
- Human approval required

---

## 🛠️ Technology Stack

### Frontend
- React + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- TanStack Query (data fetching)

### Backend
- FastAPI (Python web framework)
- Pydantic (validation)
- SQLAlchemy (ORM)
- Alembic (migrations available)
- Uvicorn (ASGI server)

### Database
- SQLite (development/testing)
- PostgreSQL (production, via DATABASE_URL)
- pgvector (embeddings, production only)

### Auth & Security
- Custom JWT authentication (python-jose)
- bcrypt password hashing
- CORS middleware

### Background Jobs
- APScheduler (lightweight scheduling)

### Testing
- Pytest (backend)
- TestClient (API integration tests)

---

## 📁 Project Structure

```
careeros/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   ├── core/             # Configuration, logging, security
│   │   ├── db/               # Database connection, models
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── repositories/     # Data access layer
│   │   ├── services/         # Business logic
│   │   ├── agents/           # LangGraph agents
│   │   ├── tools/            # AI tools and utilities
│   │   ├── integrations/     # External service integrations
│   │   ├── workers/          # Background job definitions
│   │   ├── security/         # Auth, permissions, validation
│   │   └── utils/            # Helper functions
│   ├── migrations/           # Alembic database migrations
│   ├── tests/                # Pytest test suite
│   ├── main.py               # FastAPI application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── pyproject.toml        # Project metadata
│   └── .pylintrc             # Python linting config
│
├── frontend/
│   ├── src/
│   │   ├── app/              # Main app component
│   │   ├── components/       # Reusable UI components
│   │   ├── features/         # Feature modules
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utilities and helpers
│   │   ├── services/         # API client services
│   │   ├── stores/           # Zustand stores
│   │   ├── types/            # TypeScript type definitions
│   │   ├── routes/           # Route definitions
│   │   └── main.tsx          # React entry point
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   ├── tsconfig.json         # TypeScript config
│   ├── vite.config.ts        # Vite config
│   ├── tailwind.config.js    # Tailwind config
│   ├── .prettierrc            # Code formatting
│   ├── .eslintrc.json        # Linting rules
│   └── vitest.config.ts      # Testing config
│
├── docs/                     # Project documentation
│   ├── ARCHITECTURE.md       # System design and diagrams
│   ├── API.md                # API documentation
│   ├── DATABASE.md           # Database schema design
│   ├── AGENTS.md             # Agent definitions
│   ├── TOOLS.md              # Tool registry
│   ├── SECURITY.md           # Security guidelines
│   ├── TESTING.md            # Testing strategy
│   ├── DEPLOYMENT.md         # Deployment guide
│   └── INTEGRATIONS.md       # External integrations
│
├── .github/
│   └── workflows/            # CI/CD pipeline definitions
│
├── .env.example              # Environment template
├── .gitignore                # Git ignore patterns
├── README.md                 # This file
├── ARCHITECTURE.md           # High-level architecture
├── CONTRIBUTING.md           # Contribution guidelines
└── LICENSE                   # MIT License

```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (via Supabase)
- Redis (optional, for background jobs)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd careeros
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp ../.env.example ../.env
   # Edit .env with your configuration
   uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Database Setup**
   - Create a Supabase project
   - Set `DATABASE_URL` in .env
   - Run migrations: `alembic upgrade head`

---

## 📋 Core Principles

1. **Inspect before modifying** - Understand existing code
2. **Never blindly overwrite** - Preserve working functionality
3. **Treat external data as untrusted** - Job descriptions, emails are untrusted
4. **No fabrication** - Never invent career information
5. **Human approval for consequential actions** - Applications, emails, offers
6. **Respect source policies** - No CAPTCHA bypass, anti-bot defeat, scraping abuse
7. **Strong typing** - TypeScript, Pydantic everywhere
8. **Observable and auditable** - Structured logging, audit trails
9. **Modular architecture** - Easy to test, replace, extend
10. **Production-ready from day one** - Security, error handling, testing

---

## 🔐 Security

This project handles sensitive career information and interacts with external systems.

**Key Security Principles**:
- Never expose API keys, OAuth secrets, or database credentials
- User isolation: No cross-user data access
- Prompt injection defense: Treat external content as untrusted
- Audit logging: Record important actions
- Rate limiting: Prevent API abuse
- CORS: Restrict frontend origin access
- Secrets management: .env files are gitignored

See [SECURITY.md](docs/SECURITY.md) for detailed security guidelines.

---

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design, data flow, diagrams
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development workflow, code standards
- **[DATABASE.md](docs/DATABASE.md)** - Schema design, migrations
- **[API.md](docs/API.md)** - API endpoints, request/response formats
- **[AGENTS.md](docs/AGENTS.md)** - AI agent definitions and capabilities
- **[TOOLS.md](docs/TOOLS.md)** - Tool registry and security levels
- **[TESTING.md](docs/TESTING.md)** - Testing strategy and examples
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide

---

## 🧪 Testing

CareerOS maintains comprehensive test coverage:

- **Backend**: Pytest with unit, integration, and E2E tests
- **Frontend**: Vitest + React Testing Library
- **Browser Automation**: Playwright integration tests
- **AI**: Golden test cases, factuality validation, prompt injection tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd ../frontend
npm test

# E2E tests
npm run test:e2e
```

---

## 🤝 Contributing

We welcome contributions that align with CareerOS principles.

1. Review [CONTRIBUTING.md](CONTRIBUTING.md)
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow project conventions (see docs/)
4. Write tests for all features
5. Ensure all tests pass
6. Submit a pull request

---

## 📊 Current Capabilities

**Phase 6 (Resume Engine)**:
- ✓ Resume CRUD with versioning
- ✓ Resume sections management
- ✓ Resume import from text
- ✓ ATS compatibility analysis
- ✓ Resume tailoring for specific jobs
- ✓ Phase 5 match integration
- ✓ Multi-user isolation
- ✓ Prompt injection protection
- ✓ Factuality guarantees

**Phase 5 (Job Matching)**:
- ✓ Career Profile aggregation
- ✓ Match scoring engine
- ✓ Skill gap analysis
- ✓ Job requirement extraction

**Phase 4 (Job Discovery)**:
- ✓ Multi-source job discovery
- ✓ Job normalization and deduplication
- ✓ Saved jobs and preferences

**Phase 3 (Career Brain)**:
- ✓ RAG-enabled knowledge base
- ✓ Career evidence retrieval

**Phase 2 (Career Profile)**:
- ✓ Profile CRUD
- ✓ Skills management
- ✓ Work experience tracking
- ✓ Education tracking
- ✓ Certification tracking

**Phase 1 (Foundation)**:
- ✓ React + FastAPI
- ✓ Authentication
- ✓ Database connection
- ✓ API structure

---

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Supabase Documentation](https://supabase.com/docs)
- [Playwright Documentation](https://playwright.dev/)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👤 Author

Built as a production-grade career AI system.

---

## 🤖 AI Assistance

This project was architected with consideration for AI-assisted development while maintaining strict security and factuality principles.

---

**Ready to build the future of AI-powered career intelligence.**
