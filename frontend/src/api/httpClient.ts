import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../lib/tokenStorage";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_V1 = `${API_URL}/api/v1`;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // response wasn't JSON - fall through to the generic message
  }
  return `Request failed with status ${response.status}`;
}

// Concurrent 401s from several in-flight requests must share one refresh
// attempt, not each fire their own - this is the guard against that.
let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_V1}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) return false;
        const body = await response.json();
        setTokens(body.access_token, body.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean; // attach Authorization header if a token is present (default true)
  formData?: FormData;
  parseResponse?: boolean; // false for endpoints returning no body (204)
}

async function rawFetch(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = {};
  if (!options.formData) headers["Content-Type"] = "application/json";

  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  return fetch(`${API_V1}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.formData ?? (options.body !== undefined ? JSON.stringify(options.body) : undefined),
  });
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await rawFetch(path, options);

  if (response.status === 401 && options.auth !== false && getRefreshToken()) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawFetch(path, options);
    } else {
      clearTokens();
    }
  }

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response), response.status);
  }

  if (options.parseResponse === false || response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function apiUrl(path: string): string {
  return `${API_V1}${path}`;
}
