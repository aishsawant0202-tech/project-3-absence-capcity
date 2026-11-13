# Project 3 – Absence & Capacity · API Contracts

**Version:** 0.2 – based on the team requirements and data model (Req.pdf, Meeting 1, 31.10.2026)
**Replaces:** `api_contracts_draft.md` v0.1
**Base path:** `/api/v1` · REST · JSON · Python FastAPI · PostgreSQL

> **Status: proposal for team review.** All rules marked **(A)** are *assumptions* taken from the
> "Our assumption (to confirm)" column of Req.pdf. They must be confirmed with the customer.
> Items marked **(OPEN)** are not decided yet. Cross-group payloads must be agreed with the
> owning group before implementation.

---

## 1. Conventions

| Concern | Rule |
|---|---|
| IDs | Integer IDs (data model PKs are `int`). Cross-group calls never use our internal IDs; they use the shared IDs below. |
| Shared person ID | `externalRef` = employee ID owned by **G2 Onboarding** (e.g. `"G2-5531"`) (A) |
| Shared team ID | `teamId` – the same team IDs must be used by all groups (OPEN: agree list with G1, G2, G6) |
| Field names | camelCase, identical to the data model (`startDate`, `teamId`, `workingDays` …) |
| Dates | `YYYY-MM-DD` (inclusive ranges: `endDate` is the last day) |
| Timestamps | ISO 8601 UTC, e.g. `2026-11-20T10:00:00Z` |
| Working days | Mon–Fri, minus public holidays of **Hesse** (A); half days allowed (A) |
| Auth (users) | Bearer token. Demo login by role selection (A: no real login needed) |
| Auth (groups) | Header `X-API-Key: <key per group>` → role `SYSTEM` |
| Docs | FastAPI generates `/docs` (Swagger) and `/openapi.json` from this contract |

### 1.1 Roles

| Role | Can do |
|---|---|
| `EMPLOYEE` | Request / cancel own absences, see own entitlement, see team calendar (masked) |
| `TEAM_LEAD` | Everything an employee can + approve/reject own team's requests, see team capacity, confirm capacity gaps |
| `HR_ADMIN` | Maintain entitlements, absence types, carry-over rule, blackout periods; approve requests of Team Leads (A); read audit log |
| `SYSTEM` | Other groups calling our integration endpoints |

All permissions are checked **in the backend**. Hiding a button in the frontend is not security.

### 1.2 Error format

```json
{
  "error": {
    "code": "INSUFFICIENT_ENTITLEMENT",
    "message": "Not enough leave days left.",
    "details": { "requestedDays": 5, "availableDays": 3 }
  }
}
```

| HTTP | `code` | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Wrong JSON, missing field, `endDate` before `startDate` |
| 401 | `UNAUTHENTICATED` | Missing/invalid token or API key |
| 403 | `FORBIDDEN` | Role not allowed (e.g. employee calls HR endpoint) |
| 404 | `NOT_FOUND` | Unknown ID |
| 409 | `OVERLAPPING_ABSENCE` | Employee already has a REQUESTED/APPROVED absence in this period |
| 409 | `INVALID_STATUS` | e.g. approving a request that is already CANCELLED |
| 422 | `INSUFFICIENT_ENTITLEMENT` | Not enough remaining days (only for types that deduct) |
| 422 | `BLACKOUT_PERIOD` | Period hits a blackout with `mode = BLOCK` |
| 422 | `NO_WORKING_DAYS` | Period contains only weekends/holidays |
| 422 | `CANCEL_NOT_ALLOWED` | Cancelling an approved absence that has already started |
| 422 | `INVALID_SUBSTITUTE` | Substitute is the requester or not in the same team |

---

## 2. Endpoint overview

