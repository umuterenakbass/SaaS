"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  FlatSummaryReport,
  PeriodSummaryReport,
  buildCsvExportUrl,
  getFlatSummary,
  getPeriodSummary,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ReportsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [period, setPeriod] = useState("2026-05");
  const [periodReport, setPeriodReport] = useState<PeriodSummaryReport | null>(null);
  const [flatReport, setFlatReport] = useState<FlatSummaryReport | null>(null);
  const [allFlats, setAllFlats] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !siteId) {
      router.replace("/login");
    }
  }, [router, siteId, token]);

  const handleLoad = async () => {
    if (!token || !siteId) {
      setError(`Oturum bilgisi eksik — token: ${token ? "var" : "YOK"}, siteId: ${siteId ? "var" : "YOK"}`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [ps, fs] = await Promise.all([
        getPeriodSummary(token, siteId, period),
        getFlatSummary(token, siteId, allFlats ? undefined : period),
      ]);
      setPeriodReport(ps);
      setFlatReport(fs);
    } catch (err) {
      console.error("Rapor hatası:", err);
      setError(err instanceof Error ? `${err.name}: ${err.message}` : "Rapor yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  const handleCsvDownload = (type: "charges" | "payments") => {
    if (!token || !siteId) return;
    const url = buildCsvExportUrl(type, siteId, allFlats ? undefined : period);
    // CSV indirme: token ile authenticated link açılamaz doğrudan;
    // Bu nedenle fetch + Blob yöntemi kullanıyoruz
    void (async () => {
      try {
        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}`, "X-Site-Id": siteId },
        });
        if (!resp.ok) throw new Error(`İndirme başarısız (${resp.status})`);
        const blob = await resp.blob();
        const anchor = document.createElement("a");
        anchor.href = URL.createObjectURL(blob);
        anchor.download = `${type}_${allFlats ? "all" : period}.csv`;
        anchor.click();
        URL.revokeObjectURL(anchor.href);
      } catch (err) {
        setError(err instanceof Error ? err.message : "CSV indirilemedi.");
      }
    })();
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Raporlar</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      {/* Filtreler */}
      <section className="flex flex-wrap items-end gap-3 rounded-xl bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700">Dönem (YYYY-MM)</label>
          <input
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="2026-05"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-zinc-700">
          <input
            type="checkbox"
            checked={allFlats}
            onChange={(e) => setAllFlats(e.target.checked)}
            className="h-4 w-4"
          />
          Tüm zamanlar (dönem filtresi yok)
        </label>
        <button
          onClick={() => void handleLoad()}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:bg-zinc-300"
        >
          {loading ? "Yükleniyor..." : "Raporu Getir"}
        </button>
        <button
          onClick={() => handleCsvDownload("charges")}
          className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700"
        >
          ⬇ Borçlar CSV
        </button>
        <button
          onClick={() => handleCsvDownload("payments")}
          className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700"
        >
          ⬇ Ödemeler CSV
        </button>
      </section>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {/* Dönem Özeti */}
      {periodReport ? (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-zinc-800">
            Dönem Özeti — {periodReport.period}
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            {[
              { label: "Toplam Borç", value: `${periodReport.total_charges} ₺` },
              { label: "Toplam Ödeme", value: `${periodReport.total_payments} ₺` },
              { label: "Tahsis Edilen", value: `${periodReport.total_allocated} ₺` },
              {
                label: "Tahsilat Oranı",
                value: `%${periodReport.collection_rate}`,
                highlight: parseFloat(periodReport.collection_rate) >= 80,
              },
            ].map((card) => (
              <article
                key={card.label}
                className={`rounded-xl border p-4 shadow-sm ${
                  card.highlight ? "border-emerald-300 bg-emerald-50" : "border-zinc-200 bg-white"
                }`}
              >
                <p className="text-sm text-zinc-500">{card.label}</p>
                <p className="mt-1 text-xl font-semibold text-zinc-900">{card.value}</p>
              </article>
            ))}
          </div>

          {/* Tipe göre dağılım */}
          {periodReport.by_charge_type.length > 0 && (
            <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
              <table className="w-full text-sm">
                <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
                  <tr>
                    <th className="px-4 py-3">Borç Tipi</th>
                    <th className="px-4 py-3">Adet</th>
                    <th className="px-4 py-3">Toplam</th>
                    <th className="px-4 py-3">Bekleyen</th>
                    <th className="px-4 py-3">Ödenen</th>
                    <th className="px-4 py-3">İptal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {periodReport.by_charge_type.map((row) => (
                    <tr key={row.charge_type}>
                      <td className="px-4 py-3 font-medium text-zinc-900">{row.charge_type}</td>
                      <td className="px-4 py-3 text-zinc-700">{row.charge_count}</td>
                      <td className="px-4 py-3 text-zinc-700">{row.total_amount} ₺</td>
                      <td className="px-4 py-3 text-amber-700">{row.pending_amount} ₺</td>
                      <td className="px-4 py-3 text-emerald-700">{row.paid_amount} ₺</td>
                      <td className="px-4 py-3 text-zinc-400">{row.cancelled_amount} ₺</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}

      {/* Daire Bazlı Özet */}
      {flatReport ? (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-800">
            Daire Özeti{flatReport.period ? ` — ${flatReport.period}` : " — Tüm Zamanlar"}
            <span className="ml-2 text-sm font-normal text-zinc-500">
              ({flatReport.flat_count} daire)
            </span>
          </h2>
          <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-3">Blok</th>
                  <th className="px-4 py-3">Daire</th>
                  <th className="px-4 py-3">Borç</th>
                  <th className="px-4 py-3">Ödeme</th>
                  <th className="px-4 py-3">Bakiye</th>
                  <th className="px-4 py-3">Bekleyen</th>
                  <th className="px-4 py-3">Vadesi Geçmiş</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {flatReport.items.map((item) => (
                  <tr key={item.flat_id} className={parseFloat(item.balance) > 0 ? "bg-rose-50" : ""}>
                    <td className="px-4 py-3 text-zinc-700">{item.block_name}</td>
                    <td className="px-4 py-3 font-medium text-zinc-900">{item.unit_no}</td>
                    <td className="px-4 py-3 text-zinc-700">{item.total_charges} ₺</td>
                    <td className="px-4 py-3 text-zinc-700">{item.total_payments} ₺</td>
                    <td className={`px-4 py-3 font-semibold ${parseFloat(item.balance) > 0 ? "text-rose-700" : "text-emerald-700"}`}>
                      {item.balance} ₺
                    </td>
                    <td className="px-4 py-3 text-zinc-500">{item.pending_charge_count}</td>
                    <td className="px-4 py-3 text-rose-600 font-medium">{item.overdue_charge_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </main>
  );
}
