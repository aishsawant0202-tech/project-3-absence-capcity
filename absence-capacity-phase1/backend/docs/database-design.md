# Database Design – Employee & Team Management

**Project:** Absence & Capacity Management  
**Module:** Employee & Team Management  


## 1. Overview

This document defines the common database structure for the Employee & Team Management module.

The database uses PostgreSQL and SQLAlchemy ORM.

The initial design contains three main tables:

- TEAM
- EMPLOYEE
- USER_ACCOUNT

## 2. TEAM Table

| Field | Data type | Constraints | Description |
|---|---|---|---|
| id | Integer | Primary Key | Internal team ID |
| team_ref | String(50) | Unique, nullable | External team reference |
| name | String(100) | Not Null | Team name |
| description | Text | Nullable | Team description |
| min_required_fte | Numeric(5,2) | Not Null, Default 0 | Minimum required FTE |
| team_lead_employee_id | Integer | Foreign Key, Unique, nullable | Designated team lead |
| status | Enum | ACTIVE / INACTIVE | Team status |
| created_at | DateTime | Not Null | Creation timestamp |
| updated_at | DateTime | Not Null | Last update timestamp |

## 3. EMPLOYEE Table

| Field | Data type | Constraints | Description |
|---|---|---|---|
| id | Integer | Primary Key | Internal employee ID |
| employee_ref | String(50) | Unique, nullable | External employee reference |
| first_name | String(100) | Not Null | First name |
| last_name | String(100) | Not Null | Last name |
| email | String(255) | Unique, Not Null | Employee email |
| team_id | Integer | Foreign Key, Not Null | Assigned team |
| job_title | String(100) | Not Null | Job title |
| employment_type | Enum | PERMANENT / CONTRACT | Employment type |
| working_time_share | Numeric(5,2) | Not Null | FTE share (0.01–1.00) |
| start_date | Date | Not Null | Employment start date |
| end_date | Date | Nullable | Contract end date |
| status | Enum | ACTIVE / INACTIVE | Employee status |
| created_at | DateTime | Not Null | Creation timestamp |
| updated_at | DateTime | Not Null | Last update timestamp |

### Employee Business Rules

1. Permanent employees normally have no end date.
2. Contract employees must have an end date.
3. End date must not be earlier than start date.
4. Working time share must be greater than 0 and at most 1.
5. Expired contracts must not contribute to future capacity calculations.
6. Employee records must be retained for historical reporting.

## 4. USER_ACCOUNT Table

| Field | Data type | Constraints | Description |
|---|---|---|---|
| id | Integer | Primary Key | Internal account ID |
| employee_id | Integer | Foreign Key, Unique, Not Null | Linked employee |
| username | String(100) | Unique, Not Null | Login username |
| password_hash | String(255) | Not Null | Hashed password |
| system_role | Enum | EMPLOYEE / TEAM_LEAD / HR_ADMIN | User role |
| status | Enum | ACTIVE / INACTIVE / LOCKED | Account status |
| must_change_password | Boolean | Default False | Password change requirement |
| last_login_at | DateTime | Nullable | Last successful login |
| created_at | DateTime | Not Null | Creation timestamp |
| updated_at | DateTime | Not Null | Last update timestamp |

## 5. Entity Relationships

- One TEAM can contain multiple EMPLOYEEs.
- Each EMPLOYEE belongs to one TEAM at a time.
- Each EMPLOYEE can have zero or one USER_ACCOUNT.
- Each TEAM has at most one designated team lead.
- The designated team lead must belong to that same team.
- An employee can lead at most one team.

## 6. FTE-Based Capacity Rules

Capacity is measured using Full-Time Equivalent (FTE).

Examples:

| Working time share | FTE |
|---|---:|
| Full-time | 1.00 |
| 80% employment | 0.80 |
| Half-time | 0.50 |
| 25% employment | 0.25 |

**Available FTE** is calculated from eligible employees' working time shares, adjusted for approved absences and other capacity deductions.

The `min_required_fte` field represents the minimum FTE requirement of a team.

## 7. Enumerated Values

| Field | Allowed values |
|---|---|
| Team status | ACTIVE, INACTIVE |
| Employee status | ACTIVE, INACTIVE |
| Employment type | PERMANENT, CONTRACT |
| Account status | ACTIVE, INACTIVE, LOCKED |
| System role | EMPLOYEE, TEAM_LEAD, HR_ADMIN |

## 8. Database Constraints

- Primary keys for all three tables.
- Foreign keys between TEAM, EMPLOYEE and USER_ACCOUNT.
- Unique employee email.
- Unique external references when provided.
- Unique account username.
- Unique USER_ACCOUNT.employee_id.
- Unique TEAM.team_lead_employee_id.
- Non-negative minimum required FTE.
- Valid working time share.
- Valid employment date range.
- Team lead must belong to the team they lead.

## 9. Implementation Plan

1. Create SQLAlchemy models.
2. Configure entity relationships.
3. Set up Alembic migrations.
4. Generate the initial migration.
5. Test the migration against PostgreSQL.
6. Publish the database setup instructions for all team members.

**Status:** Initial design proposal – subject to team review.