| Module | Method | Path | Roles |
|---|---|---|---|
| System | GET | `/health` | public |
| Auth | POST | `/auth/demo-login` | public (demo only) |
| Teams | GET | `/teams` | all users |
| Teams | GET | `/teams/{teamId}` | all users |
| Teams | PATCH | `/teams/{teamId}` | HR_ADMIN, TEAM_LEAD of this team |
| Teams | GET | `/teams/{teamId}/employees` | members of team, HR_ADMIN |
| Employees | GET | `/employees/me` | all users |
| Employees | GET | `/employees/{employeeId}` | HR_ADMIN, TEAM_LEAD of the employee |
| Absence types | GET | `/absence-types` | all users |
| Absence types | POST | `/admin/absence-types` | HR_ADMIN |
| Absence types | PATCH | `/admin/absence-types/{typeId}` | HR_ADMIN |
| Absences | POST | `/absences` | EMPLOYEE, TEAM_LEAD |
| Absences | POST | `/absences/preview` | EMPLOYEE, TEAM_LEAD |
| Absences | GET | `/absences/me` | all users |
| Absences | GET | `/absences/{absenceId}` | owner, deciding TEAM_LEAD, HR_ADMIN |
| Absences | POST | `/absences/{absenceId}/cancel` | owner, HR_ADMIN |
| Approvals | GET | `/approvals/pending` | TEAM_LEAD, HR_ADMIN |
| Approvals | GET | `/absences/{absenceId}/capacity-impact` | TEAM_LEAD, HR_ADMIN |
| Approvals | POST | `/absences/{absenceId}/approve` | TEAM_LEAD of team, HR_ADMIN for Team Leads |
| Approvals | POST | `/absences/{absenceId}/reject` | same as approve |
| Entitlements | GET | `/employees/me/entitlements` | all users |
| Entitlements | GET | `/employees/{employeeId}/entitlements` | HR_ADMIN, TEAM_LEAD of employee |
| Entitlements | POST | `/admin/entitlements` | HR_ADMIN |
| Entitlements | PATCH | `/admin/entitlements/{entitlementId}` | HR_ADMIN |
| Entitlements | POST | `/admin/entitlements/carry-over` | HR_ADMIN |
| Absence rule | GET | `/admin/absence-rule` | HR_ADMIN |
| Absence rule | PUT | `/admin/absence-rule` | HR_ADMIN |
| Blackouts | GET | `/blackout-periods` | all users |
| Blackouts | POST | `/admin/blackout-periods` | HR_ADMIN |
| Blackouts | PATCH | `/admin/blackout-periods/{id}` | HR_ADMIN |
| Blackouts | DELETE | `/admin/blackout-periods/{id}` | HR_ADMIN |
| Calendar | GET | `/teams/{teamId}/calendar` | members of team, HR_ADMIN |
| Calendar | GET | `/employees/me/calendar.ics` | all users |
| Capacity | GET | `/teams/{teamId}/capacity` | TEAM_LEAD of team, HR_ADMIN |
| Capacity gaps | GET | `/teams/{teamId}/capacity-gaps` | TEAM_LEAD of team, HR_ADMIN |
| Capacity gaps | POST | `/capacity-gaps/{gapId}/request` | TEAM_LEAD of team |
| Capacity gaps | POST | `/capacity-gaps/{gapId}/resolve` | TEAM_LEAD of team, HR_ADMIN |
| Audit | GET | `/admin/audit-log` | HR_ADMIN |
| Integration in | PUT | `/integrations/employees/{externalRef}` | SYSTEM (G2) |
| Integration in | PUT | `/integrations/planned-hires/{sourceRef}` | SYSTEM (G1) |
| Integration in | DELETE | `/integrations/planned-hires/{sourceRef}` | SYSTEM (G1) |
| Integration in | PUT | `/integrations/trainings/{sourceRef}` | SYSTEM (G4) |
| Integration in | DELETE | `/integrations/trainings/{sourceRef}` | SYSTEM (G4) |
| Integration in | PUT | `/integrations/external-experts/{sourceRef}` | SYSTEM (G6) |
| Integration in | DELETE | `/integrations/external-experts/{sourceRef}` | SYSTEM (G6) |

Outgoing calls to G1, G6 and G5 are described in section 12.

---

## 3. System and demo login

### `GET /health`
```json
{ "status": "ok", "database": "ok", "version": "0.2.0" }
```

### `POST /auth/demo-login`
Simple role selection for the demo (A). The frontend shows a list of demo users; the user picks one.

Request:
```json
{ "employeeId": 102 }
```
Response `200`:
```json
{
  "accessToken": "eyJhbGciOi...",
  "tokenType": "Bearer",
  "employee": { "id": 102, "name": "Rahul Sharma", "role": "EMPLOYEE", "teamId": 10 }
}
```
All further calls send `Authorization: Bearer <accessToken>`.

---

## 4. Teams and employees

