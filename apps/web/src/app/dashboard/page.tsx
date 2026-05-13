"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  OverdueChargeItem,
  TopDebtorItem,
  fetchCurrentUser,
  fetchTenantContext,
  getOverdueCharges,
  getTopDebtors,
  getUnreadCount,
} from "@/lib/api";
import { clearSession, getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");
  const [siteId, setSiteId] = useState<string>("");
  const [role, setRole] = useState<string>("");
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [overdueList, setOverdueList] = useState<OverdueChargeItem[]>([]);
  const [topDebtors, setTopDebtors] = useState<TopDebtorItem[]>([]);

  useEffect(() => {
    const run = async () => {
      const token = getAccessToken();
      const storedSiteId = getSiteId();

      if (!token || !storedSiteId) {
        router.replace("/login");
        return;
      }

      try {
        const me = await fetchCurrentUser(token);
        const tenant = await fetchTenantContext(token, storedSiteId);

        setUserEmail(me.email);
        setSiteId(tenant.site_id);
        setRole(tenant.role);

        // Bildirim sayısı
        try { setUnreadCount(await getUnreadCount(token, storedSiteId)); } catch { /* ignore */ }

        // Vadesi geçmiş + en borçlu daireler (sadece manager/admin görebilir)
        try {
          const [overdue, debtors] = await Promise.all([
            getOverdueCharges(token, storedSiteId, 5),
            getTopDebtors(token, storedSiteId, 5),
          ]);
          setOverdueList(overdue);
          setTopDebtors(debtors);
        } catch { /* ignore — resident rolü erişemez */ }

      } catch (err) {
        clearSession();
        setError(err instanceof Error ? err.message : "Dashboard yüklenemedi.");
        router.replace("/login");
        return;
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [router]);

  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };

  if (loading) {
    return <div className="p-8 text-sm text-zinc-600">Dashboard yükleniyor...</div>;
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-10">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="rounded-2xl bg-indigo-600 p-6 text-white shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Yönetici Dashboard</h1>
              <p className="mt-1 text-sm text-indigo-200">{userEmail} · {role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg border border-indigo-400 px-3 py-1.5 text-sm text-white"
            >
              Çıkış
            </button>
          </div>
        </header>

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        {/* İstatistik Kartları */}
        {(overdueList.length > 0 || topDebtors.length > 0) && (
          <section className="grid gap-4 md:grid-cols-2">
            {/* Vadesi Geçmiş Borçlar */}
            {overdueList.length > 0 && (
              <article className="rounded-xl border border-rose-200 bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-rose-100 px-4 py-3">
                  <h2 className="font-semibold text-rose-700">⚠ Vadesi Geçmiş Borçlar</h2>
                  <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-bold text-rose-700">
                    {overdueList.length}
                  </span>
                </div>
                <ul className="divide-y divide-zinc-50">
                  {overdueList.map((item) => (
                    <li key={item.charge_id} className="flex items-center justify-between px-4 py-2.5">
                      <div>
                        <p className="text-sm font-medium text-zinc-900">
                          {item.block_name} / {item.unit_no} — {item.charge_type}
                        </p>
                        <p className="text-xs text-zinc-500">{item.period} · {item.days_overdue} gün gecikmiş</p>
                      </div>
                      <span className="text-sm font-semibold text-rose-700">{item.amount} ₺</span>
                    </li>
                  ))}
                </ul>
                <div className="px-4 py-2">
                  <Link href="/dashboard/charges" className="text-xs font-medium text-indigo-600">
                    Tümünü gör →
                  </Link>
                </div>
              </article>
            )}

            {/* En Borçlu Daireler */}
            {topDebtors.length > 0 && (
              <article className="rounded-xl border border-amber-200 bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-amber-100 px-4 py-3">
                  <h2 className="font-semibold text-amber-700">📊 En Borçlu Daireler</h2>
                </div>
                <ul className="divide-y divide-zinc-50">
                  {topDebtors.map((item, idx) => (
                    <li key={item.flat_id} className="flex items-center justify-between px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-100 text-xs font-bold text-amber-700">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-zinc-900">
                            {item.block_name} / {item.unit_no}
                          </p>
                          <p className="text-xs text-zinc-500">{item.pending_charge_count} bekleyen borç</p>
                        </div>
                      </div>
                      <span className="text-sm font-semibold text-amber-700">{item.total_debt} ₺</span>
                    </li>
                  ))}
                </ul>
                <div className="px-4 py-2">
                  <Link href="/dashboard/analytics" className="text-xs font-medium text-indigo-600">
                    Analytics →
                  </Link>
                </div>
              </article>
            )}
          </section>
        )}

        {/* Navigasyon */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Yönetim</h2>
          <div className="flex flex-wrap gap-2">
            {[
              { href: "/dashboard/users", label: "Kullanıcı Yönetimi", color: "bg-indigo-600" },
              { href: "/dashboard/blocks", label: "Blok Yönetimi", color: "bg-indigo-600" },
              { href: "/dashboard/flats", label: "Daire Yönetimi", color: "bg-indigo-600" },
              { href: "/dashboard/residents", label: "Sakin İlişkileri", color: "bg-indigo-600" },
              { href: "/dashboard/portal", label: "Sakin Portalı", color: "bg-indigo-500" },
            ].map((l) => (
              <Link key={l.href} href={l.href} className={`rounded-lg ${l.color} px-4 py-2 text-sm font-medium text-white`}>
                {l.label}
              </Link>
            ))}
          </div>

          <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Finans</h2>
          <div className="flex flex-wrap gap-2">
            {[
              { href: "/dashboard/charges", label: "Borç Yönetimi", color: "bg-emerald-600" },
              { href: "/dashboard/payments", label: "Ödeme Yönetimi", color: "bg-emerald-600" },
              { href: "/dashboard/ledger", label: "Ekstre / Bakiye", color: "bg-emerald-600" },
              { href: "/dashboard/installments", label: "Taksit Planları", color: "bg-emerald-700" },
              { href: "/dashboard/allocations", label: "Tahsis Yönetimi", color: "bg-emerald-600" },
            ].map((l) => (
              <Link key={l.href} href={l.href} className={`rounded-lg ${l.color} px-4 py-2 text-sm font-medium text-white`}>
                {l.label}
              </Link>
            ))}
          </div>

          <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Otomasyon & Raporlama</h2>
          <div className="flex flex-wrap gap-2">
            {[
              { href: "/dashboard/charge-plans", label: "Plan Yönetimi", color: "bg-amber-600" },
              { href: "/dashboard/bulk-charge", label: "Toplu Borç", color: "bg-violet-600" },
              { href: "/dashboard/scheduled-charges", label: "Otomatik Kurallar", color: "bg-violet-600" },
              { href: "/dashboard/analytics", label: "Analytics", color: "bg-sky-600" },
              { href: "/dashboard/reports", label: "Raporlar", color: "bg-sky-600" },
              {
                href: "/dashboard/notifications",
                label: unreadCount > 0 ? `Bildirimler (${unreadCount})` : "Bildirimler",
                color: "bg-zinc-700",
              },
            ].map((l) => (
              <Link key={l.href} href={l.href} className={`rounded-lg ${l.color} px-4 py-2 text-sm font-medium text-white`}>
                {l.label}
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}


