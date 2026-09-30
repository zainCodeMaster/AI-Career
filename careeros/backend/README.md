# CareerOS Backend

This backend is the Phase 1 foundation for the CareerOS API. It provides FastAPI app startup, environment-driven configuration, SQLAlchemy database setup, and JWT-based user authentication.

## Activate the project virtual environment

From the repository root:

```powershell
cd C:\Users\LENOVO\Desktop\AI-Career\careeros
.\.venv\Scripts\Activate.ps1
```

## Start the FastAPI app

```powershell
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

You can also run the app directly:

```powershell
cd backend
python main.py
```

## Run tests

```powershell
cd C:\Users\LENOVO\Desktop\AI-Career\careeros\backend
..\.venv\Scripts\python.exe -m pytest -q
```

## Required environment variables

Create or update a root `.env` file in the repository, then set values such as:

```env
DATABASE_URL=sqlite:///./careeros.db
SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

Production or Supabase-backed setups should use a PostgreSQL URL such as:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/careeros_db
```

## Available Phase 1 endpoints

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

The API uses JWT Bearer tokens for authenticated requests.
