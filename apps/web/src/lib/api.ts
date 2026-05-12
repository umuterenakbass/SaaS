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

export type ChargeStatus = "pending" | "paid" | "cancelled";

export type Charge = {
  id: string;
  site_id: string;
  flat_id: string;
  charge_type: string;
  period: string;
  amount: string;
  due_date: string;
  status: ChargeStatus;
};

export type PaymentMethod = "cash" | "bank_transfer" | "credit_card" | "other";

export type Payment = {
  id: string;
  site_id: string;
  flat_id: string;
  amount: string;
  paid_at: string;
  method: PaymentMethod;
  reference_no: string | null;
  note: string | null;
};

export type ChargePlanFrequency = "monthly";

export type ChargePlan = {
  id: string;
  site_id: string;
  name: string;
  charge_type: string;
  amount: string;
  frequency: ChargePlanFrequency;
  start_period: string;
  end_period: string | null;
  is_active: boolean;
};

export type ChargePlanAssignment = {
  id: string;
  site_id: string;
  charge_plan_id: string;
  flat_id: string;
};

export type ChargePlanGenerateResult = {
  charge_plan_id: string;
  period: string;
  requested_assignments: number;
  created_count: number;
  skipped_count: number;
  created_charge_ids: string[];
};

export type PaymentAllocation = {
  id: string;
  site_id: string;
  payment_id: string;
  charge_id: string;
  allocated_amount: string;
};

