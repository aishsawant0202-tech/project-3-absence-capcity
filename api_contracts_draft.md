# Project 3 -- Absence & Capacity

## API Contract Specification

**Version:** 0.1 -- Draft for Sprint 1\
**API base path:** `/api/v1`\
**Backend:** Python + FastAPI\
**Frontend:** React + TypeScript\
**Database:** PostgreSQL\
**API style:** REST over HTTPS, JSON request and response bodies

> **Status:** This document is a proposed API contract for group
> discussion. Internal endpoints are proposed for Project 3. Cross-group
> integration endpoints and payloads must be confirmed with the owning
> project groups before implementation.

------------------------------------------------------------------------

## 1. Purpose and scope

Project 3 manages employee absences and team capacity. It supports three
main roles:

-   **Employee:** submits and tracks absence requests, views leave
    entitlement and may propose a substitute.
-   **Team Lead:** reviews requests, monitors team capacity and
    organises coverage.
-   **HR Administrator:** maintains leave entitlements and absence
    rules, and handles corrections.

The system consumes information from:

-   **G2 -- Onboarding:** newly registered employees.
-   **G1 -- Recruiting:** planned hires and expected start dates.
-   **G4 -- Learning & Development:** booked training periods.
-   **G6 -- External Recruiting:** planned external experts.

The system provides information to:

-   **G1 -- Recruiting:** capacity gaps and potential hiring needs.
-   **G6 -- External Recruiting:** requests for external experts.
-   **G5 -- People Analytics:** pseudonymised absence and capacity
    reporting data.

Project 3 also provides an absence calendar.

## 2. Technology and API conventions

  -----------------------------------------------------------------------
  Concern                             Proposed convention
  ----------------------------------- -----------------------------------
  API style                           REST

  Data format                         JSON

  Versioning                          `/api/v1`

  Identifiers                         UUIDs internally; external source
                                      IDs retained for integrations

  Dates                               `YYYY-MM-DD`

  Timestamps                          ISO 8601 UTC,
                                      e.g. `2026-11-02T12:00:00Z`

  Authentication                      Bearer token (JWT)

  Authorisation                       Role-based access control and
                                      team-level permissions

  Documentation                       OpenAPI / FastAPI Swagger UI

  Pagination                          `page` and `page_size` for
                                      collection endpoints

  Content type                        `application/json`
  -----------------------------------------------------------------------

### 2.1 Roles and access

-   `EMPLOYEE`
-   `TEAM_LEAD`
-   `HR_ADMIN`
-   `SYSTEM_INTEGRATION` (for authenticated service-to-service calls)

Access must be checked on the server. Hiding a frontend button is not
sufficient authorisation.

### 2.2 Common HTTP status codes

  -----------------------------------------------------------------------------
  Status                        Meaning                 Typical use
  ----------------------------- ----------------------- -----------------------
  `200 OK`                      Successful request      Retrieve or update a
                                                        resource

  `201 Created`                 Resource created        Submit an absence
                                                        request

  `204 No Content`              Successful operation    Cancel a request
                                without response body   

  `400 Bad Request`             Invalid request syntax  Malformed input
                                or parameters           

  `401 Unauthorized`            Missing or invalid      Invalid token
                                authentication          

  `403 Forbidden`               Authenticated user      Employee attempts
                                lacks permission        HR-only action

  `404 Not Found`               Resource not found      Unknown absence ID

  `409 Conflict`                Conflicting state or    Duplicate integration
                                duplicate               event

  `422 Unprocessable Entity`    Data is syntactically   End date before start
                                valid but fails         date
                                validation/business     
                                rules                   

  `500 Internal Server Error`   Unexpected server error Unhandled server-side
                                                        failure
  -----------------------------------------------------------------------------

### 2.3 Standard error response

