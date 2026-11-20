/** Team API calls. Types match backend/app/schemas/team.py (camelCase JSON, API contract v2). */
import { apiRequest } from "./client";

export interface TeamCreate {
  name: string;
  description: string | null;
  minRequiredFte: number;
}

export interface Team {
  id: number;
  teamRef: string | null;
  name: string;
  description: string | null;
  minRequiredFte: number;
  teamLeadEmployeeId: number | null;
  status: "ACTIVE" | "INACTIVE";
}

export function createTeam(data: TeamCreate): Promise<Team> {
  return apiRequest<Team>("POST", "/api/v1/teams", data);
}

/** All teams (active and inactive), sorted by name. */
export function listTeams(): Promise<Team[]> {
  return apiRequest<Team[]>("GET", "/api/v1/teams");
}

/** Edit a team (only its Team Lead). Only the fields sent are changed. */
export function updateTeam(teamId: number, data: Partial<TeamCreate>): Promise<Team> {
  return apiRequest<Team>("PATCH", `/api/v1/teams/${teamId}`, data);
}

/** Activate or deactivate a team (only its Team Lead). */
export function setTeamStatus(teamId: number, status: Team["status"]): Promise<Team> {
  return apiRequest<Team>("PATCH", `/api/v1/teams/${teamId}/status`, { status });
}

/** One team; ApiError code NOT_FOUND if the id does not exist. */
export function getTeam(teamId: number): Promise<Team> {
  return apiRequest<Team>("GET", `/api/v1/teams/${teamId}`);
}

/**
 * A team member. Ordinary members get only id and name; HR Admin and the lead of the team
 * also get the other fields (API contract v2), so those are optional here.
 */
export interface TeamMember {
  id: number;
  name: string;
  email?: string;
  jobTitle?: string | null;
  workingTimeShare?: number;
  status?: "ACTIVE" | "INACTIVE";
}

/** Members of a team, sorted by last name; ApiError code FORBIDDEN if the caller may not see them. */
export function listTeamMembers(teamId: number): Promise<TeamMember[]> {
  return apiRequest<TeamMember[]>("GET", `/api/v1/teams/${teamId}/employees`);
}
