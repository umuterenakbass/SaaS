import { ApiHealthCard } from "@/components/api-health-card";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-10 text-zinc-900">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8">
        <header className="rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 p-8 text-white shadow-lg">
          <p className="mb-2 text-sm font-medium uppercase tracking-wide text-indigo-100">
            Site & Apartman Yönetim SaaS
          </p>
          <h1 className="text-3xl font-semibold">Yönetici Dashboard (MVP Başlangıç)</h1>
          <p className="mt-3 max-w-3xl text-sm text-indigo-100">
            Sprint 1 kapsamında frontend iskeleti hazırlandı. Sonraki sprintlerde site/blok/daire,
            sakin, aidat ve finans modülleri bu panel üzerinden yönetilecek.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-zinc-500">Toplam Site</p>
            <p className="mt-2 text-2xl font-semibold">-</p>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-zinc-500">Aylık Tahakkuk</p>
            <p className="mt-2 text-2xl font-semibold">-</p>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-zinc-500">Tahsilat Oranı</p>
            <p className="mt-2 text-2xl font-semibold">-</p>
          </div>
        </section>

        <section className="flex flex-wrap gap-3">
          <Link
            href="/register"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Site Yöneticisi Kaydı
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100"
          >
            Giriş Yap
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100"
          >
            Dashboard&apos;a Git
          </Link>
        </section>

        <ApiHealthCard />

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold">Sprint 1 Notu</h2>
          <p className="text-sm text-zinc-600">
            Bu ekran, API-first geliştirme yaklaşımıyla ilerleyen MVP için başlangıç yüzeyidir.
            Kimlik doğrulama, tenant bağlamı ve RBAC Sprint 2’de eklenecek.
          </p>
        </section>
      </main>
    </div>
  );
}