export type FlatLedger = {
  site_id: string;
  flat_id: string;
  total_charges: string;
  total_payments: string;
  allocated_total: string;
  open_charge_total: string;
  unallocated_payment_total: string;
  balance: string;
  charge_count: number;
  payment_count: number;
  recent_charges: Array<{
    charge_id: string;
    charge_type: string;
    period: string;
    amount: string;
    allocated_amount: string;
    remaining_amount: string;
    due_date: string;
    status: ChargeStatus;
  }>;
  recent_payments: Array<{
    payment_id: string;
    amount: string;
    allocated_amount: string;
    remaining_amount: string;
    paid_at: string;
    method: PaymentMethod;
    reference_no: string | null;
  }>;
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

export async function listCharges(
  token: string,
  siteId: string,
  params?: { flat_id?: string; period?: string; status?: ChargeStatus },
): Promise<Charge[]> {
  const query = new URLSearchParams();
  if (params?.flat_id) query.set("flat_id", params.flat_id);
  if (params?.period) query.set("period", params.period);
  if (params?.status) query.set("status", params.status);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/charges${query.toString() ? `?${query.toString()}` : ""}`,
    {
      method: "GET",
      headers: buildTenantHeaders(token, siteId, false),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Borçlar alınamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as Charge[];
}

export async function createCharge(
  token: string,
  siteId: string,
  payload: {
    flat_id: string;
    charge_type: string;
    period: string;
    amount: string;
    due_date: string;
    status: ChargeStatus;
  },
): Promise<Charge> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charges`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Borç oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as Charge;
}

export async function deleteCharge(token: string, siteId: string, chargeId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charges/${chargeId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Borç silinemedi (${response.status}): ${text}`);
  }
}

export async function listPayments(
  token: string,
  siteId: string,
  params?: { flat_id?: string },
): Promise<Payment[]> {
  const query = new URLSearchParams();
  if (params?.flat_id) query.set("flat_id", params.flat_id);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/payments${query.toString() ? `?${query.toString()}` : ""}`,
    {
      method: "GET",
      headers: buildTenantHeaders(token, siteId, false),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Ödemeler alınamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as Payment[];
}

export async function createPayment(
  token: string,
  siteId: string,
  payload: {
    flat_id: string;
    amount: string;
    paid_at: string;
    method: PaymentMethod;
    reference_no: string | null;
    note: string | null;
  },
): Promise<Payment> {
  const response = await fetch(`${API_BASE_URL}/api/v1/payments`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Ödeme oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as Payment;
}

export async function deletePayment(token: string, siteId: string, paymentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/payments/${paymentId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Ödeme silinemedi (${response.status}): ${text}`);
  }
}

export async function getFlatLedger(
  token: string,
  siteId: string,
  flatId: string,
  limit = 10,
): Promise<FlatLedger> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ledger/flats/${flatId}?limit=${limit}`, {
    method: "GET",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Ekstre alınamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as FlatLedger;
}

export async function listChargePlans(
  token: string,
  siteId: string,
  params?: { is_active?: boolean },
): Promise<ChargePlan[]> {
  const query = new URLSearchParams();
  if (typeof params?.is_active === "boolean") {
    query.set("is_active", String(params.is_active));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/charge-plans${query.toString() ? `?${query.toString()}` : ""}`,
    {
      method: "GET",
      headers: buildTenantHeaders(token, siteId, false),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Planlar alınamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as ChargePlan[];
}

export async function createChargePlan(
  token: string,
  siteId: string,
  payload: {
    name: string;
    charge_type: string;
    amount: string;
    frequency: ChargePlanFrequency;
    start_period: string;
    end_period: string | null;
    is_active: boolean;
  },
): Promise<ChargePlan> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charge-plans`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as ChargePlan;
}

export async function updateChargePlan(
  token: string,
  siteId: string,
  planId: string,
  payload: {
    name?: string;
    charge_type?: string;
    amount?: string;
    frequency?: ChargePlanFrequency;
    start_period?: string;
    end_period?: string | null;
    is_active?: boolean;
  },
): Promise<ChargePlan> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charge-plans/${planId}`, {
    method: "PATCH",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan güncellenemedi (${response.status}): ${text}`);
  }
  return (await response.json()) as ChargePlan;
}

export async function deleteChargePlan(token: string, siteId: string, planId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charge-plans/${planId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan silinemedi (${response.status}): ${text}`);
  }
}

export async function listChargePlanAssignments(
  token: string,
  siteId: string,
  planId: string,
): Promise<ChargePlanAssignment[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charge-plans/${planId}/assignments`, {
    method: "GET",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan atamaları alınamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as ChargePlanAssignment[];
}

export async function createChargePlanAssignment(
  token: string,
  siteId: string,
  planId: string,
  payload: { flat_id: string },
): Promise<ChargePlanAssignment> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charge-plans/${planId}/assignments`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan ataması oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as ChargePlanAssignment;
}

export async function deleteChargePlanAssignment(
  token: string,
  siteId: string,
  planId: string,
  assignmentId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/charge-plans/${planId}/assignments/${assignmentId}`,
    {
      method: "DELETE",
      headers: buildTenantHeaders(token, siteId, false),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan ataması silinemedi (${response.status}): ${text}`);
  }
}

export async function generateChargesFromPlan(
  token: string,
  siteId: string,
  planId: string,
  payload: {
    period: string;
    due_date: string;
    status: ChargeStatus;
  },
): Promise<ChargePlanGenerateResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/charge-plans/${planId}/generate`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Plan üretimi başarısız (${response.status}): ${text}`);
  }
  return (await response.json()) as ChargePlanGenerateResult;
}

export async function listPaymentAllocations(
  token: string,
  siteId: string,
  params?: { payment_id?: string; charge_id?: string },
): Promise<PaymentAllocation[]> {
  const query = new URLSearchParams();
  if (params?.payment_id) query.set("payment_id", params.payment_id);
  if (params?.charge_id) query.set("charge_id", params.charge_id);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/payment-allocations${query.toString() ? `?${query.toString()}` : ""}`,
    {
      method: "GET",
      headers: buildTenantHeaders(token, siteId, false),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Tahsisler alınamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as PaymentAllocation[];
}

export async function createPaymentAllocation(
  token: string,
  siteId: string,
  payload: { payment_id: string; charge_id: string; allocated_amount: string },
): Promise<PaymentAllocation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/payment-allocations`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Tahsis oluşturulamadı (${response.status}): ${text}`);
  }
  return (await response.json()) as PaymentAllocation;
}

export async function deletePaymentAllocation(
  token: string,
  siteId: string,
  allocationId: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/payment-allocations/${allocationId}`, {
    method: "DELETE",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Tahsis silinemedi (${response.status}): ${text}`);
  }
}

export type NotificationType =
  | "charge_created"
  | "payment_received"
  | "charge_overdue"
  | "plan_generated";

export type Notification = {
  id: string;
  site_id: string;
  user_id: string | null;
  notification_type: NotificationType;
  title: string;
  body: string;
  related_flat_id: string | null;
  related_charge_id: string | null;
  related_payment_id: string | null;
  is_read: boolean;
  created_at: string;
};

export async function listNotifications(
  token: string,
  siteId: string,
  params?: { is_read?: boolean; limit?: number },
): Promise<Notification[]> {
  const query = new URLSearchParams();
  if (typeof params?.is_read === "boolean") query.set("is_read", String(params.is_read));
  if (params?.limit) query.set("limit", String(params.limit));

  const response = await fetch(
    `${API_BASE_URL}/api/v1/notifications${query.toString() ? `?${query.toString()}` : ""}`,
    { method: "GET", headers: buildTenantHeaders(token, siteId, false) },
  );
  if (!response.ok) throw new Error(`Bildirimler alınamadı (${response.status})`);
  return (await response.json()) as Notification[];
}

export async function getUnreadCount(token: string, siteId: string): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/unread-count`, {
    method: "GET",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) throw new Error(`Sayım alınamadı (${response.status})`);
  const data = (await response.json()) as { unread_count: number };
  return data.unread_count;
}

export async function markNotificationRead(
  token: string,
  siteId: string,
  notificationId: string,
): Promise<Notification> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/notifications/${notificationId}/read`,
    { method: "PATCH", headers: buildTenantHeaders(token, siteId, false) },
  );
  if (!response.ok) throw new Error(`Okundu işareti başarısız (${response.status})`);
  return (await response.json()) as Notification;
}