``` json
{
  "error": {
    "code": "INSUFFICIENT_LEAVE_BALANCE",
    "message": "The employee does not have sufficient leave entitlement.",
    "details": {
      "requested_days": 5,
      "remaining_days": 3
    }
  }
}
```

Error `code` values should be stable and suitable for frontend handling.
The `message` is intended for display or logging; sensitive information
must not be exposed.

------------------------------------------------------------------------

## 3. Internal API contracts

These endpoints are used by Project 3's own frontend and backend.

### 3.1 Employee management

  ------------------------------------------------------------------------------------
  Method            Endpoint                       Description       Access
  ----------------- ------------------------------ ----------------- -----------------
  `GET`             `/employees/me`                Get the           Employee
                                                   authenticated     
                                                   employee's        
                                                   details           

  `GET`             `/employees/{employee_id}`     Get employee      HR Admin;
                                                   details           authorised Team
                                                                     Lead

  `GET`             `/teams/{team_id}/employees`   List members of a Team Lead; HR
                                                   team              Admin
  ------------------------------------------------------------------------------------

Example response -- `GET /api/v1/employees/me`:

``` json
{
  "employee_id": "EMP-101",
  "first_name": "Alex",
  "last_name": "Miller",
  "team_id": "TEAM-01",
  "department_id": "DEPT-01",
  "employment_start_date": "2026-12-01",
  "employment_status": "ACTIVE"
}
```

The example uses readable IDs for illustration. The implementation
should use UUIDs or a consistent identifier strategy.

### 3.2 Absence management

  ---------------------------------------------------------------------------------------
  Method            Endpoint                          Description       Access
  ----------------- --------------------------------- ----------------- -----------------
  `POST`            `/absences`                       Submit an absence Employee
                                                      request           

  `GET`             `/absences/me`                    List the          Employee
                                                      authenticated     
                                                      employee's        
                                                      requests          

  `GET`             `/absences/{absence_id}`          Retrieve an       Owner; authorised
                                                      absence request   Team Lead; HR
                                                                        Admin

  `PATCH`           `/absences/{absence_id}/cancel`   Cancel an         Owner; HR Admin
                                                      eligible request  where permitted

  `GET`             `/teams/{team_id}/absences`       Retrieve the team Team members;
                                                      absence calendar  Team Lead; HR
                                                                        Admin, subject to
                                                                        field-level
                                                                        visibility
  ---------------------------------------------------------------------------------------

#### Submit an absence request

`POST /api/v1/absences`

Request:

``` json
{
  "absence_type": "VACATION",
  "start_date": "2026-12-10",
  "end_date": "2026-12-12",
  "substitute_employee_id": "EMP-102",
  "reason": "Personal vacation"
}
```

Response -- `201 Created`:

``` json
{
  "absence_id": "ABS-101",
  "employee_id": "EMP-101",
  "absence_type": "VACATION",
  "start_date": "2026-12-10",
  "end_date": "2026-12-12",
  "status": "PENDING",
  "substitute_employee_id": "EMP-102",
  "created_at": "2026-11-02T12:00:00Z"
}
```

Proposed absence types:

-   `VACATION`
-   `SICK_LEAVE`
-   `PERSONAL_LEAVE`
-   `SPECIAL_LEAVE`
-   `UNPAID_LEAVE`

Proposed absence statuses:

-   `PENDING`
-   `APPROVED`
-   `REJECTED`
-   `CANCELLED`

The final list of absence types and which types require approval must be
agreed with the HR/business rules.

#### Cancel an absence request

`PATCH /api/v1/absences/{absence_id}/cancel`

Request:

``` json
{
  "cancellation_reason": "Change of plans"
}
```

Successful response: `204 No Content`.

The backend must enforce cancellation rules, for example whether a
request is still pending or whether an approved absence can be cancelled
under the configured policy.

#### Team absence calendar

`GET /api/v1/teams/{team_id}/absences?start_date=2026-12-01&end_date=2026-12-31`

Example response for an ordinary colleague:

