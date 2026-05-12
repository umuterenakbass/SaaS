"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ScheduledCharge,
  ScheduledChargeRunResult,
  createScheduledCharge,
  deleteScheduledCharge,
  getScheduledCharges,
  runAllScheduledCharges,
  runScheduledCharge,
  updateScheduledCharge,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ScheduledChargesPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [rules, setRules] = useState<ScheduledCharge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runResults, setRunResults] = useState<ScheduledChargeRunResult[] | null>(null);

  // Form state
  const [formType, setFormType] = useState("aidat");
  const [formAmount, setFormAmount] = useState("");
  const [formDay, setFormDay] = useState("5");
  const [formActive, setFormActive] = useState(true);
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    if (!token || !siteId) {
      router.replace("/login");
      return;
    }
    void loadRules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadRules = async () => {
    if (!token || !siteId) return;
    setLoading(true);
    try {
      setRules(await getScheduledCharges(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kurallar yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !siteId) return;
    setFormLoading(true);
    setError(null);
    try {
      await createScheduledCharge(token, siteId, {
        charge_type: formType,
        amount: formAmount,
        day_of_month: Number(formDay),
        active: formActive,
      });
      setFormType("aidat");
      setFormAmount("");
      setFormDay("5");
      setFormActive(true);
      await loadRules();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kural oluşturulamadı.");
    } finally {
      setFormLoading(false);
    }
  };

  const handleToggleActive = async (sc: ScheduledCharge) => {
    if (!token || !siteId) return;
    try {
      await updateScheduledCharge(token, siteId, sc.id, { active: !sc.active });
      await loadRules();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Güncelleme başarısız.");
    }
  };

  const handleDelete = async (scId: string) => {
    if (!token || !siteId) return;
    if (!confirm("Bu kuralı silmek istiyor musunuz?")) return;
    try {
      await deleteScheduledCharge(token, siteId, scId);
      await loadRules();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Silme başarısız.");
    }
  };

  const handleRun = async (scId: string) => {
    if (!token || !siteId) return;
    try {
      const res = await runScheduledCharge(token, siteId, scId);
      setRunResults([res]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kural çalıştırılamadı.");
    }
  };

  const handleRunAll = async () => {
    if (!token || !siteId) return;
    try {
      const res = await runAllScheduledCharges(token, siteId);
      setRunResults(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kurallar çalıştırılamadı.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Zamanlanmış Borçlar</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => void handleRunAll()}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
          >
            ▶ Tümünü Çalıştır
          </button>
          <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
            Dashboard
          </Link>
        </div>
      </header>

      {error ? (
        <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>
      ) : null}

      {/* Yeni Kural Formu */}
      <form
        onSubmit={(e) => void handleCreate(e)}
        className="rounded-xl bg-white p-5 shadow-sm space-y-4"
      >
        <h2 className="font-semibold text-zinc-800">Yeni Kural Ekle</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700">Borç Tipi</label>
            <input
              required
              value={formType}
              onChange={(e) => setFormType(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700">Tutar (₺)</label>
            <input
              required
              type="number"
              step="0.01"
              min="0.01"
              value={formAmount}
              onChange={(e) => setFormAmount(e.target.value)}
              placeholder="1500.00"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700">Ayın Kaçı (1-28)</label>
            <input
              required
              type="number"
              min="1"
              max="28"
              value={formDay}
              onChange={(e) => setFormDay(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            />
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm text-zinc-700">
          <input
            type="checkbox"
            checked={formActive}
            onChange={(e) => setFormActive(e.target.checked)}
            className="h-4 w-4"
          />
          Aktif
        </label>
        <button
          type="submit"
          disabled={formLoading}
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white disabled:bg-zinc-300"
        >
          {formLoading ? "Kaydediliyor..." : "Kural Ekle"}
        </button>
      </form>

      {/* Kural Listesi */}
      {loading ? (
        <p className="text-sm text-zinc-500">Yükleniyor...</p>
      ) : rules.length === 0 ? (
        <p className="text-sm text-zinc-500">Henüz kural yok.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3">Borç Tipi</th>
                <th className="px-4 py-3">Tutar</th>
                <th className="px-4 py-3">Vade (gün)</th>
                <th className="px-4 py-3">Durum</th>
                <th className="px-4 py-3">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {rules.map((sc) => (
                <tr key={sc.id}>
                  <td className="px-4 py-3 font-medium text-zinc-900">{sc.charge_type}</td>
                  <td className="px-4 py-3 text-zinc-700">{sc.amount} ₺</td>
                  <td className="px-4 py-3 text-zinc-700">{sc.day_of_month}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => void handleToggleActive(sc)}
                      className={`rounded-full px-3 py-1 text-xs font-medium ${
                        sc.active
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-zinc-100 text-zinc-500"
                      }`}
                    >
                      {sc.active ? "Aktif" : "Pasif"}
                    </button>
                  </td>
                  <td className="flex gap-2 px-4 py-3">
                    <button
                      onClick={() => void handleRun(sc.id)}
                      className="rounded-lg bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700"
                    >
                      ▶ Çalıştır
                    </button>
                    <button
                      onClick={() => void handleDelete(sc.id)}
                      className="rounded-lg bg-rose-100 px-3 py-1 text-xs font-medium text-rose-700"
                    >
                      Sil
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Çalıştırma Sonuçları */}
      {runResults && runResults.length > 0 && (
        <section className="space-y-2">
          <h2 className="font-semibold text-zinc-800">Çalıştırma Sonuçları</h2>
          {runResults.map((r, i) => (
            <div key={i} className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-zinc-700">Dönem: {r.period}</p>
              <div className="mt-2 flex gap-4 text-sm">
                <span className="text-emerald-700">✓ {r.created} oluşturuldu</span>
                <span className="text-amber-600">⊘ {r.skipped} atlandı</span>
                {r.errors.length > 0 && (
                  <span className="text-rose-600">✕ {r.errors.length} hata</span>
                )}
              </div>
            </div>
          ))}
        </section>
      )}
    </main>
  );
}
