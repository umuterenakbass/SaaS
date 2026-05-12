"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AnalyticsDashboardResponse, getAnalyticsDashboard } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const PIE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316"];

export default function AnalyticsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [data, setData] = useState<AnalyticsDashboardResponse | null>(null);
  const [months, setMonths] = useState(12);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async (m: number) => {
    if (!token || !siteId) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getAnalyticsDashboard(token, siteId, m));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void load(months);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Grafik için veriyi sayıya çevir
  const trendData = (data?.monthly_trend ?? []).map((t) => ({
    period: t.period,
    Borç: parseFloat(t.total_charges),
    Ödeme: parseFloat(t.total_payments),
    "Tahsilat %": parseFloat(t.collection_rate),
  }));

  const pieData = (data?.charge_type_breakdown ?? []).map((b) => ({
    name: b.charge_type,
    value: parseFloat(b.total_amount),
    count: b.charge_count,
  }));

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-8 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Analytics Dashboard</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      {/* Dönem seçici */}
      <div className="flex items-center gap-3">
        {[6, 12, 24].map((m) => (
          <button
            key={m}
            onClick={() => { setMonths(m); void load(m); }}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              months === m
                ? "bg-indigo-600 text-white"
                : "border border-zinc-300 bg-white text-zinc-700"
            }`}
          >
            Son {m} ay
          </button>
        ))}
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {loading ? <p className="text-sm text-zinc-500">Yükleniyor...</p> : null}

      {data && (
        <>
          {/* Özet Kartlar */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                label: "Toplam Daire",
                value: data.occupancy.total_flats,
                color: "text-zinc-900",
              },
              {
                label: "Aktif Daire",
                value: data.occupancy.active_flats,
                color: "text-indigo-700",
              },
              {
                label: "Sakinli Daire",
                value: data.occupancy.occupied_flats,
                color: "text-emerald-700",
              },
              {
                label: "Ort. Tahsilat",
                value: `%${data.avg_collection_rate}`,
                color:
                  parseFloat(data.avg_collection_rate) >= 80
                    ? "text-emerald-700"
                    : "text-amber-700",
              },
            ].map((card) => (
              <article
                key={card.label}
                className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm"
              >
                <p className="text-sm text-zinc-500">{card.label}</p>
                <p className={`mt-1 text-2xl font-bold ${card.color}`}>{card.value}</p>
              </article>
            ))}
          </section>

          {/* Borç vs Ödeme Çizgi Grafik */}
          <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold text-zinc-800">Aylık Borç & Ödeme Trendi</h2>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => [`${Number(value).toLocaleString("tr-TR")} ₺`]} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="Borç"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Ödeme"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </section>

          {/* Tahsilat Oranı Bar Grafik */}
          <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold text-zinc-800">Aylık Tahsilat Oranı (%)</h2>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(value) => [`%${Number(value)}`]} />
                <Bar dataKey="Tahsilat %" fill="#6366f1" radius={[4, 4, 0, 0]}>
                  {trendData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry["Tahsilat %"] >= 80 ? "#10b981" : entry["Tahsilat %"] >= 50 ? "#f59e0b" : "#ef4444"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </section>

          {/* Borç Tipi Dağılımı */}
          {pieData.length > 0 && (
            <section className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 font-semibold text-zinc-800">Borç Tipi Dağılımı</h2>
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      dataKey="value"
                      label={({ name, percent }) =>
                        `${name} %${((percent ?? 0) * 100).toFixed(0)}`
                      }
                      labelLine={false}
                    >
                      {pieData.map((_, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={PIE_COLORS[index % PIE_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [`${Number(value).toLocaleString("tr-TR")} ₺`]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Breakdown Tablo */}
              <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
                <table className="w-full text-sm">
                  <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
                    <tr>
                      <th className="px-4 py-3">Tür</th>
                      <th className="px-4 py-3">Adet</th>
                      <th className="px-4 py-3">Toplam</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {data.charge_type_breakdown.map((b, i) => (
                      <tr key={b.charge_type}>
                        <td className="flex items-center gap-2 px-4 py-3">
                          <span
                            className="h-3 w-3 rounded-full"
                            style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                          />
                          <span className="font-medium text-zinc-900">{b.charge_type}</span>
                        </td>
                        <td className="px-4 py-3 text-zinc-600">{b.charge_count}</td>
                        <td className="px-4 py-3 font-medium text-zinc-900">
                          {parseFloat(b.total_amount).toLocaleString("tr-TR")} ₺
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Daire Doluluk */}
          <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold text-zinc-800">Daire Doluluk Durumu</h2>
            <div className="flex gap-6">
              {[
                { label: "Toplam", value: data.occupancy.total_flats, color: "bg-zinc-200" },
                { label: "Aktif", value: data.occupancy.active_flats, color: "bg-indigo-200" },
                { label: "Sakinli", value: data.occupancy.occupied_flats, color: "bg-emerald-200" },
                { label: "Boş", value: data.occupancy.vacant_flats, color: "bg-amber-200" },
              ].map((item) => (
                <div key={item.label} className="text-center">
                  <div
                    className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${item.color}`}
                  >
                    <span className="text-xl font-bold text-zinc-800">{item.value}</span>
                  </div>
                  <p className="mt-2 text-xs text-zinc-500">{item.label}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
