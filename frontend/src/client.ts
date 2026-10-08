import type { components } from './api';

export type Schema<K extends keyof components['schemas']> = components['schemas'][K];
export type Actor = Schema<'Actor'>;
type Session = { username: string; access: string; refresh: string; expires: number };
type AuthConfig = Schema<'PublicAuthConfig'>;
const KEY = 'airwise.session.v1';
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
let session: Session | null = null;
let refreshFlight: Promise<void> | null = null;
const listeners = new Set<() => void>();

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

function restore() {
  try {
    const value = JSON.parse(sessionStorage.getItem(KEY) || 'null');
    if (value && typeof value.username === 'string' && typeof value.access === 'string' && typeof value.refresh === 'string' && Number.isFinite(value.expires)) session = value;
  } catch { sessionStorage.removeItem(KEY); }
}
restore();

function save(value: Session | null) {
  session = value;
  if (value) sessionStorage.setItem(KEY, JSON.stringify(value)); else sessionStorage.removeItem(KEY);
  listeners.forEach(listener => listener());
}
export function subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
export function sessionUser() { return session?.username ?? null; }
export function signOut() { save(null); }

async function transport(url: string, options: RequestInit, timeout = 45000): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal, cache: 'no-store' });
    const bytes = await response.arrayBuffer();
    return new Response([204, 205, 304].includes(response.status) ? null : bytes, { status: response.status, statusText: response.statusText, headers: response.headers });
  }
  catch { throw new ApiError(0, 'Connection failed or timed out. The result may be unknown; check the current state before repeating an action.'); }
  finally { window.clearTimeout(timer); }
}

let authConfig: AuthConfig | null = import.meta.env.VITE_COGNITO_CLIENT_ID ? {
  region: import.meta.env.VITE_COGNITO_REGION,
  pool_id: import.meta.env.VITE_COGNITO_POOL_ID,
  client_id: import.meta.env.VITE_COGNITO_CLIENT_ID,
} : null;
async function cognito(flow: string, parameters: Record<string, string>) {
  if (!authConfig) {
    const response = await transport(`${API_BASE}/auth/config`, {}, 10000);
    if (!response.ok) throw new ApiError(response.status, 'Sign-in configuration is unavailable.');
    authConfig = await response.json();
  }
  const response = await transport(`https://cognito-idp.${authConfig!.region}.amazonaws.com/`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-amz-json-1.1', 'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth' },
    body: JSON.stringify({ AuthFlow: flow, ClientId: authConfig!.client_id, AuthParameters: parameters }),
  }, 15000);
  if (!response.ok) throw new ApiError(response.status, 'Cognito could not authenticate this session. Check your credentials or sign in again.');
  const body = await response.json();
  if (!body.AuthenticationResult) throw new ApiError(401, 'This account requires a password change or an unsupported sign-in challenge. Ask the administrator to complete it privately.');
  const result = body.AuthenticationResult;
  if (typeof result.AccessToken !== 'string' || !Number.isFinite(result.ExpiresIn)) throw new ApiError(401, 'Cognito returned an incomplete session.');
  return result as { AccessToken: string; RefreshToken?: string; ExpiresIn: number };
}

export async function signIn(username: string, password: string) {
  const result = await cognito('USER_PASSWORD_AUTH', { USERNAME: username, PASSWORD: password });
  if (!result.RefreshToken) throw new ApiError(401, 'Cognito did not return a refresh session.');
  save({ username, access: result.AccessToken, refresh: result.RefreshToken, expires: Date.now() + result.ExpiresIn * 1000 });
}

async function freshSession() {
  if (!session) throw new ApiError(401, 'Sign in to continue.');
  if (session.expires > Date.now() + 30000) return;
  if (!refreshFlight) {
    const previous = session;
    refreshFlight = (async () => {
      try {
        const result = await cognito('REFRESH_TOKEN_AUTH', { REFRESH_TOKEN: previous.refresh });
        if (session !== previous) throw new ApiError(401, 'Session changed. Sign in again.');
        // Refresh in this tab only; no credentials enter URLs, logs or localStorage.
        session = { ...previous, access: result.AccessToken, refresh: result.RefreshToken || previous.refresh, expires: Date.now() + result.ExpiresIn * 1000 };
        sessionStorage.setItem(KEY, JSON.stringify(session));
      } catch (error) {
        if (session === previous && error instanceof ApiError && error.status !== 0) signOut();
        throw error;
      }
    })().finally(() => { refreshFlight = null; });
  }
  await refreshFlight;
}

export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  await freshSession();
  const response = await transport(`${API_BASE}${path}`, {
    method, headers: { Authorization: `Bearer ${session!.access}`, ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}) },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  }, method === 'POST' && path === '/notice-analyses' ? 60000 : 45000);
  if (!response.ok) {
    if (response.status === 401) signOut();
    const payload = await response.json().catch(() => null);
    const detail = typeof payload?.detail === 'string' ? payload.detail : 'The request was rejected. Check the required fields and your permissions.';
    throw new ApiError(response.status, detail);
  }
  return response.json();
}
