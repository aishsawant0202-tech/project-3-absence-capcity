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
python -m alembic upgrade head      # creates / updates the tables (run again after pulling new migrations)
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

### Troubleshooting: `ModuleNotFoundError: No module named 'app'`

Don't run `main.py` directly (`python app\main.py` or the editor's ▶ Run button). Python then looks for imports
inside `backend\app\` and can't find the `app` package. Start the app with **uvicorn** from the `backend` folder
instead:

```powershell
cd backend
uvicorn app.main:app --reload          # or: python -m uvicorn app.main:app --reload
```

uvicorn is the web server: it listens on port 8000 and passes each request to the FastAPI `app` object in
`app/main.py`. `--reload` restarts it when you save a file.

## 3. Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install          # again after pulling, when package.json changed
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

The frontend calls the backend through Vite's proxy: requests to `/api/...` are forwarded to
`http://localhost:8000` (see `frontend/vite.config.ts`), so the backend must be running too. In Docker Compose
the target is `http://backend:8000`, set with `API_PROXY_TARGET`.

**Demo login (temporary):** the bar at the top of the page chooses the role and employee id that are sent as
`X-Role` / `X-Employee-Id`. It will be replaced by Member 4's login.

## 4. API rules (all members)

- JSON fields are camelCase: `minRequiredFte`, `teamLeadEmployeeId`.
- Errors always look like `{"error": {"code": "FORBIDDEN", "message": "...", "details": {}}}`.
  In code: `raise ApiError(403, "FORBIDDEN", "Not allowed.")` (see `app/errors.py`).
- Codes: `VALIDATION_ERROR` 400 · `UNAUTHENTICATED` 401 · `FORBIDDEN` 403 · `NOT_FOUND` 404 · `TEAM_NAME_TAKEN` /
  `ALREADY_TEAM_LEAD` 409.
- Temporary login (until Member 4): headers `X-Role` (`EMPLOYEE` / `TEAM_LEAD` / `HR_ADMIN`) and `X-Employee-Id`.
  In Swagger they are the **x-role** / **x-employee-id** boxes, in the app the **Demo login** bar.
- UI rules for all screens: `docs/ui_design_guidelines.md`.

## 5. Check Team Management

**Who can do what**

| Action | Who |
|---|---|
| Create a team | `TEAM_LEAD` (becomes lead and member; one team per lead) |
| See the team list and team details | everyone |
| See a team's members | members of that team, `HR_ADMIN` (other members see names only) |
| Edit, deactivate / activate | the lead of that team only |

**1. Tests** – in `backend`: `pytest` → all pass.

**2. Test data** – pgAdmin, Query Tool:

```sql
INSERT INTO employees (first_name, last_name, email, job_title, employment_type, working_time_share, start_date, status)
VALUES ('Ada',  'Weber',   'ada@example.com',  'Manager',   'PERMANENT', 1.0, '2025-01-01', 'ACTIVE'),
       ('Ben',  'Klein',   'ben@example.com',  'Developer', 'PERMANENT', 0.8, '2025-01-01', 'ACTIVE'),
       ('Cara', 'Schmidt', 'cara@example.com', 'Tester',    'PERMANENT', 1.0, '2025-01-01', 'ACTIVE')
RETURNING id, first_name;
```

**3. In the app** (http://localhost:5173) – set the **Demo login** before each step:

| # | Demo login | Do | Expect |
|---|---|---|---|
| 1 | `TEAM_LEAD` / Ada | Create team `Development`, FTE `5` | Success message, team in the list |
| 2 | `TEAM_LEAD` / Ada | Create another team | "You already lead a team." |
| 3 | `TEAM_LEAD` / Cara | Create ` development ` | "A team with this name already exists." |
| 4 | – | pgAdmin: `UPDATE employees SET team_id = (SELECT id FROM teams WHERE name = 'Development') WHERE email = 'ben@example.com';` | Ben is a member |
| 5 | anyone | Search `DEV`, then `xyz` | Development only, then "No team matches" |
| 6 | `TEAM_LEAD` / Ada | Open Development | Members with details, **Edit** + **Deactivate** |
| 7 | `EMPLOYEE` / Ben | Open Development | Member names only, no buttons |
| 8 | `EMPLOYEE` / Cara | Open Development | "Only members of this team and HR Admin can see its members." |
| 9 | `TEAM_LEAD` / Ada | **Edit** → change description → **Save** | "Team … was updated." |
| 10 | `TEAM_LEAD` / Ada | **Deactivate** → OK, then **Activate** | Badge INACTIVE (grey), then ACTIVE (green) |
| 11 | anyone | Open `/teams/999` | "Team not found" |

**Start again:** `UPDATE employees SET team_id = NULL; DELETE FROM teams;`

**Tip:** 403 where you expected 409 → that employee id is not the lead of this team.

## 6. Start everything with Docker (optional)

```powershell
docker compose up --build
```

This builds and starts PostgreSQL, the backend and the frontend. The backend container runs
`alembic upgrade head` first, so the tables are created in the (new, empty) Docker database.

- Frontend: http://localhost:5173 · Swagger UI: http://localhost:8000/docs · PostgreSQL: port `5432`
- The first start takes a few minutes (downloads and `npm install`). Wait until the log shows
  `Uvicorn running on http://0.0.0.0:8000` and Vite's `Local: http://localhost:5173/`.
- The Docker database is **separate** from a PostgreSQL installed on Windows: add the test data (section 5.2)
  again, connecting pgAdmin to `localhost:5432` with user `app_user` / password `change_me_local`.
- **Stop the Windows PostgreSQL service first**, or both want port 5432 (`port is already allocated`).
- If a page does not open: `docker compose ps` shows which container is not running, and
  `docker compose logs backend` / `docker compose logs frontend` shows why.

## 7. Git initialisation

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