### `GET /teams/{teamId}`
```json
{
  "id": 10,
  "name": "Sales",
  "leadId": 101,
  "department": "Sales",
  "minRequiredPeople": 4
}
```

### `PATCH /teams/{teamId}` – set required capacity
Required capacity is **one number per team**: `minRequiredPeople` (A). (OPEN: who sets it – HR Admin or Team Lead? Both allowed for now.)
```json
{ "minRequiredPeople": 5 }
```
Response `200`: the updated team. Change is written to the audit log.

### `GET /employees/me`
```json
{
  "id": 102,
  "externalRef": "G2-5531",
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "teamId": 10,
  "role": "EMPLOYEE",
  "employmentType": "INTERNAL",
  "startDate": "2026-12-01",
  "endDate": null,
  "workingTimeShare": 1.0
}
```
`pseudonymId` is **never** returned by any user-facing endpoint.

### `GET /teams/{teamId}/employees`
Used e.g. for the substitute dropdown. Ordinary employees get only `id` and `name`; Team Lead and HR Admin get the full employee object.
```json
[
  { "id": 101, "name": "Maria Weber" },
  { "id": 110, "name": "Jonas Klein" }
]
```

---

## 5. Absence types

An absence type is a row in the `ABSENCE_TYPE` table. Requests point to it with `typeId`.

### `GET /absence-types`
```json
[
  { "id": 1, "name": "Vacation",      "deductsFromEntitlement": true  },
  { "id": 2, "name": "Special leave", "deductsFromEntitlement": false },
  { "id": 3, "name": "Other",         "deductsFromEntitlement": false }
]
```
Initial types: Vacation, Special leave, Other (A). **Sick leave is out of scope** (A) – it is health
data (GDPR Art. 9).

### `POST /admin/absence-types` · `PATCH /admin/absence-types/{typeId}`
```json
{ "name": "Parental leave", "deductsFromEntitlement": false }
```

---

## 6. Absence requests (R1)

Status flow:
```
REQUESTED ──approve──► APPROVED ──cancel (before start)──► CANCELLED
    │  └──cancel─────────────────────────────────────────► CANCELLED
    └──reject──► REJECTED
```

### `POST /absences/preview`
Same body as `POST /absences`. Nothing is saved. The frontend calls it while the user fills the form
to show working days, remaining balance and warnings before submitting.
```json
{
  "workingDays": 2.5,
  "remainingDaysAfter": 17.5,
  "warnings": [ { "code": "BLACKOUT_WARN", "message": "Year-end closing (15.12.–05.01.)" } ]
}
```

### `POST /absences`
Request:
```json
{
  "typeId": 1,
  "startDate": "2026-12-10",
  "endDate": "2026-12-12",
  "halfDayStart": false,
  "halfDayEnd": true,
  "substituteId": 110,
  "reason": "Family event"
}
```

| Field | Required | Rule |
|---|---|---|
| `typeId` | yes | Must exist in `ABSENCE_TYPE` |
| `startDate`, `endDate` | yes | `endDate ≥ startDate`; `startDate` not in the past |
| `halfDayStart`, `halfDayEnd` | no (default `false`) | First/last day counts as 0.5. If start = end, only one of them may be `true` |
| `substituteId` | no (A: optional, no acceptance step) | Same team, not the requester |
| `reason` | no | **Private.** Only the requester and HR Admin can read it. Team Lead sees only the type (A). Never in the calendar, never sent to other groups |

Backend checks, in this order:
1. Validation (fields, dates) → `400`
2. `workingDays` = working days in range (Mon–Fri, minus Hesse holidays, minus half days) → `422 NO_WORKING_DAYS` if 0
3. Overlap with own REQUESTED/APPROVED absences → `409 OVERLAPPING_ABSENCE`
4. Blackout periods for the employee's team or company-wide: `BLOCK` → `422 BLACKOUT_PERIOD` (A: hard block); `WARN` → request is saved, warning returned
5. If type deducts: `workingDays ≤ remaining − pending` → else `422 INSUFFICIENT_ENTITLEMENT`
6. Substitute rules → `422 INVALID_SUBSTITUTE`. If substitute is absent in the same period → warning only (OPEN)

