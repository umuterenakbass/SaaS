"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Flat, FlatLedger, getFlatLedger, listFlats } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function LedgerPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [flats, setFlats] = useState<Flat[]>([]);
  const [flatId, setFlatId] = useState("");
  const [ledger, setLedger] = useState<FlatLedger | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async (selectedFlatId: string) => {
    if (!token || !siteId || !selectedFlatId) return;
    const data = await getFlatLedger(token, siteId, selectedFlatId, 10);
    setLedger(data);
  };

  useEffect(() => {
    const load = async () => {
      if (!token || !siteId) {
        router.replace("/login");
        return;
      }

      try {
        const loadedFlats = await listFlats(token, siteId);
        setFlats(loadedFlats);

        const initialFlatId = loadedFlats[0]?.id ?? "";
        setFlatId(initialFlatId);
        if (initialFlatId) {
          await refresh(initialFlatId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ekstre yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Daire Ekstresi</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <section className="rounded-xl bg-white p-4 shadow-sm">
        <label className="mb-2 block text-sm font-medium text-zinc-700">Daire seç</label>
        <div className="flex gap-3">
          <select
            value={flatId}
            onChange={(event) => {
              const value = event.target.value;
              setFlatId(value);
              void refresh(value);
            }}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          >
            {flats.map((flat) => (
              <option value={flat.id} key={flat.id}>
                Daire {flat.unit_no} (Kat {flat.floor})
              </option>
            ))}
          </select>
          <button
            onClick={() => void refresh(flatId)}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
          >
            Yenile
          </button>
        </div>
      </section>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {ledger ? (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">Toplam Borç</p>
              <p className="mt-1 text-xl font-semibold text-zinc-900">{ledger.total_charges} ₺</p>
            </article>
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">Toplam Ödeme</p>
              <p className="mt-1 text-xl font-semibold text-zinc-900">{ledger.total_payments} ₺</p>
            </article>
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">Bakiye</p>
              <p className="mt-1 text-xl font-semibold text-zinc-900">{ledger.balance} ₺</p>
            </article>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">Tahsis Edilen Toplam</p>
              <p className="mt-1 text-xl font-semibold text-zinc-900">{ledger.allocated_total} ₺</p>
            </article>
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">Açık Borç</p>
              <p className="mt-1 text-xl font-semibold text-zinc-900">{ledger.open_charge_total} ₺</p>
            </article>
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-zinc-500">Tahsis Edilmemiş Ödeme</p>
              <p className="mt-1 text-xl font-semibold text-zinc-900">{ledger.unallocated_payment_total} ₺</p>
            </article>
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <h2 className="text-base font-semibold text-zinc-900">Son Borçlar</h2>
              <ul className="mt-3 space-y-2 text-sm text-zinc-700">
                {ledger.recent_charges.map((item) => (
                  <li key={item.charge_id}>
                    {item.period} • {item.charge_type} • {item.amount} ₺ ({item.status})
                    <span className="block text-xs text-zinc-500">
                      Tahsis: {item.allocated_amount} ₺ • Kalan: {item.remaining_amount} ₺
                    </span>
                  </li>
                ))}
              </ul>
            </article>

            <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <h2 className="text-base font-semibold text-zinc-900">Son Ödemeler</h2>
              <ul className="mt-3 space-y-2 text-sm text-zinc-700">
                {ledger.recent_payments.map((item) => (
                  <li key={item.payment_id}>
                    {new Date(item.paid_at).toLocaleDateString("tr-TR")} • {item.amount} ₺ • {item.method}
                    <span className="block text-xs text-zinc-500">
                      Tahsis: {item.allocated_amount} ₺ • Kalan: {item.remaining_amount} ₺
                    </span>
                  </li>
                ))}
              </ul>
            </article>
          </section>
        </>
      ) : null}
    </main>
  );
}
