# API Contracts – Absence & Capacity

## 1. Overview

This document defines the REST API contracts for the Absence & Capacity application.

It establishes common endpoint URLs, HTTP methods, request structures, response structures, validation rules and error handling.

### 1.1 Technology Stack

- Backend: Python FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Database migrations: Alembic
- API format: REST with JSON

### 1.2 API Conventions

- Base URL: `/api`
- Request and response format: JSON
- Primary identifier: `id` (integer)
- Date format: `YYYY-MM-DD`
- Date-time format: ISO 8601
- Field names: `snake_case`
- HTTP status codes follow REST conventions.

### 1.3 Common HTTP Status Codes

| Status | Meaning |
|---|---|
| 200 | Request successful |
| 201 | Resource created |
| 204 | Request successful, no response body |
| 400 | Invalid request |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Resource conflict |
| 422 | Validation error |
| 500 | Internal server error |

---

## 2. Team API Contracts

**Responsible implementation:** Member 2

### 2.1 Team Business Rules

1. Every team must have a unique name.
2. Team-name uniqueness is case-insensitive and ignores leading/trailing whitespace.
3. `min_required_fte` must be greater than or equal to zero.
4. New teams are created with `ACTIVE` status.
5. A team can be deactivated instead of permanently deleted.
6. A team can have at most one designated team lead.
7. Team lead must be an employee assigned to that team.
8. Team capacity is measured in FTE.

### 2.2 Team Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/teams` | Create a team |
| GET | `/api/teams` | Retrieve all teams |
| GET | `/api/teams/{team_id}` | Retrieve a team by ID |
| PUT | `/api/teams/{team_id}` | Update team details |
| PATCH | `/api/teams/{team_id}/status` | Activate/deactivate a team |
| PATCH | `/api/teams/{team_id}/lead` | Assign/change team lead |
| GET | `/api/teams/{team_id}/capacity` | Retrieve team capacity summary |

### 2.3 Create a Team

**Endpoint:** `POST /api/teams`

**Purpose:** Creates a new team in the system.

**Request Body:**

```json
{
  "name": "Development",
  "description": "Software development team",
  "min_required_fte": 5.0
}
```

**Field details:**

| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Unique team name |
| description | string | No | Description of the team |
| min_required_fte | number | Yes | Minimum required team capacity in FTE |

**Successful Response: `201 Created`**

```json
{
  "id": 1,
  "team_ref": null,
  "name": "Development",
  "description": "Software development team",
  "min_required_fte": 5.0,
  "team_lead_employee_id": null,
  "status": "ACTIVE"
}
```

**Validation Rules:**

1. `name` is mandatory and cannot be blank.
2. Leading and trailing whitespace must be removed from the name.
3. Team names must be unique, ignoring case.
4. `min_required_fte` must be greater than or equal to zero.
5. `description` is optional.
6. The system automatically generates the team ID.
7. The team status defaults to `ACTIVE`.
8. `team_lead_employee_id` defaults to `null`.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 409 Conflict | Team name already exists | `{"detail": "A team with this name already exists."}` |
| 422 Unprocessable Entity | Missing name or invalid FTE | FastAPI validation error |



### 2.4 Retrieve All Teams

**Endpoint:** `GET /api/teams`

**Purpose:** Retrieves all teams from the system.

**Request Parameters:** None required.

**Successful Response: `200 OK`**

```json
[
  {
    "id": 1,
    "team_ref": null,
    "name": "Development",
    "description": "Software development team",
    "min_required_fte": 5.0,
    "team_lead_employee_id": 3,
    "status": "ACTIVE"
  },
  {
    "id": 2,
    "team_ref": null,
    "name": "Quality Assurance",
    "description": "Testing and quality team",
    "min_required_fte": 3.0,
    "team_lead_employee_id": null,
    "status": "ACTIVE"
  }
]
```

**Response Fields:**

| Field | Type | Description |
|---|---|---|
| id | integer | Unique team ID |
| name | string | Team name |
| description | string/null | Team description |
| min_required_fte | number | Minimum required FTE |
| team_lead_employee_id | integer/null | Assigned team lead employee ID |
| status | string | ACTIVE or INACTIVE |

**Business Rules:**

