"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ChargePlan,
  ChargePlanAssignment,
  Flat,
  createChargePlan,
  createChargePlanAssignment,
  deleteChargePlan,
  deleteChargePlanAssignment,
  generateChargesFromPlan,
  listChargePlanAssignments,
  listChargePlans,
  listFlats,
  updateChargePlan,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ChargePlansPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [flats, setFlats] = useState<Flat[]>([]);
  const [plans, setPlans] = useState<ChargePlan[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string>("");
  const [assignments, setAssignments] = useState<ChargePlanAssignment[]>([]);
  const [assignmentFlatId, setAssignmentFlatId] = useState<string>("");

  const [name, setName] = useState("Aylık Aidat");
  const [chargeType, setChargeType] = useState("aidat");
  const [amount, setAmount] = useState("2500.00");
  const [startPeriod, setStartPeriod] = useState("2026-05");
  const [endPeriod, setEndPeriod] = useState("");

  const [generatePeriod, setGeneratePeriod] = useState("2026-05");
  const [generateDueDate, setGenerateDueDate] = useState("");
  const [generateResult, setGenerateResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const flatMap = useMemo(() => {
    return new Map(flats.map((flat) => [flat.id, flat]));
  }, [flats]);

  const refreshPlans = async () => {
    if (!token || !siteId) return;
    const loadedPlans = await listChargePlans(token, siteId);
    setPlans(loadedPlans);

    const nextSelected = loadedPlans.find((plan) => plan.id === selectedPlanId)?.id ?? loadedPlans[0]?.id ?? "";
    setSelectedPlanId(nextSelected);
  };

  const refreshAssignments = async (planId: string) => {
    if (!token || !siteId || !planId) {
      setAssignments([]);
      return;
    }
    const loaded = await listChargePlanAssignments(token, siteId, planId);
    setAssignments(loaded);
  };

  useEffect(() => {
    const load = async () => {
      if (!token || !siteId) {
        router.replace("/login");
        return;
      }

      try {
        const [loadedFlats, loadedPlans] = await Promise.all([
          listFlats(token, siteId),
          listChargePlans(token, siteId),
        ]);

        setFlats(loadedFlats);
        setAssignmentFlatId(loadedFlats[0]?.id ?? "");

        setPlans(loadedPlans);
        const firstPlan = loadedPlans[0]?.id ?? "";
        setSelectedPlanId(firstPlan);

        if (firstPlan) {
          const loadedAssignments = await listChargePlanAssignments(token, siteId, firstPlan);
          setAssignments(loadedAssignments);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Planlar yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  useEffect(() => {
    void refreshAssignments(selectedPlanId);
  }, [selectedPlanId]);

  const handleCreatePlan = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId) return;

    try {
      await createChargePlan(token, siteId, {
        name,
        charge_type: chargeType,
        amount,
        frequency: "monthly",
        start_period: startPeriod,
        end_period: endPeriod || null,
        is_active: true,
      });
      setError(null);
      await refreshPlans();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan oluşturulamadı.");
    }
  };

  const handleToggleActive = async (plan: ChargePlan) => {
    if (!token || !siteId) return;

    try {
      await updateChargePlan(token, siteId, plan.id, { is_active: !plan.is_active });
      setError(null);
      await refreshPlans();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan güncellenemedi.");
    }
  };

  const handleDeletePlan = async (planId: string) => {
    if (!token || !siteId) return;

    try {
      await deleteChargePlan(token, siteId, planId);
      setError(null);
      setGenerateResult(null);
      await refreshPlans();
      const remainingSelected = plans.find((plan) => plan.id !== planId)?.id ?? "";
      setSelectedPlanId(remainingSelected);
      await refreshAssignments(remainingSelected);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan silinemedi.");
    }
  };

  const handleCreateAssignment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId || !selectedPlanId || !assignmentFlatId) return;

    try {
      await createChargePlanAssignment(token, siteId, selectedPlanId, {
        flat_id: assignmentFlatId,
      });
      setError(null);
      await refreshAssignments(selectedPlanId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan ataması yapılamadı.");
    }
  };

  const handleDeleteAssignment = async (assignmentId: string) => {
    if (!token || !siteId || !selectedPlanId) return;

    try {
      await deleteChargePlanAssignment(token, siteId, selectedPlanId, assignmentId);
      setError(null);
      await refreshAssignments(selectedPlanId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan ataması silinemedi.");
    }
  };

  const handleGenerate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId || !selectedPlanId || !generateDueDate) return;

    try {
      const result = await generateChargesFromPlan(token, siteId, selectedPlanId, {
        period: generatePeriod,
        due_date: generateDueDate,
        status: "pending",
      });
      setError(null);
      setGenerateResult(
        `Üretim tamamlandı • İstenen: ${result.requested_assignments}, Oluşturulan: ${result.created_count}, Atlanan: ${result.skipped_count}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Borç üretimi başarısız.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Borç Planları</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <form onSubmit={handleCreatePlan} className="grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-6">
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Plan adı"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />
        <input
          value={chargeType}
          onChange={(event) => setChargeType(event.target.value)}
          placeholder="Borç tipi"
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
          value={startPeriod}
          onChange={(event) => setStartPeriod(event.target.value)}
          placeholder="Başlangıç (YYYY-MM)"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
          required
        />
        <input
          value={endPeriod}
          onChange={(event) => setEndPeriod(event.target.value)}
          placeholder="Bitiş (opsiyonel)"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
        />

        <button
          type="submit"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          Plan Oluştur
        </button>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
          <h2 className="text-base font-semibold text-zinc-900">Planlar</h2>
          <div className="mt-3 space-y-2">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`rounded-lg border p-3 ${selectedPlanId === plan.id ? "border-indigo-400" : "border-zinc-200"}`}
              >
                <button
                  onClick={() => setSelectedPlanId(plan.id)}
                  className="w-full text-left"
                >
                  <p className="font-medium text-zinc-900">{plan.name}</p>
                  <p className="text-sm text-zinc-500">
                    {plan.charge_type} • {plan.amount} ₺ • {plan.start_period}
                    {plan.end_period ? ` → ${plan.end_period}` : " → devam"}
                  </p>
                </button>
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={() => void handleToggleActive(plan)}
                    className="rounded border border-zinc-300 px-2 py-1 text-xs text-zinc-700"
                  >
                    {plan.is_active ? "Pasif Yap" : "Aktif Yap"}
                  </button>
                  <button
                    onClick={() => void handleDeletePlan(plan.id)}
                    className="rounded border border-rose-200 px-2 py-1 text-xs text-rose-600"
                  >
                    Sil
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="space-y-4 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
          <h2 className="text-base font-semibold text-zinc-900">Seçili Plan İşlemleri</h2>

          <form onSubmit={handleCreateAssignment} className="grid gap-2 md:grid-cols-[1fr_auto]">
            <select
              value={assignmentFlatId}
              onChange={(event) => setAssignmentFlatId(event.target.value)}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
              required
            >
              {flats.map((flat) => (
                <option key={flat.id} value={flat.id}>
                  Daire {flat.unit_no} (Kat {flat.floor})
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!selectedPlanId}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-zinc-300"
            >
              Daire Ata
            </button>
          </form>

          <div className="space-y-2">
            {assignments.map((assignment) => {
              const flat = flatMap.get(assignment.flat_id);
              return (
                <div
                  key={assignment.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 p-2"
                >
                  <p className="text-sm text-zinc-700">
                    {flat ? `Daire ${flat.unit_no} (Kat ${flat.floor})` : assignment.flat_id}
                  </p>
                  <button
                    onClick={() => void handleDeleteAssignment(assignment.id)}
                    className="rounded border border-rose-200 px-2 py-1 text-xs text-rose-600"
                  >
                    Sil
                  </button>
                </div>
              );
            })}
          </div>

          <form onSubmit={handleGenerate} className="grid gap-2 md:grid-cols-3">
            <input
              value={generatePeriod}
              onChange={(event) => setGeneratePeriod(event.target.value)}
              placeholder="Dönem (YYYY-MM)"
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
              required
            />
            <input
              type="date"
              value={generateDueDate}
              onChange={(event) => setGenerateDueDate(event.target.value)}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm"
              required
            />
            <button
              type="submit"
              disabled={!selectedPlanId}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-zinc-300"
            >
              Borç Üret
            </button>
          </form>

          {generateResult ? <p className="text-sm text-emerald-700">{generateResult}</p> : null}
        </article>
      </section>
    </main>
  );
}