``` json
{
  "team_id": "TEAM-01",
  "entries": [
    {
      "employee_id": "EMP-101",
      "display_name": "Alex Miller",
      "start_date": "2026-12-10",
      "end_date": "2026-12-12",
      "availability": "ABSENT"
    }
  ]
}
```

**Privacy requirement:** Ordinary colleagues must see only that a
colleague is `ABSENT`; they must not see the reason or sensitive absence
category. The API should return different fields depending on the
caller's permissions. Do not rely on frontend filtering to protect this
information.

### 3.3 Entitlement and absence-rule management

  -------------------------------------------------------------------------------------
  Method            Endpoint                        Description       Access
  ----------------- ------------------------------- ----------------- -----------------
  `GET`             `/entitlements/me`              View own          Employee
                                                    entitlement       

  `GET`             `/entitlements/{employee_id}`   View an           HR Admin
                                                    employee's        
                                                    entitlement       

  `POST`            `/entitlements`                 Create an         HR Admin
                                                    entitlement       
                                                    record            

  `PATCH`           `/entitlements/{employee_id}`   Correct an        HR Admin
                                                    entitlement       
                                                    record            

  `GET`             `/absence-rules`                List absence      HR Admin
                                                    rules             

  `POST`            `/absence-rules`                Create an absence HR Admin
                                                    rule              

  `PATCH`           `/absence-rules/{rule_id}`      Update an absence HR Admin
                                                    rule              

  `GET`             `/carry-over/deadlines`         Retrieve          HR Admin
                                                    carry-over        
                                                    deadlines         
  -------------------------------------------------------------------------------------

Example response -- `GET /api/v1/entitlements/me`:

``` json
{
  "employee_id": "EMP-101",
  "year": 2026,
  "annual_entitlement": 30,
  "used_days": 12,
  "pending_days": 3,
  "remaining_days": 15,
  "carry_over_days": 2
}
```

The exact definition of `remaining_days` must be agreed. Recommended
interpretation: `remaining_days` is the official balance after approved
leave; `pending_days` is shown separately and does not reduce the
official balance until approval. The UI may also show a provisional
balance after pending requests.

### 3.4 Approval management

  -----------------------------------------------------------------------------------------
  Method            Endpoint                            Description       Access
  ----------------- ----------------------------------- ----------------- -----------------
  `GET`             `/approvals/pending`                List pending      Team Lead
                                                        requests assigned 
                                                        to the Team Lead  

  `PATCH`           `/absences/{absence_id}/decision`   Approve or reject Authorised Team
                                                        a request         Lead
  -----------------------------------------------------------------------------------------

Approve request:

`PATCH /api/v1/absences/ABS-101/decision`

``` json
{
  "decision": "APPROVED",
  "comment": "Approved. Team capacity is sufficient."
}
```

Reject request:

``` json
{
  "decision": "REJECTED",
  "comment": "Insufficient team capacity during this period."
}
```

Example response:

``` json
{
  "absence_id": "ABS-101",
  "status": "APPROVED",
  "approved_by": "EMP-201",
  "decision_date": "2026-11-03T10:00:00Z"
}
```

The backend should validate the request's current status, the
decision-maker's team permissions, applicable absence rules and
entitlement. Capacity should be shown to the Team Lead as part of the
decision process. The business rules must specify whether insufficient
capacity blocks approval or merely raises a warning.

### 3.5 Capacity management

Capacity is measured as **headcount**, not working hours or FTE.

  ------------------------------------------------------------------------------------------------
  Method            Endpoint                                   Description       Access
  ----------------- ------------------------------------------ ----------------- -----------------
  `GET`             `/teams/{team_id}/capacity`                Calculate         Team Lead; HR
                                                               capacity over a   Admin
                                                               date range        

  `GET`             `/teams/{team_id}/capacity-gaps`           Retrieve staffing Team Lead; HR
                                                               gaps              Admin

  `POST`            `/teams/{team_id}/capacity-requirements`   Define required   Authorised Team
                                                               headcount for a   Lead; HR Admin
                                                               period            
  ------------------------------------------------------------------------------------------------