export async function markAllNotificationsRead(
  token: string,
  siteId: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/read-all`, {
    method: "PATCH",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) throw new Error(`Tümünü okundu işaretleme başarısız (${response.status})`);
}

export async function triggerOverdueNotifications(
  token: string,
  siteId: string,
): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/trigger-overdue`, {
    method: "POST",
    headers: buildTenantHeaders(token, siteId, false),
  });
  if (!response.ok) throw new Error(`Vade tetikleyici başarısız (${response.status})`);
  const data = (await response.json()) as { unread_count: number };
  return data.unread_count;
}

// ── Reports ──────────────────────────────────────────────────────────────────

export type PeriodChargeSummary = {
  charge_type: string;
  charge_count: number;
  total_amount: string;
  paid_amount: string;
  pending_amount: string;
  cancelled_amount: string;
};

export type PeriodSummaryReport = {
  site_id: string;
  period: string;
  total_charges: string;
  total_payments: string;
  total_allocated: string;
  collection_rate: string;
  charge_count: number;
  payment_count: number;
  by_charge_type: PeriodChargeSummary[];
};

export type FlatSummaryItem = {
  flat_id: string;
  unit_no: string;
  block_name: string;
  total_charges: string;
  total_payments: string;
  balance: string;
  pending_charge_count: number;
  overdue_charge_count: number;
};

export type FlatSummaryReport = {
  site_id: string;
  period: string | null;
  flat_count: number;
  items: FlatSummaryItem[];
};

export async function getPeriodSummary(
  token: string,
  siteId: string,
  period: string,
): Promise<PeriodSummaryReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/reports/period-summary?period=${encodeURIComponent(period)}`,
    { method: "GET", headers: buildTenantHeaders(token, siteId, false) },
  );
  if (!response.ok) throw new Error(`Dönem özeti alınamadı (${response.status})`);
  return (await response.json()) as PeriodSummaryReport;
}

export async function getFlatSummary(
  token: string,
  siteId: string,
  period?: string,
): Promise<FlatSummaryReport> {
  const query = period ? `?period=${encodeURIComponent(period)}` : "";
  const response = await fetch(
    `${API_BASE_URL}/api/v1/reports/flat-summary${query}`,
    { method: "GET", headers: buildTenantHeaders(token, siteId, false) },
  );
  if (!response.ok) throw new Error(`Daire özeti alınamadı (${response.status})`);
  return (await response.json()) as FlatSummaryReport;
}

export function buildCsvExportUrl(
  type: "charges" | "payments",
  siteId: string,
  period?: string,
  flatId?: string,
): string {
  const query = new URLSearchParams();
  if (period) query.set("period", period);
  if (flatId) query.set("flat_id", flatId);
  return `${API_BASE_URL}/api/v1/reports/export/${type}${query.toString() ? `?${query.toString()}` : ""}`;
}

// ---------------------------------------------------------------------------
// Sprint 8 — Bulk Charge & Scheduled Charges
// ---------------------------------------------------------------------------

export interface BulkChargeRequest {
  flat_ids?: string[];
  charge_type: string;
  period: string;
  amount: string;
  due_date: string;
  status?: string;
}

export interface BulkChargeResult {
  created: number;
  skipped: number;
  errors: string[];
}

export interface ScheduledCharge {
  id: string;
  site_id: string;
  charge_type: string;
  amount: string;
  day_of_month: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScheduledChargeRunResult {
  period: string;
  created: number;
  skipped: number;
  errors: string[];
}

export async function bulkCreateCharges(
  token: string,
  siteId: string,
  payload: BulkChargeRequest,
): Promise<BulkChargeResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/charges/bulk`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Site-Id": siteId,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Toplu borç oluşturulamadı");
  }
  return res.json() as Promise<BulkChargeResult>;
}