1. Return all teams, including active and inactive teams.
2. Return an empty array (`[]`) if no teams exist.
3. Do not include employee details in this response; use the dedicated employee endpoints when needed.

**Error Responses:**

| Status | Condition |
|---|---|
| 500 Internal Server Error | Unexpected server-side error |


### 2.5 Retrieve a Team by ID

**Endpoint:** `GET /api/teams/{team_id}`

**Purpose:** Retrieves the details of a specific team using its unique ID.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| team_id | integer | Yes | Unique ID of the team |

**Example Request:**

```http
GET /api/teams/1
```

**Successful Response: `200 OK`**

```json
{
  "id": 1,
  "team_ref": null,
  "name": "Development",
  "description": "Software development team",
  "min_required_fte": 5.0,
  "team_lead_employee_id": 3,
  "status": "ACTIVE"
}
```

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | No team exists with the given ID | `{"detail": "Team not found."}` |
| 422 Unprocessable Entity | Invalid team ID format | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

**Business Rules:**

1. The system must verify that the requested team exists.
2. Return only the requested team's details.
3. Inactive teams can also be retrieved.

### 2.6 Update a Team

**Endpoint:** `PUT /api/teams/{team_id}`

**Purpose:** Updates the details of an existing team.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| team_id | integer | Yes | Unique ID of the team to update |

**Request Body:**

```json
{
  "name": "Software Development",
  "description": "Application development team",
  "min_required_fte": 6.0
}
```

**Field Details:**

| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Updated team name |
| description | string or null | Yes | Updated team description; use null to clear the existing description |
| min_required_fte | number | Yes | Updated minimum required FTE |

**Successful Response: `200 OK`**

```json
{
  "id": 1,
  "team_ref": null,
  "name": "Software Development",
  "description": "Application development team",
  "min_required_fte": 6.0,
  "team_lead_employee_id": 3,
  "status": "ACTIVE"
}
```

**Validation Rules:**

1. The team must exist before updating.
2. The team name cannot be blank.
3. Team names must remain unique, ignoring case and leading/trailing whitespace.
4. `min_required_fte` must be greater than or equal to zero.
5. The existing team status and assigned team lead must remain unchanged.
6. The system must automatically update the `updated_at` timestamp.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Team does not exist | `{"detail": "Team not found."}` |
| 409 Conflict | Another team already uses the requested name | `{"detail": "A team with this name already exists."}` |
| 422 Unprocessable Entity | Invalid request data | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

### 2.7 Activate or Deactivate a Team

**Endpoint:** `PATCH /api/teams/{team_id}/status`

**Purpose:** Changes the status of an existing team without permanently deleting it.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| team_id | integer | Yes | Unique ID of the team |

**Request Body:**

```json
{
  "status": "INACTIVE"
}
```

Allowed values: `ACTIVE`, `INACTIVE`.

**Successful Response: `200 OK`**

```json
{
  "id": 1,
  "name": "Development",
  "status": "INACTIVE"
}
```

**Validation Rules:**

1. The team must exist.
2. Only `ACTIVE` and `INACTIVE` are accepted.
3. Deactivation must not permanently delete the team or its associated records.
4. An inactive team cannot be assigned new employees or receive new operational assignments.
5. Reactivating a team changes its status back to `ACTIVE`.
6. The system automatically updates the `updated_at` timestamp.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Team does not exist | `{"detail": "Team not found."}` |
| 422 Unprocessable Entity | Invalid status value | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

### 2.8 Assign or Change Team Lead

**Endpoint:** `PATCH /api/teams/{team_id}/lead`

**Purpose:** Assigns a team lead to a team or changes/removes the existing team lead.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| team_id | integer | Yes | Unique ID of the team |

**Request Body:**

```json id="k4sh8f"
{
  "team_lead_employee_id": 3
}
```

To remove the current team lead:

```json id="f2d4mj"
{
  "team_lead_employee_id": null
}
```

**Successful Response: `200 OK`**

```json id="kz4p9a"
{
  "id": 1,
  "name": "Development",
  "team_lead_employee_id": 3,
  "status": "ACTIVE"
}
```

**Validation Rules:**

