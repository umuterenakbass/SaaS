"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  type ActionItem,
  type TodayActionsResponse,
  fetchCurrentUser,
  fetchTenantContext,
  getTodayActions,
  getUnreadCount,
} from "@/lib/api";
import { clearSession, getAccessToken, getSiteId } from "@/lib/auth-storage";

function StatCard({
  label,
  value,
  sub,
  color,
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color: string;
  icon: string;
}) {
  return (
    <div className={`rounded-xl border ${color} bg-white p-4 shadow-sm`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
        </div>
        <span className="text-2xl">{icon}</span>
      </div>
    </div>
  );
}

function ActionList({
  title,
  items,
  emptyText,
  badge,
  badgeColor,
  renderItem,
}: {
  title: string;
  items: ActionItem[];
  emptyText: string;
  badge?: number;
  badgeColor?: string;
  renderItem: (item: ActionItem) => React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, 5);

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-50">
        <h3 className="font-semibold text-gray-800 text-sm">{title}</h3>
        {badge !== undefined && badge > 0 && (
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-gray-400 px-4 py-4">{emptyText}</p>
      ) : (
        <>
          <ul className="divide-y divide-gray-50">
            {visible.map((item, i) => (
              <li key={i} className="px-4 py-3">
                {renderItem(item)}
              </li>
            ))}
          </ul>
          {items.length > 5 && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="w-full text-xs text-blue-500 hover:text-blue-700 py-2 border-t border-gray-50"
            >
              {expanded ? "Daha az göster" : `+${items.length - 5} daha göster`}
            </button>
          )}
        </>
      )}
    </div>
  );
}

