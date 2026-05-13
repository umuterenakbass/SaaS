"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  type BlockSetupItem,
  type ChargeTemplateItem,
  type OnboardingSetupResult,
  runOnboardingSetup,
} from "@/lib/api";

// ── Helpers ──────────────────────────────────────────────────────────────────

function getAuth() {
  if (typeof window === "undefined") return { token: "", siteId: "" };
  return {
    token: localStorage.getItem("token") ?? "",
    siteId: localStorage.getItem("site_id") ?? "",
  };
}

const EMPTY_BLOCK: BlockSetupItem = {
  name: "",
  code: "",
  floors: 4,
  flats_per_floor: 4,
  unit_prefix: "",
};

// Örnek daire no önizleme
function previewUnits(block: BlockSetupItem): string[] {
  const prefix = block.unit_prefix || block.code || "A";
  const units: string[] = [];
  for (let floor = 1; floor <= Math.min(block.floors, 2); floor++) {
    for (let pos = 1; pos <= Math.min(block.flats_per_floor, 3); pos++) {
      units.push(`${prefix}${floor}${String(pos).padStart(2, "0")}`);
    }
  }
  if (block.floors > 2 || block.flats_per_floor > 3) units.push("...");
  return units;
}

// ── Step indicator ────────────────────────────────────────────────────────────

