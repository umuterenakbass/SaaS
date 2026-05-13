"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Announcement,
  AnnouncementCreate,
  Block,
  createAnnouncement,
  deleteAnnouncement,
  listAnnouncements,
  listBlocks,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function AnnouncementsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [blockId, setBlockId] = useState("");
  const [isPinned, setIsPinned] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token || !siteId) { router.replace("/login"); return; }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load() {
    try {
      const [anns, bls] = await Promise.all([
        listAnnouncements(token!, siteId!),
        listBlocks(token!, siteId!),
      ]);
      setAnnouncements(anns);
      setBlocks(bls);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yüklenemedi.");
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!token || !siteId) return;
    setSubmitting(true);
    try {
      const payload: AnnouncementCreate = {
        title,
        body,
        block_id: blockId || null,
        is_pinned: isPinned,
        is_published: true,
      };
      await createAnnouncement(token, siteId, payload);
      setTitle(""); setBody(""); setBlockId(""); setIsPinned(false);
      setAnnouncements(await listAnnouncements(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Duyuru oluşturulamadı.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!token || !siteId) return;
    try {
      await deleteAnnouncement(token, siteId, id);
      setAnnouncements((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Silinemedi.");
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Duyurular</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      {/* Create Form */}
      <form
        onSubmit={(e) => void handleCreate(e)}
        className="space-y-3 rounded-xl bg-white p-5 shadow-sm"
      >
        <h2 className="text-sm font-semibold text-zinc-700">Yeni Duyuru</h2>
        <input
          type="text"
          placeholder="Başlık"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
        />
        <textarea
          placeholder="Duyuru metni…"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          rows={4}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm"
        />
        <div className="flex flex-wrap gap-3">
          <select
            value={blockId}
            onChange={(e) => setBlockId(e.target.value)}
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          >
            <option value="">Tüm site</option>
            {blocks.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm text-zinc-600">
            <input
              type="checkbox"
              checked={isPinned}
              onChange={(e) => setIsPinned(e.target.checked)}
            />
            Sabit tut (pinned)
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {submitting ? "Gönderiliyor…" : "Yayınla"}
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {/* List */}
      <section className="space-y-3">
        {announcements.length === 0 && (
          <p className="text-sm text-zinc-400">Henüz duyuru yok.</p>
        )}
        {announcements.map((ann) => (
          <article
            key={ann.id}
            className="relative rounded-xl border border-zinc-200 bg-white p-4 shadow-sm"
          >
            {ann.is_pinned && (
              <span className="absolute right-3 top-3 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                📌 Sabit
              </span>
            )}
            <p className="font-semibold text-zinc-900">{ann.title}</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-zinc-600">{ann.body}</p>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-zinc-400">
                {ann.block_id
                  ? `📍 ${blocks.find((b) => b.id === ann.block_id)?.name ?? "Belirli blok"}`
                  : "📢 Tüm site"}{" "}
                · {new Date(ann.created_at).toLocaleDateString("tr-TR")}
              </span>
              <button
                onClick={() => void handleDelete(ann.id)}
                className="rounded-lg border border-rose-200 px-3 py-1 text-xs text-rose-600 hover:bg-rose-50"
              >
                Sil
              </button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
