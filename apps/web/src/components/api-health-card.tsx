"use client";

import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, type ApiHealthResponse, fetchApiHealth } from "@/lib/api";

type FetchState = "idle" | "loading" | "success" | "error";

export function ApiHealthCard() {
  const [state, setState] = useState<FetchState>("idle");
  const [health, setHealth] = useState<ApiHealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setState("loading");
      setError(null);

      try {
        const result = await fetchApiHealth();
        if (!cancelled) {
          setHealth(result);
          setState("success");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
          setState("error");
        }
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, []);

  const statusPill = useMemo(() => {
    if (state === "success") {
      return "bg-emerald-100 text-emerald-700";
    }

    if (state === "error") {
      return "bg-rose-100 text-rose-700";
    }

    return "bg-amber-100 text-amber-700";
  }, [state]);

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">API Health</h2>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusPill}`}>
          {state === "success" ? "healthy" : state === "error" ? "unreachable" : "checking"}
        </span>
      </div>

      <div className="space-y-2 text-sm text-zinc-700">
        <p>
          <span className="font-medium">Endpoint:</span> {API_BASE_URL}/api/v1/health
        </p>
        {health ? (
          <>
            <p>
              <span className="font-medium">Service:</span> {health.service}
            </p>
            <p>
              <span className="font-medium">Version:</span> {health.version}
            </p>
            <p>
              <span className="font-medium">Environment:</span> {health.env}
            </p>
          </>
        ) : (
          <p className="text-zinc-500">
            {state === "error"
              ? `Error: ${error}`
              : "Backend response bekleniyor (ilk açılışta birkaç saniye sürebilir)."}
          </p>
        )}
      </div>
    </section>
  );
}
