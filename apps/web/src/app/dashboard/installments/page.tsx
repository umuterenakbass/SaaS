"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  Flat,
  InstallmentPlanOut,
  createInstallmentPlan,
  deleteInstallmentPlan,
  listFlats,
  listInstallmentPlans,
  payInstallmentItem,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function InstallmentsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [plans, setPlans] = useState<InstallmentPlanOut[]>([]);
  const [flats, setFlats] = useState<Flat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  // Form state
  const [flatId, setFlatId] = useState("");
  const [title, setTitle] = useState("");
  const [totalAmount, setTotalAmount] = useState("");
  const [installmentCount, setInstallmentCount] = useState("3");
  const [firstDueDate, setFirstDueDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = async () => {
    if (!token || !siteId) return;
    try {
      const [p, f] = await Promise.all([
        listInstallmentPlans(token, siteId),
        listFlats(token, siteId),
      ]);
      setPlans(p);
      setFlats(f);
      if (f.length > 0 && !flatId) setFlatId(f[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !siteId) return;
    setSubmitting(true);
    setError(null);
    try {
      await createInstallmentPlan(token, siteId, {
        flat_id: flatId,
        title,
        total_amount: totalAmount,
        installment_count: parseInt(installmentCount),
        first_due_date: firstDueDate,
      });
      setTitle("");
      setTotalAmount("");
      setInstallmentCount("3");
      setFirstDueDate("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Oluşturulamadı.");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePay = async (planId: string, itemId: string) => {
    if (!token || !siteId) return;
    try {
      await payInstallmentItem(token, siteId, planId, itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ödeme başarısız.");
    }
  };

  const handleDelete = async (planId: string) => {
    if (!token || !siteId) return;
    if (!confirm("Bu taksit planını silmek istediğinize emin misiniz?")) return;
    try {
      await deleteInstallmentPlan(token, siteId, planId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Silinemedi.");
    }
  };

  const statusLabel = (s: string) => ({ pending: "Bekliyor", paid: "Ödendi", overdue: "Gecikmiş", cancelled: "İptal" }[s] ?? s);
  const statusColor = (s: string) => ({ pending: "text-amber-700 bg-amber-50", paid: "text-emerald-700 bg-emerald-50", overdue: "text-rose-700 bg-rose-50", cancelled: "text-zinc-400 bg-zinc-50" }[s] ?? "");

  if (loading) return <div className="p-8 text-sm text-zinc-500">Yükleniyor...</div>;

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Taksit Planları</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">← Dashboard</Link>
      </header>

      {/* Yeni Plan Formu */}
      <form
        onSubmit={(e) => void handleCreate(e)}
        className="grid gap-3 rounded-xl bg-white p-5 shadow-sm sm:grid-cols-3"
      >
        <div className="sm:col-span-3">
          <h2 className="mb-3 font-semibold text-zinc-800">Yeni Taksit Planı Oluştur</h2>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-600">Daire</label>
          <select
            value={flatId}
            onChange={(e) => setFlatId(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            required
          >
            {flats.map((f) => (
              <option key={f.id} value={f.id}>{f.unit_no}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-600">Plan Başlığı</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="2026 Yılı Aidat Taksiti"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-600">Toplam Tutar (₺)</label>
          <input
            type="number"
            step="0.01"
            min="1"
            value={totalAmount}
            onChange={(e) => setTotalAmount(e.target.value)}
            placeholder="6000.00"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-600">Taksit Sayısı</label>
          <input
            type="number"
            min="2"
            max="60"
            value={installmentCount}
            onChange={(e) => setInstallmentCount(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-600">İlk Vade Tarihi</label>
          <input
            type="date"
            value={firstDueDate}
            onChange={(e) => setFirstDueDate(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            required
          />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white disabled:bg-zinc-300"
          >
            {submitting ? "Oluşturuluyor..." : "Plan Oluştur"}
          </button>
        </div>
      </form>

      {error && <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}

      {/* Plan Listesi */}
      <section className="space-y-3">
        {plans.length === 0 && (
          <p className="text-sm text-zinc-500">Henüz taksit planı yok.</p>
        )}
        {plans.map((plan) => {
          const paidCount = plan.items.filter((i) => i.status === "paid").length;
          const paidAmount = plan.items.filter((i) => i.status === "paid").reduce((s, i) => s + parseFloat(i.amount), 0);
          const progress = Math.round((paidCount / plan.installment_count) * 100);

          return (
            <article key={plan.id} className="rounded-xl border border-zinc-200 bg-white shadow-sm">
              {/* Plan Header */}
              <div className="flex items-center justify-between p-4">
                <div className="flex-1">
                  <p className="font-semibold text-zinc-900">{plan.title}</p>
                  <p className="text-sm text-zinc-500">
                    {flats.find((f) => f.id === plan.flat_id)?.unit_no ?? plan.flat_id.slice(0, 8)} •{" "}
                    {plan.installment_count} taksit • Toplam: {plan.total_amount} ₺
                  </p>
                  {/* Progress bar */}
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-2 w-48 overflow-hidden rounded-full bg-zinc-100">
                      <div
                        className="h-full rounded-full bg-emerald-500 transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-zinc-500">
                      {paidCount}/{plan.installment_count} ödendi ({paidAmount.toFixed(2)} ₺)
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setExpanded(expanded === plan.id ? null : plan.id)}
                    className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700"
                  >
                    {expanded === plan.id ? "Gizle" : "Detay"}
                  </button>
                  <button
                    onClick={() => void handleDelete(plan.id)}
                    className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600"
                  >
                    Sil
                  </button>
                </div>
              </div>

              {/* Taksit Detayları */}
              {expanded === plan.id && (
                <div className="border-t border-zinc-100">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-50 text-xs font-semibold uppercase text-zinc-500">
                      <tr>
                        <th className="px-4 py-2 text-left">#</th>
                        <th className="px-4 py-2 text-left">Tutar</th>
                        <th className="px-4 py-2 text-left">Vade</th>
                        <th className="px-4 py-2 text-left">Durum</th>
                        <th className="px-4 py-2 text-left">Ödeme Tarihi</th>
                        <th className="px-4 py-2 text-left">İşlem</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-50">
                      {plan.items.map((item) => (
                        <tr key={item.id}>
                          <td className="px-4 py-2 text-zinc-600">{item.installment_no}.</td>
                          <td className="px-4 py-2 font-medium text-zinc-900">{item.amount} ₺</td>
                          <td className="px-4 py-2 text-zinc-600">{item.due_date}</td>
                          <td className="px-4 py-2">
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColor(item.status)}`}>
                              {statusLabel(item.status)}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-zinc-500">{item.paid_at ?? "—"}</td>
                          <td className="px-4 py-2">
                            {item.status === "pending" && (
                              <button
                                onClick={() => void handlePay(plan.id, item.id)}
                                className="rounded-lg bg-emerald-600 px-2 py-1 text-xs font-medium text-white"
                              >
                                Ödendi
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          );
        })}
      </section>
    </main>
  );
}
