"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { MyChargeItem, getMyCharges } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ResidentChargesPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [charges, setCharges] = useState<MyChargeItem[]>([]);
  const [period, setPeriod] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = async () => {
    if (!token || !siteId) return;
    setLoading(true);
    setError(null);
    try {
      setCharges(await getMyCharges(token, siteId, period || undefined, statusFilter || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Borçlar yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  const statusLabel = (s: string) => ({ pending: "Bekliyor", paid: "Ödendi", cancelled: "İptal" }[s] ?? s);
  const statusColor = (s: string) => ({ pending: "text-amber-700", paid: "text-emerald-700", cancelled: "text-zinc-400" }[s] ?? "");

  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Borçlarım</h1>
        <Link href="/resident" className="text-sm font-medium text-indigo-600">← Ana Sayfa</Link>
      </header>

      {/* Filtreler */}
      <div className="flex flex-wrap gap-3 rounded-xl bg-white p-4 shadow-sm">
        <input
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          placeholder="Dönem (2026-05)"
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
        >
          <option value="">Tüm durumlar</option>
          <option value="pending">Bekliyor</option>
          <option value="paid">Ödendi</option>
          <option value="cancelled">İptal</option>
        </select>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:bg-zinc-300"
        >
          {loading ? "Yükleniyor..." : "Filtrele"}
        </button>
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {charges.length === 0 && !loading ? (
        <p className="text-sm text-zinc-500">Borç bulunamadı.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3">Daire</th>
                <th className="px-4 py-3">Tür</th>
                <th className="px-4 py-3">Dönem</th>
                <th className="px-4 py-3">Tutar</th>
                <th className="px-4 py-3">Vade</th>
                <th className="px-4 py-3">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {charges.map((c) => (
                <tr key={c.id}>
                  <td className="px-4 py-3 text-zinc-700">{c.block_name} / {c.unit_no}</td>
                  <td className="px-4 py-3 font-medium text-zinc-900">{c.charge_type}</td>
                  <td className="px-4 py-3 text-zinc-700">{c.period}</td>
                  <td className="px-4 py-3 text-zinc-700">{c.amount} ₺</td>
                  <td className="px-4 py-3 text-zinc-500">{c.due_date}</td>
                  <td className={`px-4 py-3 font-medium ${statusColor(c.status)}`}>{statusLabel(c.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
