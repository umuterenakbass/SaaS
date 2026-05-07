"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Block, Flat, createFlat, deleteFlat, listBlocks, listFlats } from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function FlatsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [blocks, setBlocks] = useState<Block[]>([]);
  const [flats, setFlats] = useState<Flat[]>([]);
  const [blockId, setBlockId] = useState("");
  const [unitNo, setUnitNo] = useState("");
  const [floor, setFloor] = useState(0);
  const [status, setStatus] = useState<"active" | "inactive">("active");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!token || !siteId) {
        router.replace("/login");
        return;
      }

      try {
        const loadedBlocks = await listBlocks(token, siteId);
        setBlocks(loadedBlocks);
        if (loadedBlocks[0]) setBlockId(loadedBlocks[0].id);
        setFlats(await listFlats(token, siteId));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Daireler yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId) return;

    try {
      await createFlat(token, siteId, {
        block_id: blockId,
        unit_no: unitNo,
        floor,
        status,
      });
      setUnitNo("");
      setFloor(0);
      setFlats(await listFlats(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Daire oluşturulamadı.");
    }
  };

  const handleDelete = async (flatId: string) => {
    if (!token || !siteId) return;

    try {
      await deleteFlat(token, siteId, flatId);
      setFlats(await listFlats(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Daire silinemedi.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Daire Yönetimi</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <form onSubmit={handleCreate} className="grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-5">
        <select
          value={blockId}
          onChange={(event) => setBlockId(event.target.value)}
          className="rounded-lg border border-zinc-300 !bg-white px-3 py-2 text-base font-semibold !text-zinc-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          style={{ colorScheme: "light" }}
        >
          {blocks.map((block) => (
            <option value={block.id} key={block.id}>
              {block.name} ({block.code})
            </option>
          ))}
        </select>
        <input
          placeholder="Daire No"
          value={unitNo}
          onChange={(event) => setUnitNo(event.target.value)}
          className="rounded-lg border border-zinc-300 !bg-white px-3 py-2 text-base font-semibold !text-zinc-900 caret-zinc-900 placeholder:font-medium !placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          style={{ colorScheme: "light" }}
          required
        />
        <input
          type="number"
          placeholder="Kat"
          value={floor}
          onChange={(event) => setFloor(Number(event.target.value))}
          className="rounded-lg border border-zinc-300 !bg-white px-3 py-2 text-base font-semibold !text-zinc-900 caret-zinc-900 placeholder:font-medium !placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          style={{ colorScheme: "light" }}
        />
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value as "active" | "inactive")}
          className="rounded-lg border border-zinc-300 !bg-white px-3 py-2 text-base font-semibold !text-zinc-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          style={{ colorScheme: "light" }}
        >
          <option value="active">active</option>
          <option value="inactive">inactive</option>
        </select>
        <button
          type="submit"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          Daire Ekle
        </button>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="space-y-2">
        {flats.map((flat) => (
          <article
            key={flat.id}
            className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3"
          >
            <div>
              <p className="font-medium text-zinc-900">
                Daire {flat.unit_no} - Kat {flat.floor}
              </p>
              <p className="text-sm text-zinc-500">
                Block: {blocks.find((item) => item.id === flat.block_id)?.name ?? flat.block_id}
              </p>
            </div>
            <button
              onClick={() => void handleDelete(flat.id)}
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