export async function getScheduledCharges(
  token: string,
  siteId: string,
): Promise<ScheduledCharge[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scheduled-charges`, {
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Zamanlanmış kurallar yüklenemedi");
  return res.json() as Promise<ScheduledCharge[]>;
}

export async function createScheduledCharge(
  token: string,
  siteId: string,
  payload: { charge_type: string; amount: string; day_of_month: number; active?: boolean },
): Promise<ScheduledCharge> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scheduled-charges`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Site-Id": siteId,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Kural oluşturulamadı");
  }
  return res.json() as Promise<ScheduledCharge>;
}

export async function updateScheduledCharge(
  token: string,
  siteId: string,
  scId: string,
  payload: Partial<{ charge_type: string; amount: string; day_of_month: number; active: boolean }>,
): Promise<ScheduledCharge> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scheduled-charges/${scId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Site-Id": siteId,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Kural güncellenemedi");
  }
  return res.json() as Promise<ScheduledCharge>;
}

export async function deleteScheduledCharge(
  token: string,
  siteId: string,
  scId: string,
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scheduled-charges/${scId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Kural silinemedi");
}

export async function runScheduledCharge(
  token: string,
  siteId: string,
  scId: string,
): Promise<ScheduledChargeRunResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scheduled-charges/${scId}/run`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Kural çalıştırılamadı");
  return res.json() as Promise<ScheduledChargeRunResult>;
}

export async function runAllScheduledCharges(
  token: string,
  siteId: string,
): Promise<ScheduledChargeRunResult[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/scheduled-charges/run-all`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Kurallar çalıştırılamadı");
  return res.json() as Promise<ScheduledChargeRunResult[]>;
}

// ---------------------------------------------------------------------------
// Sprint 9 — Resident Portal
// ---------------------------------------------------------------------------

export interface MyFlatInfo {
  flat_id: string;
  unit_no: string;
  block_name: string;
  floor: number;
  relation_type: string;
  move_in_date: string | null;
  move_out_date: string | null;
}

export interface MyChargeItem {
  id: string;
  flat_id: string;
  unit_no: string;
  block_name: string;
  charge_type: string;
  period: string;
  amount: string;
  due_date: string;
  status: string;
  paid_at: string | null;
}

export interface MyPaymentItem {
  id: string;
  flat_id: string;
  unit_no: string;
  block_name: string;
  amount: string;
  paid_at: string;
  method: string;
  reference_no: string | null;
  note: string | null;
}

export interface MyBalanceSummary {
  total_charges: string;
  total_payments: string;
  balance: string;
  pending_count: number;
  overdue_count: number;
}

