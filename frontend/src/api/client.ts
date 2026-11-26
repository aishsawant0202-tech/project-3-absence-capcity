
/**
 * API client with JWT authentication.
 */

/**
 * API client with JWT authentication.
 */

export type Role = "EMPLOYEE" | "TEAM_LEAD" | "HR_ADMIN";

export const ROLES: Role[] = ["EMPLOYEE", "TEAM_LEAD", "HR_ADMIN"];

// Temporary compatibility type for existing team pages.
export interface DemoUser {
  role: Role;
  employeeId: number;
}
export interface LoginResponse {
  access_token: string;
  token_type: string;
  must_change_password: boolean;
}

export interface CurrentUser {
  id: number;
  employee_id: number;
  username: string;
  role: Role;
  status: string;
  must_change_password: boolean;
  first_name: string;
  last_name: string;
  email: string;
}

const TOKEN_KEY = "accessToken";

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export interface FieldError {
  field: string;
  message: string;
}

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
  error?: {
    code?: string;
    message?: string;
    details?: { fields?: FieldError[] };
  };
}

async function toApiError(res: Response): Promise<ApiError> {
  let body: ErrorBody | null = null;

  try {
    body = await res.json();
  } catch {
    // Response was not JSON.
  }

  const err = body?.error;

  if (err?.code) {
    return new ApiError(
      res.status,
      err.code,
      err.message ?? `Request failed (${res.status}).`,
      err.details?.fields ?? [],
    );
  }

  return new ApiError(
    res.status,
    res.status >= 500 ? "SERVER_ERROR" : "UNKNOWN",
    res.status >= 500
      ? "The server encountered an error. Is the backend running?"
      : `Request failed (${res.status}).`,
  );
}

export async function apiRequest<T>(
  method: string,
  path: string,
  body?: unknown,
  authenticated = true,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = getToken();

  if (authenticated && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let res: Response;

  try {
    res = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      "Cannot reach the server. Is the backend running?",
    );
  }

  if (!res.ok) {
    throw await toApiError(res);
  }

  return (res.status === 204 ? undefined : await res.json()) as T;
}

export function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(
    "POST",
    "/api/auth/login",
    { username, password },
    false,
  );
}

export function getCurrentUser(): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("GET", "/api/auth/me");
}