Response `201`:
```json
{
  "id": 5,
  "employeeId": 102,
  "typeId": 1,
  "typeName": "Vacation",
  "startDate": "2026-12-10",
  "endDate": "2026-12-12",
  "halfDayStart": false,
  "halfDayEnd": true,
  "workingDays": 2.5,
  "status": "REQUESTED",
  "substituteId": 110,
  "reason": "Family event",
  "decidedBy": null,
  "decidedAt": null,
  "createdAt": "2026-11-13T09:00:00Z",
  "warnings": []
}
```

### `GET /absences/me?year=2026&status=REQUESTED`
List of the caller's own absences (same object as above).

### `GET /absences/{absenceId}`
Same object. For a Team Lead the field `reason` is **removed**.

### `POST /absences/{absenceId}/cancel`
No body. Allowed when status is `REQUESTED`, or `APPROVED` and `startDate` is still in the future (A).
Response `200` with `status: "CANCELLED"`. If the absence was approved, its days are given back to
the entitlement and a `ABSENCE_CANCELLED` event is sent to G5.

---

## 7. Approval (R2)

Who decides (A):
- Request of an employee → **Team Lead** of the employee's team
- Request of a Team Lead → **HR Admin**
- Nobody may decide their own request

### `GET /approvals/pending`
```json
[
  {
    "id": 5,
    "employeeId": 102,
    "employeeName": "Rahul Sharma",
    "typeName": "Vacation",
    "startDate": "2026-12-10",
    "endDate": "2026-12-12",
    "workingDays": 2.5,
    "substituteId": 110,
    "createdAt": "2026-11-13T09:00:00Z"
  }
]
```

### `GET /absences/{absenceId}/capacity-impact`
The "view on capacity" from R2: what happens to the team if this request is approved.
```json
{
  "absenceId": 5,
  "teamId": 10,
  "minRequiredPeople": 4,
  "days": [
    { "date": "2026-12-10", "availableNow": 5.0, "availableIfApproved": 4.0, "gapIfApproved": 0 },
    { "date": "2026-12-11", "availableNow": 4.5, "availableIfApproved": 3.5, "gapIfApproved": 0.5 }
  ],
  "causesGap": true
}
```

### `POST /absences/{absenceId}/approve`
No body. Response `200`:
```json
{ "id": 5, "status": "APPROVED", "decidedBy": 101, "decidedAt": "2026-11-20T10:00:00Z", "warnings": [] }
```
Effects: `usedDays` of the entitlement increases (only if the type deducts), capacity gaps are
recalculated, event `ABSENCE_APPROVED` to G5, audit log entry.

(OPEN – customer question 3: if approval causes a gap, is it **blocked**, **warned** or only **flagged**?
Proposal: allowed, with a warning `CAUSES_CAPACITY_GAP` in `warnings` and a new OPEN capacity gap.)

### `POST /absences/{absenceId}/reject`
No body (the data model has no rejection-comment field). Response `200` with `status: "REJECTED"`.

---

## 8. Entitlements and carry-over (R3)

Formula (from data model): **remaining = totalDays + carryOverDays − usedDays**

### `GET /employees/me/entitlements?year=2026`
```json
{
  "id": 1,
  "employeeId": 102,
  "year": 2026,
  "totalDays": 30,
  "carryOverDays": 3,
  "carryOverDeadline": "2026-03-31",
  "usedDays": 12,
  "pendingDays": 2.5,
  "remainingDays": 21
}
```
`pendingDays` (sum of REQUESTED absences) is calculated, not stored. It does **not** reduce
`remainingDays`; the UI can show "21 days left, 2.5 pending".

### Rules
- **Default** `totalDays` = 30 per year (A).
- **Pro rata** (A): for employees who start or leave during the year, and for part-time:
  `totalDays = 30 × (months employed in year / 12) × workingTimeShare`, rounded to 0.5.
  Example: start 1 July, full-time → 30 × 6/12 × 1.0 = **15**.
- The entitlement for the start year is created **automatically** when G2 sends a new employee.
- Days are taken from `carryOverDays` first. Carry-over not used by the deadline expires.

### `POST /admin/entitlements` – create (e.g. next year)
```json
{ "employeeId": 102, "year": 2027, "totalDays": 30, "carryOverDays": 0 }
```

### `PATCH /admin/entitlements/{entitlementId}` – HR correction
```json
{ "totalDays": 28 }
```
Every change is written to `AUDIT_LOG` with old and new value.