1. The team must exist and be active.
2. The employee must exist and have `ACTIVE` status.
3. The employee must belong to the same team.
4. An employee cannot lead more than one team.
5. A team can have only one designated team lead.
6. The team lead can be removed by setting `team_lead_employee_id` to `null`.
7. The system automatically updates the `updated_at` timestamp.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Team or employee does not exist | `{"detail": "Team or employee not found."}` |
| 409 Conflict | Employee already leads another team | `{"detail": "Employee is already assigned as another team's lead."}` |
| 422 Unprocessable Entity | Employee is inactive or belongs to another team | Validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

### 2.9 Retrieve Team Capacity Summary

**Endpoint:** `GET /api/teams/{team_id}/capacity`

**Purpose:** Retrieves the current capacity summary of a specific team, measured in Full-Time Equivalents (FTE).

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| team_id | integer | Yes | Unique ID of the team |

**Successful Response: `200 OK`**

```json
{
  "team_id": 1,
  "team_name": "Development",
  "min_required_fte": 5.0,
  "assigned_fte": 4.0,
  "capacity_gap_fte": -1.0,
  "active_employee_count": 5
}
```

**Response Fields:**

| Field | Type | Description |
|---|---|---|
| team_id | integer | Unique team ID |
| team_name | string | Team name |
| min_required_fte | number | Minimum required team capacity |
| assigned_fte | number | Total assigned FTE of eligible employees |
| capacity_gap_fte | number | Assigned FTE minus minimum required FTE |
| active_employee_count | integer | Number of eligible active employees |

**Calculation Rules:**

1. Capacity is measured in FTE, not simply employee headcount.
2. `assigned_fte` is calculated by summing the `working_time_share` of eligible active employees assigned to the team.
3. Employees with inactive status are excluded.
4. Employees whose contract end date is in the past are excluded.
5. `capacity_gap_fte` = `assigned_fte` - `min_required_fte`.
6. A negative capacity gap indicates a shortage; zero indicates sufficient capacity; a positive value indicates capacity above the minimum requirement.
7. If no eligible employees exist, `assigned_fte` and `active_employee_count` are both zero.
8. Employees whose `start_date` is in the future are excluded from the current capacity calculation.
9. An employee with an `end_date` equal to today is still counted; employees with an `end_date` before today are excluded.

**Scope Limitation:**

This is the initial capacity summary. It does not yet account for approved absences, training blocks or external experts. These can be incorporated in a later capacity calculation.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Team does not exist | `{"detail": "Team not found."}` |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

---

## 3. Employee API Contracts

**Responsible implementation:** Member 3

### 3.1 Employee Business Rules

1. An employee may exist without being assigned to a team. In this case, `team_id` is `null`.
2. An employee can belong to only one team at a time.
3. An employee may be assigned only to an existing active team.
4. Employee email addresses must be unique.
5. `working_time_share` represents the employee's FTE share and must be greater than `0` and less than or equal to `1`.
6. `employment_type` must be `PERMANENT` or `CONTRACT`.
7. A permanent employee normally has `end_date` set to `null`.
8. A contract employee must have an `end_date`, and it cannot be earlier than `start_date`.
9. Deactivating an employee must not permanently delete the employee or associated records.
10. Employees whose contracts have expired remain in the system but are excluded from current capacity calculations.

### 3.2 Employee Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/employees` | Create an employee |
| GET | `/api/employees` | Retrieve all employees |
| GET | `/api/employees/{employee_id}` | Retrieve an employee by ID |
| PUT | `/api/employees/{employee_id}` | Update employee details |
| PATCH | `/api/employees/{employee_id}/status` | Activate/deactivate an employee |
| GET | `/api/employees/{employee_id}/team` | Retrieve the employee's team assignment |

### 3.3 Create an Employee

**Endpoint:** `POST /api/employees`

**Purpose:** Creates a new employee. The employee may be created without a team assignment.

**Request Body:**

```json
{
  "employee_ref": null,
  "first_name": "Alex",
  "last_name": "Miller",
  "email": "alex.miller@example.com",
  "team_id": 1,
  "job_title": "Software Engineer",
  "employment_type": "PERMANENT",
  "working_time_share": 1.0,
  "start_date": "2026-11-01",
  "end_date": null
}
```

To create an employee without a team, set `"team_id": null`.

**Field Details:**