Example request:

`GET /api/v1/teams/TEAM-01/capacity?start_date=2027-01-10&end_date=2027-01-12`

Example response:

``` json
{
  "team_id": "TEAM-01",
  "period_start": "2027-01-10",
  "period_end": "2027-01-12",
  "daily_capacity": [
    {
      "date": "2027-01-10",
      "active_employees": 10,
      "absent_employees": 2,
      "training_employees": 1,
      "available_employees": 7,
      "required_employees": 8,
      "capacity_gap": 1,
      "status": "WARNING"
    },
    {
      "date": "2027-01-11",
      "active_employees": 10,
      "absent_employees": 1,
      "training_employees": 1,
      "available_employees": 8,
      "required_employees": 8,
      "capacity_gap": 0,
      "status": "SUFFICIENT"
    }
  ]
}
```

The response contains two illustrative days; the actual API should
return one record for each date in the requested range.

Recommended calculation:

`available_employees = active_employees - unavailable_employees`

`capacity_gap = max(0, required_employees - available_employees)`

For the MVP, `unavailable_employees` is the number of unique employees
who are unavailable on that date because of an approved absence or
booked training. An employee who is both absent and booked for training
must be counted only once.

Proposed status values:

-   `SUFFICIENT`: available headcount meets or exceeds the requirement.
-   `WARNING`: available headcount is below the requirement.
-   `CRITICAL`: available headcount is below a separately configured
    minimum staffing threshold.

The minimum threshold and whether `WARNING` and `CRITICAL` are both
needed should be agreed by the group.

#### Create a capacity requirement

`POST /api/v1/teams/TEAM-01/capacity-requirements`

``` json
{
  "period_start": "2027-01-10",
  "period_end": "2027-01-20",
  "required_employees": 8
}
```

Example response:

``` json
{
  "requirement_id": "REQ-CAP-101",
  "team_id": "TEAM-01",
  "period_start": "2027-01-10",
  "period_end": "2027-01-20",
  "required_employees": 8
}
```

#### Important forecast distinction

The live capacity calculation and the future forecast should be
distinguished:

-   **Current/confirmed availability:** active employees minus approved
    absences and booked training.
-   **Forecast availability:** current/confirmed availability plus hires
    whose start dates have arrived and external experts whose
    engagements are confirmed and active.

Planned hires should not be counted as available before their actual
start date. External experts should be shown separately or clearly
identified in the forecast so that the team does not confuse employees
with external capacity.

### 3.6 Coverage management

  -----------------------------------------------------------------------------------------
  Method            Endpoint                            Description       Access
  ----------------- ----------------------------------- ----------------- -----------------
  `POST`            `/coverage-plans`                   Create a coverage Team Lead
                                                        plan              

  `GET`             `/coverage-plans/{plan_id}`         Retrieve a        Team Lead
                                                        coverage plan     

  `GET`             `/teams/{team_id}/coverage-plans`   List coverage     Team Lead
                                                        plans for a team  
  -----------------------------------------------------------------------------------------

Example request -- `POST /api/v1/coverage-plans`:

``` json
{
  "team_id": "TEAM-01",
  "absence_id": "ABS-101",
  "substitute_employee_id": "EMP-102",
  "start_date": "2026-12-10",
  "end_date": "2026-12-12",
  "notes": "Substitute will handle the assigned tasks."
}
```

Example response:

``` json
{
  "coverage_plan_id": "COV-101",
  "team_id": "TEAM-01",
  "absence_id": "ABS-101",
  "substitute_employee_id": "EMP-102",
  "start_date": "2026-12-10",
  "end_date": "2026-12-12",
  "status": "PLANNED"
}
```

