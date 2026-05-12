const TOKEN_KEY = "saas_access_token";
const SITE_ID_KEY = "saas_site_id";
const ROLE_KEY = "saas_user_role";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function saveSession(accessToken: string, siteId: string, role?: string): void {
  if (!isBrowser()) return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(SITE_ID_KEY, siteId);
  if (role) localStorage.setItem(ROLE_KEY, role);
}

export function getAccessToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getSiteId(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(SITE_ID_KEY);
}

export function getUserRole(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(ROLE_KEY);
}

export function clearSession(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(SITE_ID_KEY);
  localStorage.removeItem(ROLE_KEY);
}
