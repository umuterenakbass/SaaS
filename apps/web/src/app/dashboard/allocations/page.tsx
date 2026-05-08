"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  Charge,
  Flat,
  Payment,
  PaymentAllocation,
  createPaymentAllocation,
  deletePaymentAllocation,
  listCharges,
  listFlats,
  listPaymentAllocations,
  listPayments,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function AllocationsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [flats, setFlats] = useState<Flat[]>([]);
  const [charges, setCharges] = useState<Charge[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [allocations, setAllocations] = useState<PaymentAllocation[]>([]);

  const [flatId, setFlatId] = useState("");
  const [paymentId, setPaymentId] = useState("");
  const [chargeId, setChargeId] = useState("");
  const [allocatedAmount, setAllocatedAmount] = useState("0.00");
  const [error, setError] = useState<string | null>(null);

  const paymentMap = useMemo(() => new Map(payments.map((payment) => [payment.id, payment])), [payments]);
  const chargeMap = useMemo(() => new Map(charges.map((charge) => [charge.id, charge])), [charges]);

  const refreshForFlat = async (selectedFlatId: string) => {
    if (!token || !siteId || !selectedFlatId) return;

    const [loadedCharges, loadedPayments] = await Promise.all([
      listCharges(token, siteId, { flat_id: selectedFlatId }),
      listPayments(token, siteId, { flat_id: selectedFlatId }),
    ]);
    setCharges(loadedCharges);
    setPayments(loadedPayments);

    const nextPaymentId = loadedPayments[0]?.id ?? "";
    const nextChargeId = loadedCharges[0]?.id ?? "";
    setPaymentId(nextPaymentId);
    setChargeId(nextChargeId);

    if (nextPaymentId || nextChargeId) {
      const loadedAllocations = await listPaymentAllocations(token, siteId, {
        payment_id: nextPaymentId || undefined,
        charge_id: nextChargeId || undefined,
      });
      setAllocations(loadedAllocations);
    } else {
      setAllocations([]);
    }
  };

  const refreshAllocations = async (nextPaymentId = paymentId, nextChargeId = chargeId) => {
    if (!token || !siteId) return;
    const loaded = await listPaymentAllocations(token, siteId, {
      payment_id: nextPaymentId || undefined,
      charge_id: nextChargeId || undefined,
    });
    setAllocations(loaded);
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

        const firstFlatId = loadedFlats[0]?.id ?? "";
        setFlatId(firstFlatId);
        if (firstFlatId) {
          await refreshForFlat(firstFlatId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Tahsis verileri yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId || !paymentId || !chargeId) return;

    try {
      await createPaymentAllocation(token, siteId, {
        payment_id: paymentId,
        charge_id: chargeId,
        allocated_amount: allocatedAmount,
      });
      setError(null);
      setAllocatedAmount("0.00");
      await refreshAllocations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tahsis oluşturulamadı.");
    }
  };

  const handleDelete = async (allocationId: string) => {
    if (!token || !siteId) return;

    try {
      await deletePaymentAllocation(token, siteId, allocationId);
      setError(null);
      await refreshAllocations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tahsis silinemedi.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Ödeme Tahsisleri</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <section className="rounded-xl bg-white p-4 shadow-sm">
        <label className="mb-2 block text-sm font-medium text-zinc-700">Daire</label>
        <select
          value={flatId}
          onChange={(event) => {
            const value = event.target.value;
            setFlatId(value);
            void refreshForFlat(value);
          }}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
        >
          {flats.map((flat) => (
            <option key={flat.id} value={flat.id}>
              Daire {flat.unit_no} (Kat {flat.floor})
            </option>
          ))}
        </select>
      </section>

      <form onSubmit={handleCreate} className="grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-4">
        <select
          value={paymentId}
          onChange={(event) => {
            const value = event.target.value;
            setPaymentId(value);
            void refreshAllocations(value, chargeId);
          }}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        >
          {payments.map((payment) => (
            <option key={payment.id} value={payment.id}>
              {new Date(payment.paid_at).toLocaleDateString("tr-TR")} • {payment.amount} ₺ • {payment.method}
            </option>
          ))}
        </select>

        <select
          value={chargeId}
          onChange={(event) => {
            const value = event.target.value;
            setChargeId(value);
            void refreshAllocations(paymentId, value);
          }}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        >
          {charges.map((charge) => (
            <option key={charge.id} value={charge.id}>
              {charge.period} • {charge.charge_type} • {charge.amount} ₺
            </option>
          ))}
        </select>

        <input
          type="number"
          step="0.01"
          value={allocatedAmount}
          onChange={(event) => setAllocatedAmount(event.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white">
          Tahsis Ekle
        </button>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="space-y-2">
        {allocations.map((allocation) => {
          const payment = paymentMap.get(allocation.payment_id);
          const charge = chargeMap.get(allocation.charge_id);
          return (
            <article
              key={allocation.id}
              className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3"
            >
              <div>
                <p className="font-medium text-zinc-900">Tahsis: {allocation.allocated_amount} ₺</p>
                <p className="text-sm text-zinc-500">
                  Ödeme: {payment ? `${payment.amount} ₺ / ${payment.method}` : allocation.payment_id} | Borç: {charge
                    ? `${charge.period} ${charge.charge_type} ${charge.amount} ₺`
                    : allocation.charge_id}
                </p>
              </div>
              <button
                onClick={() => void handleDelete(allocation.id)}
                className="rounded-lg border border-rose-200 px-3 py-1 text-sm text-rose-600"
              >
                Sil
              </button>
            </article>
          );
        })}
      </section>
    </main>
  );
}
