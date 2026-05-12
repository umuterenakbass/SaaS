"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { MyNotificationItem, getMyNotifications } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const typeLabel = (t: string) =>
  ({
    charge_created: "Yeni Borç",
    payment_received: "Ödeme Alındı",
    charge_overdue: "Vadesi Geçti",
    plan_generated: "Plan Üretildi",
  }[t] ?? t);

const typeColor = (t: string) =>
  ({
    charge_created: "bg-amber-100 text-amber-700",
    payment_received: "bg-emerald-100 text-emerald-700",
    charge_overdue: "bg-rose-100 text-rose-700",
    plan_generated: "bg-indigo-100 text-indigo-700",
  }[t] ?? "bg-zinc-100 text-zinc-600");

export default function ResidentNotificationsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [notifications, setNotifications] = useState<MyNotificationItem[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async (unread: boolean) => {
    if (!token || !siteId) return;
    setLoading(true);
    setError(null);
    try {
      setNotifications(await getMyNotifications(token, siteId, unread));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bildirimler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void load(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggle = (val: boolean) => {
    setUnreadOnly(val);
    void load(val);
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Bildirimler</h1>
        <Link href="/resident" className="text-sm font-medium text-indigo-600">← Ana Sayfa</Link>
      </header>

      <label className="flex items-center gap-2 text-sm text-zinc-700">
        <input
          type="checkbox"
          checked={unreadOnly}
          onChange={(e) => handleToggle(e.target.checked)}
          className="h-4 w-4"
        />
        Sadece okunmamışlar
      </label>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {loading ? <p className="text-sm text-zinc-500">Yükleniyor...</p> : null}

      {!loading && notifications.length === 0 ? (
        <p className="text-sm text-zinc-500">Bildirim bulunamadı.</p>
      ) : (
        <ul className="space-y-3">
          {notifications.map((n) => (
            <li
              key={n.id}
              className={`rounded-xl border p-4 shadow-sm ${
                n.is_read ? "border-zinc-200 bg-white" : "border-indigo-200 bg-indigo-50"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${typeColor(n.notification_type)}`}>
                      {typeLabel(n.notification_type)}
                    </span>
                    {!n.is_read && (
                      <span className="h-2 w-2 rounded-full bg-indigo-500" />
                    )}
                  </div>
                  <p className="mt-1 font-medium text-zinc-900">{n.title}</p>
                  <p className="mt-0.5 text-sm text-zinc-600">{n.body}</p>
                </div>
                <p className="shrink-0 text-xs text-zinc-400">{n.created_at.slice(0, 10)}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