| Field | Type | Required | Description |
|---|---|---|---|
| employee_ref | string or null | No | Optional external/business reference |
| first_name | string | Yes | Employee's first name |
| last_name | string | Yes | Employee's last name |
| email | string | Yes | Unique employee email address |
| team_id | integer or null | No | Assigned team; null if not yet assigned |
| job_title | string or null | No | Employee's job title |
| employment_type | string | Yes | PERMANENT or CONTRACT |
| working_time_share | number | Yes | FTE share, greater than 0 and at most 1 |
| start_date | date | Yes | Employment start date |
| end_date | date or null | Conditional | Required for CONTRACT; normally null for PERMANENT |

**Successful Response: `201 Created`**

```json
{
  "id": 1,
  "employee_ref": null,
  "first_name": "Alex",
  "last_name": "Miller",
  "email": "alex.miller@example.com",
  "team_id": 1,
  "job_title": "Software Engineer",
  "employment_type": "PERMANENT",
  "working_time_share": 1.0,
  "start_date": "2026-11-01",
  "end_date": null,
  "status": "ACTIVE"
}
```

**Validation Rules:**

1. `first_name`, `last_name` and `email` are mandatory and cannot be blank.
2. The email address must be unique.
3. If `team_id` is provided, the team must exist and have `ACTIVE` status.
4. `employment_type` must be `PERMANENT` or `CONTRACT`.
5. `working_time_share` must be greater than `0` and less than or equal to `1`.
6. `start_date` is mandatory.
7. For `CONTRACT`, `end_date` is mandatory and must not be earlier than `start_date`.
8. For `PERMANENT`, `end_date` should be `null`.
9. The employee ID is generated by the system.
10. The employee status defaults to `ACTIVE`.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Supplied team ID does not exist | `{"detail": "Team not found."}` |
| 409 Conflict | Email address or employee reference already exists | `{"detail": "An employee with this email already exists."}` |
| 422 Unprocessable Entity | Invalid employment type, FTE share or dates | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

### 3.4 Retrieve All Employees

**Endpoint:** `GET /api/employees`

**Purpose:** Retrieves employees from the system.

**Optional Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| team_id | integer | No | Return employees assigned to the specified team |
| status | string | No | Filter by ACTIVE or INACTIVE |

**Example Request:**

```http
GET /api/employees?team_id=1&status=ACTIVE
```

**Successful Response: `200 OK`**

```json
[
  {
    "id": 1,
    "employee_ref": null,
    "first_name": "Alex",
    "last_name": "Miller",
    "email": "alex.miller@example.com",
    "team_id": 1,
    "job_title": "Software Engineer",
    "employment_type": "PERMANENT",
    "working_time_share": 1.0,
    "start_date": "2026-11-01",
    "end_date": null,
    "status": "ACTIVE"
  },
  {
    "id": 2,
    "employee_ref": null,
    "first_name": "Sam",
    "last_name": "Taylor",
    "email": "sam.taylor@example.com",
    "team_id": null,
    "job_title": "QA Engineer",
    "employment_type": "CONTRACT",
    "working_time_share": 0.5,
    "start_date": "2026-10-01",
    "end_date": "2027-03-31",
    "status": "ACTIVE"
  }
]
```

**Business Rules:**

1. Without query parameters, return all employees, including active and inactive employees.
2. Employees without a team assignment must also be included unless a `team_id` filter is supplied.
3. If no employees match the filters, return an empty array (`[]`).
4. The `status` filter accepts only `ACTIVE` or `INACTIVE`.

**Error Responses:**

| Status | Condition |
|---|---|
| 422 Unprocessable Entity | Invalid query parameter |
| 500 Internal Server Error | Unexpected server-side error |

### 3.5 Retrieve an Employee by ID

**Endpoint:** `GET /api/employees/{employee_id}`

**Purpose:** Retrieves the details of a specific employee using the employee ID.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| employee_id | integer | Yes | Unique employee ID |

**Example Request:**

```http
GET /api/employees/1
```

**Successful Response: `200 OK`**

```json
{
  "id": 1,
  "employee_ref": null,
  "first_name": "Alex",
  "last_name": "Miller",
  "email": "alex.miller@example.com",
  "team_id": 1,
  "job_title": "Software Engineer",
  "employment_type": "PERMANENT",
  "working_time_share": 1.0,
  "start_date": "2026-11-01",
  "end_date": null,
  "status": "ACTIVE"
}
```

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Employee does not exist | `{"detail": "Employee not found."}` |
| 422 Unprocessable Entity | Invalid employee ID format | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

