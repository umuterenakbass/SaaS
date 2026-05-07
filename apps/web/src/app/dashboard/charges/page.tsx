"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  Charge,
  ChargeStatus,
  Flat,
  createCharge,
  deleteCharge,
  listCharges,
  listFlats,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ChargesPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [flats, setFlats] = useState<Flat[]>([]);
  const [charges, setCharges] = useState<Charge[]>([]);
  const [flatId, setFlatId] = useState("");
  const [chargeType, setChargeType] = useState("aidat");
  const [period, setPeriod] = useState("2026-05");
  const [amount, setAmount] = useState("0.00");
  const [dueDate, setDueDate] = useState("");
  const [status, setStatus] = useState<ChargeStatus>("pending");
  const [error, setError] = useState<string | null>(null);

  const refresh = async (selectedFlatId?: string) => {
    if (!token || !siteId) return;
    const loadedCharges = await listCharges(token, siteId, {
      flat_id: selectedFlatId || undefined,
    });
    setCharges(loadedCharges);
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
        await refresh(initialFlatId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Borçlar yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId || !flatId) return;

    try {
      await createCharge(token, siteId, {
        flat_id: flatId,
        charge_type: chargeType,
        period,
        amount,
        due_date: dueDate,
        status,
      });
      await refresh(flatId);
      setAmount("0.00");
      setDueDate("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Borç oluşturulamadı.");
    }
  };

  const handleDelete = async (chargeId: string) => {
    if (!token || !siteId) return;

    try {
      await deleteCharge(token, siteId, chargeId);
      await refresh(flatId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Borç silinemedi.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Borç Yönetimi</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <form onSubmit={handleCreate} className="grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-6">
        <select
          value={flatId}
          onChange={(event) => {
            const value = event.target.value;
            setFlatId(value);
            void refresh(value);
          }}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        >
          {flats.map((flat) => (
            <option value={flat.id} key={flat.id}>
              Daire {flat.unit_no} (Kat {flat.floor})
            </option>
          ))}
        </select>

        <input
          value={chargeType}
          onChange={(event) => setChargeType(event.target.value)}
          placeholder="Borç tipi"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <input
          value={period}
          onChange={(event) => setPeriod(event.target.value)}
          placeholder="2026-05"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <input
          type="number"
          step="0.01"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder="Tutar"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <input
          type="date"
          value={dueDate}
          onChange={(event) => setDueDate(event.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <select
          value={status}
          onChange={(event) => setStatus(event.target.value as ChargeStatus)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
        >
          <option value="pending">pending</option>
          <option value="paid">paid</option>
          <option value="cancelled">cancelled</option>
        </select>

        <button
          type="submit"
          className="md:col-span-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          Borç Ekle
        </button>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="space-y-2">
        {charges.map((charge) => (
          <article
            key={charge.id}
            className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3"
          >
            <div>
              <p className="font-medium text-zinc-900">
                {charge.charge_type} | {charge.period} | {charge.amount} ₺
              </p>
              <p className="text-sm text-zinc-500">
                Durum: {charge.status} | Son ödeme: {charge.due_date}
              </p>
            </div>
            <button
              onClick={() => void handleDelete(charge.id)}
              className="rounded-lg border border-rose-200 px-3 py-1 text-sm text-rose-600"
            >
              Sil
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}
