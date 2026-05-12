"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { MyPaymentItem, getMyPayments } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const methodLabel = (m: string) =>
  ({ cash: "Nakit", bank_transfer: "Havale/EFT", credit_card: "Kredi Kartı", other: "Diğer" }[m] ?? m);

export default function ResidentPaymentsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [payments, setPayments] = useState<MyPaymentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void (async () => {
      try {
        setPayments(await getMyPayments(token, siteId));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ödemeler yüklenemedi.");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, siteId, token]);

  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Ödemelerim</h1>
        <Link href="/resident" className="text-sm font-medium text-indigo-600">← Ana Sayfa</Link>
      </header>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {loading ? <p className="text-sm text-zinc-500">Yükleniyor...</p> : null}

      {!loading && payments.length === 0 ? (
        <p className="text-sm text-zinc-500">Henüz ödeme kaydı yok.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3">Daire</th>
                <th className="px-4 py-3">Tutar</th>
                <th className="px-4 py-3">Tarih</th>
                <th className="px-4 py-3">Yöntem</th>
                <th className="px-4 py-3">Referans</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {payments.map((p) => (
                <tr key={p.id}>
                  <td className="px-4 py-3 text-zinc-700">{p.block_name} / {p.unit_no}</td>
                  <td className="px-4 py-3 font-semibold text-emerald-700">{p.amount} ₺</td>
                  <td className="px-4 py-3 text-zinc-500">{p.paid_at.slice(0, 10)}</td>
                  <td className="px-4 py-3 text-zinc-700">{methodLabel(p.method)}</td>
                  <td className="px-4 py-3 text-zinc-400">{p.reference_no ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
