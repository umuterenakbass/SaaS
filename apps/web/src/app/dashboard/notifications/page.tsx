"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  Notification,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  triggerOverdueNotifications,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const TYPE_LABELS: Record<string, string> = {
  charge_created: "Borç Oluşturuldu",
  payment_received: "Ödeme Alındı",
  charge_overdue: "Vadesi Geçti",
  plan_generated: "Plan Üretildi",
};

const TYPE_COLORS: Record<string, string> = {
  charge_created: "bg-blue-50 border-blue-200",
  payment_received: "bg-emerald-50 border-emerald-200",
  charge_overdue: "bg-rose-50 border-rose-200",
  plan_generated: "bg-amber-50 border-amber-200",
};

export default function NotificationsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [onlyUnread, setOnlyUnread] = useState(false);
  const [overdueResult, setOverdueResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async (unread = onlyUnread) => {
    if (!token || !siteId) return;
    try {
      const data = await listNotifications(token, siteId, {
        is_read: unread ? false : undefined,
        limit: 100,
      });
      setNotifications(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bildirimler yüklenemedi.");
    }
  };

  useEffect(() => {
    if (!token || !siteId) {
      router.replace("/login");
      return;
    }
    void refresh();
  }, [router, siteId, token]);

  const handleMarkRead = async (id: string) => {
    if (!token || !siteId) return;
    try {
      await markNotificationRead(token, siteId, id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "İşlem başarısız.");
    }
  };

  const handleMarkAll = async () => {
    if (!token || !siteId) return;
    try {
      await markAllNotificationsRead(token, siteId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "İşlem başarısız.");
    }
  };

  const handleTriggerOverdue = async () => {
    if (!token || !siteId) return;
    try {
      const count = await triggerOverdueNotifications(token, siteId);
      setOverdueResult(
        count > 0
          ? `${count} yeni vade geçmiş bildirimi oluşturuldu.`
          : "Yeni vadesi geçmiş borç bulunamadı.",
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Vade tetikleyici başarısız.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Bildirimler</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <section className="flex flex-wrap gap-3">
        <button
          onClick={() => {
            const next = !onlyUnread;
            setOnlyUnread(next);
            void refresh(next);
          }}
          className={`rounded-lg border px-4 py-2 text-sm font-medium ${onlyUnread ? "border-indigo-400 bg-indigo-50 text-indigo-700" : "border-zinc-300 bg-white text-zinc-700"}`}
        >
          {onlyUnread ? "Tümünü Göster" : "Sadece Okunmayanlar"}
        </button>
        <button
          onClick={() => void handleMarkAll()}
          className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700"
        >
          Tümünü Okundu İşaretle
        </button>
        <button
          onClick={() => void handleTriggerOverdue()}
          className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white"
        >
          Vadesi Geçenleri Tara
        </button>
      </section>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {overdueResult ? <p className="text-sm text-amber-700">{overdueResult}</p> : null}

      <section className="space-y-2">
        {notifications.length === 0 ? (
          <p className="text-sm text-zinc-500">Bildirim yok.</p>
        ) : null}
        {notifications.map((notif) => (
          <article
            key={notif.id}
            className={`flex items-start justify-between rounded-lg border p-4 ${TYPE_COLORS[notif.notification_type] ?? "bg-white border-zinc-200"} ${notif.is_read ? "opacity-60" : ""}`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  {TYPE_LABELS[notif.notification_type] ?? notif.notification_type}
                </span>
                {!notif.is_read && (
                  <span className="h-2 w-2 rounded-full bg-indigo-500" />
                )}
              </div>
              <p className="mt-1 font-medium text-zinc-900">{notif.title}</p>
              <p className="text-sm text-zinc-600">{notif.body}</p>
              <p className="mt-1 text-xs text-zinc-400">
                {new Date(notif.created_at).toLocaleString("tr-TR")}
              </p>
            </div>
            {!notif.is_read && (
              <button
                onClick={() => void handleMarkRead(notif.id)}
                className="ml-4 shrink-0 rounded border border-zinc-300 px-2 py-1 text-xs text-zinc-600"
              >
                Okundu
              </button>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
