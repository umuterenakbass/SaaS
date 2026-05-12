"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  BulkChargeResult,
  bulkCreateCharges,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function BulkChargePage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [chargeType, setChargeType] = useState("aidat");
  const [period, setPeriod] = useState("2026-05");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [flatIds, setFlatIds] = useState(""); // virgülle ayrılmış, boşsa hepsi
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BulkChargeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !siteId) router.replace("/login");
  }, [router, siteId, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !siteId) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const parsedIds = flatIds.trim()
      ? flatIds.split(",").map((s) => s.trim()).filter(Boolean)
      : undefined;

    try {
      const res = await bulkCreateCharges(token, siteId, {
        flat_ids: parsedIds,
        charge_type: chargeType,
        period,
        amount,
        due_date: dueDate,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-2xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Toplu Borç Oluştur</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <form
        onSubmit={(e) => void handleSubmit(e)}
        className="space-y-4 rounded-xl bg-white p-6 shadow-sm"
      >
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700">Borç Tipi</label>
          <input
            required
            value={chargeType}
            onChange={(e) => setChargeType(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700">Dönem (YYYY-MM)</label>
            <input
              required
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              placeholder="2026-05"
              pattern="\d{4}-\d{2}"
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
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="1500.00"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700">Vade Tarihi</label>
          <input
            required
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700">
            Daire IDler (opsiyonel — virgülle ayır, boş bırakırsan tüm dairelere)
          </label>
          <textarea
            rows={2}
            value={flatIds}
            onChange={(e) => setFlatIds(e.target.value)}
            placeholder="uuid1, uuid2, uuid3"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white disabled:bg-zinc-300"
        >
          {loading ? "Oluşturuluyor..." : "Tüm Dairelere Uygula"}
        </button>
      </form>

      {error ? (
        <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>
      ) : null}

      {result ? (
        <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 space-y-2">
          <h2 className="font-semibold text-emerald-800">İşlem Tamamlandı</h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-lg bg-white p-3 shadow-sm">
              <p className="text-sm text-zinc-500">Oluşturuldu</p>
              <p className="text-2xl font-bold text-emerald-700">{result.created}</p>
            </div>
            <div className="rounded-lg bg-white p-3 shadow-sm">
              <p className="text-sm text-zinc-500">Atlandı</p>
              <p className="text-2xl font-bold text-amber-600">{result.skipped}</p>
            </div>
            <div className="rounded-lg bg-white p-3 shadow-sm">
              <p className="text-sm text-zinc-500">Hata</p>
              <p className="text-2xl font-bold text-rose-600">{result.errors.length}</p>
            </div>
          </div>
          {result.errors.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs text-rose-700">
              {result.errors.map((e, i) => (
                <li key={i}>• {e}</li>
              ))}
            </ul>
          )}
        </section>
      ) : null}
    </main>
  );
}
