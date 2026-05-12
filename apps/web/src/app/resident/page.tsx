"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { MyBalanceSummary, MyFlatInfo, getMyBalance, getMyFlats } from "@/lib/api";
import { clearSession, getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ResidentHomePage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [flats, setFlats] = useState<MyFlatInfo[]>([]);
  const [balance, setBalance] = useState<MyBalanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void (async () => {
      try {
        const [f, b] = await Promise.all([
          getMyFlats(token, siteId),
          getMyBalance(token, siteId),
        ]);
        setFlats(f);
        setBalance(b);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Veriler yüklenemedi.");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, siteId, token]);

  const handleLogout = () => { clearSession(); router.push("/login"); };

  if (loading) return <div className="p-8 text-sm text-zinc-500">Yükleniyor...</div>;

  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between rounded-2xl bg-indigo-600 p-5 text-white">
        <div>
          <h1 className="text-xl font-semibold">Sakin Portalı</h1>
          <p className="mt-1 text-sm text-indigo-200">Hesabına hoş geldin</p>
        </div>
        <button
          onClick={handleLogout}
          className="rounded-lg border border-indigo-400 px-3 py-1.5 text-sm text-white"
        >
          Çıkış
        </button>
      </header>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {/* Bakiye Kartları */}
      {balance && (
        <section className="grid gap-4 sm:grid-cols-3">
          {[
            { label: "Toplam Borç", value: `${balance.total_charges} ₺`, color: "text-zinc-900" },
            { label: "Toplam Ödeme", value: `${balance.total_payments} ₺`, color: "text-emerald-700" },
            {
              label: "Net Bakiye",
              value: `${balance.balance} ₺`,
              color: parseFloat(balance.balance) > 0 ? "text-rose-700" : "text-emerald-700",
            },
          ].map((c) => (
            <article key={c.label} className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">{c.label}</p>
              <p className={`mt-1 text-xl font-bold ${c.color}`}>{c.value}</p>
            </article>
          ))}
        </section>
      )}

      {balance && (balance.overdue_count > 0) && (
        <div className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">
          ⚠ <strong>{balance.overdue_count}</strong> adet vadesi geçmiş borcunuz var.
        </div>
      )}

      {/* Dairelerim */}
      {flats.length > 0 && (
        <section className="space-y-2">
          <h2 className="font-semibold text-zinc-800">Dairelerim</h2>
          <div className="divide-y divide-zinc-100 rounded-xl border border-zinc-200 bg-white shadow-sm">
            {flats.map((f) => (
              <div key={f.flat_id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium text-zinc-900">{f.block_name} — {f.unit_no}</p>
                  <p className="text-sm text-zinc-500">Kat {f.floor} · {f.relation_type === "owner" ? "Mal Sahibi" : "Kiracı"}</p>
                </div>
                {f.move_in_date && (
                  <p className="text-xs text-zinc-400">Giriş: {f.move_in_date}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Hızlı Navigasyon */}
      <nav className="flex flex-wrap gap-3">
        <Link href="/resident/charges" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white">
          Borçlarım
        </Link>
        <Link href="/resident/payments" className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white">
          Ödemelerim
        </Link>
        <Link href="/resident/notifications" className="rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium text-white">
          Bildirimler
        </Link>
      </nav>
    </main>
  );
}
