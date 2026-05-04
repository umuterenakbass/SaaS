export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ApiHealthResponse = {
  status: string;
  service: string;
  version: string;
  env: string;
};

export type RegisterAdminPayload = {
  site_name: string;
  full_name: string;
  email: string;
  password: string;
};

export type CurrentUserResponse = {
  id: string;
  site_id: string;
  email: string;
  full_name: string;
  role: "admin" | "manager" | "accountant" | "resident";
  is_active: boolean;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type TenantContextResponse = {
  site_id: string;
  user_id: string;
  role: string;
};

export async function fetchApiHealth(): Promise<ApiHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return (await response.json()) as ApiHealthResponse;
}

export async function registerAdmin(payload: RegisterAdminPayload): Promise<CurrentUserResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Kayıt başarısız (${response.status}): ${text}`);
  }

  return (await response.json()) as CurrentUserResponse;
}

export async function loginWithPassword(email: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams({
    username: email,
    password,
  });

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Giriş başarısız (${response.status}): ${text}`);
  }

  return (await response.json()) as LoginResponse;
}

export async function fetchCurrentUser(token: string): Promise<CurrentUserResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Kullanıcı bilgisi alınamadı (${response.status}): ${text}`);
  }

  return (await response.json()) as CurrentUserResponse;
}

export async function fetchTenantContext(
  token: string,
  siteId: string,
): Promise<TenantContextResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tenant/context`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Site-Id": siteId,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Tenant kontrolü başarısız (${response.status}): ${text}`);
  }

  return (await response.json()) as TenantContextResponse;
}