function StepIndicator({ step }: { step: number }) {
  const steps = ["Blok Yapısı", "Aidat Şablonu", "Özet & Onayla"];
  return (
    <div className="flex items-center gap-2 mb-8">
      {steps.map((label, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              i + 1 === step
                ? "bg-blue-600 text-white"
                : i + 1 < step
                ? "bg-green-500 text-white"
                : "bg-gray-200 text-gray-500"
            }`}
          >
            {i + 1 < step ? "✓" : i + 1}
          </div>
          <span
            className={`text-sm font-medium ${
              i + 1 === step ? "text-blue-600" : i + 1 < step ? "text-green-600" : "text-gray-400"
            }`}
          >
            {label}
          </span>
          {i < steps.length - 1 && (
            <div className={`h-0.5 w-12 ${i + 1 < step ? "bg-green-400" : "bg-gray-200"}`} />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Step 1 — Blok yapısı ──────────────────────────────────────────────────────

function Step1Blocks({
  blocks,
  onChange,
}: {
  blocks: BlockSetupItem[];
  onChange: (blocks: BlockSetupItem[]) => void;
}) {
  const add = () => onChange([...blocks, { ...EMPTY_BLOCK }]);
  const remove = (i: number) => onChange(blocks.filter((_, idx) => idx !== i));
  const update = (i: number, field: keyof BlockSetupItem, value: string | number) =>
    onChange(blocks.map((b, idx) => (idx === i ? { ...b, [field]: value } : b)));

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-800 mb-1">Blok Yapısını Tanımla</h2>
      <p className="text-sm text-gray-500 mb-6">
        Kaç blok olduğunu, her blokta kaç kat ve kat başına kaç daire olduğunu gir. Daireler
        otomatik oluşturulacak.
      </p>

      <div className="space-y-4">
        {blocks.map((block, i) => (
          <div key={i} className="border border-gray-200 rounded-xl p-4 bg-white shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="font-semibold text-gray-700">Blok {i + 1}</span>
              {blocks.length > 1 && (
                <button
                  onClick={() => remove(i)}
                  className="text-red-400 hover:text-red-600 text-sm"
                >
                  Kaldır
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Blok Adı</label>
                <input
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  placeholder="A Blok"
                  value={block.name}
                  onChange={(e) => update(i, "name", e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Kod</label>
                <input
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  placeholder="A"
                  value={block.code}
                  maxLength={5}
                  onChange={(e) => update(i, "code", e.target.value.toUpperCase())}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Kat Sayısı</label>
                <input
                  type="number"
                  min={1}
                  max={99}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  value={block.floors}
                  onChange={(e) => update(i, "floors", parseInt(e.target.value) || 1)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Kat Başına Daire</label>
                <input
                  type="number"
                  min={1}
                  max={99}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  value={block.flats_per_floor}
                  onChange={(e) => update(i, "flats_per_floor", parseInt(e.target.value) || 1)}
                />
              </div>
            </div>

            {block.code && (
              <div className="mt-3 flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-400">Örnek daire numaraları:</span>
                {previewUnits(block).map((u, j) => (
                  <span
                    key={j}
                    className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono"
                  >
                    {u}
                  </span>
                ))}
                <span className="text-xs text-gray-400 ml-1">
                  (Toplam: {block.floors * block.flats_per_floor} daire)
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={add}
        className="mt-4 flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
      >
        <span className="text-lg">+</span> Başka blok ekle
      </button>

      <div className="mt-6 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
        <strong>Toplam:</strong>{" "}
        {blocks.reduce((s, b) => s + b.floors * b.flats_per_floor, 0)} daire,{" "}
        {blocks.length} blok
      </div>
    </div>
  );
}

// ── Step 2 — Aidat Şablonu ────────────────────────────────────────────────────

function Step2Charge({
  enabled,
  template,
  onEnabledChange,
  onTemplateChange,
}: {
  enabled: boolean;
  template: ChargeTemplateItem;
  onEnabledChange: (v: boolean) => void;
  onTemplateChange: (t: ChargeTemplateItem) => void;
}) {
  const today = new Date();
  const defaultPeriod = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-800 mb-1">Aidat Şablonu (Opsiyonel)</h2>
      <p className="text-sm text-gray-500 mb-6">
        İstersen tüm yeni dairelere hemen bir borç kaydı oluşturabilirsin. Daha sonra da
        ekleyebilirsin.
      </p>

      <label className="flex items-center gap-3 cursor-pointer mb-6">
        <div
          onClick={() => onEnabledChange(!enabled)}
          className={`relative w-12 h-6 rounded-full transition-colors ${
            enabled ? "bg-blue-500" : "bg-gray-300"
          }`}
        >
          <div
            className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${
              enabled ? "translate-x-7" : "translate-x-1"
            }`}
          />
        </div>
        <span className="font-medium text-gray-700">
          {enabled ? "Borç şablonu ekle" : "Şimdilik borç ekleme"}
        </span>
      </label>

      {enabled && (
        <div className="grid grid-cols-2 gap-4 p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Borç Türü</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              placeholder="aidat"
              value={template.charge_type}
              onChange={(e) => onTemplateChange({ ...template, charge_type: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Tutar (₺)</label>
            <input
              type="number"
              min={0}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={template.amount}
              onChange={(e) =>
                onTemplateChange({ ...template, amount: parseFloat(e.target.value) || 0 })
              }
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Dönem (YYYY-MM)</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              placeholder={defaultPeriod}
              value={template.period}
              onChange={(e) => onTemplateChange({ ...template, period: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Vade Tarihi</label>
            <input
              type="date"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={template.due_date}
              onChange={(e) => onTemplateChange({ ...template, due_date: e.target.value })}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ── Step 3 — Özet ─────────────────────────────────────────────────────────────

function Step3Summary({
  blocks,
  chargeEnabled,
  template,
  result,
  loading,
  error,
  onSubmit,
}: {
  blocks: BlockSetupItem[];
  chargeEnabled: boolean;
  template: ChargeTemplateItem;
  result: OnboardingSetupResult | null;
  loading: boolean;
  error: string;
  onSubmit: () => void;
}) {
  const totalFlats = blocks.reduce((s, b) => s + b.floors * b.flats_per_floor, 0);

  if (result) {
    return (
      <div className="text-center py-8">
        <div className="text-5xl mb-4">🎉</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Kurulum Tamamlandı!</h2>
        <p className="text-gray-500 mb-6">{result.message}</p>
        <div className="flex justify-center gap-6 mb-8">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{result.blocks_created}</div>
            <div className="text-sm text-gray-500">Blok</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{result.flats_created}</div>
            <div className="text-sm text-gray-500">Daire</div>
          </div>
          {result.charges_created > 0 && (
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-600">{result.charges_created}</div>
              <div className="text-sm text-gray-500">Borç Kaydı</div>
            </div>
          )}
        </div>
        <div className="space-y-2 text-left max-w-xs mx-auto">
          {result.blocks.map((b) => (
            <div key={b.id} className="flex justify-between text-sm bg-gray-50 rounded-lg px-3 py-2">
              <span className="font-medium">{b.name} ({b.code})</span>
              <span className="text-gray-500">{b.flats_created} daire</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-800 mb-1">Özet & Onayla</h2>
      <p className="text-sm text-gray-500 mb-6">
        Aşağıdaki bilgileri kontrol et ve kurulumu başlat.
      </p>

      <div className="space-y-3 mb-6">
        <div className="bg-blue-50 rounded-xl p-4">
          <div className="text-sm font-semibold text-blue-700 mb-2">
            📦 {blocks.length} Blok · {totalFlats} Daire
          </div>
          {blocks.map((b, i) => (
            <div key={i} className="text-sm text-blue-800 flex justify-between">
              <span>
                {b.name || `Blok ${i + 1}`} ({b.code || "?"})
              </span>
              <span>
                {b.floors} kat × {b.flats_per_floor} daire = {b.floors * b.flats_per_floor} daire
              </span>
            </div>
          ))}
        </div>

        {chargeEnabled && (
          <div className="bg-amber-50 rounded-xl p-4 text-sm text-amber-800">
            <div className="font-semibold mb-1">💰 Borç Şablonu</div>
            <div>
              {template.charge_type} · {template.amount.toLocaleString("tr-TR")}₺ · {template.period}{" "}
              · Vade: {template.due_date}
            </div>
            <div className="text-xs mt-1 text-amber-600">
              → {totalFlats} daireye uygulanacak
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 rounded-lg p-3 text-sm mb-4">{error}</div>
      )}

      <button
        onClick={onSubmit}
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition"
      >
        {loading ? "Oluşturuluyor..." : "🚀 Kurulumu Başlat"}
      </button>
    </div>
  );
}

// ── Ana bileşen ───────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [blocks, setBlocks] = useState<BlockSetupItem[]>([{ ...EMPTY_BLOCK }]);
  const [chargeEnabled, setChargeEnabled] = useState(false);
  const today = new Date();
  const [template, setTemplate] = useState<ChargeTemplateItem>({
    charge_type: "aidat",
    amount: 0,
    period: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`,
    due_date: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-20`,
  });
  const [result, setResult] = useState<OnboardingSetupResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Validation
  const step1Valid = blocks.every(
    (b) => b.name.trim() && b.code.trim() && b.floors >= 1 && b.flats_per_floor >= 1,
  );
  const step2Valid =
    !chargeEnabled ||
    (template.charge_type.trim() && template.amount > 0 && template.period && template.due_date);

  const handleSubmit = async () => {
    const { token, siteId } = getAuth();
    setLoading(true);
    setError("");
    try {
      const res = await runOnboardingSetup(token, siteId, {
        blocks,
        charge_template: chargeEnabled ? template : null,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-gray-400 hover:text-gray-600 mb-4 flex items-center gap-1"
          >
            ← Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">🏗️ Hızlı Site Kurulumu</h1>
          <p className="text-gray-500 text-sm mt-1">
            Blokları, daireleri ve opsiyonel olarak ilk aidat dönemini birkaç adımda oluştur.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          {!result && <StepIndicator step={step} />}

          {step === 1 && (
            <Step1Blocks blocks={blocks} onChange={setBlocks} />
          )}
          {step === 2 && (
            <Step2Charge
              enabled={chargeEnabled}
              template={template}
              onEnabledChange={setChargeEnabled}
              onTemplateChange={setTemplate}
            />
          )}
          {step === 3 && (
            <Step3Summary
              blocks={blocks}
              chargeEnabled={chargeEnabled}
              template={template}
              result={result}
              loading={loading}
              error={error}
              onSubmit={handleSubmit}
            />
          )}

          {!result && (
            <div className="flex justify-between mt-8 pt-4 border-t border-gray-100">
              <button
                onClick={() => setStep((s) => s - 1)}
                disabled={step === 1}
                className="px-5 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-30 text-sm font-medium"
              >
                ← Geri
              </button>
              {step < 3 ? (
                <button
                  onClick={() => setStep((s) => s + 1)}
                  disabled={step === 1 ? !step1Valid : !step2Valid}
                  className="px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 text-sm font-medium"
                >
                  İleri →
                </button>
              ) : null}
            </div>
          )}

          {result && (
            <div className="flex justify-center gap-3 mt-6">
              <button
                onClick={() => router.push("/dashboard/blocks")}
                className="px-5 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm font-medium"
              >
                Bloklara Git
              </button>
              <button
                onClick={() => router.push("/dashboard")}
                className="px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium"
              >
                Dashboard'a Dön
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
