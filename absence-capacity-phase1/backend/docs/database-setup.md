# Database Setup Guide

## 1. Overview

The Absence & Capacity project uses:

- PostgreSQL 16 – Database server
- SQLAlchemy – Python ORM
- Alembic – Database schema migrations

Each team member runs their own local PostgreSQL database. All members use the same database schema through shared Alembic migrations.

## 2. Prerequisites

Install the following:

- Python 3.12 or compatible project-supported version
- PostgreSQL 16
- Git

## 3. Create the Database

Open pgAdmin and connect to your local PostgreSQL server.

1. Create a login role named `app_user` with a password of your choice.
2. Grant the role permission to create databases if needed.
3. Create a database named `absence_capacity`.
4. Set `app_user` as the database owner.

Do not share your PostgreSQL superuser credentials.

## 4. Configure Environment Variables

In the backend directory, copy `.env.example` and rename the copy to `.env`.

Configure the database connection:

```env
DATABASE_URL=postgresql+psycopg://app_user:YOUR_PASSWORD@localhost:5432/absence_capacity
```

Replace `YOUR_PASSWORD` with your own local PostgreSQL password.

Never commit `.env` to Git.

## 5. Install Python Dependencies

From the backend directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 6. Create Database Tables

Run the following command:

```powershell
python -m alembic upgrade head
```

Alembic automatically creates the database tables using the migrations in the shared repository.

The initial migration creates:

- `teams`
- `employees`
- `user_accounts`

No manual table creation is required.

## 7. Verify the Migration

Run:

```powershell
python -m alembic current
```

The latest migration should be displayed with `(head)`.

## 8. Updating the Database

Whenever a teammate adds or changes database models:

1. The responsible developer creates a new Alembic migration.
2. The migration is committed and pushed to the shared repository.
3. Other team members pull the latest changes.
4. Each member runs:

```powershell
python -m alembic upgrade head
```

This updates their local database schema.

## 9. Important Notes

- Every team member has an independent local database.
- All databases should use the same Alembic migration history.
- Database records are not automatically shared between team members.
- Do not manually modify the schema in pgAdmin.
- Do not commit `.env` or database passwords to Git.
- Use migrations for all future schema changes.