export interface MyNotificationItem {
  id: string;
  notification_type: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

export async function getMyFlats(token: string, siteId: string): Promise<MyFlatInfo[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/me/flats`, {
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Daireler yüklenemedi");
  return res.json() as Promise<MyFlatInfo[]>;
}

export async function getMyCharges(
  token: string,
  siteId: string,
  period?: string,
  chargeStatus?: string,
): Promise<MyChargeItem[]> {
  const q = new URLSearchParams();
  if (period) q.set("period", period);
  if (chargeStatus) q.set("status", chargeStatus);
  const res = await fetch(
    `${API_BASE_URL}/api/v1/me/charges${q.toString() ? `?${q.toString()}` : ""}`,
    { headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId } },
  );
  if (!res.ok) throw new Error("Borçlar yüklenemedi");
  return res.json() as Promise<MyChargeItem[]>;
}

export async function getMyPayments(token: string, siteId: string): Promise<MyPaymentItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/me/payments`, {
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Ödemeler yüklenemedi");
  return res.json() as Promise<MyPaymentItem[]>;
}

export async function payMyCharge(
  token: string,
  siteId: string,
  payload: { charge_id: string; amount: string; method?: string; note?: string },
): Promise<MyPaymentItem> {
  const res = await fetch(`${API_BASE_URL}/api/v1/me/payments`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? `Ödeme başarısız (${res.status})`);
  }
  return res.json() as Promise<MyPaymentItem>;
}

export async function getMyBalance(token: string, siteId: string): Promise<MyBalanceSummary> {
  const res = await fetch(`${API_BASE_URL}/api/v1/me/balance`, {
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Bakiye yüklenemedi");
  return res.json() as Promise<MyBalanceSummary>;
}

export async function getMyNotifications(
  token: string,
  siteId: string,
  unreadOnly = false,
): Promise<MyNotificationItem[]> {
  const q = unreadOnly ? "?unread_only=true" : "";
  const res = await fetch(`${API_BASE_URL}/api/v1/me/notifications${q}`, {
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Bildirimler yüklenemedi");
  return res.json() as Promise<MyNotificationItem[]>;
}

// ---------------------------------------------------------------------------
// Sprint 10 — Analytics
// ---------------------------------------------------------------------------

export interface MonthlyTrendItem {
  period: string;
  total_charges: string;
  total_payments: string;
  collection_rate: string;
}

export interface FlatOccupancyStats {
  total_flats: number;
  active_flats: number;
  occupied_flats: number;
  vacant_flats: number;
}

export interface ChargeTypeBreakdownItem {
  charge_type: string;
  total_amount: string;
  charge_count: number;
}

export interface AnalyticsDashboardResponse {
  monthly_trend: MonthlyTrendItem[];
  occupancy: FlatOccupancyStats;
  charge_type_breakdown: ChargeTypeBreakdownItem[];
  avg_collection_rate: string;
}

export async function getAnalyticsDashboard(
  token: string,
  siteId: string,
  months = 12,
): Promise<AnalyticsDashboardResponse> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/analytics/dashboard?months=${months}`,
    { headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId } },
  );
  if (!res.ok) throw new Error("Analytics yüklenemedi");
  return res.json() as Promise<AnalyticsDashboardResponse>;
}

export async function getMonthlyTrend(
  token: string,
  siteId: string,
  months = 12,
): Promise<MonthlyTrendItem[]> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/analytics/monthly-trend?months=${months}`,
    { headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId } },
  );
  if (!res.ok) throw new Error("Trend verisi yüklenemedi");
  return res.json() as Promise<MonthlyTrendItem[]>;
}

// ---------------------------------------------------------------------------
// User Management
// ---------------------------------------------------------------------------

export type UserRole = "manager" | "accountant" | "resident";

export type UserResponse = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  site_id: string;
};

export type UserCreatePayload = {
  email: string;
  full_name: string;
  password: string;
  role: UserRole;
};

export type UserUpdatePayload = {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
};

export async function listUsers(token: string, siteId: string): Promise<UserResponse[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users`, {
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Kullanıcılar yüklenemedi");
  return res.json() as Promise<UserResponse[]>;
}

export async function createUser(
  token: string,
  siteId: string,
  payload: UserCreatePayload,
): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Site-Id": siteId,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Kullanıcı oluşturulamadı");
  }
  return res.json() as Promise<UserResponse>;
}

export async function updateUser(
  token: string,
  siteId: string,
  userId: string,
  payload: UserUpdatePayload,
): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Site-Id": siteId,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Kullanıcı güncellenemedi");
  return res.json() as Promise<UserResponse>;
}

export async function deleteUser(
  token: string,
  siteId: string,
  userId: string,
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
  });
  if (!res.ok) throw new Error("Kullanıcı silinemedi");
}
