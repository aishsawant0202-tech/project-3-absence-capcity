/**
 * Small fetch wrapper for the backend API.
 *
 * TEMPORARY: until Member 4's login is ready, every request sends the demo user
 * as X-Role / X-Employee-Id headers (the same stub as backend/app/dependencies.py).
 * TODO(Member 4): replace getDemoUser() with the logged-in user / token.
 */

export type Role = "EMPLOYEE" | "TEAM_LEAD" | "HR_ADMIN";
export const ROLES: Role[] = ["EMPLOYEE", "TEAM_LEAD", "HR_ADMIN"];

export interface DemoUser {
  role: Role;
  employeeId: number;
}

const STORAGE_KEY = "demoUser";
const DEFAULT_USER: DemoUser = { role: "TEAM_LEAD", employeeId: 1 };

export function getDemoUser(): DemoUser {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "null");
    if (saved && ROLES.includes(saved.role) && Number.isInteger(saved.employeeId)) {
      return saved;
    }
  } catch {
    // storage blocked or broken value: use the default
  }
  return DEFAULT_USER;
}

export function saveDemoUser(user: DemoUser): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  } catch {
    // storage blocked: the choice only lasts until reload
  }
}

/** One invalid field from a 400 VALIDATION_ERROR, e.g. { field: "minRequiredFte", message: "..." }. */
export interface FieldError {
  field: string;
  message: string;
}

/**
 * An error response from the backend (API contract v2, section 1.2):
 *   { "error": { "code": "TEAM_NAME_TAKEN", "message": "...", "details": { "fields": [...] } } }
 * Pages decide by `code`, never by the message text.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fieldErrors: FieldError[] = [],
  ) {
    super(message);
  }
}

interface ErrorBody {
  error?: { code?: string; message?: string; details?: { fields?: FieldError[] } };
}

async function toApiError(res: Response): Promise<ApiError> {
  let body: ErrorBody | null = null;
  try {
    body = await res.json();
  } catch {
    // not JSON (e.g. proxy error when the backend is not running)
  }
  const err = body?.error;
  if (err?.code) {
    return new ApiError(res.status, err.code, err.message ?? `Request failed (${res.status}).`, err.details?.fields ?? []);
  }
  if (res.status >= 500) {
    return new ApiError(res.status, "SERVER_ERROR", "The server is not reachable or had an error. Is the backend running?");
  }
  return new ApiError(res.status, "UNKNOWN", `Request failed (${res.status}).`);
}

export async function apiRequest<T>(method: string, path: string, body?: unknown): Promise<T> {
  const user = getDemoUser();
  let res: Response;
  try {
    res = await fetch(path, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Role": user.role,
        "X-Employee-Id": String(user.employeeId),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Cannot reach the server. Is the backend running?");
  }
  if (!res.ok) {
    throw await toApiError(res);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}