### `POST /admin/entitlements/carry-over`
Year-end job, triggered by HR (for the demo; later a scheduled job).
```json
{ "fromYear": 2026 }
```
For each employee: `carryOverDays(2027) = min(remaining(2026), maxCarryOverDays)`.
Response `200`: `{ "processed": 42 }`.

### `GET /admin/absence-rule` · `PUT /admin/absence-rule`
One global rule (data model `ABSENCE_RULE`).
```json
{ "maxCarryOverDays": 5, "carryOverDeadline": "03-31" }
```
Defaults: 5 days, 31 March (A). `carryOverDeadline` is stored as day+month because it repeats every year.

---

## 9. Blackout periods (R3)

### `GET /blackout-periods?teamId=10`
Returns company-wide periods (`teamId: null`) and those for the team.

### `POST /admin/blackout-periods`
```json
{
  "teamId": 10,
  "startDate": "2026-12-15",
  "endDate": "2027-01-05",
  "description": "Year-end closing",
  "mode": "BLOCK"
}
```
| Field | Rule |
|---|---|
| `teamId` | `null` = whole company. Both company-wide and per team are possible (A) |
| `mode` | `BLOCK` = request is refused · `WARN` = request allowed, Team Lead sees a warning. Default `BLOCK` (A) |

Existing requests are **not** changed when a new blackout is created (OPEN: confirm).

---

## 10. Calendar and notifications (R7)

### `GET /teams/{teamId}/calendar?from=2026-12-01&to=2026-12-31`
Role-based masking. Colleagues only see **"absent"** – no type, no reason.

Ordinary employee:
```json
{
  "teamId": 10,
  "entries": [
    { "employeeId": 102, "name": "Rahul Sharma", "startDate": "2026-12-10", "endDate": "2026-12-12", "label": "ABSENT" }
  ]
}
```
Team Lead / HR Admin additionally get `typeName`, `status` (incl. REQUESTED) and `substituteId`.
Training periods from G4 are shown as `"label": "ABSENT"` for colleagues and `"TRAINING"` for the Team Lead.
Only APPROVED absences are shown to colleagues.

### `GET /employees/me/calendar.ics`
iCalendar file (`text/calendar`) with the caller's own approved absences, for import into Outlook/Google.

### Notifications
(OPEN) Proposal for MVP: write notifications to the log / show in-app on the next page load:
- Team Lead: new request to decide
- Employee: request approved / rejected
- Substitute: you were named as substitute
- Team Lead: new capacity gap

The data model has no NOTIFICATION table yet. Decide whether to add one or use e-mail.

---

## 11. Capacity and capacity gaps (R5, R6)

### Capacity formula (per team, per working day)

```
available(team, day) =
    Σ workingTimeShare of active internal employees   ← G2   (startDate ≤ day ≤ endDate)
  + 1.0 × planned hires with startDate ≤ day           ← G1
  + 1.0 × external experts with startDate ≤ day ≤ endDate ← G6  (A: full capacity)
  − Σ workingTimeShare of employees on APPROVED absence ← own data (half day = × 0.5)
  − Σ workingTimeShare of employees in training         ← G4

gap(team, day) = max(0, minRequiredPeople − available)
```

Rules:
- Part-timers count with their `workingTimeShare` (A). **(OPEN: team confirms FTE instead of pure headcount.)**
- An employee who is absent **and** in training on the same day is subtracted **once**.
- Weekends and Hesse public holidays are not calculated.
- A planned hire disappears from the calculation when G2 sends the real employee (see 12.1).
- External capacity disappears after the expert's `endDate`.
- Outlook horizon: default **3 months**, maximum **6 months** (A).

### `GET /teams/{teamId}/capacity?from=2027-01-04&to=2027-01-08`
```json
{
  "teamId": 10,
  "minRequiredPeople": 4,
  "days": [
    {
      "date": "2027-01-05",
      "employees": 5.5,
      "plannedHires": 0,
      "externalExperts": 1.0,
      "absent": 2.0,
      "inTraining": 1.0,
      "available": 3.5,
      "required": 4,
      "gap": 0.5
    }
  ]
}
```
`from`/`to` are optional (default: today + 3 months). Range > 6 months → `400`.

### Capacity gaps

The system recalculates gaps whenever capacity changes (approval, cancellation, any integration call,
change of `minRequiredPeople`). Consecutive days with a gap become **one** `CAPACITY_GAP` row;
`missingPeople` = largest gap in that period.

