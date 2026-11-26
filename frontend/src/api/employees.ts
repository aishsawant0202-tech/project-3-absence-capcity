/** Employee API calls (Member 3). Types match backend/app/schemas/employee.py (camelCase JSON, API contract v2). */
import { apiRequest } from "./client"; // Shared helper: adds the demo login headers and turns errors into ApiError

export type EmploymentType = "PERMANENT" | "CONTRACT"; // Only these two values are allowed
export type EmployeeStatus = "ACTIVE" | "INACTIVE";

/** An employee as the API returns it (same fields as EmployeeRead in the backend). */
export interface Employee {
  id: number;
  employeeRef: string | null;
  firstName: string;
  lastName: string;
  email: string;
  teamId: number | null;
  jobTitle: string | null;
  employmentType: EmploymentType;
  workingTimeShare: number;
  startDate: string; // YYYY-MM-DD
  endDate: string | null;
  status: EmployeeStatus;
}

/** The fields of the Add / Edit form (everything except id and status). */
export interface EmployeeInput {
  employeeRef: string | null;
  firstName: string;
  lastName: string;
  email: string;
  teamId: number | null;
  jobTitle: string | null;
  employmentType: EmploymentType;
  workingTimeShare: number;
  startDate: string;
  endDate: string | null;
}

/** Optional filters for the employee list. Empty values are not sent. */
export interface EmployeeFilters {
  search?: string;
  teamId?: number | null;
  status?: EmployeeStatus | "";
  employmentType?: EmploymentType | "";
}

/** US-02: employees, sorted by last name. Filters are applied by the backend. */
export function listEmployees(filters: EmployeeFilters = {}): Promise<Employee[]> {
  const params = new URLSearchParams();                                   // Builds ?search=...&teamId=...
  if (filters.search?.trim()) params.set("search", filters.search.trim());
  if (filters.teamId) params.set("teamId", String(filters.teamId));
  if (filters.status) params.set("status", filters.status);
  if (filters.employmentType) params.set("employmentType", filters.employmentType);
  const query = params.toString();
  return apiRequest<Employee[]>("GET", `/api/v1/employees${query ? `?${query}` : ""}`);
}

/** US-02: one employee; ApiError code NOT_FOUND if the id does not exist. */
export function getEmployee(employeeId: number): Promise<Employee> {
  return apiRequest<Employee>("GET", `/api/v1/employees/${employeeId}`);
}

/** US-04: the logged-in user's own employee record. */
export function getMyProfile(): Promise<Employee> {
  return apiRequest<Employee>("GET", "/api/v1/employees/me");
}

/** US-01: create an employee (HR Admin only). */
export function createEmployee(data: EmployeeInput): Promise<Employee> {
  return apiRequest<Employee>("POST", "/api/v1/employees", data);
}

/** US-03: edit an employee or move them to another team (HR Admin only). */
export function updateEmployee(employeeId: number, data: Partial<EmployeeInput>): Promise<Employee> {
  return apiRequest<Employee>("PATCH", `/api/v1/employees/${employeeId}`, data);
}

/** US-04: activate or deactivate an employee (HR Admin only). */
export function setEmployeeStatus(employeeId: number, status: EmployeeStatus): Promise<Employee> {
  return apiRequest<Employee>("PATCH", `/api/v1/employees/${employeeId}/status`, { status });
}

/** "Alex Miller" */
export function fullName(e: Pick<Employee, "firstName" | "lastName">): string {
  return `${e.firstName} ${e.lastName}`;
}

/** API date "2026-11-01" -> "01.11.2026" (UI guidelines, section 10). */
export function formatDate(value: string | null): string {
  if (!value) return "—";
  const [y, m, d] = value.split("-");
  return `${d}.${m}.${y}`;
}