const NAV_GROUPS = [
  {
    label: "Site Yönetimi",
    icon: "🏢",
    links: [
      { href: "/dashboard/onboarding", label: "🚀 Hızlı Kurulum", highlight: true },
      { href: "/dashboard/blocks", label: "Bloklar" },
      { href: "/dashboard/flats", label: "Daireler" },
      { href: "/dashboard/residents", label: "Sakinler" },
      { href: "/dashboard/users", label: "Kullanıcılar" },
    ],
  },
  {
    label: "Finans",
    icon: "💰",
    links: [
      { href: "/dashboard/charges", label: "Borçlar" },
      { href: "/dashboard/payments", label: "Ödemeler" },
      { href: "/dashboard/ledger", label: "Ekstre" },
      { href: "/dashboard/installments", label: "Taksit Planları" },
      { href: "/dashboard/allocations", label: "Tahsisler" },
    ],
  },
  {
    label: "Otomasyon",
    icon: "⚙️",
    links: [
      { href: "/dashboard/charge-plans", label: "Ödeme Planları" },
      { href: "/dashboard/bulk-charge", label: "Toplu Borç" },
      { href: "/dashboard/scheduled-charges", label: "Otomatik Kurallar" },
    ],
  },
  {
    label: "Raporlama",
    icon: "📊",
    links: [
      { href: "/dashboard/analytics", label: "Analytics" },
      { href: "/dashboard/reports", label: "Raporlar" },
    ],
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState("");
  const [siteName, setSiteName] = useState("");
  const [role, setRole] = useState("");
  const [unreadCount, setUnreadCount] = useState(0);
  const [actions, setActions] = useState<TodayActionsResponse | null>(null);

  useEffect(() => {
    const run = async () => {
      const token = getAccessToken();
      const storedSiteId = getSiteId();
      if (!token || !storedSiteId) { router.replace("/login"); return; }

      try {
        const [me, tenant] = await Promise.all([
          fetchCurrentUser(token),
          fetchTenantContext(token, storedSiteId),
        ]);
        setUserEmail(me.email);
        setSiteName(tenant.site_name ?? storedSiteId);
        setRole(tenant.role);

        try { setUnreadCount(await getUnreadCount(token, storedSiteId)); } catch { /* ignore */ }
        try { setActions(await getTodayActions(token, storedSiteId)); } catch { /* resident rolü erişemez */ }
      } catch {
        clearSession();
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400 text-sm animate-pulse">Yükleniyor...</div>
      </div>
    );
  }

  const isManager = ["admin", "manager", "accountant"].includes(role);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">{siteName || "Dashboard"}</h1>
          <p className="text-xs text-gray-400">{userEmail} · {role}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/notifications"
            className="relative text-gray-500 hover:text-gray-700"
          >
            <span className="text-xl">🔔</span>
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-4 h-4 rounded-full flex items-center justify-center font-bold">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </Link>
          <button
            onClick={() => { clearSession(); router.push("/login"); }}
            className="text-sm text-gray-400 hover:text-gray-600"
          >
            Çıkış
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">

        {/* Bugün ne yapmalıyım? */}
        {isManager && actions && (
          <>
            {/* KPI Özet */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard
                label="Vadesi Geçmiş"
                value={actions.overdue_count}
                sub={`${Number(actions.overdue_total).toLocaleString("tr-TR")} ₺`}
                color="border-red-200"
                icon="🔴"
              />
              <StatCard
                label="Bu Hafta Vadesi Dolacak"
                value={actions.due_this_week_count}
                sub={`${Number(actions.due_this_week_total).toLocaleString("tr-TR")} ₺`}
                color="border-amber-200"
                icon="⏰"
              />
              <StatCard
                label="Bugün Ödeme Yapan"
                value={actions.paid_today_count}
                sub={`${Number(actions.paid_today_total).toLocaleString("tr-TR")} ₺`}
                color="border-green-200"
                icon="✅"
              />
              <StatCard
                label="Bu Ay Tahsilat"
                value={`%${actions.collection_rate_this_month}`}
                color="border-blue-200"
                icon="📈"
              />
            </div>

            {/* Aksiyon Listeleri */}
            <div className="grid md:grid-cols-2 gap-4">
              <ActionList
                title="🔴 Vadesi Geçmiş Borçlar"
                items={actions.overdue_items}
                emptyText="Vadesi geçmiş borç yok 🎉"
                badge={actions.overdue_count}
                badgeColor="bg-red-100 text-red-700"
                renderItem={(item) => (
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {item.block_name} / {item.unit_no}
                      </p>
                      <p className="text-xs text-gray-400">{item.description}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-semibold text-red-600">
                        {Number(item.amount ?? 0).toLocaleString("tr-TR")} ₺
                      </p>
                      <p className="text-xs text-red-400">{item.days_overdue} gün</p>
                    </div>
                  </div>
                )}
              />

              <ActionList
                title="⏰ Bu Hafta Vadesi Dolacak"
                items={actions.due_this_week_items}
                emptyText="Bu hafta vadesi dolacak borç yok."
                badge={actions.due_this_week_count}
                badgeColor="bg-amber-100 text-amber-700"
                renderItem={(item) => (
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {item.block_name} / {item.unit_no}
                      </p>
                      <p className="text-xs text-gray-400">{item.description}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-semibold text-amber-700">
                        {Number(item.amount ?? 0).toLocaleString("tr-TR")} ₺
                      </p>
                      <p className="text-xs text-gray-400">{item.due_date}</p>
                    </div>
                  </div>
                )}
              />

              {actions.paid_today_items.length > 0 && (
                <ActionList
                  title="✅ Bugün Ödeme Yapanlar"
                  items={actions.paid_today_items}
                  emptyText=""
                  badge={actions.paid_today_count}
                  badgeColor="bg-green-100 text-green-700"
                  renderItem={(item) => (
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {item.block_name} / {item.unit_no}
                        </p>
                        <p className="text-xs text-gray-400">{item.description}</p>
                      </div>
                      <p className="text-sm font-semibold text-green-600">
                        +{Number(item.amount ?? 0).toLocaleString("tr-TR")} ₺
                      </p>
                    </div>
                  )}
                />
              )}
            </div>
          </>
        )}

        {/* Navigasyon */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.label} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-50">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {group.icon} {group.label}
                </h3>
              </div>
              <ul className="py-1">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className={`block px-4 py-2 text-sm transition-colors hover:bg-gray-50 ${
                        link.highlight
                          ? "text-blue-600 font-semibold"
                          : "text-gray-700"
                      }`}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

      </main>
    </div>
  );
}