The system should check that the substitute belongs to an eligible team
and is not already unavailable during the coverage period.

------------------------------------------------------------------------

## 4. External integration contracts

The following integration endpoints are proposed for discussion. For
incoming integrations, Project 3 exposes the receiving endpoint. For
outgoing integrations, the destination endpoint is owned by the
receiving project group and must be confirmed with that group.

### 4.1 Incoming integrations -- data consumed by Project 3

  -----------------------------------------------------------------------------------------------
  Source                  Data                    Proposed Project 3 endpoint
  ----------------------- ----------------------- -----------------------------------------------
  G2 -- Onboarding        New employees and       `POST /api/v1/integrations/employees`
                          relevant start          
                          information             

  G1 -- Recruiting        Planned hires and       `POST /api/v1/integrations/planned-hires`
                          expected start dates    

  G4 -- Learning &        Booked training periods `POST /api/v1/integrations/training-bookings`
  Development                                     

  G6 -- External          Planned/confirmed       `POST /api/v1/integrations/external-experts`
  Recruiting              external experts        
  -----------------------------------------------------------------------------------------------

#### G2 → G3: new employee

`POST /api/v1/integrations/employees`

``` json
{
  "source_record_id": "ONB-101",
  "employee_id": "EMP-101",
  "department_id": "DEPT-01",
  "team_id": "TEAM-01",
  "start_date": "2026-12-01",
  "annual_leave_days": 30
}
```

#### G1 → G3: planned hire

`POST /api/v1/integrations/planned-hires`

``` json
{
  "source_record_id": "PH-101",
  "department_id": "DEPT-01",
  "team_id": "TEAM-01",
  "expected_start_date": "2027-01-15",
  "status": "PLANNED"
}
```

#### G4 → G3: booked training

`POST /api/v1/integrations/training-bookings`

``` json
{
  "source_record_id": "TR-501",
  "employee_id": "EMP-101",
  "course_id": "COURSE-10",
  "start_date": "2026-12-10",
  "end_date": "2026-12-11",
  "status": "BOOKED"
}
```

#### G6 → G3: external expert engagement

`POST /api/v1/integrations/external-experts`

``` json
{
  "source_record_id": "EXT-301",
  "expert_id": "EXPERT-101",
  "team_id": "TEAM-01",
  "start_date": "2026-12-01",
  "end_date": "2027-03-31",
  "status": "CONFIRMED"
}
```

For every incoming integration, the groups must agree on the source of
truth, identifier format, update/cancellation process and status values.
The `source_record_id` is an illustrative field intended to support
matching and duplicate prevention.

### 4.2 Outgoing integrations -- data provided by Project 3

  ---------------------------------------------------------------------------------------------
  Destination             Data provided           Proposed destination endpoint
  ----------------------- ----------------------- ---------------------------------------------
  G1 -- Recruiting        Capacity gaps / hiring  `POST /api/v1/integrations/capacity-gaps`
                          needs                   

  G6 -- External          Requests for external   `POST /api/v1/integrations/expert-requests`
  Recruiting              experts                 

  G5 -- People Analytics  Pseudonymised           `POST /api/v1/integrations/absence-events`
                          absence/capacity events 
  ---------------------------------------------------------------------------------------------

These are **example destination paths**, not endpoints that Project 3
can unilaterally define. The receiving group must confirm its actual
endpoint and schema.

#### G3 → G1: capacity gap

``` json
{
  "gap_id": "GAP-201",
  "team_id": "TEAM-01",
  "period_start": "2027-01-10",
  "period_end": "2027-01-20",
  "required_employees": 8,
  "available_employees": 6,
  "capacity_gap": 2,
  "reason": "INSUFFICIENT_TEAM_CAPACITY"
}
```

#### G3 → G6: external expert request

``` json
{
  "request_id": "EXT-REQ-301",
  "gap_id": "GAP-201",
  "team_id": "TEAM-01",
  "period_start": "2027-01-10",
  "period_end": "2027-01-20",
  "required_experts": 2,
  "required_skills": ["NETWORK_ENGINEERING"]
}
```

