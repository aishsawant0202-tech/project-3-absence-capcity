# Sprint 1 Roadmap – Project 3 Absence & Capacity

**Sprint 1:** 30.10.2026 – 26.11.2026 · **Review / Retro / Planning S2:** 27.11.2026
**Sprint goal:** Requirements, data model, API and integration contracts agreed; a walking skeleton
(FastAPI + Postgres + React) runs locally and on Azure with CI.

> Proposal for the team. Who takes which role, priorities and estimates are **team decisions**
> (course rule – not delegated to AI). Swap names into A–D and adjust in the first sync.

## Roles

| Member | Scrum role | Focus in Sprint 1 |
|---|---|---|
| **A** | Product Owner | Customer contact, open decisions, user stories, backlog |
| **B** | Scrum Master | Repo, board, Docker, CI/CD, Azure, meeting minutes |
| **C** | Developer | Backend skeleton, database models, migrations, core calculations |
| **D** | Developer | Cross-group integration agreements, frontend skeleton, mock API |

## Already done ✅

- [x] Requirements R1–R8 with hidden complexity and customer questions (Req.pdf, 31.10)
- [x] Data model v1 – 13 tables with assumptions (Req.pdf)
- [x] API contract draft v0.2 (`docs/api-contracts.md`, 13.11)

## Week 3 · 13.11 – 19.11 · Contracts & skeleton start

| | Member A (PO) | Member B (SM / DevOps) | Member C (Backend) | Member D (Integration / Frontend) |
|---|---|---|---|---|
| 1 | Run team review of `api-contracts.md` v0.2; decide the 11 open points (section 15) | Repo structure `backend/`, `frontend/`, `docs/`; `.gitignore`, `.env.example` | FastAPI skeleton: `/health`, settings, DB connection | Send section 12 (integrations) to G1, G2, G4, G5, G6 with a contact person each |
| 2 | Customer meeting: capacity unit (FTE/headcount), gap blocks approval?, who sets `minRequiredPeople`, data retention | Branch protection on `main`, PR template, Definition of Done in README | SQLAlchemy models for all 13 tables + Alembic initial migration | Cross-group meeting: shared `teamId`, `externalRef` (G2 ID), `plannedHireRef`, `X-API-Key` auth |
| 3 | Write user stories + acceptance criteria for R1–R8 on the GitHub Projects board | GitHub Projects board: Backlog · Ready · In progress · Review · Done | Seed data: Hesse holidays 2026–27, absence types, absence rule, demo team + 4 demo users | React + TypeScript (Vite) skeleton; page that calls `/health` |
| 4 | Apply data-model changes (contract section 14) to the data-model doc | `docker-compose.yml`: Postgres + backend, one command to start | Spike: working-days calculator (weekends, holidays, half days) + unit tests | Demo login page: pick a demo user / role |
| 5 | | GitHub Actions CI: lint + tests on every PR | | |

**Milestone 19.11:** contract decisions recorded · skeleton runs locally with `docker compose up` · CI green.

## Week 4 · 20.11 – 26.11 · Deploy, publish, close

| | Member A (PO) | Member B (SM / DevOps) | Member C (Backend) | Member D (Integration / Frontend) |
|---|---|---|---|---|
| 1 | Freeze `api-contracts.md` v1.0 with team + group feedback | Azure: Container Apps + PostgreSQL Flexible (B1ms); deploy skeleton | Endpoint stubs for all contract paths (return example data) → OpenAPI generated | Publish `openapi.json` to all groups; Prism mock server for them |
| 2 | Draft Sprint 2 backlog candidates (core absence flow) for planning on 27.11 | CI/CD: build Docker image → push GHCR → deploy | Unit test: pro-rata entitlement (30 × months/12 × share) | Record agreed payloads per group in `docs/integration-contracts.md` |
| 3 | Sprint 1 review script + demo (stories, data model, contracts, live skeleton) | Cost table (service, tier, €/month) for the report | Demo-login endpoint + role check (JWT) | Frontend: absence request form against mock API |
| 4 | | Organise retrospective; collect meeting minutes for the report | | |

**Milestone 24.11:** skeleton reachable on Azure.
**Milestone 26.11:** all Sprint 1 work merged to `main`, board up to date.

## Everyone, every week

- Weekly sync (date, attendees, decisions) → minutes in `docs/meetings/`
- Every PR reviewed by at least 1 other member before merge
- Log AI use in `AI_USAGE.md` (date, tool, purpose, prompt summary, result, verification)

## Dependencies

```
A: open decisions ──► C: models & migration ──► C: endpoint stubs ──► D: publish OpenAPI / mock
B: repo + compose ──► C: skeleton ──► B: Azure deploy
D: group agreements ──► A: contract v1.0 freeze
```

## 27.11 · Sprint ceremonies

1. **Review:** show stories, data model, contract v1.0, live skeleton on Azure
2. **Retrospective:** went well / improve / actions
3. **Planning Sprint 2** (27.11 – 17.12): team prioritises and estimates (planning poker) – R1 request,
   R2 approval, R3 entitlements, role checks, CI/CD live
