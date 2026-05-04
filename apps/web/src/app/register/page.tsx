"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { fetchCurrentUser, loginWithPassword, registerAdmin } from "@/lib/api";
import { saveSession } from "@/lib/auth-storage";

export default function RegisterPage() {
  const router = useRouter();
  const [siteName, setSiteName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await registerAdmin({
        site_name: siteName,
        full_name: fullName,
        email,
        password,
      });

      const loginResponse = await loginWithPassword(email, password);
      const me = await fetchCurrentUser(loginResponse.access_token);

      saveSession(loginResponse.access_token, me.site_id);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kayıt sırasında bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-10">
      <main className="mx-auto w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-zinc-900">Site Yöneticisi Kaydı</h1>
        <p className="mt-2 text-sm text-zinc-600">Yeni bir site oluşturup admin hesabı açabilirsin.</p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="siteName">
              Site adı
            </label>
            <input
              id="siteName"
              required
              value={siteName}
              onChange={(event) => setSiteName(event.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="fullName">
              Ad Soyad
            </label>
            <input
              id="fullName"
              required
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="email">
              E-posta
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="password">
              Şifre
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          </div>

          {error ? <p className="text-sm text-rose-600">{error}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Kayıt oluşturuluyor..." : "Kayıt Ol"}
          </button>
        </form>

        <p className="mt-4 text-sm text-zinc-600">
          Zaten hesabın var mı?{" "}
          <Link href="/login" className="font-medium text-indigo-600">
            Giriş yap
          </Link>
        </p>
      </main>
    </div>
  );
}
