"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { fetchCurrentUser, fetchTenantContext } from "@/lib/api";
import { clearSession, getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");
  const [siteId, setSiteId] = useState<string>("");
  const [role, setRole] = useState<string>("");

  useEffect(() => {
    const run = async () => {
      const token = getAccessToken();
      const storedSiteId = getSiteId();

      if (!token || !storedSiteId) {
        router.replace("/login");
        return;
      }

      try {
        const me = await fetchCurrentUser(token);
        const tenant = await fetchTenantContext(token, storedSiteId);

        setUserEmail(me.email);
        setSiteId(tenant.site_id);
        setRole(tenant.role);
      } catch (err) {
        clearSession();
        setError(err instanceof Error ? err.message : "Dashboard yüklenemedi.");
        router.replace("/login");
        return;
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [router]);

  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };

  if (loading) {
    return <div className="p-8 text-sm text-zinc-600">Dashboard yükleniyor...</div>;
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-10">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <header className="rounded-2xl bg-indigo-600 p-6 text-white shadow-sm">
          <h1 className="text-2xl font-semibold">Yönetici Dashboard</h1>
          <p className="mt-2 text-sm text-indigo-100">Sprint 2 auth + tenant doğrulama aktif.</p>
        </header>

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <section className="grid gap-4 md:grid-cols-3">
          <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-zinc-500">Kullanıcı</p>
            <p className="mt-1 font-medium text-zinc-900">{userEmail}</p>
          </article>
          <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-zinc-500">Site Kimliği</p>
            <p className="mt-1 break-all font-medium text-zinc-900">{siteId}</p>
          </article>
          <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-zinc-500">Rol</p>
            <p className="mt-1 font-medium capitalize text-zinc-900">{role}</p>
          </article>
        </section>

        <section className="flex flex-wrap gap-3">
          <Link
            href="/dashboard/blocks"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
          >
            Blok Yönetimi
          </Link>
          <Link
            href="/dashboard/flats"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
          >
            Daire Yönetimi
          </Link>
          <Link
            href="/dashboard/residents"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
          >
            Sakin İlişkileri
          </Link>
          <Link
            href="/dashboard/charges"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
          >
            Borç Yönetimi
          </Link>
          <Link
            href="/dashboard/payments"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
          >
            Ödeme Yönetimi
          </Link>
          <Link
            href="/dashboard/ledger"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
          >
            Ekstre / Bakiye
          </Link>
        </section>

        <button
          onClick={handleLogout}
          className="w-fit rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100"
        >
          Çıkış Yap
        </button>
      </main>
    </div>
  );
}
