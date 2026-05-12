"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Flat,
  ResidentRelation,
  UserResponse,
  createResidentRelation,
  deleteResidentRelation,
  fetchCurrentUser,
  listFlats,
  listResidentRelations,
  listUsers,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

export default function ResidentsPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [relations, setRelations] = useState<ResidentRelation[]>([]);
  const [flats, setFlats] = useState<Flat[]>([]);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [userId, setUserId] = useState("");
  const [flatId, setFlatId] = useState("");
  const [relationType, setRelationType] = useState<"owner" | "tenant">("owner");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!token || !siteId) {
        router.replace("/login");
        return;
      }

      try {
        const me = await fetchCurrentUser(token);
        const loadedFlats = await listFlats(token, siteId);
        const loadedRelations = await listResidentRelations(token, siteId);
        const loadedUsers = await listUsers(token, siteId);

        setUserId(me.id);
        setFlats(loadedFlats);
        setFlatId(loadedFlats[0]?.id ?? "");
        setRelations(loadedRelations);
        setUsers(loadedUsers);
      } catch (err) {
        setError(err instanceof Error ? err.message : "İlişkiler yüklenemedi.");
      }
    };

    void load();
  }, [router, siteId, token]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !siteId) return;

    try {
      await createResidentRelation(token, siteId, {
        user_id: userId,
        flat_id: flatId,
        relation_type: relationType,
        start_date: startDate,
        end_date: endDate || null,
        is_primary: isPrimary,
      });
      setRelations(await listResidentRelations(token, siteId));
      setEndDate("");
      setIsPrimary(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "İlişki oluşturulamadı.");
    }
  };

  const handleDelete = async (relationId: string) => {
    if (!token || !siteId) return;

    try {
      await deleteResidentRelation(token, siteId, relationId);
      setRelations(await listResidentRelations(token, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "İlişki silinemedi.");
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl space-y-6 bg-zinc-50 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900">Sakin - Daire İlişkileri</h1>
        <Link href="/dashboard" className="text-sm font-medium text-indigo-600">
          Dashboard
        </Link>
      </header>

      <form onSubmit={handleCreate} className="grid gap-3 rounded-xl bg-white p-4 shadow-sm md:grid-cols-6">
        <select
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          required
        >
          <option value="">Kullanıcı seçin…</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.full_name ? `${user.full_name} (${user.email})` : user.email} — {user.role}
            </option>
          ))}
        </select>

        <select
          value={flatId}
          onChange={(event) => setFlatId(event.target.value)}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          required
        >
          {flats.map((flat) => (
            <option key={flat.id} value={flat.id}>
              {flat.unit_no} ({flat.id.slice(0, 6)})
            </option>
          ))}
        </select>

        <select
          value={relationType}
          onChange={(event) => setRelationType(event.target.value as "owner" | "tenant")}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
        >
          <option value="owner">owner</option>
          <option value="tenant">tenant</option>
        </select>

        <input
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          required
        />

        <input
          type="date"
          value={endDate}
          onChange={(event) => setEndDate(event.target.value)}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
        />

        <button
          type="submit"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          İlişki Ekle
        </button>

        <label className="col-span-full flex items-center gap-2 text-sm text-zinc-600">
          <input
            type="checkbox"
            checked={isPrimary}
            onChange={(event) => setIsPrimary(event.target.checked)}
          />
          Primary ilişki
        </label>
      </form>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="space-y-2">
        {relations.map((relation) => (
          <article
            key={relation.id}
            className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3"
          >
            <div>
              <p className="font-medium text-zinc-900">
                {relation.relation_type} | flat: {relation.flat_id.slice(0, 8)} |{" "}
                {(() => {
                  const u = users.find((x) => x.id === relation.user_id);
                  return u ? (u.full_name ?? u.email) : relation.user_id.slice(0, 8);
                })()}
              </p>
              <p className="text-sm text-zinc-500">
                {relation.start_date} - {relation.end_date ?? "devam ediyor"}
              </p>
            </div>
            <button
              onClick={() => void handleDelete(relation.id)}
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
