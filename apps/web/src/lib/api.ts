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

export type Block = {
  id: string;
  site_id: string;
  name: string;
  code: string;
};

export type Flat = {
  id: string;
  site_id: string;
  block_id: string;
  unit_no: string;
  floor: number;
  status: "active" | "inactive";
};

export type ResidentRelation = {
  id: string;
  site_id: string;
  user_id: string;
  flat_id: string;
  relation_type: "owner" | "tenant";
  start_date: string;
  end_date: string | null;
  is_primary: boolean;
};

function buildTenantHeaders(token: string, siteId: string, withJsonContent = true): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "X-Site-Id": siteId,
    ...(withJsonContent ? { "Content-Type": "application/json" } : {}),
  };
}

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

export async function listBlocks(token: string, siteId: string): Promise<Block[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blocks`, {
    method: "GET",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    throw new Error(`Bloklar alınamadı (${response.status})`);
  }
  return (await response.json()) as Block[];
}

export async function createBlock(
  token: string,
  siteId: string,
  payload: { name: string; code: string },
): Promise<Block> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blocks`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Blok oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as Block;
}

export async function deleteBlock(token: string, siteId: string, blockId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blocks/${blockId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Blok silinemedi (${response.status}): ${text}`);
  }
}

export async function listFlats(token: string, siteId: string, blockId?: string): Promise<Flat[]> {
  const query = blockId ? `?block_id=${encodeURIComponent(blockId)}` : "";
  const response = await fetch(`${API_BASE_URL}/api/v1/flats${query}`, {
    method: "GET",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    throw new Error(`Daireler alınamadı (${response.status})`);
  }
  return (await response.json()) as Flat[];
}

export async function createFlat(
  token: string,
  siteId: string,
  payload: { block_id: string; unit_no: string; floor: number; status: "active" | "inactive" },
): Promise<Flat> {
  const response = await fetch(`${API_BASE_URL}/api/v1/flats`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Daire oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as Flat;
}

export async function deleteFlat(token: string, siteId: string, flatId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/flats/${flatId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Daire silinemedi (${response.status}): ${text}`);
  }
}

export async function listResidentRelations(
  token: string,
  siteId: string,
): Promise<ResidentRelation[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/resident-relations`, {
    method: "GET",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    throw new Error(`İlişkiler alınamadı (${response.status})`);
  }
  return (await response.json()) as ResidentRelation[];
}

export async function createResidentRelation(
  token: string,
  siteId: string,
  payload: {
    user_id: string;
    flat_id: string;
    relation_type: "owner" | "tenant";
    start_date: string;
    end_date: string | null;
    is_primary: boolean;
  },
): Promise<ResidentRelation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/resident-relations`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`İlişki oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as ResidentRelation;
}

export async function deleteResidentRelation(
  token: string,
  siteId: string,
  relationId: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/resident-relations/${relationId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`İlişki silinemedi (${response.status}): ${text}`);
  }
}
