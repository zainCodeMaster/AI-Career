# CareerOS AI — Installation Guide

**Version:** 1.0  
**Date:** October 30, 2026

---

## 1. Prerequisites

### 1.1 System Requirements
| Component | Minimum Version |
|-----------|-----------------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Git | 2.30+ |
| SQLite | 3.35+ (dev) |
| PostgreSQL | 15+ (prod) |

### 1.2 Optional (for AI Features)
- **Google Gemini API Key** — Get from [Google AI Studio](https://aistudio.google.com/)

---

## 2. Quick Start (Development)

### 2.1 Clone Repository
```bash
git clone https://github.com/zainCodeMaster/AI-Career.git
cd AI-Career/careeros
```

### 2.2 Backend Setup

#### Option A: Automatic (Recommended)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

#### Option B: Manual
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m alembic upgrade head
cp .env.example .env  # Edit with your settings
python -m uvicorn app.main:app --reload --port 8000
```

**Verify:** Open http://localhost:8000/docs

### 2.3 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Verify:** Open http://localhost:5173

### 2.4 Environment Variables

Create `.env` in `backend/`:
```env
# Database
DATABASE_URL=sqlite:///./careeros.db

# JWT (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# AI Provider (Optional - for Career Brain AI answers)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Job Discovery
JOB_DISCOVERY_ENABLED=true
JOB_DISCOVERY_SCHEDULER_ENABLED=true
JOB_DISCOVERY_INTERVAL_MINUTES=60

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

---

## 3. Production Deployment

### 3.1 Database Setup (PostgreSQL + pgvector)

```bash
# Create database
sudo -u postgres createdb careeros
sudo -u postgres psql -d careeros -c "CREATE EXTENSION vector;"

# Run migrations
cd backend
DATABASE_URL=postgresql://user:pass@localhost/careeros python -m alembic upgrade head
```

### 3.2 Backend Production

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### 3.3 Frontend Production Build

```bash
cd frontend
npm run build
# Output in dist/
# Serve with nginx or any static file server
```

### 3.4 Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /var/www/careeros/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket for future real-time features
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3.5 Systemd Service (Backend)

```ini
# /etc/systemd/system/careeros-backend.service
[Unit]
Description=CareerOS Backend
After=network.target postgresql.service

[Service]
Type=exec
User=careeros
WorkingDirectory=/opt/careeros/backend
Environment=PATH=/opt/careeros/backend/.venv/bin
EnvironmentFile=/opt/careeros/backend/.env
ExecStart=/opt/careeros/backend/.venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable careeros-backend
sudo systemctl start careeros-backend
```

---

## 4. Docker Deployment (Optional)

### 4.1 Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 4.2 Dockerfile (Frontend)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: careeros
      POSTGRES_USER: careeros
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U careeros"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://careos:${DB_PASSWORD}@postgres/careos
      SECRET_KEY: ${SECRET_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      FRONTEND_URL: ${FRONTEND_URL}
    depends_on:
      postgres:
        condition: service_healthy
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]

volumes:
  postgres_data:
```

---

## 5. Configuration Reference

### 5.1 Backend Settings (`app/core/config.py`)

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `database_url` | `DATABASE_URL` | `sqlite:///./careeros.db` | Database connection |
| `secret_key` | `SECRET_KEY` | *required* | JWT signing key |
| `jwt_algorithm` | `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `access_token_expire_minutes` | `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `frontend_url` | `FRONTEND_URL` | `http://localhost:5173` | CORS origin |
| `gemini_api_key` | `GEMINI_API_KEY` | `None` | Google Gemini key |
| `gemini_model` | `GEMINI_MODEL` | `gemini-1.5-flash` | LLM model |
| `llm_provider` | `LLM_PROVIDER` | `auto` | auto/gemini/mock |

### 5.2 Frontend Environment

```bash
# .env (frontend)
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 6. Troubleshooting

### 6.1 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: bs4` | Run `pip install beautifulsoup4` |
| `sqlite3.OperationalError: no such column` | Run `python -m alembic upgrade head` |
| `CORS error` | Check `FRONTEND_URL` matches frontend origin |
| `GEMINI_API_KEY not working` | Verify key at https://aistudio.google.com/ |
| `Port 8000/5173 in use` | Change ports or kill existing processes |

### 6.2 Database Reset
```bash
cd backend
rm careeros.db  # SQLite only
python -m alembic upgrade head
```

### 6.3 Clear Frontend Cache
```bash
cd frontend
rm -rf node_modules dist .vite
npm install
npm run dev
```

---

## 7. Verification Checklist

After installation, verify:

- [ ] Backend health: `GET http://localhost:8000/health` → `{"status":"ok"}`
- [ ] Backend ready: `GET http://localhost:8000/ready` → `{"status":"ready"}`
- [ ] API docs: `GET http://localhost:8000/docs` → Swagger UI
- [ ] Frontend loads: `GET http://localhost:5173` → CareerOS login page
- [ ] Register → Login → Dashboard works
- [ ] Run job discovery → Jobs appear
- [ ] Career Brain index → Search works
- [ ] Resume upload → ATS analysis works

---

## 8. Updating

```bash
# Pull latest
git pull origin main

# Backend
cd backend
source .venv/bin/activate
pip install -e .[dev]
python -m alembic upgrade head

# Frontend
cd frontend
npm install
npm run build
```

---

## 9. Support

- **Issues:** https://github.com/zainCodeMaster/AI-Career/issues
- **Documentation:** See `docs/` folder
- **API Reference:** http://localhost:8000/docs (when running)