#### G3 → G5: People Analytics event

``` json
{
  "event_id": "EVT-501",
  "event_type": "ABSENCE_APPROVED",
  "pseudonymous_employee_id": "PSEUDO-101",
  "team_id": "TEAM-01",
  "absence_category": "PLANNED_LEAVE",
  "duration_days": 3,
  "event_date": "2026-11-02"
}
```

People Analytics should receive only the data required for its reporting
purpose. Do not send employee names, free-text absence reasons or
unnecessary personal information. Pseudonymisation is not the same as
anonymisation; access and retention must still be controlled.

------------------------------------------------------------------------

## 5. Integration behaviour and reliability

The following points should be agreed between groups before integration
implementation:

1.  **Ownership:** Each group owns and documents its own API. Project 3
    owns its incoming integration endpoints; destination groups own
    their receiving endpoints.
2.  **Authentication:** Use an agreed service-to-service authentication
    mechanism. Do not expose integration endpoints without
    authentication.
3.  **Duplicate prevention:** Use a stable source record ID or event ID.
    Repeated delivery of the same event should not create duplicate
    records.
4.  **Updates:** Agree whether changes are sent as `POST` upserts,
    `PUT`/`PATCH` updates, or separate event types.
5.  **Cancellations:** Define how cancelled hires, training bookings and
    expert engagements are communicated.
6.  **Failures:** Agree retry behaviour and how failed deliveries are
    logged or reported.
7.  **Versioning:** Coordinate breaking schema changes rather than
    silently changing payload fields.
8.  **Data minimisation:** Exchange only the fields needed by the
    receiving group.

For a small semester project, synchronous REST/JSON calls are sufficient
unless the groups jointly choose an event-based approach.

------------------------------------------------------------------------

## 6. Validation and business rules

The backend should enforce at least the following rules:

1.  `end_date` must be on or after `start_date`.
2.  An employee can submit an absence request only for themselves,
    unless an authorised administrative workflow explicitly allows
    otherwise.
3.  A Team Lead can review only requests within their authorised team.
4.  Only a request in an eligible state can be approved, rejected or
    cancelled.
5.  Leave entitlement must be checked according to the configured
    absence rules.
6.  Capacity calculations must include approved absences and booked
    training.
7.  The same employee must not be counted twice as unavailable on the
    same day.
8.  Cancelled training bookings and cancelled external engagements must
    no longer affect forecast capacity.
9.  A planned hire must not count as active before the applicable start
    date.
10. An external expert must be included only for a confirmed, active
    engagement period.
11. The team calendar must hide absence reasons and sensitive absence
    categories from ordinary colleagues.
12. Approval decisions and HR corrections should be auditable.

The group must still decide whether capacity shortages block an absence
approval or produce a warning for the Team Lead.

------------------------------------------------------------------------

## 7. Consolidated endpoint checklist

All paths below are relative to `/api/v1`.

### Internal APIs

  Module             Method   Endpoint
  ------------------ -------- ------------------------------------------
  Employee           GET      `/employees/me`
  Employee           GET      `/employees/{employee_id}`
  Employee           GET      `/teams/{team_id}/employees`
  Absence            POST     `/absences`
  Absence            GET      `/absences/me`
  Absence            GET      `/absences/{absence_id}`
  Absence            PATCH    `/absences/{absence_id}/cancel`
  Absence calendar   GET      `/teams/{team_id}/absences`
  Entitlement        GET      `/entitlements/me`
  Entitlement        GET      `/entitlements/{employee_id}`
  Entitlement        POST     `/entitlements`
  Entitlement        PATCH    `/entitlements/{employee_id}`
  Rules              GET      `/absence-rules`
  Rules              POST     `/absence-rules`
  Rules              PATCH    `/absence-rules/{rule_id}`
  Carry-over         GET      `/carry-over/deadlines`
  Approval           GET      `/approvals/pending`
  Approval           PATCH    `/absences/{absence_id}/decision`
  Capacity           GET      `/teams/{team_id}/capacity`
  Capacity           GET      `/teams/{team_id}/capacity-gaps`
  Capacity           POST     `/teams/{team_id}/capacity-requirements`
  Coverage           POST     `/coverage-plans`
  Coverage           GET      `/coverage-plans/{plan_id}`
  Coverage           GET      `/teams/{team_id}/coverage-plans`