**Business Rules:**

1. The system must verify that the employee exists.
2. Inactive employees can also be retrieved.
3. The response includes `team_id`, which is `null` when the employee is not assigned to a team.

### 3.6 Update an Employee

**Endpoint:** `PUT /api/employees/{employee_id}`

**Purpose:** Updates the details of an existing employee.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| employee_id | integer | Yes | Unique employee ID |

**Request Body:**

```json
{
  "employee_ref": null,
  "first_name": "Alex",
  "last_name": "Miller",
  "email": "alex.miller@example.com",
  "team_id": 2,
  "job_title": "Senior Software Engineer",
  "employment_type": "PERMANENT",
  "working_time_share": 0.8,
  "start_date": "2026-11-01",
  "end_date": null
}
```

**Field Details:** The request uses the same fields and validation rules as employee creation. All editable fields must be supplied. `team_id` may be `null` to remove the employee's team assignment.

**Successful Response: `200 OK`**

```json
{
  "id": 1,
  "employee_ref": null,
  "first_name": "Alex",
  "last_name": "Miller",
  "email": "alex.miller@example.com",
  "team_id": 2,
  "job_title": "Senior Software Engineer",
  "employment_type": "PERMANENT",
  "working_time_share": 0.8,
  "start_date": "2026-11-01",
  "end_date": null,
  "status": "ACTIVE"
}
```

**Validation Rules:**

1. The employee must exist.
2. All editable fields must satisfy the employee creation validation rules.
3. If `team_id` is provided, the team must exist and be active.
4. Setting `team_id` to `null` removes the employee's team assignment.
5. The employee's existing status must remain unchanged.
6. The system automatically updates the `updated_at` timestamp.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Employee or supplied team does not exist | `{"detail": "Employee or team not found."}` |
| 409 Conflict | Email or employee reference is already used by another employee | `{"detail": "An employee with this email already exists."}` |
| 422 Unprocessable Entity | Invalid request data | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

### 3.7 Activate or Deactivate an Employee

**Endpoint:** `PATCH /api/employees/{employee_id}/status`

**Purpose:** Changes an employee's status without permanently deleting the employee.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| employee_id | integer | Yes | Unique employee ID |

**Request Body:**

```json
{
  "status": "INACTIVE"
}
```

Allowed values: `ACTIVE`, `INACTIVE`.

**Successful Response: `200 OK`**

```json
{
  "id": 1,
  "first_name": "Alex",
  "last_name": "Miller",
  "status": "INACTIVE"
}
```

**Validation Rules:**

1. The employee must exist.
2. Only `ACTIVE` and `INACTIVE` are accepted.
3. Deactivation must not permanently delete the employee or associated records.
4. Inactive employees must be excluded from current team capacity calculations.
5. Reactivating an employee changes the status back to `ACTIVE`.
6. The system automatically updates the `updated_at` timestamp.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Employee does not exist | `{"detail": "Employee not found."}` |
| 422 Unprocessable Entity | Invalid status value | FastAPI validation error |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

### 3.8 Retrieve an Employee's Team

**Endpoint:** `GET /api/employees/{employee_id}/team`

**Purpose:** Retrieves the team assigned to a specific employee.

**Path Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| employee_id | integer | Yes | Unique employee ID |

**Example Request:**

```http
GET /api/employees/1/team
```

**Successful Response when the employee has a team: `200 OK`**

```json
{
  "employee_id": 1,
  "team": {
    "id": 1,
    "team_ref": null,
    "name": "Development",
    "description": "Software development team",
    "status": "ACTIVE"
  }
}
```

**Successful Response when the employee has no team: `200 OK`**

```json
{
  "employee_id": 1,
  "team": null
}
```

**Business Rules:**

1. The employee must exist.
2. If the employee has a team assignment, return the assigned team's details.
3. If the employee is not assigned to a team, return `team: null`.
4. An inactive employee's existing team assignment can still be retrieved.

**Error Responses:**

| Status | Condition | Example response |
|---|---|---|
| 404 Not Found | Employee does not exist | `{"detail": "Employee not found."}` |
| 500 Internal Server Error | Unexpected server-side error | Generic server error |

