"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  MaintenanceRequest,
  MaintenanceStatus,
  listMaintenanceRequests,
  updateMaintenanceRequest,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const STATUS_LABELS: Record<MaintenanceStatus, string> = {
  open: "Açık",
  in_progress: "İşlemde",
  resolved: "Çözüldü",
  cancelled: "İptal",
};

const STATUS_COLORS: Record<MaintenanceStatus, string> = {
  open: "bg-rose-100 text-rose-700",
  in_progress: "bg-amber-100 text-amber-700",
  resolved: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-zinc-100 text-zinc-500",
};

const CATEGORY_LABELS: Record<string, string> = {
  electrical: "⚡ Elektrik",
  plumbing: "🔧 Tesisat",
  elevator: "🛗 Asansör",
  common_area: "🏢 Ortak Alan",
  heating: "🔥 Isıtma",
  other: "📋 Diğer",
};

export default function MaintenancePage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState<MaintenanceStatus | "">("");
  const [editNote, setEditNote] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function load() {
    try {
      setRequests(
        await listMaintenanceRequests(token!, siteId!, statusFilter || undefined)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yüklenemedi.");
    }
  }

  async function handleStatusChange(id: string, newStatus: MaintenanceStatus) {
    if (!token || !siteId) return;
    try {
      const updated = await updateMaintenanceRequest(token, siteId, id, {
        status: newStatus,
        admin_note: editNote[id],
      });
      setRequests((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Güncellenemedi.");
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Arıza / Talep Kayıtları</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      {/* Filter */}
      <div className="flex gap-2">
        {(["", "open", "in_progress", "resolved", "cancelled"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === s
                ? "bg-indigo-600 text-white"
                : "bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
            }`}
          >
            {s === "" ? "Tümü" : STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      <section className="space-y-3">
        {requests.length === 0 && (
          <p className="text-sm text-zinc-400">Bu filtrede talep yok.</p>
        )}
        {requests.map((req) => (
          <article
            key={req.id}
            className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500">
                    {CATEGORY_LABELS[req.category] ?? req.category}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[req.status]}`}
                  >
                    {STATUS_LABELS[req.status]}
                  </span>
                </div>
                <p className="mt-1 font-semibold text-zinc-900">{req.title}</p>
                <p className="text-sm text-zinc-600">{req.description}</p>
                <p className="mt-1 text-xs text-zinc-400">
                  {req.flat_block_name && req.flat_unit_no
                    ? `📍 ${req.flat_block_name} / ${req.flat_unit_no} · `
                    : ""}
                  {req.reporter_name ?? "—"} ·{" "}
                  {new Date(req.created_at).toLocaleDateString("tr-TR")}
                </p>
                {req.admin_note && (
                  <p className="mt-1 rounded bg-zinc-50 px-2 py-1 text-xs text-zinc-500">
                    Not: {req.admin_note}
                  </p>
                )}
              </div>

              {/* Admin actions */}
              <div className="flex flex-col gap-2 min-w-52">
                <textarea
                  placeholder="Admin notu…"
                  value={editNote[req.id] ?? req.admin_note ?? ""}
                  onChange={(e) =>
                    setEditNote((prev) => ({ ...prev, [req.id]: e.target.value }))
                  }
                  rows={2}
                  className="rounded-lg border border-zinc-300 px-2 py-1 text-xs"
                />
                <div className="flex gap-1 flex-wrap">
                  {(["open", "in_progress", "resolved", "cancelled"] as MaintenanceStatus[])
                    .filter((s) => s !== req.status)
                    .map((s) => (
                      <button
                        key={s}
                        onClick={() => void handleStatusChange(req.id, s)}
                        className={`rounded-lg border px-2 py-1 text-xs font-medium transition-colors ${STATUS_COLORS[s]} border-transparent`}
                      >
                        → {STATUS_LABELS[s]}
                      </button>
                    ))}
                </div>
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
