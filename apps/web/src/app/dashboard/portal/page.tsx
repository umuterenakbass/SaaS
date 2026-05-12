"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  MyBalanceSummary,
  MyChargeItem,
  MyFlatInfo,
  MyNotificationItem,
  MyPaymentItem,
  getMyBalance,
  getMyCharges,
  getMyFlats,
  getMyNotifications,
  getMyPayments,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const CHARGE_STATUS_LABELS: Record<string, string> = {
  pending: "Bekliyor",
  paid: "Ödendi",
  partially_paid: "Kısmi Ödendi",
  overdue: "Vadesi Geçti",
  cancelled: "İptal",
};

const CHARGE_STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  paid: "bg-emerald-100 text-emerald-700",
  partially_paid: "bg-sky-100 text-sky-700",
  overdue: "bg-rose-100 text-rose-700",
  cancelled: "bg-zinc-100 text-zinc-500",
};

type Tab = "overview" | "charges" | "payments" | "notifications";

export default function ResidentPortalPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [flats, setFlats] = useState<MyFlatInfo[]>([]);
  const [balance, setBalance] = useState<MyBalanceSummary | null>(null);
  const [charges, setCharges] = useState<MyChargeItem[]>([]);
  const [payments, setPayments] = useState<MyPaymentItem[]>([]);
  const [notifications, setNotifications] = useState<MyNotificationItem[]>([]);

  // Charge filters
  const [filterPeriod, setFilterPeriod] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    if (!token || !siteId) {
      router.replace("/login");
      return;
    }
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [flatsData, balanceData, chargesData, paymentsData, notifData] =
        await Promise.all([
          getMyFlats(token!, siteId!),
          getMyBalance(token!, siteId!),
          getMyCharges(token!, siteId!),
          getMyPayments(token!, siteId!),
          getMyNotifications(token!, siteId!),
        ]);
      setFlats(flatsData);
      setBalance(balanceData);
      setCharges(chargesData);
      setPayments(paymentsData);
      setNotifications(notifData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }

  async function applyChargeFilters() {
    if (!token || !siteId) return;
    try {
      const data = await getMyCharges(
        token,
        siteId,
        filterPeriod || undefined,
        filterStatus || undefined,
      );
      setCharges(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Borçlar filtrelenemedi.");
    }
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Genel Bakış" },
    { key: "charges", label: "Borçlarım" },
    { key: "payments", label: "Ödemelerim" },
    { key: "notifications", label: `Bildirimler${unreadCount > 0 ? ` (${unreadCount})` : ""}` },
  ];

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <p className="text-sm text-zinc-500">Yükleniyor…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-10">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6">

        {/* Header */}
        <header className="flex items-center justify-between rounded-2xl bg-indigo-600 p-6 text-white shadow-sm">
          <div>
            <h1 className="text-2xl font-semibold">Sakin Portalı</h1>
            <p className="mt-1 text-sm text-indigo-100">Hesabınızı ve borçlarınızı yönetin.</p>
          </div>
          <Link
            href="/dashboard"
            className="rounded-lg bg-white/20 px-4 py-2 text-sm font-medium text-white hover:bg-white/30"
          >
            ← Dashboard
          </Link>
        </header>

        {error && (
          <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-600">{error}</p>
        )}

        {/* Tabs */}
        <nav className="flex gap-1 rounded-xl border border-zinc-200 bg-white p-1 shadow-sm">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-indigo-600 text-white"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* ── OVERVIEW ── */}
        {activeTab === "overview" && (
          <div className="flex flex-col gap-4">
            {/* Balance Cards */}
            {balance && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-medium text-zinc-500">Toplam Borç</p>
                  <p className="mt-1 text-xl font-bold text-zinc-900">
                    ₺{Number(balance.total_charges).toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                  </p>
                </article>
                <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-medium text-zinc-500">Toplam Ödeme</p>
                  <p className="mt-1 text-xl font-bold text-emerald-600">
                    ₺{Number(balance.total_payments).toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                  </p>
                </article>
                <article
                  className={`rounded-xl border p-4 shadow-sm ${
                    Number(balance.balance) > 0
                      ? "border-rose-200 bg-rose-50"
                      : "border-emerald-200 bg-emerald-50"
                  }`}
                >
                  <p className="text-xs font-medium text-zinc-500">Net Bakiye</p>
                  <p
                    className={`mt-1 text-xl font-bold ${
                      Number(balance.balance) > 0 ? "text-rose-600" : "text-emerald-600"
                    }`}
                  >
                    ₺{Number(balance.balance).toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                  </p>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {Number(balance.balance) > 0 ? "Borçlusunuz" : "Alacaklısınız"}
                  </p>
                </article>
                <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-medium text-zinc-500">Bekleyen / Vadesi Geçmiş</p>
                  <p className="mt-1 text-xl font-bold text-zinc-900">
                    {balance.pending_count}
                    {balance.overdue_count > 0 && (
                      <span className="ml-1 text-sm font-medium text-rose-600">
                        ({balance.overdue_count} gecikmiş)
                      </span>
                    )}
                  </p>
                </article>
              </div>
            )}

            {/* My Flats */}
            <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
              <h2 className="border-b border-zinc-100 px-6 py-4 text-sm font-semibold text-zinc-800">
                Dairelerim
              </h2>
              {flats.length === 0 ? (
                <p className="px-6 py-6 text-sm text-zinc-500">Kayıtlı daire bulunamadı.</p>
              ) : (
                <ul className="divide-y divide-zinc-100">
                  {flats.map((f) => (
                    <li key={f.flat_id} className="flex items-center justify-between px-6 py-4">
                      <div>
                        <p className="font-medium text-zinc-900">
                          {f.block_name} — {f.unit_no}
                        </p>
                        <p className="text-sm text-zinc-500">
                          {f.floor}. Kat ·{" "}
                          {f.relation_type === "owner" ? "Mülk Sahibi" : "Kiracı"}
                        </p>
                      </div>
                      <div className="text-right text-sm text-zinc-400">
                        {f.move_in_date && <p>Giriş: {f.move_in_date}</p>}
                        {f.move_out_date && <p>Çıkış: {f.move_out_date}</p>}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}

        {/* ── CHARGES ── */}
        {activeTab === "charges" && (
          <div className="flex flex-col gap-4">
            {/* Filters */}
            <div className="flex flex-wrap gap-3 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <input
                type="month"
                value={filterPeriod}
                onChange={(e) => setFilterPeriod(e.target.value.replace("-", "").slice(0, 6))}
                placeholder="Dönem (YYYY-MM)"
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Tüm Durumlar</option>
                <option value="pending">Bekliyor</option>
                <option value="paid">Ödendi</option>
                <option value="partially_paid">Kısmi Ödendi</option>
                <option value="overdue">Vadesi Geçti</option>
                <option value="cancelled">İptal</option>
              </select>
              <button
                onClick={() => void applyChargeFilters()}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
              >
                Filtrele
              </button>
              <button
                onClick={() => { setFilterPeriod(""); setFilterStatus(""); void loadAll(); }}
                className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50"
              >
                Temizle
              </button>
            </div>

            <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
              {charges.length === 0 ? (
                <p className="px-6 py-8 text-sm text-zinc-500">Borç bulunamadı.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead className="border-b border-zinc-100 text-xs font-medium text-zinc-500">
                    <tr>
                      <th className="px-6 py-3 text-left">Daire</th>
                      <th className="px-6 py-3 text-left">Tür</th>
                      <th className="px-6 py-3 text-left">Dönem</th>
                      <th className="px-6 py-3 text-right">Tutar</th>
                      <th className="px-6 py-3 text-left">Vade</th>
                      <th className="px-6 py-3 text-left">Durum</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {charges.map((c) => (
                      <tr key={c.id} className="hover:bg-zinc-50">
                        <td className="px-6 py-3 font-medium text-zinc-900">
                          {c.block_name} — {c.unit_no}
                        </td>
                        <td className="px-6 py-3 text-zinc-600">{c.charge_type}</td>
                        <td className="px-6 py-3 text-zinc-600">{c.period}</td>
                        <td className="px-6 py-3 text-right font-medium text-zinc-900">
                          ₺{Number(c.amount).toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-3 text-zinc-600">{c.due_date}</td>
                        <td className="px-6 py-3">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              CHARGE_STATUS_COLORS[c.status] ?? "bg-zinc-100 text-zinc-500"
                            }`}
                          >
                            {CHARGE_STATUS_LABELS[c.status] ?? c.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </div>
        )}

        {/* ── PAYMENTS ── */}
        {activeTab === "payments" && (
          <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
            {payments.length === 0 ? (
              <p className="px-6 py-8 text-sm text-zinc-500">Ödeme kaydı bulunamadı.</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="border-b border-zinc-100 text-xs font-medium text-zinc-500">
                  <tr>
                    <th className="px-6 py-3 text-left">Daire</th>
                    <th className="px-6 py-3 text-right">Tutar</th>
                    <th className="px-6 py-3 text-left">Tarih</th>
                    <th className="px-6 py-3 text-left">Yöntem</th>
                    <th className="px-6 py-3 text-left">Referans</th>
                    <th className="px-6 py-3 text-left">Not</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {payments.map((p) => (
                    <tr key={p.id} className="hover:bg-zinc-50">
                      <td className="px-6 py-3 font-medium text-zinc-900">
                        {p.block_name} — {p.unit_no}
                      </td>
                      <td className="px-6 py-3 text-right font-medium text-emerald-600">
                        ₺{Number(p.amount).toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-3 text-zinc-600">{p.paid_at.slice(0, 10)}</td>
                      <td className="px-6 py-3 text-zinc-600 capitalize">{p.method}</td>
                      <td className="px-6 py-3 text-zinc-500">{p.reference_no ?? "—"}</td>
                      <td className="px-6 py-3 text-zinc-500">{p.note ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}

        {/* ── NOTIFICATIONS ── */}
        {activeTab === "notifications" && (
          <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
            {notifications.length === 0 ? (
              <p className="px-6 py-8 text-sm text-zinc-500">Bildirim bulunamadı.</p>
            ) : (
              <ul className="divide-y divide-zinc-100">
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    className={`px-6 py-4 ${!n.is_read ? "bg-indigo-50" : ""}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className={`font-medium text-zinc-900 ${!n.is_read ? "font-semibold" : ""}`}>
                          {n.title}
                        </p>
                        <p className="mt-1 text-sm text-zinc-600">{n.body}</p>
                        <p className="mt-1 text-xs text-zinc-400">
                          {n.notification_type} · {n.created_at.slice(0, 10)}
                        </p>
                      </div>
                      {!n.is_read && (
                        <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-indigo-500" />
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

      </main>
    </div>
  );
}