### Incoming integration APIs exposed by Project 3

  -----------------------------------------------------------------------------------
  Source group            Method                  Endpoint
  ----------------------- ----------------------- -----------------------------------
  G2 -- Onboarding        POST                    `/integrations/employees`

  G1 -- Recruiting        POST                    `/integrations/planned-hires`

  G4 -- Learning &        POST                    `/integrations/training-bookings`
  Development                                     

  G6 -- External          POST                    `/integrations/external-experts`
  Recruiting                                      
  -----------------------------------------------------------------------------------

### Outgoing integrations to be agreed with receiving groups

  Destination group           Proposed method   Proposed destination endpoint
  --------------------------- ----------------- ---------------------------------
  G1 -- Recruiting            POST              `/integrations/capacity-gaps`
  G6 -- External Recruiting   POST              `/integrations/expert-requests`
  G5 -- People Analytics      POST              `/integrations/absence-events`

------------------------------------------------------------------------

## 8. Suggested implementation structure

``` text
project-3-absence-capacity/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── employees.py
│   │   │   ├── absences.py
│   │   │   ├── approvals.py
│   │   │   ├── entitlements.py
│   │   │   ├── capacity.py
│   │   │   ├── coverage.py
│   │   │   └── integrations.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│
├── docs/
│   ├── api-contracts.md
│   ├── database-design.md
│   └── integration-contracts.md
│
├── docker-compose.yml
└── README.md
```

This is a suggested structure; it can be adjusted to match the group's
repository and agreed framework conventions.

------------------------------------------------------------------------

## 9. Sprint 1 completion checklist

-   [ ] Review internal endpoints with all four group members.
-   [ ] Agree request and response fields, enums and validation rules.
-   [ ] Confirm role permissions and calendar privacy behaviour.
-   [ ] Contact G1, G2, G4, G5 and G6 to agree integration ownership and
    schemas.
-   [ ] Agree how external records are updated and cancelled.
-   [ ] Align the API entities with the database model.
-   [ ] Document the agreed API using OpenAPI.
-   [ ] Create example requests and responses for Postman testing.
-   [ ] Record unresolved decisions rather than treating draft examples
    as final.

## 10. Open decisions before implementation

  -----------------------------------------------------------------------
  Decision                Suggested starting      Status
                          point                   
  ----------------------- ----------------------- -----------------------
  Capacity unit           Headcount per team per  Agreed by group/user
                          day                     

  Capacity shortage       Warning shown to Team   Open
  handling                Lead; approval policy   
                          to be agreed            

  Absence types and rules HR-configurable list    Open

  Calendar privacy        Colleagues see only     Required
                          `ABSENT`                

  External integration    Agree with counterpart  Open
  paths and schemas       groups                  

  Integration             Stable source IDs and   Open
  update/cancellation     explicit status updates 
  mechanism                                       

  Authentication between  Agreed                  Open
  groups                  service-to-service      
                          mechanism               

  Minimum staffing        Team-configured value   Open
  threshold               if `CRITICAL` status is 
                          used                    
  -----------------------------------------------------------------------

------------------------------------------------------------------------

**Document note:** This specification is a Sprint 1 draft. It should be
updated after the group has agreed the internal API design and
coordinated the cross-group contracts. The example IDs and payload
values are illustrative, not production data.
