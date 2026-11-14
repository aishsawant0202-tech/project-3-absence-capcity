# Project 3 – Absence & Capacity (Phase 1)

Starter scaffold for the Absence & Capacity Management project.

## Included
- FastAPI backend with `GET /health`
- React + TypeScript + Vite frontend
- PostgreSQL service through Docker Compose
- Environment variable example
- Basic `.gitignore`

## Prerequisites
- Git
- Python 3.11+
- Node.js 20+
- Docker Desktop

## 1. Start PostgreSQL

From the project root:

```powershell
docker compose up -d db
```

PostgreSQL is exposed locally on port `5432`.
Database: `absence_capacity`
Username: `app_user`
Password: `change_me_local`

These are local development credentials only. Change them before sharing or deploying.

## 2. Start the backend (Windows PowerShell)

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open:
- API health: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs

Expected health response:

```json
{
  "status": "ok",
  "service": "absence-capacity-api"
}
```

## 3. Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

## 4. Start everything with Docker (optional)

```powershell
docker compose up --build
```

The frontend is exposed on port `5173`, backend on `8000`, and PostgreSQL on `5432`.

## 5. Git initialisation

If the repository is not already a Git repository:

```powershell
git init
git add .
git commit -m "Initial Phase 1 project scaffold"
```

Suggested branch workflow:
- `main`: stable shared version
- `develop`: integration branch (if the team chooses to use one)
- `feature/<short-description>`: individual tasks

Before committing, ensure `.env` and local secrets are not staged.

## Phase 1 completion checklist

- [ ] All team members can clone the repository.
- [ ] PostgreSQL starts successfully.
- [ ] Backend starts and `/health` returns `status: ok`.
- [ ] Swagger UI opens.
- [ ] Frontend starts and displays the starter page.
- [ ] Each member can run the project locally.

## Next phase

Phase 2 will add the agreed database model, SQLAlchemy models, Alembic migrations, Pydantic schemas, and the first CRUD APIs. Do not add business logic to this Phase 1 scaffold yet.
