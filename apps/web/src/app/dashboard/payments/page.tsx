"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  Flat,
  Payment,
  PaymentMethod,
  createPayment,
  deletePayment,
  listFlats,
  listPayments,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function PaymentsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [flats, setFlats] = useState<Flat[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [flatId, setFlatId] = useState("");
  const [amount, setAmount] = useState("0.00");
  const [paidAt, setPaidAt] = useState("");
  const [method, setMethod] = useState<PaymentMethod>("bank_transfer");
  const [referenceNo, setReferenceNo] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  const refresh = async (selectedFlatId?: string) => {
    if (!token || !siteId) return;
    const loadedPayments = await listPayments(token, siteId, {
      flat_id: selectedFlatId || undefined,
    });
    setPayments(loadedPayments);
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
        setError(err instanceof Error ? err.message : "Ödemeler yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId || !flatId) return;

    try {
      await createPayment(token, siteId, {
        flat_id: flatId,
        amount,
        paid_at: new Date(paidAt).toISOString(),
        method,
        reference_no: referenceNo || null,
        note: note || null,
      });
      await refresh(flatId);
      setAmount("0.00");
      setPaidAt("");
      setReferenceNo("");
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ödeme oluşturulamadı.");
    }
  };

  const handleDelete = async (paymentId: string) => {
    if (!token || !siteId) return;

    try {
      await deletePayment(token, siteId, paymentId);
      await refresh(flatId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ödeme silinemedi.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Ödeme Yönetimi</h1>
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
          type="number"
          step="0.01"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder="Tutar"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <input
          type="datetime-local"
          value={paidAt}
          onChange={(event) => setPaidAt(event.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />

        <select
          value={method}
          onChange={(event) => setMethod(event.target.value as PaymentMethod)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
        >
          <option value="bank_transfer">bank_transfer</option>
          <option value="cash">cash</option>
          <option value="credit_card">credit_card</option>
          <option value="other">other</option>
        </select>

        <input
          value={referenceNo}
          onChange={(event) => setReferenceNo(event.target.value)}
          placeholder="Referans No"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
        />

        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Not"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
        />

        <button
          type="submit"
          className="md:col-span-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          Ödeme Ekle
        </button>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="space-y-2">
        {payments.map((payment) => (
          <article
            key={payment.id}
            className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3"
          >
            <div>
              <p className="font-medium text-zinc-900">
                {payment.amount} ₺ | {payment.method}
              </p>
              <p className="text-sm text-zinc-500">
                {new Date(payment.paid_at).toLocaleString("tr-TR")} | Ref: {payment.reference_no ?? "-"}
              </p>
            </div>
            <button
              onClick={() => void handleDelete(payment.id)}
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
