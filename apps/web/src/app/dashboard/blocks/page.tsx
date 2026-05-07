"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Block, createBlock, deleteBlock, listBlocks } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function BlocksPage() {
  const router = useRouter();
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  const token = getAccessToken();
  const siteId = getSiteId();

  useEffect(() => {
    const load = async () => {
      if (!token || !siteId) {
        router.replace("/login");
        return;
      }

      try {
        setBlocks(await listBlocks(token, siteId));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Bloklar yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId) return;

    try {
      await createBlock(token, siteId, { name, code });
      setName("");
      setCode("");
      setBlocks(await listBlocks(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blok oluşturulamadı.");
    }
  };

  const handleDelete = async (blockId: string) => {
    if (!token || !siteId) return;
    try {
      await deleteBlock(token, siteId, blockId);
      setBlocks(await listBlocks(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blok silinemedi.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Blok Yönetimi</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <form onSubmit={handleCreate} className="grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-3">
        <input
          placeholder="Blok adı"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="rounded-lg border border-zinc-300 !bg-white px-3 py-2 text-base font-semibold !text-zinc-900 caret-zinc-900 placeholder:font-medium !placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          style={{ colorScheme: "light" }}
          required
        />
        <input
          placeholder="Kod (A, B...)"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          className="rounded-lg border border-zinc-300 !bg-white px-3 py-2 text-base font-semibold !text-zinc-900 caret-zinc-900 placeholder:font-medium !placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          style={{ colorScheme: "light" }}
          required
        />
        <button
          type="submit"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          Blok Ekle
        </button>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="space-y-2">
        {blocks.map((block) => (
          <article
            key={block.id}
            className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3"
          >
            <div>
              <p className="font-medium text-zinc-900">{block.name}</p>
              <p className="text-sm text-zinc-500">Kod: {block.code}</p>
            </div>
            <button
              onClick={() => void handleDelete(block.id)}
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