Status flow (A: Team Lead confirms, Team Lead chooses G1 or G6):
```
OPEN ──Team Lead requests hire──────► REQUESTED_HIRE   ──► RESOLVED
     └─Team Lead requests expert────► REQUESTED_EXPERT ──► RESOLVED
     └─capacity back to normal / resolve ──────────────────► RESOLVED
```

### `GET /teams/{teamId}/capacity-gaps?status=OPEN`
```json
[
  {
    "id": 1,
    "teamId": 10,
    "startDate": "2027-01-05",
    "endDate": "2027-01-16",
    "missingPeople": 2,
    "status": "OPEN",
    "requestedFrom": null
  }
]
```

### `POST /capacity-gaps/{gapId}/request`
Team Lead confirms the gap and chooses where to send it.
```json
{ "target": "GROUP1", "role": "Sales Analyst" }
```
| `target` | Effect |
|---|---|
| `GROUP1` | Call G1 (vacancy request), status → `REQUESTED_HIRE`, `requestedFrom = "GROUP1"` |
| `GROUP6` | Call G6 (external expert request), status → `REQUESTED_EXPERT`, `requestedFrom = "GROUP6"` |

Response `200`: updated gap. If the other group is not reachable → `502 DOWNSTREAM_UNAVAILABLE`,
status stays `OPEN`, the Team Lead can retry.

### `POST /capacity-gaps/{gapId}/resolve`
Manually close a gap. Status → `RESOLVED`.

---

## 12. Integrations with other groups (R4, R5, R6, R8)

General rules for all incoming calls:
- Auth with `X-API-Key` (one key per group).
- **Idempotent:** we use `PUT` with the other group's ID in the URL. Sending the same record twice
  **updates** it, never creates a duplicate (answers the "G2 sends the same employee twice" question).
  Response `201` when created, `200` when updated.
- **Cancellation:** `DELETE` with the same ID. Response `204`. Unknown ID → `204` as well (idempotent).
- Every call is written to `AUDIT_LOG` with `actorId = null` and the group name.
- After each call, capacity gaps are recalculated.

### 12.1 G2 Onboarding → G3: new employee
`PUT /integrations/employees/{externalRef}`
```json
{
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "teamId": 10,
  "role": "EMPLOYEE",
  "employmentType": "INTERNAL",
  "startDate": "2026-12-01",
  "endDate": null,
  "workingTimeShare": 1.0,
  "plannedHireRef": "G1-778"
}
```
Effects: create/update `EMPLOYEE`, generate `pseudonymId`, create the pro-rata `ENTITLEMENT` for the
start year. If `plannedHireRef` is given, the matching `PLANNED_HIRE` is removed so the person is not
counted twice. (OPEN: agree `plannedHireRef` with G1 and G2.)

### 12.2 G1 Recruiting → G3: planned hire
`PUT /integrations/planned-hires/{sourceRef}` · `DELETE /integrations/planned-hires/{sourceRef}`
```json
{ "teamId": 10, "role": "Sales Analyst", "startDate": "2027-02-01" }
```
Counted in capacity from `startDate` (A). `DELETE` = hire cancelled.

### 12.3 G4 Learning → G3: booked training (blocked time)
`PUT /integrations/trainings/{sourceRef}` · `DELETE /integrations/trainings/{sourceRef}`
```json
{ "employeeRef": "G2-5531", "startDate": "2026-11-10", "endDate": "2026-11-12" }
```
`employeeRef` is the G2 ID. Unknown employee → `404 NOT_FOUND`. `DELETE` = booking cancelled.

### 12.4 G6 External Recruiting → G3: planned external expert
`PUT /integrations/external-experts/{sourceRef}` · `DELETE /integrations/external-experts/{sourceRef}`
```json
{ "teamId": 10, "startDate": "2027-01-05", "endDate": "2027-06-30" }
```
Counts as 1.0 capacity between `startDate` and `endDate` (A).

### 12.5 G3 → G1 Recruiting: vacancy request (outgoing)
Sent when the Team Lead chooses `GROUP1`. **Path is owned by G1 – to be agreed.**
```json
{
  "sourceRef": "G3-GAP-1",
  "teamId": 10,
  "department": "Sales",
  "role": "Sales Analyst",
  "missingPeople": 2,
  "neededFrom": "2027-01-05",
  "neededUntil": "2027-01-16"
}
```

### 12.6 G3 → G6 External Recruiting: expert request (outgoing)
Sent when the Team Lead chooses `GROUP6`. Direct API call (A), because the dependency slide does
not show this path. **Path is owned by G6 – to be agreed.**
```json
{
  "sourceRef": "G3-GAP-1",
  "teamId": 10,
  "department": "Sales",
  "role": "Sales Analyst",
  "missingPeople": 2,
  "neededFrom": "2027-01-05",
  "neededUntil": "2027-01-16"
}
```
When G6 later plans an expert for this gap, they call 12.4.

### 12.7 G3 → G5 People Analytics: pseudonymised events (outgoing)
**Path is owned by G5 – to be agreed.** Fields sent (A): pseudonym ID, department, broad category,
dates, days.

```json
{
  "eventId": "6f1c2a40-0f7e-4b1e-9a51-0d2d7d3e8a11",
  "eventType": "ABSENCE_APPROVED",
  "occurredAt": "2026-11-20T10:00:00Z",
  "pseudonymId": "P-8f3a21",
  "department": "Sales",
  "category": "Vacation",
  "startDate": "2026-12-10",
  "endDate": "2026-12-12",
  "workingDays": 2.5
}
```

| `eventType` | When |
|---|---|
| `ABSENCE_APPROVED` | Request approved |
| `ABSENCE_CANCELLED` | Approved absence cancelled |
| `CAPACITY_GAP_OPENED` | New gap (fields: department, startDate, endDate, missingPeople – no person data) |
| `CAPACITY_GAP_RESOLVED` | Gap resolved |

**Never sent to any group:** `name`, `email`, `reason`, `substituteId`, internal `id`, `externalRef`.
Pseudonymised is not anonymous – G5 must still protect the data.

Outgoing failures: 3 retries, then logged in `AUDIT_LOG` with `action = "SEND_FAILED"`.

---

## 13. Audit log

### `GET /admin/audit-log?entity=ENTITLEMENT&from=2026-11-01`
```json
[
  {
    "id": 1,
    "actorId": 101,
    "entity": "ENTITLEMENT",
    "action": "UPDATE",
    "oldValue": { "totalDays": 28 },
    "newValue": { "totalDays": 30 },
    "at": "2026-11-20T10:00:00Z"
  }
]
```
Logged: every create/update/delete of entitlements, absence rule, blackouts, absence types, team
minimum, every approval/rejection/cancellation, every integration call.
(OPEN: retention period for absence and audit data – GDPR.)

---

## 14. Changes needed in the data model

This contract needs a few fields that are not in Req.pdf yet. Team to agree:

| Table | Add | Why |
|---|---|---|
| `ABSENCE_REQUEST` | `halfDayStart` bool, `halfDayEnd` bool | Half days (A) – needed to show the calendar and recalculate days |
| `ABSENCE_REQUEST` | `createdAt` timestamp | Sorting pending requests, audit |
| `AUDIT_LOG` | `actorId` nullable + `source` string | Integration calls have no employee as actor |
| `ABSENCE_RULE` | `carryOverDeadline` as `MM-DD` string instead of date | Deadline repeats every year |

Data model question for the team: external experts appear both as `EMPLOYEE` with
`employmentType = EXTERNAL` **and** in `EXTERNAL_EXPERT`. This contract uses **only `EXTERNAL_EXPERT`**
for capacity. Decide whether `EXTERNAL` employees are needed at all.

---

## 15. Open decisions (bring to team / customer)

| # | Question | Assumption used in this contract |
|---|---|---|
| 1 | Capacity unit: headcount or FTE (`workingTimeShare`)? | FTE |
| 2 | Who sets `minRequiredPeople`? | HR Admin and Team Lead |
| 3 | Approval that causes a gap: block, warn or flag? | Warn + create gap |
| 4 | Substitute absent at the same time? | Warning only |
| 5 | Pro rata also for part-time? | Yes |
| 6 | Shared `teamId` values across groups | To agree with G1, G2, G6 |
| 7 | `plannedHireRef` to link G1 hire and G2 employee | To agree with G1, G2 |
| 8 | Endpoint paths and payloads for G1, G5, G6 (outgoing) | Proposals in 12.5–12.7 |
| 9 | Notifications: table, e-mail or in-app? | Log only for MVP |
| 10 | Data retention (GDPR) | Not defined |
| 11 | New blackout affects already approved requests? | No |
